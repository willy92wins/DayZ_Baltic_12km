"""Read-only prototypes for deployed Roadway and water surfaces; not map acceptance.

Input discovery is sealed by artifact-hashes.json. Root matrices are the actual
compiled WRP matrices. Proxy coordinates remain explicitly conditional.
"""
import os, time
STARTED = time.monotonic()
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '1'
import argparse, hashlib, importlib.util, io, json, struct, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROADWAY = 3000000028082176.0
TOL = 1e-9
WATER_MATERIALS = frozenset(('dz/water/streams/data/water_streambed.rvmat',
                            'dz/water/ponds/data/pond_moss_1.rvmat'))
PROXY_CONDITIONAL, AMBIGUOUS_FACE, DEGENERATE_FACE = 1, 2, 4
META = np.dtype([('model', '<i4'), ('source_model', '<i4'), ('face', '<i4'),
                 ('section', '<i4'), ('lod', '<i4'), ('kind', 'u1'),
                 ('vertices', 'u1'), ('flags', 'u1'), ('proxy', '<i4'), ('planarity_m', '<f8')])


def require(condition, message):
    if not bool(condition): raise ValueError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def norm(value):
    return value.replace('\\', '/').strip('/').lower()


def exact(f, length):
    result = f.read(length); require(len(result) == length, 'truncated_pbo'); return result


def string(f):
    result = bytearray()
    for _ in range(4096):
        c = exact(f, 1)
        if c == b'\0': return result.decode('utf-8')
        result.extend(c)
    raise ValueError('unbounded_pbo_string')


def pbo_table(f, length):
    entries, properties, seen = [], {}, set()
    while True:
        name = string(f)
        mime, original, reserved, timestamp, size = struct.unpack('<5I', exact(f, 20))
        if not name:
            if mime == 0x56657273:
                while True:
                    key = string(f)
                    if not key: break
                    require(key not in properties, 'duplicate_property'); properties[key] = string(f)
                continue
            require(not any((mime, original, reserved, timestamp, size)), 'invalid_pbo_sentinel'); break
        key = name.replace('\\', '/').lower()
        require(not key.startswith('/') and ':' not in key and
                all(p not in ('', '.', '..') for p in key.split('/')), 'unsafe_pbo_path')
        require(key not in seen, 'duplicate_pbo_path'); seen.add(key)
        entries.append(dict(name=key, mime=mime, size=size))
        require(len(entries) <= 100000, 'pbo_entry_budget')
    offset = f.tell()
    for e in entries:
        e['offset'] = offset; offset += e['size']; require(offset <= length, 'truncated_pbo_payload')
    return properties, entries


def read_payload(f, entry, digest):
    require(entry['mime'] == 0, 'compressed_payload_unsupported')
    f.seek(entry['offset']); data = exact(f, entry['size'])
    require(hashlib.sha256(data).hexdigest() == digest, 'payload_hash'); return data


def transform(vertices, matrix):
    v, m = np.asarray(vertices, float), np.asarray(matrix, float)
    require(v.shape[-1] == 3 and m.shape == (12,) and np.isfinite(v).all() and np.isfinite(m).all(), 'transform_input')
    return v @ m[:9].reshape(3, 3) + m[9:]


def proxy_transform(vertices, child_center, matrix):
    """Hypothesis, deliberately marked conditional by the caller."""
    c = np.asarray(child_center, float)
    require(c.shape == (3,) and np.isfinite(c).all(), 'proxy_center')
    return transform(np.asarray(vertices, float) + c, matrix)


def face_diagnostics(vertices):
    """Retain original face; diagnose whether a convex planar fan is safe."""
    v = np.asarray(vertices, float)
    require(v.shape in ((3, 3), (4, 3)) and np.isfinite(v).all(), 'face_input')
    normal = np.cross(v[1]-v[0], v[2]-v[0]); size = np.linalg.norm(normal)
    if size == 0: return DEGENERATE_FACE, float('nan')
    if len(v) == 3: return 0, 0.
    residual = abs((v[3]-v[0]) @ normal) / size
    if residual > TOL: return AMBIGUOUS_FACE, float(residual)
    axes = [k for k in range(3) if k != int(np.argmax(abs(normal)))]
    p = v[:, axes]; d = np.roll(p, -1, axis=0)-p
    following = np.roll(d, -1, axis=0)
    turns = d[:, 0]*following[:, 1]-d[:, 1]*following[:, 0]
    return (0 if (turns > 0).all() or (turns < 0).all() else AMBIGUOUS_FACE), float(residual)


