"""Read-only constraint attribution, not terrain authoring or visual acceptance.

Certificates are conditional on the current pilot's full fixed_C and unchanged
water/native grid. They do not grant permission to remove those constraints.
"""
import os
import time
STARTED = time.monotonic()
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '1'
import argparse
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import threading

HERE = Path(__file__).resolve().parent
MAX_SECONDS = 120
MAX_BYTES = 2*1024**3


def memory():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
            (k, ctypes.c_size_t) for k in ('PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    c = Counters(); c.cb = ctypes.sizeof(c)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return dict(pid=os.getpid(), parent_pid=os.getppid(), seconds=time.monotonic()-STARTED,
                peak_resident_bytes=c.PeakWorkingSetSize, peak_commit_bytes=c.PeakPagefileUsage)


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def bounded(output):
    stop = threading.Event()
    def watcher():
        while not stop.wait(.1):
            try:
                m = memory()
                exceeded = m['seconds'] > MAX_SECONDS or max(m['peak_resident_bytes'], m['peak_commit_bytes']) > MAX_BYTES
                if exceeded:
                    dump(output/'resource-stop.json', dict(status='INCONCLUSIVE_RESOURCE', measurement=m))
                    os._exit(3)  # This interpreter only; no shared process management.
            except Exception as e:
                dump(output/'resource-stop.json', dict(status='INCONCLUSIVE_MEASUREMENT', reason=str(e)))
                os._exit(3)
    threading.Thread(target=watcher, daemon=True).start()
    return stop


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod); return mod


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4 << 20), b''): h.update(block)
    return h.hexdigest()


def require(ok, reason):
    if not bool(ok): raise ValueError(reason)


def ownership(cells, owners, n):
    """S6(c2v(cell)) for all owners, without reflecting or overwriting cells."""
    import numpy as np
    cells, owners = np.asarray(cells, int), np.asarray(owners, np.int32)
    require(cells.shape == (len(owners), 2) and ((cells >= 0) & (cells < n-1)).all() and
            (owners >= 0).all(), 'ownership_input')
    low = np.full(n*n, np.iinfo(np.int32).max, np.int32); high = np.full(n*n, -1, np.int32)
    offsets = {(a+dr, b+dc) for a in (0, 1) for b in (0, 1)
               for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1))}
    for dr, dc in offsets:
        r, c = cells[:, 0]+dr, cells[:, 1]+dc
        valid = (r >= 0) & (c >= 0) & (r < n) & (c < n)
        v = r[valid]*n+c[valid]
        np.minimum.at(low, v, owners[valid]); np.maximum.at(high, v, owners[valid])
    return low.reshape(n, n), high.reshape(n, n)


def foreign(low, high, owner):
    return (high >= 0) & ((low != high) | (low != owner))


def classify(points, closed, full_fixed, degree_two, sea_only, screen, budget=None):
    if not closed: return dict(status='NOT_EVALUATED_OPEN')
    if not sea_only: return dict(status='OUT_OF_SCOPE_POND')
    if not full_fixed: return dict(status='PARTIAL_CONSTRAINTS_INCONCLUSIVE')
    if not degree_two: return dict(status='INCONCLUSIVE_EDGE_INCIDENCE')
    if len(points)-1 > 512: return dict(status='NOT_EVALUATED_COST')
    cost = (len(points)-1)**2
    if budget is not None:
        if cost > budget['pairs_left']: return dict(status='NOT_EVALUATED_COST')
        budget['pairs_left'] -= cost
    try: metrics = screen(points)
    except ValueError as e: return dict(status='INCONCLUSIVE_DEGENERATE', reason=str(e))
    conflict = metrics['maximum_abrupt_turns'] > 0 or metrics['maximum_long_straights'] > 0
    return dict(status='FROZEN_SCREEN_CONFLICT' if conflict else 'FROZEN_SCREEN_COMPATIBLE',
                metrics=metrics, conditions='Current fixed_C, all three vertices of every face, fixed water/grid; no permission to edit.')


