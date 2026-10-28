"""Read-only contact census on reference road axes and nominal native water.

Not a bridge inventory, not proof of paved or traversable roads. No generated
bridge list participates in discovery. Full submerged intervals are retained.
"""
from pathlib import Path
import time
STARTED=time.monotonic()
import argparse
from collections import Counter
import importlib.util
import json
import math
import numpy as np

HERE = Path(__file__).resolve().parent
GRID = 6.
TOL = 1e-9
OFF = ((0, 0), (0, 1), (1, 0), (1, 1))
TRI = ((0, 1, 3), (0, 2, 3))


def require(ok, reason):
    if not bool(ok): raise ValueError(reason)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def cuts(a, b, top):
    a, b = np.asarray(a, float), np.asarray(b, float)
    require(a.shape == b.shape == (2,) and np.isfinite([a, b]).all(), 'road_nonfinite')
    require(((a >= 0) & (a <= top) & (b >= 0) & (b <= top)).all(), 'road_outside_grid')
    require(np.linalg.norm(b-a) > 0, 'zero_road_edge')
    out = {0., 1.}
    for start, end in ((a[0], b[0]), (a[1], b[1]), (a.sum(), b.sum())):
        if start == end: continue
        for k in range(math.floor(min(start, end)/GRID)+1, math.ceil(max(start, end)/GRID)):
            t = (k*GRID-start)/(end-start)
            if 0 < t < 1: out.add(float(t))
    return sorted(out)


def bary(point, row, col, tri, top):
    u, v = point[0]/GRID-col, (top-point[1])/GRID-row
    return np.array((1-u, u-v, v) if tri == 0 else (1-v, v-u, u))


def faces_at(point, n, top):
    r, c = (top-point[1])/GRID, point[0]/GRID
    rows, cols = {math.floor(r)}, {math.floor(c)}
    # Floating-point incidence tolerance only. Both sides remain in the report;
    # wet/dry signs themselves are never rounded or given a tolerance.
    if abs(r-round(r)) <= 1e-12: rows.update((round(r)-1, round(r)))
    if abs(c-round(c)) <= 1e-12: cols.update((round(c)-1, round(c)))
    out = []
    for row in sorted(rows):
        for col in sorted(cols):
            if not (0 <= row < n-1 and 0 <= col < n-1): continue
            for ti in (0, 1):
                if bary(point, row, col, ti, top).min() >= -1e-12: out.append((row, col, ti))
    require(out, 'no_incident_face'); return out


def intervals(d0, d1, lo, hi):
    if d0 == d1 == 0: return [], [], True
    roots = []
    if (d0 < 0 < d1) or (d1 < 0 < d0):
        root = lo+(hi-lo)*d0/(d0-d1); roots.append(float(root))
        wet = [(lo, root)] if d0 < 0 else [(root, hi)]
    elif d0 < 0 or d1 < 0: wet = [(lo, hi)]
    else: wet = []
    return wet, roots, False