def face_flag(vertices):
    return face_diagnostics(vertices)[0]


def sections(lod):
    """Partition every face, including unknown/empty materials and textures."""
    assignments = np.full(len(lod.faces), -1, np.int32); rows = []
    for si, s in enumerate(lod.sections):
        require(-1 <= s.texture_index < len(lod.textures) and
                -1 <= s.material_index < len(lod.materials), 'section_index')
        material = lod.materials[s.material_index].material_name if s.material_index >= 0 else s.mat_name
        texture = lod.textures[s.texture_index] if s.texture_index >= 0 else ''
        ids = np.asarray(s.get_face_indices(lod.faces), np.int64)
        require(((ids >= 0) & (ids < len(assignments))).all() and len(np.unique(ids)) == len(ids), 'section_faces')
        require((assignments[ids] == -1).all(), 'overlapping_sections'); assignments[ids] = si
        rows.append(dict(index=si, material_raw=material, material=norm(material),
                         texture_raw=texture, texture=norm(texture), faces=len(ids)))
    require((assignments >= 0).all(), 'unassigned_face'); return assignments, rows


def select_lods(resolutions):
    r = np.asarray(resolutions, float); require(np.isfinite(r).all(), 'lod_resolution')
    visual = np.flatnonzero((r >= 0) & (r < 1000))
    require(len(visual) > 0, 'missing_visual_lod')
    vi = np.flatnonzero(r == r[visual].min()); require(len(vi) == 1, 'duplicate_visual_lod')
    road = np.flatnonzero(r == ROADWAY); require(len(road) <= 1, 'duplicate_roadway_lod')
    return int(vi[0]), int(road[0]) if len(road) else None


def extract(odol, model_index):
    require(not odol.lod_errors and len(odol.lods) == len(odol.resolutions), 'incomplete_odol')
    visual, road = select_lods([l.resolution for l in odol.lods])
    vertices, records, evidence = [], [], []
    for li, lod in enumerate(odol.lods):
        require(lod.lod_end_ok, 'lod_cursor')
        assignment, ss = sections(lod)
        evidence.append(dict(index=li, resolution=lod.resolution, faces=len(lod.faces), sections=ss))
        points = np.asarray([[p.x, p.y, p.z] for p in lod.vertices], float).reshape(-1, 3)
        require(np.isfinite(points).all(), 'nonfinite_model_vertex')
        for fi, f in enumerate(lod.faces):
            ids = np.asarray(f.vertex_indices, np.int64)
            require(len(ids) in (3, 4) and ((ids >= 0) & (ids < len(points))).all(), 'face_vertex_indices')
            si = int(assignment[fi]); kinds = []
            if li == road: kinds.append(0)
            if li == visual and ss[si]['material'] in WATER_MATERIALS: kinds.append(1)
            if not kinds: continue
            v = points[ids]; flag, residual = face_diagnostics(v)
            padded = np.zeros((4, 3), float); padded[:len(v)] = v
            for kind in kinds:
                vertices.append(padded)
                records.append((model_index, model_index, fi, si, li, kind, len(v), flag, -1, residual))
    proxies = []
    for p in odol.lods[visual].proxies:
        t = p.transformation
        matrix = [z for v in (t.orientation.aside, t.orientation.up, t.orientation.dir, t.position) for z in (v.x, v.y, v.z)]
        name = norm(p.model); name += '' if name.endswith('.p3d') else '.p3d'
        proxies.append(dict(model=name, matrix=matrix))
    c = odol.model_info.bounding_center
    return (np.asarray(vertices, float).reshape(-1, 4, 3), np.asarray(records, META),
            dict(lods=evidence, proxies=proxies, center=[c.x, c.y, c.z]))