def support_at(h, row, col, kind):
    """Independent local enumeration of every native shape containing a vertex."""
    import numpy as np
    shapes = (((0, 0),), ((0, 0), (1, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 1)),
              ((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (1, 1)))
    nb = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1))
    candidates = []
    for shape_id, p in enumerate(shapes):
        ring = sorted({(a+dr, b+dc) for a, b in p for dr, dc in nb} - set(p))
        for member in p:
            anchor = (row-member[0], col-member[1])
            if not (0 <= anchor[0] < len(h) and 0 <= anchor[1] < len(h)): continue
            positions = [ [(anchor[0]+dr, anchor[1]+dc) for dr, dc in offsets] for offsets in (p, ring)]
            values = [np.array([h[np.clip(r, 0, len(h)-1), np.clip(c, 0, len(h)-1)] for r, c in coords]) for coords in positions]
            score = values[0].min()-values[1].max() if kind == 'peak' else values[1].min()-values[0].max()
            candidates.append(dict(value=float(score), shape_id=shape_id, anchor=list(anchor), shape=positions[0], ring=positions[1]))
    best = max(x['value'] for x in candidates)
    return dict(value=best, witnesses=[x for x in candidates if x['value'] == best])


def diagnose(root, output):
    import numpy as np
    from scipy.ndimage import binary_dilation
    source = root/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
    census = root/'native-shore-census-20261028/native-shore.npz'
    footprint = root/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz'
    candidate = root/'small-native-water-candidate-20261028/candidate.npz'
    domain_path = root/'small-native-water-setup-fixed-20261028/domain.npz'
    expected = {source:'815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40',
                census:'b6612009ff531ef2f3932240ea52cf0660bce97f7904b7d667f962ce0fd95847',
                footprint:'084171b0e29df5c220f9d5aab42a3dc683a2f70a07579f08cd930dfd109e716b',
                candidate:'73b8fa8abeef6b213e3811c282787f9499554bc5be1aef29cfb4b79080a41101',
                domain_path:'427b953890fd78f61256d10b3bbd17a955ecef989b2db616c61cad86484dcdc8'}
    context_path = root/'small-native-water-setup-fixed-20261028/context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    expected[context_path] = sha(context_path)
    for name in ('small_native_water_pilot_ev112.py', 'verify_small_native_water_pilot_ev112.py',
                 'verify_native_shore_census_ev112.py', 'shape_patterns_ev112.py'):
        path = HERE/name
        expected[path] = next(digest for key, digest in context['source_hashes'].items() if Path(key).name == name)
    shore_path = HERE.parent/'water/shore_ramp_v31.py'
    expected[shore_path] = next(digest for key, digest in context['source_hashes'].items() if Path(key).name == shore_path.name)
    expected[Path(__file__).resolve()] = sha(__file__)
    inventory = HERE.parents[1]/'evidence/v31-pond-layer-2026-10-13/bridges/crossings-ev106.json'
    expected[inventory] = context['source_hashes'][r'evidence\v31-pond-layer-2026-10-13\bridges\crossings-ev106.json']
    for path, digest in expected.items(): require(sha(path) == digest, 'input_hash_'+str(path))
    a = module('constraint_author_reference', HERE/'small_native_water_pilot_ev112.py')
    v = module('constraint_screen', HERE/'verify_small_native_water_pilot_ev112.py')
    t, s, saved = (a.arrays(p) for p in (source, census, domain_path))
    with np.load(footprint) as f: fp = {key:f[key] for key in ('plane', 'env_plane')}
    h = t['heights']; n = len(h); categories = list(a.PROTECTED)+['model_buffer', 'pond_envelope', 'crossing60']
    bits = np.zeros(h.shape, np.uint32)
    for i, name in enumerate(a.PROTECTED): bits[t[name]] |= np.uint32(1 << i)
    mask = np.zeros(h.shape, bool)
    for name in t:
        if name.startswith(('v31_bridge_', 'v31_lattice')) or name == 'v31_kit':
            mask |= binary_dilation(t[name], np.ones((3, 3), bool))
    bits[mask] |= np.uint32(1 << categories.index('model_buffer'))
    bits[a.shore.c2v(np.isfinite(fp['plane']) | np.isfinite(fp['env_plane']))] |= np.uint32(1 << categories.index('pond_envelope'))
    for crossing in json.loads(inventory.read_text(encoding='utf-8')):
        x, z = crossing['x'], crossing['z']
        r0, r1 = max(0, int((12282-z-60)//6)), min(n, int((12282-z+60)//6)+2)
        c0, c1 = max(0, int((x-60)//6)), min(n, int((x+60)//6)+2)
        rr, cc = np.mgrid[r0:r1, c0:c1]
        close = np.hypot(cc*6-x, 12282-rr*6-z) < 60
        bits[rr[close], cc[close]] |= np.uint32(1 << categories.index('crossing60'))
    owner = np.full(len(s['p']), -1, np.int32)
    for i in range(len(s['closed'])):
        owner[s['chain_order'][s['chain_offsets'][i]:s['chain_offsets'][i+1]]] = i
    require((owner >= 0).all(), 'owner_coverage')
    low, high = ownership(s['cell'], owner, n)
    require(np.array_equal((bits != 0) | foreign(low, high, 769), saved['fixed']), 'pilot_fixed_reconstruction')
    tri = np.array([[[0, 0], [0, 1], [1, 1]], [[0, 0], [1, 0], [1, 1]]])[s['tri']]
    rr = s['cell'][:, 0, None]+tri[:, :, 0]; cc = s['cell'][:, 1, None]+tri[:, :, 1]
    face_base = bits[rr, cc]; face_other = foreign(low[rr, cc], high[rr, cc], owner[:, None])
    face_fixed = (face_base != 0) | face_other
    unique_keys, counts = np.unique(s['key'], return_counts=True)
    rows = []; witnesses = {}; budget = dict(pairs_left=2_000_000)
    for i, closed in enumerate(s['closed']):
        ids = s['chain_order'][s['chain_offsets'][i]:s['chain_offsets'][i+1]]
        p = s['chain_points'][s['point_offsets'][i]:s['point_offsets'][i+1]]
        keys = s['chain_keys'][s['point_offsets'][i]:s['point_offsets'][i+1]]
        ka, kb = keys//(n*n), keys % (n*n)
        pin = ((bits.ravel()[ka] != 0) | foreign(low.ravel()[ka], high.ravel()[ka], i)) & ((bits.ravel()[kb] != 0) | foreign(low.ravel()[kb], high.ravel()[kb], i))
        k = keys[:-1] if closed else keys
        incidence = bool((counts[np.searchsorted(unique_keys, k)] == 2).all())
        whole = bool(face_fixed[ids].all()); sea = not s['pond'][ids].any() and bool((s['lev'][ids] == .75).all())
        row = dict(chain=i, segments=len(ids), closed=bool(closed), fixed_edge_fraction=float(pin[:-1].mean() if closed else pin.mean()),
                   fully_fixed_faces=int(face_fixed[ids].all(1).sum()), base_fixed_faces=int((face_base[ids] != 0).all(1).sum()),
                   raw_fixed_turns=[], classification=classify(p, bool(closed), whole, incidence, sea, v.closed_screen, budget))
        if closed and len(p) > 3:
            edges = np.diff(p, axis=0); lengths = np.linalg.norm(edges, axis=1)
            if (lengths > 1e-8).all():
                unit = edges/lengths[:, None]; angles = np.degrees(np.arccos(np.clip((unit*np.roll(unit, 1, axis=0)).sum(1), -1, 1)))
                fixed_corner = pin[:-1] & np.roll(pin[:-1], 1) & np.roll(pin[:-1], -1)
                row['raw_fixed_turns'] = [dict(index=int(j), xz=p[j].tolist(), degrees=float(angles[j])) for j in np.flatnonzero(fixed_corner & (angles >= 45))]
        rows.append(row)
        if i in (292, 769):
            faces = []
            for j in ids:
                faces.append(dict(face=int(j), cell=s['cell'][j].tolist(), triangle=int(s['tri'][j]), vertices=[
                    dict(row=int(r), col=int(c), height=float(h[r, c]), base=[name for bit, name in enumerate(categories) if int(bits[r, c]) & (1 << bit)],
                         other_chain=bool(face_other[j, k])) for k, (r, c) in enumerate(zip(rr[j], cc[j]))]))
            witnesses[str(i)] = dict(summary=row, faces=faces)
    with np.load(candidate) as f: after = f['heights']
    raw_regressions = root/'small-native-water-rejection-diagnostic-20261028/prominence-regressions.json'
    expected[raw_regressions] = sha(raw_regressions)
    distance = {(int(r), int(c)):float(d) for r, c, d in zip(saved['rows'].ravel(), saved['cols'].ravel(), saved['distance'].ravel())}
    supports = []
    for item in json.loads(raw_regressions.read_text()):
        row, col, kind = item['row'], item['col'], item['kind']
        old, new = support_at(h, row, col, kind), support_at(after, row, col, kind)
        require(old['value'] == item['before'] and new['value'] == item['after'], 'prominence_witness_value')
        for witness in new['witnesses']:
            coords = sorted({(int(np.clip(r, 0, n-1)), int(np.clip(c, 0, n-1))) for r, c in witness['shape']+witness['ring']})
            witness['support'] = [dict(row=r, col=c, before=float(h[r, c]), after=float(after[r, c]), changed=bool(h[r, c] != after[r, c]),
                                      distance_m=distance.get((r, c)), side=int(saved['side'][r, c]), fixed=bool(saved['fixed'][r, c])) for r, c in coords]
        supports.append(dict(regression=item, before=old, after=new))
    require(len(rows) == 1030 and len(supports) == 9, 'diagnostic_coverage')
    require(rows[769]['classification']['status'] == 'PARTIAL_CONSTRAINTS_INCONCLUSIVE' and len(rows[769]['raw_fixed_turns']) >= 2,
            'real_negative_control_769')
    for p, digest in expected.items(): require(sha(p) == digest, 'input_changed_during_diagnostic')
    summary = {status:sum(x['classification']['status'] == status for x in rows) for status in sorted({x['classification']['status'] for x in rows})}
    dump(output/'chains.json', rows); dump(output/'case-witnesses.json', witnesses); dump(output/'prominence-supports.json', supports)
    np.savez_compressed(output/'face-protection.npz', owner=owner, vertex_rows=rr, vertex_cols=cc, base_bits=face_base, other_chain=face_other)
    dump(output/'inputs.json', {str(p):v for p, v in expected.items()})
    return dict(status='DIAGNOSTIC_COMPLETE_NOT_MAP_ACCEPTANCE', chains=len(rows), classification_counts=summary,
                pilot_fixed_mask_exact=True, verified_prominence_supports=len(supports), screen_budget=budget,
                cases={key:val['summary'] for key, val in witnesses.items()},
                limitations=['Certificates conditional on current pilot constraints; no global impossibility.',
                             'Open, partial, pond and cost-excluded contours are not accepted.',
                             'No terrain generation, no MLOD, no build, no DayZ or new performance comparison.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('root', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    stop = bounded(args.output)
    try:
        result = diagnose(args.root, args.output); result['resources'] = memory()
        require(result['resources']['seconds'] <= MAX_SECONDS and
                max(result['resources']['peak_commit_bytes'], result['resources']['peak_resident_bytes']) <= MAX_BYTES, 'resource_budget')
        stop.set()
        dump(args.output/'report.json', result); print(json.dumps(result))
    except Exception as error:
        dump(args.output/'failure.json', dict(status='INCONCLUSIVE_FAILURE', error_type=type(error).__name__, reason=str(error)))
        raise
    finally: stop.set()