def edge_contacts(a, b, h, plane, field):
    n = len(h); top = (n-1)*GRID; a, b = np.asarray(a, float), np.asarray(b, float)
    ts = cuts(a, b, top); parts = []
    for lo, hi in zip(ts, ts[1:]):
        p, q = a+(b-a)*lo, a+(b-a)*hi; mid = a+(b-a)*(.5*(lo+hi)); faces = []
        for row, col, ti in faces_at(mid, n, top):
            corners = TRI[ti]
            hv = np.array([h[row+OFF[k][0], col+OFF[k][1]] for k in corners], float)
            wv = field[row, col, list(corners)] if np.isfinite(plane[row, col]) else np.full(3, .75)
            weights = np.array([bary(p, row, col, ti, top), bary(q, row, col, ti, top)])
            require(weights.min() >= -TOL and np.isfinite(hv).all() and np.isfinite(wv).all(), 'face_domain_or_nonfinite')
            water = weights@wv; ds = weights@(hv-wv)
            wet, roots, contact = intervals(float(ds[0]), float(ds[1]), lo, hi)
            faces.append(dict(cell=[row, col], triangle=ti, exact_shared_edge=bool(((weights[0] == 0) & (weights[1] == 0)).any()), water=water.tolist(), difference=ds.tolist(),
                              wet=wet, roots=roots, contact_interval=contact))
        ambiguous = any(max(abs(np.array(f['water'])-faces[0]['water'])) > TOL for f in faces[1:])
        numerical = len(faces)>2 or (len(faces)>1 and not all(f['exact_shared_edge'] for f in faces))
        parts.append(dict(lo=lo, hi=hi, faces=faces, ambiguous_water_boundary=ambiguous, numerical_incidence_ambiguity=numerical))
    require(parts[0]['lo'] == 0 and parts[-1]['hi'] == 1 and
            all(x['hi'] == y['lo'] for x, y in zip(parts, parts[1:])), 'partition_gap')
    length = float(np.linalg.norm(b-a))
    require(abs(math.fsum((p['hi']-p['lo'])*length for p in parts)-length) <= TOL, 'partition_length')
    steps = []
    for left, right in zip(parts, parts[1:]):
        for lf in left['faces']:
            for rf in right['faces']:
                if abs(lf['water'][1]-rf['water'][0]) > TOL:
                    steps.append(dict(kind='NUMERICALLY_AMBIGUOUS_WATER_STEP' if left['numerical_incidence_ambiguity'] or right['numerical_incidence_ambiguity'] else 'WATER_STEP_AT_CELL_CUT', t=left['hi'],
                        left_cell=lf['cell'], left_triangle=lf['triangle'], right_cell=rf['cell'], right_triangle=rf['triangle'],
                        water=[lf['water'][1], rf['water'][0]], difference=[lf['difference'][1], rf['difference'][0]]))
    return dict(parts=parts, steps=steps, length_m=length)


def graph_guard(xy, edges, chains):
    require(xy.ndim == 2 and xy.shape[1] == 2 and np.isfinite(xy).all(), 'road_nodes')
    require(edges.ndim == 2 and edges.shape[1] == 3 and np.isfinite(edges).all(), 'road_edges')
    expected = Counter()
    for a, b, length in edges:
        require(a == int(a) and b == int(b) and 0 <= a < len(xy) and 0 <= b < len(xy), 'edge_node_id')
        require(length > 0 and abs(np.linalg.norm(xy[int(b)]-xy[int(a)])-length) <= TOL, 'edge_length')
        expected[tuple(sorted((int(a), int(b))))] += 1
    actual = Counter()
    for chain in chains:
        require(len(chain) >= 2 and all(isinstance(i, int) and 0 <= i < len(xy) for i in chain), 'chain_node_id')
        actual.update(tuple(sorted((a, b))) for a, b in zip(chain, chain[1:]))
    require(actual == expected and all(v == 1 for v in expected.values()), 'edge_multiset')
    return dict(chains=len(chains), nodes=len(xy), edges=sum(actual.values()), length_m=math.fsum(edges[:, 2]))


def point_segment_distance(point, seg):
    delta = seg[1]-seg[0]; size = float(delta@delta)
    t = np.clip(((point-seg[0])@delta)/size, 0, 1) if size else 0.
    return float(np.linalg.norm(point-(seg[0]+t*delta)))


def check_roots(a, b, parts, by_face):
    checked=0; worst=0.
    for part in parts:
        for f in part['faces']:
            for t in f['roots']:
                face=(*f['cell'],f['triangle']); require(face in by_face,'root_face_missing')
                residual=point_segment_distance(a+(b-a)*t,by_face[face])
                require(residual <= TOL,'root_not_on_native_shore'); worst=max(worst,residual); checked+=1
    return checked,worst


def union_length(intervals):
    total=0.; end=-1.
    for lo,hi in sorted(intervals):
        if hi > end: total += hi-max(lo,end); end=hi
    return total


def observe_node(observations, node, point, ci, ei, part, endpoint):
    """Record jumps between ALL incident road edges, including chain junctions."""
    known=observations.setdefault(node,{})
    events=[]
    for f in part['faces']:
        face=(*f['cell'],f['triangle']); water=f['water'][endpoint]; difference=f['difference'][endpoint]
        if face in known:
            require(abs(known[face]['water']-water) <= TOL,'node_face_inconsistent'); continue
        new=dict(chain=ci,edge=ei,face=list(face),water=water,difference=difference,uncertain=part['numerical_incidence_ambiguity'])
        for previous in known.values():
            if abs(previous['water']-water) > TOL:
                events.append(dict(kind='NUMERICALLY_AMBIGUOUS_WATER_STEP' if new['uncertain'] or previous['uncertain'] else 'WATER_STEP_AT_CELL_CUT',
                    location='ROAD_GRAPH_NODE',node=node,xz=np.asarray(point).tolist(),left=previous,right=new))
        known[face]=new
    return events