def expand_proxies(model, prototypes, models, stack=(), path=(), paths=None):
    """Return descendant water only. Never turn child Roadway into bridge support."""
    require(model not in stack, 'proxy_cycle'); require(len(stack) < 16, 'proxy_depth')
    if paths is None: paths = []
    parts, records = [], []
    for slot, p in enumerate(prototypes[model][2]['proxies']):
        child = p['model']; require(child in prototypes, 'missing_proxy')
        vertices, meta, info = prototypes[child]
        water = meta['kind'] == 1
        chain = path+((models[model],slot),)
        direct_meta = meta[water].copy()
        if len(direct_meta):
            direct_meta['proxy'] = len(paths)
            paths.append(dict(root_model=chain[0][0],slots=[list(x) for x in chain],source_model=models[child]))
        sub, sm = expand_proxies(child, prototypes, models, stack+(model,), chain, paths)
        if len(sub):
            vertices = np.concatenate((vertices[water], sub)); meta = np.concatenate((direct_meta, sm))
        else: vertices, meta = vertices[water].copy(), direct_meta
        for i, count in enumerate(meta['vertices']):
            vertices[i, :count] = proxy_transform(vertices[i, :count], info['center'], p['matrix'])
            flag, residual = face_diagnostics(vertices[i, :count])
            meta['flags'][i] |= PROXY_CONDITIONAL | flag
            meta['planarity_m'][i] = residual
        meta['model'] = models[model]; meta['kind'] = 2
        parts.append(vertices); records.append(meta)
    return (np.concatenate(parts), np.concatenate(records)) if parts else (np.empty((0,4,3)), np.empty(0,META))


def matrix_inventory(matrix):
    m = np.asarray(matrix, float).reshape(-1, 12); require(np.isfinite(m).all(), 'nonfinite_pose')
    a = m[:, :9].reshape(-1, 3, 3); gram = a @ a.transpose(0, 2, 1)
    off = gram.copy(); off[:, np.arange(3), np.arange(3)] = 0
    return dict(norm=np.linalg.norm(a, axis=2), determinant=np.linalg.det(a), nonorthogonality=np.abs(off).max(axis=(1,2)))


def manifest_keys(artifacts):
    result = {}
    for name, record in artifacts.items():
        key = norm(name); require(key not in result, 'ambiguous_artifact_path'); result[key] = record
    return result


def sealed_bytes(path, root, artifacts):
    key = norm(path.relative_to(root).as_posix()); require(key in artifacts, 'artifact_missing')
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == artifacts[key]['sha256'], 'discovery_changed:'+path.name)
    return data


def instance_guard(ids, mi, matrix, catalog):
    require(ids.ndim == mi.ndim == 1 and matrix.shape == (len(ids),12), 'instance_shape')
    require(len(ids) == len(np.unique(ids)) == len(mi), 'instance_identity')
    counts = dict(zip(*np.unique(mi, return_counts=True)))
    require(counts == {x['index']:x['instances'] for x in catalog if x['group'] != 'vegetation_not_inspected'}, 'instance_coverage')
    return matrix_inventory(matrix)