def census(root, road_root, output, guard):
    source = root/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
    footprint = root/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz'
    native = root/'native-shore-census-20261028/native-shore.npz'
    road = road_root/'tests/regional_foundation_roads_v6/reference.npz'
    chain_path = road_root/'evidence/regional-foundation-v1/road-grade-chains-v6.json'
    expected = {source:'815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40',
        footprint:'084171b0e29df5c220f9d5aab42a3dc683a2f70a07579f08cd930dfd109e716b',
        native:'b6612009ff531ef2f3932240ea52cf0660bce97f7904b7d667f962ce0fd95847',
        road:'94ecbca61bd5ba9ba61f89b765b043676a4a65703729a0b69009ae233984a1c2',
        chain_path:'b31fb7d72398981ee98132ce59eab48c4aa404043718475fbb2725b13de1b824'}
    for p in (Path(__file__), HERE/'water_constraint_diagnostic_ev112.py', HERE/'verify_native_shore_census_ev112.py'):
        expected[p.resolve()] = guard.sha(p)
    for p, digest in expected.items(): require(guard.sha(p) == digest, 'input_hash_'+str(p))
    with np.load(source) as data: h = data['heights']
    with np.load(footprint) as data: plane, field = data['plane'], data['field']
    with np.load(road) as data:
        require('edges' in data.files, 'INCONCLUSIVE_NO_EDGE_KEY'); xy, edges = data['xy'], data['edges']
    chains = json.loads(chain_path.read_text(encoding='utf-8'))['chains']
    verify = load('native_input_guard', HERE/'verify_native_shore_census_ev112.py'); verify.inputs(h, plane, field)
    coverage = graph_guard(xy, edges, chains)
    require((coverage['chains'], coverage['nodes'], coverage['edges']) == (124, 36428, 36467), 'road_universe')
    with np.load(native) as data:
        by_face = {(int(r), int(c), int(ti)):p for (r,c),ti,p in zip(data['cell'],data['tri'],data['p'])}
        require(len(by_face) == len(data['p']), 'duplicate_native_face')
    partitions = []; face_partitions=[]; contacts = []; chain_rows = []; roots_checked = 0; worst_residual = 0.; edge_count = 0
    nodes={}; node_steps=[]; fully_wet_parts=0
    for ci, chain in enumerate(chains):
        station = 0.; hits = 0; wet_lengths=[]
        for ei, (va, vb) in enumerate(zip(chain, chain[1:])):
            a, b = xy[va], xy[vb]; result = edge_contacts(a, b, h, plane, field); edge_count += 1
            parts = result['parts']
            incoming=observe_node(nodes,va,a,ci,ei,parts[0],0)+observe_node(nodes,vb,b,ci,ei,parts[-1],1)
            node_steps.extend(incoming); result['node_steps']=incoming
            count,residual=check_roots(a,b,parts,by_face);roots_checked+=count;worst_residual=max(worst_residual,residual)
            wet_lengths.append(union_length([w for p in parts for f in p['faces'] for w in f['wet']])*result['length_m'])
            for part in parts:
                partitions.append((ci, ei, part['lo'], part['hi'], len(part['faces'])))
                for f in part['faces']:
                    face_partitions.append((ci,ei,part['lo'],part['hi'],*f['cell'],f['triangle']))
                    fully_wet_parts+=int(bool(f['wet']) and not f['roots'])
            if incoming or result['steps'] or any(p['ambiguous_water_boundary'] or p['numerical_incidence_ambiguity'] or any(f['wet'] or f['roots'] or f['contact_interval'] or 0 in f['difference'] for f in p['faces']) for p in parts):
                contacts.append(dict(chain=ci, edge=ei, nodes=[va,vb], start_station_m=station, a=a.tolist(), b=b.tolist(), **result)); hits += 1
            station += result['length_m']
        chain_rows.append(dict(chain=ci, edges=len(chain)-1, length_m=station, nominal_wet_union_length_m=math.fsum(wet_lengths),contact_edges=hits,
                               status='CONTACTS_REQUIRE_BRIDGE_AND_MODEL_REVIEW' if hits else 'NO_NOMINAL_AXIS_CONTACT_NOT_ACCEPTANCE'))
    require(edge_count == coverage['edges'] and abs(math.fsum(r['length_m'] for r in chain_rows)-coverage['length_m']) <= TOL, 'global_coverage')
    for p, digest in expected.items(): require(guard.sha(p) == digest, 'input_changed')
    guard.dump(output/'contacts.json', contacts); guard.dump(output/'chain-coverage.json', chain_rows)
    np.savez_compressed(output/'partitions.npz', partitions=np.asarray(partitions),face_partitions=np.asarray(face_partitions))
    guard.dump(output/'road-node-water-steps.json',node_steps)
    features=[]
    for contact in contacts:
        a,b=np.asarray(contact['a']),np.asarray(contact['b'])
        for part in contact['parts']:
            for face in part['faces']:
                for lo,hi in face['wet']:
                    features.append(dict(type='Feature',geometry=dict(type='LineString',coordinates=[(a+(b-a)*lo).tolist(),(a+(b-a)*hi).tolist()]),
                        properties=dict(chain=contact['chain'],edge=contact['edge'],cell=face['cell'],triangle=face['triangle'],kind='NOMINAL_WET_AXIS',acceptance=False)))
        for step in contact['steps']:
            features.append(dict(type='Feature',geometry=dict(type='Point',coordinates=(a+(b-a)*step['t']).tolist()),
                properties=dict(chain=contact['chain'],edge=contact['edge'],**step)))
    guard.dump(output/'contacts-local-xz.geojson',dict(type='FeatureCollection',coordinate_system='Local DayZ XZ metres; NOT WGS84',features=features))
    guard.dump(output/'road-node-water-steps-local-xz.geojson',dict(type='FeatureCollection',coordinate_system='Local DayZ XZ metres; NOT WGS84',
        features=[dict(type='Feature',geometry=dict(type='Point',coordinates=e['xz']),properties=e) for e in node_steps]))
    contexts={}
    for name,point in [('narva',np.array([2391.,6941.])),('kit118',np.array([8253.,9038.])),('reported_player',np.array([4789.51465,5516.52197]))]:
        closest=sorted([dict(chain=c['chain'],edge=c['edge'],distance_m=point_segment_distance(point,np.array([c['a'],c['b']])),a=c['a'],b=c['b']) for c in contacts],key=lambda x:x['distance_m'])[:10]
        contexts[name]=dict(point=point.tolist(),association='UNCONFIRMED_CONTEXT_ONLY',nearest_contact_edges=closest)
    guard.dump(output/'contexts.json',contexts)
    guard.dump(output/'inputs.json', {str(p):v for p,v in expected.items()})
    return dict(status='CENSUS_COMPLETE_NOT_BRIDGE_ACCEPTANCE', coverage=coverage, partition_count=len(partitions),
        contact_edges=len(contacts), checked_roots=roots_checked, maximum_root_residual_m=worst_residual,
        water_steps_inside_edges=sum(len(c['steps']) for c in contacts),water_steps_at_road_nodes=len(node_steps),
        fully_wet_face_parts_without_interior_root=fully_wet_parts,nominal_wet_union_length_m=math.fsum(c['nominal_wet_union_length_m'] for c in chain_rows),
        ambiguous_parts=sum(p['ambiguous_water_boundary'] for c in contacts for p in c['parts']),
        numerical_incidence_ambiguities=sum(p['numerical_incidence_ambiguity'] for c in contacts for p in c['parts']),
        limitations=['Nominal native water and reference road axes only; lateral width and 3D water not evaluated.',
                     'No bridge absence/alignment verdict, no authoring/build/runtime or driving acceptance.'])


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('road_root',type=Path); ap.add_argument('output',type=Path)
    args=ap.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    guard=load('road_budget',HERE/'water_constraint_diagnostic_ev112.py'); guard.STARTED=STARTED; stop=guard.bounded(args.output)
    try:
        report=census(args.root,args.road_root,args.output,guard); report['resources']=guard.memory()
        require(report['resources']['seconds'] <= 120 and max(report['resources']['peak_resident_bytes'],report['resources']['peak_commit_bytes']) <= 2*1024**3,'resource_budget')
        stop.set(); guard.dump(args.output/'report.json',report); print(json.dumps(report))
    except Exception as error:
        guard.dump(args.output/'failure.json',dict(status='INCONCLUSIVE_FAILURE',reason=str(error),error_type=type(error).__name__)); raise
    finally: stop.set()