def inventory(root, worktree, output, meter):
    discovery = root/'geometry-payload-discovery-resolved-20261028'
    artifact_path = worktree/'evidence/deployed-geometry-discovery-20261028/artifact-hashes.json'
    manifest_data = artifact_path.read_bytes()
    artifacts = manifest_keys(json.loads(manifest_data))
    pins = {artifact_path:hashlib.sha256(manifest_data).hexdigest()}
    names = ('all-models.json','payload-bindings.json','inputs.json','selected-instances.npz')
    sealed = {}
    for name in names:
        p = discovery/name; sealed[name] = sealed_bytes(p,root,artifacts)
        pins[p] = hashlib.sha256(sealed[name]).hexdigest()
    catalog = json.loads(sealed['all-models.json']); bindings = json.loads(sealed['payload-bindings.json'])
    inputs = json.loads(sealed['inputs.json']); package_map = {}
    for package in inputs['packages']:
        path = Path(package['path']); require(meter.sha(path) == package['sha256'], 'package_changed')
        pins[path] = package['sha256']
        with path.open('rb') as f: props, entries = pbo_table(f, path.stat().st_size)
        require(norm(props['prefix']) == package['prefix'], 'pbo_prefix')
        require(path.name not in package_map, 'ambiguous_package')
        package_map[path.name] = (path, {e['name']:e for e in entries}, package['prefix'])
    # World identity remains the same as the visit, not merely the small mesh PBOs.
    for path, info in inputs['prior_inputs'].items():
        p = Path(path)
        if p.suffix.lower() == '.wrp' or p.name == 'narva_trial.pbo':
            require(meter.sha(p) == info['sha256'], 'world_changed')
            pins[p] = info['sha256']
    reader = Path('C:/temp/moto_lanes/review_g3/tools/odol_reader.py')
    for path, digest in inputs['reader'].items():
        p=Path(path); require(meter.sha(p) == digest, 'reader_changed'); pins[p]=digest
    sys.path.insert(0, str(reader.parent)); from odol_reader import ODOL
    require(len({norm(x['name']) for x in catalog}) == len(catalog), 'model_alias')
    models = {x['name']:x['index'] for x in catalog}
    original_models = set(models)
    for b in bindings:
        if b['name'] not in models: models[b['name']] = len(models)
    require(len({x['name'] for x in bindings}) == len(bindings), 'duplicate_binding')
    prototypes = {}; summaries = []
    for b in bindings:
        path, entries, prefix = package_map[b['package']]
        require(b['entry'] in entries and prefix+'/'+b['entry'] == b['name'], 'binding_path')
        with path.open('rb') as f: data = read_payload(f, entries[b['entry']], b['sha256'])
        require(data[:4] == b'ODOL', 'model_signature')
        od = ODOL.from_bytes(data, strict=True)
        vertices, meta, summary = extract(od, models[b['name']]); prototypes[b['name']] = (vertices, meta, summary)
        summaries.append(dict(name=b['name'], index=models[b['name']], **summary))
    selected_names = {x['name'] for x in catalog if x['group'] != 'vegetation_not_inspected'}
    require(selected_names <= prototypes.keys(), 'missing_model_binding')
    # Keep prototypes compact. Parent proxy vertices are emitted once per model.
    arrays, metadata, proxy_paths = [], [], []
    for name, (vertices, meta, info) in prototypes.items():
        if name not in original_models: continue
        arrays.append(vertices); metadata.append(meta)
        p, pm = expand_proxies(name, prototypes, models, paths=proxy_paths)
        if len(p): arrays.append(p); metadata.append(pm)
    faces, ids = np.concatenate(arrays), np.concatenate(metadata)
    require(len(faces) == len(ids), 'face_count')
    with np.load(io.BytesIO(sealed['selected-instances.npz'])) as f:
        instance_ids, mi, matrix = f['ids'], f['model_index'], f['matrix']
    metrics = instance_guard(instance_ids,mi,matrix,catalog)
    for p,digest in pins.items(): require(meter.sha(p) == digest, 'input_changed_after_hash:'+str(p))
    np.savez_compressed(output/'surface-prototypes.npz',vertices=faces,meta=ids)
    np.savez_compressed(output/'instances.npz',ids=instance_ids,model_index=mi,matrix=matrix,**metrics)
    meter.dump(output/'model-sections.json',summaries); meter.dump(output/'model-catalog.json',catalog)
    meter.dump(output/'proxy-paths.json',proxy_paths)
    result = dict(status='PROTOTYPES_ONLY_NOT_WORLD_OVERLAY',models=len(prototypes),instances=len(instance_ids),
                  prototype_faces=len(ids),roadway_faces=int((ids['kind']==0).sum()),water_faces=int((ids['kind']==1).sum()),
                  conditional_proxy_faces=int((ids['kind']==2).sum()),ambiguous_faces=int(((ids['flags']&AMBIGUOUS_FACE)!=0).sum()),
                  degenerate_faces=int(((ids['flags']&DEGENERATE_FACE)!=0).sum()),
                  max_finite_planarity_residual_m=float(np.max(ids['planarity_m'][np.isfinite(ids['planarity_m'])],initial=0)),
                  limits=['Proxy frame conditional; no engine claim.', 'Preserved faces are not accepted bridge support.',
                          'No world-space intersection, road width, driving or map acceptance.', 'Vegetation meshes not evaluated.'])
    meter.dump(output/'inputs.json',dict(discovery_artifacts=artifacts,source_pins={str(k):v for k,v in pins.items()},
                                        artifact_manifest_sha256=pins[artifact_path],
                                        script_sha256=meter.sha(Path(__file__)),reader=inputs['reader']))
    return result


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('worktree',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    meter=load('resource_meter',HERE/'water_constraint_diagnostic_ev112.py');meter.STARTED=STARTED;stop=meter.bounded(a.output)
    try:
        result=inventory(a.root,a.worktree,a.output,meter);result['measurement']=meter.memory()
        meter.dump(a.output/'report.json',result);print(json.dumps(result))
    except Exception as e:
        meter.dump(a.output/'failure.json',dict(type=type(e).__name__,reason=str(e),measurement=meter.memory()));raise
    finally: stop.set()
