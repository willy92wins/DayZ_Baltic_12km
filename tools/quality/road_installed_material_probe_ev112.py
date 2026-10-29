# Road installed-material probe. Stdlib only; fail-closed initial discovery.
import argparse, ast, hashlib, importlib.util, json, math, os, stat, sys, time
from contextlib import ExitStack
from pathlib import Path

SCHEMA = 'ROAD_INSTALLED_MATERIAL_PROBE_V1'
MANIFEST_SCHEMA = 'ROAD_INSTALLED_MATERIAL_PROBE_MANIFEST_V1'
CONTRACT_FIELDS = {'schema', 'sources', 'pins', 'helper', 'runner', 'psutil_root', 'cfgconvert', 'pbos', 'selected', 'external', 'limits'}
SOURCE_FIELDS = {'r0_report', 'r0_manifest', 'r0_contract', 'b4a1_report', 'b4a1_approval', 'catalog_models', 'catalog_entries'}
LIMIT_FIELDS = {'seconds', 'rss_bytes', 'conversion_seconds', 'conversions', 'resource_bytes', 'total_output_bytes'}
PBO_FIELDS = {'roads', 'surfaces', 'surfaces_bliss'}
RAP = b'\x00raP'
CHUNK = 65536
MAX_RESOURCE = 16777216
MAX_TOTAL = 67108864

class DiscoveryError(ValueError): pass
class DeadlineExceeded(DiscoveryError): pass

def _norm(v): return str(v).replace(chr(92), '/').strip('/').lower()
def _is_sha(v): return isinstance(v, str) and len(v) == 64 and all(c in '0123456789abcdef' for c in v.lower())
def _require(c, m):
    if not c: raise DiscoveryError(m)
def _sha_bytes(b): return hashlib.sha256(b).hexdigest()
def _sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(CHUNK), b''): h.update(b)
    return h.hexdigest()
def _pin_key(p): return os.path.normpath(str(p)).lower()
def _pin_for(pins, p):
    m = {_pin_key(k): v for k, v in pins.items()}
    v = m.get(_pin_key(p))
    _require(_is_sha(v), 'missing_pin:' + str(p))
    return v.lower()
def strict_loads(data):
    if isinstance(data, (bytes, bytearray)): data = data.decode('utf-8')
    def hook(pairs):
        o = {}
        for k, v in pairs:
            _require(k not in o, 'duplicate_json_key:' + str(k)); o[k] = v
        return o
    def bad(x): raise DiscoveryError('nonfinite_json:' + x)
    def flt(x):
        v = float(x); _require(math.isfinite(v), 'nonfinite_json'); return v
    try: return json.loads(data, object_pairs_hook=hook, parse_constant=bad, parse_float=flt)
    except DiscoveryError: raise
    except Exception as e: raise DiscoveryError('strict_json:' + str(e)) from e
def _read_pinned(path, pins):
    p = Path(path); _require(p.is_file(), 'missing_file:' + str(p))
    before = _sha_file(p); _require(before == _pin_for(pins, p), 'pin_changed_before_parse:' + str(p))
    data = p.read_bytes(); _require(_sha_bytes(data) == before, 'file_changed_during_read:' + str(p))
    return data, before
def _no_reparse(path):
    p = Path(path); cur = Path(p.anchor) if p.anchor else Path('.')
    parts = p.parts[1:] if p.anchor else p.parts
    for part in parts:
        cur = cur / part
        try: s = os.lstat(cur)
        except FileNotFoundError: return
        _require(not stat.S_ISLNK(s.st_mode), 'reparse_path:' + str(cur))
        _require(not (int(getattr(s, 'st_file_attributes', 0) or 0) & 0x400), 'reparse_path:' + str(cur))
def _stat_id(s): return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]
def _hash_stream(f):
    f.seek(0); h = hashlib.sha256()
    for b in iter(lambda: f.read(CHUNK), b''): h.update(b)
    return h.hexdigest()
def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
def _check_deadline(deadline):
    if time.monotonic() > deadline: raise DeadlineExceeded('deadline_exceeded')
def _validate_limits(lim):
    _require(isinstance(lim, dict) and set(lim) == LIMIT_FIELDS, 'bad_limits_fields')
    for k, v in lim.items(): _require(isinstance(v, int) and not isinstance(v, bool) and v > 0, 'bad_limit:' + k)
    _require(lim['seconds'] <= 120 and lim['conversion_seconds'] <= 30 and lim['conversions'] <= 2, 'limit_cap_exceeded')
    _require(lim['resource_bytes'] <= MAX_RESOURCE and lim['total_output_bytes'] <= MAX_TOTAL, 'limit_cap_exceeded')
    _require(lim['rss_bytes'] <= 536870912, 'limit_cap_exceeded')
    return lim
def _validate_raw_virtual(raw):
    _require(isinstance(raw, str) and raw != '' and raw.strip() == raw, 'unsafe_virtual_path')
    _require(chr(92) not in raw and ':' not in raw and not raw.startswith('/'), 'unsafe_virtual_path')
    parts = raw.split('/')
    _require(all(p not in ('', '.', '..') for p in parts), 'unsafe_virtual_path')
    return parts
def _validate_contract(c):
    _require(isinstance(c, dict) and set(c) == CONTRACT_FIELDS, 'bad_contract_fields')
    _require(c.get('schema') == SCHEMA, 'bad_schema')
    _require(isinstance(c.get('sources'), dict) and set(c['sources']) == SOURCE_FIELDS, 'bad_sources_fields')
    _require(isinstance(c.get('pins'), dict) and c['pins'], 'bad_pins')
    for k, v in c['pins'].items(): _require(_is_sha(v), 'bad_pin_value:' + str(k))
    _require(isinstance(c.get('pbos'), dict) and set(c['pbos']) == PBO_FIELDS, 'bad_pbos_fields')
    for name, p in c['pbos'].items():
        _require(isinstance(p, dict) and isinstance(p.get('path'), str) and isinstance(p.get('bytes'), int) and not isinstance(p.get('bytes'), bool), 'bad_pbo:' + name)
    roads = c['pbos']['roads']; _require(_is_sha(roads.get('sha256')) and isinstance(roads.get('prefix'), str), 'bad_roads_pin')
    _require(isinstance(c.get('selected'), list) and len(c['selected']) == 7, 'selected_must_be_7')
    seen = set()
    for s in c['selected']:
        _require(isinstance(s, dict) and set(s) == {'kind', 'virtual_path', 'entry', 'sha256'}, 'bad_selected_fields')
        _require(s['kind'] in ('model', 'material', 'texture') and _is_sha(s['sha256']), 'bad_selected_values')
        _validate_raw_virtual(s['virtual_path']); _validate_raw_virtual(s['entry'])
        _require(_norm(s['virtual_path']) not in seen, 'duplicate_selected'); seen.add(_norm(s['virtual_path']))
    _require(isinstance(c.get('external'), list) and len(c['external']) == 1 and isinstance(c['external'][0], str), 'bad_external')
    _validate_raw_virtual(c['external'][0])
    _validate_limits(c.get('limits'))
    return c
def _load_contract(contract, contract_sha256):
    _require(_is_sha(contract_sha256), 'contract_sha256_required')
    p = Path(contract); _require(p.is_file(), 'missing_contract')
    data = p.read_bytes(); _require(_sha_bytes(data) == contract_sha256.lower(), 'contract_sha256_mismatch')
    c = strict_loads(data); _validate_contract(c)
    required = [c['sources'][k] for k in sorted(SOURCE_FIELDS)] + [c['helper'], c['runner'], c['cfgconvert']]
    psutil_dir = Path(c['psutil_root']) / 'psutil'; psutil_files = []
    if psutil_dir.is_dir(): psutil_files = [str(x) for x in sorted(psutil_dir.rglob('*')) if x.is_file() and x.suffix.lower() in ('.py', '.pyd') and '__pycache__' not in x.parts]
    allowed = {_pin_key(x) for x in required + psutil_files}
    for k in c['pins']: _require(_pin_key(k) in allowed or _pin_key(k).startswith(_pin_key(c['psutil_root'])), 'extra_pin:' + str(k))
    for path in required + psutil_files: _require(_pin_for(c['pins'], path) == _sha_file(path), 'pin_changed_before_parse:' + str(path))
    return c, data
def _parse_sources(c):
    docs = {}; raw = {}
    for role, path in c['sources'].items():
        if role == 'catalog_models': continue
        data, h = _read_pinned(path, c['pins']); raw[role] = data
        if role == 'catalog_entries':
            obj = strict_loads(data); _require(isinstance(obj, list), 'bad_entries_doc'); docs[role] = obj
        else: docs[role] = strict_loads(data)
    data, h = _read_pinned(c['sources']['catalog_models'], c['pins']); raw['catalog_models'] = data; rows = []
    for line in data.decode('utf-8').splitlines():
        if line.strip(): rows.append(strict_loads(line))
    docs['catalog_models'] = rows
    return docs
def _linkage(docs, pins, c):
    pinned_report = _pin_for(pins, c['sources']['r0_report']); pinned_manifest = _pin_for(pins, c['sources']['r0_manifest'])
    pinned_contract = _pin_for(pins, c['sources']['r0_contract']); helper_pin = _pin_for(pins, c['helper'])
    for role in ('r0_report', 'r0_manifest', 'b4a1_report', 'b4a1_approval'): _require(isinstance(docs.get(role), dict), 'bad_linkage_doc:' + role)
    man, rep, b4, appr = docs['r0_manifest'], docs['r0_report'], docs['b4a1_report'], docs['b4a1_approval']
    _require(man.get('report_sha256') == pinned_report, 'linkage_mismatch:r0_manifest.report_sha256')
    _require(man.get('contract_sha256') == pinned_contract, 'linkage_mismatch:r0_manifest.contract_sha256')
    _require(man.get('tool_sha256') == helper_pin, 'linkage_mismatch:r0_manifest.tool_sha256')
    _require(rep.get('contract_sha256') == pinned_contract, 'linkage_mismatch:r0_report.contract_sha256')
    _require(rep.get('tool_sha256') == helper_pin, 'linkage_mismatch:r0_report.tool_sha256')
    _require(b4.get('contract_sha256') == appr.get('contract_sha256'), 'linkage_mismatch:b4a1.contract_sha256')
    _require(b4.get('helper_sha256') == helper_pin, 'linkage_mismatch:b4a1.helper_sha256')
    _require(b4.get('r0_report_sha256') == pinned_report, 'linkage_mismatch:b4a1.r0_report_sha256')
    _require(b4.get('r0_manifest_sha256') == pinned_manifest, 'linkage_mismatch:b4a1.r0_manifest_sha256')
    _require(b4.get('r0_contract_sha256') == pinned_contract, 'linkage_mismatch:b4a1.r0_contract_sha256')
    _require(b4.get('r0_tool_sha256') == helper_pin, 'linkage_mismatch:b4a1.r0_tool_sha256')
    return 'EXPLICIT_FIELDS_CHECKED'
def _bind_selected(c, docs):
    rep = docs['r0_report']; _require(isinstance(rep.get('models'), list) and isinstance(rep.get('references'), list), 'bad_r0_report_fields')
    derived = {}
    def add(normv, entry, sha):
        key = (_norm(normv), _norm(entry)); _require(key not in derived, 'duplicate_derived_selected'); _require(_is_sha(sha), 'bad_derived_sha'); derived[key] = sha.lower()
    for m in rep['models']:
        _require(isinstance(m, dict) and m.get('catalog_status') == 'READ_STRICT', 'model_catalog_not_read_strict')
        _require(m.get('pbo_status') == 'MATCH' and m.get('catalog_sha256') == m.get('pbo_sha256'), 'model_catalog_sha_mismatch')
        add(m.get('model'), m.get('entry'), m.get('pbo_sha256'))
    for r in rep['references']:
        if r.get('status') == 'UNRESOLVED_EXTERNAL':
            _require(_norm(r.get('normalized')) == _norm(c['external'][0]) and 'entry' not in r and 'pbo_sha256' not in r, 'bad_unresolved_external'); continue
        _require(r.get('pbo_sha256') == r.get('expected_sha256'), 'reference_expected_mismatch')
        add(r.get('normalized'), r.get('entry'), r.get('pbo_sha256'))
    want = {(_norm(s['virtual_path']), _norm(s['entry'])): s['sha256'].lower() for s in c['selected']}
    _require(len(derived) == 7 and derived == want, 'selected_not_bound_to_r0')
def _catalog(docs):
    entries = docs['catalog_entries']; _require(isinstance(entries, list), 'bad_entries')
    by = {}
    for e in entries:
        _require(isinstance(e, dict) and {'name', 'normalized_name', 'size', 'mime', 'sha256'} <= set(e) <= {'name', 'normalized_name', 'category', 'size', 'mime', 'sha256'}, 'bad_entry_fields')
        _require(isinstance(e['size'], int) and not isinstance(e['size'], bool) and isinstance(e['mime'], int) and not isinstance(e['mime'], bool), 'bad_entry_values')
        _require(_is_sha(e['sha256']) and _norm(e['normalized_name']) == _norm(e['name']), 'bad_entry_values')
        nn = _norm(e['normalized_name']); _require(nn not in by, 'duplicate_entry'); by[nn] = e
    models = {}
    for row in docs['catalog_models']:
        _require(isinstance(row, dict) and all(k in row for k in ('name', 'sha256', 'status', 'measurement')), 'bad_catalog_row')
        _require(row.get('status') == 'READ_STRICT' and _is_sha(row.get('sha256')), 'catalog_model_not_read_strict')
        _require(isinstance(row['measurement'], dict) and isinstance(row['measurement'].get('lods'), list), 'bad_catalog_measurement')
        key = _norm(row['name']); _require(key not in models, 'duplicate_catalog_model'); models[key] = row
    return by, models
def _all_lod_refs(c, models):
    refs = set(); used = []
    for s in [x for x in c['selected'] if x['kind'] == 'model']:
        row = models.get(_norm(s['entry'])); _require(row is not None, 'model_not_in_catalog:' + s['entry'])
        _require(row['sha256'].lower() == s['sha256'].lower(), 'selected_model_catalog_hash_mismatch:' + s['virtual_path']); used.append(row['name'])
        for lod in row['measurement']['lods']:
            _require(isinstance(lod, dict), 'bad_lod')
            for key in ('textures', 'materials'):
                for v in lod.get(key) or []:
                    if v: refs.add(_norm(v))
            for sec in lod.get('sections') or []:
                if isinstance(sec, dict):
                    for key in ('texture_raw', 'material_raw'):
                        if sec.get(key): refs.add(_norm(sec[key]))
    for s in c['selected']:
        if s['kind'] != 'model': _require(_norm(s['virtual_path']) in refs, 'selected_not_in_all_lod_refs:' + s['virtual_path'])
    for ext in c['external']: _require(_norm(ext) in refs, 'external_not_in_all_lod_refs:' + ext)
    return sorted(refs), used
def load_helper_pbo_table(helper, pins):
    data, h = _read_pinned(helper, pins); tree = ast.parse(data.decode('utf-8')); keep = []
    for node in tree.body:
        if isinstance(node, ast.Import) and all(a.name in ('struct',) for a in node.names): keep.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'BSL' for t in node.targets): keep.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in ('require', 'exact', 'string', 'unsafe_raw', 'pbo_table'): keep.append(node)
    names = {n.name for n in keep if isinstance(n, ast.FunctionDef)}
    _require({'require', 'exact', 'string', 'unsafe_raw', 'pbo_table'} <= names, 'helper_pbo_table_missing')
    custom = {'__name__': 'custom_pbo_helper'}; exec(compile(ast.Module(body=keep, type_ignores=[]), '<pinned-helper>', 'exec'), custom)
    _require(_sha_file(helper) == h, 'helper_mutated')
    return custom['pbo_table']
def _verify_runner_import(c):
    _require(_pin_for(c['pins'], c['runner']) == _sha_file(c['runner']), 'runner_pin_changed')
    psutil_dir = Path(c['psutil_root']) / 'psutil'; _require(psutil_dir.is_dir(), 'psutil_root_missing')
    for f in sorted(psutil_dir.rglob('*')):
        if f.is_file() and f.suffix.lower() in ('.py', '.pyd') and '__pycache__' not in f.parts: _require(_pin_for(c['pins'], str(f)) == _sha_file(f), 'psutil_pin_changed:' + str(f))
    spec = importlib.util.spec_from_file_location('pinned_council29_runner', c['runner']); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    psutil_file = Path(mod.psutil.__file__).resolve()
    try: psutil_file.relative_to(Path(c['psutil_root']).resolve())
    except ValueError: raise DiscoveryError('psutil_not_rooted_to_pinned_package')
    return mod
def _default_converter_factory(c, deadline, state):
    def factory():
        runner = _verify_runner_import(c); cfg = c['cfgconvert']; _require(_pin_for(c['pins'], cfg) == _sha_file(cfg), 'cfgconvert_pin_changed')
        def convert(original, decoded, receipt, timeout_s, max_bytes):
            _require(not decoded.exists() and not Path(receipt).exists(), 'conversion_output_not_fresh')
            before_in = _sha_file(original); before_exe = _sha_file(cfg)
            job = {'id': 'rvmat', 'out': str(receipt), 'seconds': float(timeout_s), 'max_bytes': int(max_bytes), 'cwd': str(receipt), 'command': [cfg, '-txt', '-dst', str(decoded), str(original)], 'input_file': str(original)}
            result = runner.run(job)
            _require(_sha_file(original) == before_in, 'input_mutated_during_conversion'); _require(_sha_file(cfg) == before_exe, 'exe_mutated_during_conversion')
            receipt_p = Path(receipt); running_p, completion_p = receipt_p / 'running.json', receipt_p / 'completion.json'
            _require(running_p.is_file() and completion_p.is_file(), 'conversion_receipt_missing')
            running = strict_loads(running_p.read_bytes()); completion = strict_loads(completion_p.read_bytes())
            _require(isinstance(running.get('pid'), int) and running.get('birth') is not None, 'conversion_birth_receipt_missing')
            ids = completion.get('identities') or {}; _require(str(running['pid']) in ids or running['pid'] in ids, 'conversion_pid_not_in_completion')
            birth = ids.get(str(running['pid']), ids.get(running['pid'])); _require(birth == running['birth'], 'conversion_pid_birth_mismatch')
            stdout_p, stderr_p = receipt_p / 'stdout', receipt_p / 'stderr'; _require(stdout_p.is_file() and stderr_p.is_file(), 'conversion_stream_missing')
            stdout_b, stderr_b = stdout_p.read_bytes(), stderr_p.read_bytes(); _require(completion.get('stdout_sha') == _sha_bytes(stdout_b), 'conversion_stdout_hash_mismatch'); _require(completion.get('stderr_sha') == _sha_bytes(stderr_b), 'conversion_stderr_hash_mismatch')
            _require(result.get('stdout_sha') == _sha_bytes(stdout_b) and result.get('stderr_sha') == _sha_bytes(stderr_b), 'conversion_stream_result_mismatch')
            enriched = dict(result); enriched['receipt_running_path'] = 'receipts/' + receipt_p.name + '/running.json'; enriched['receipt_running_sha256'] = _sha_file(running_p)
            enriched['receipt_completion_path'] = 'receipts/' + receipt_p.name + '/completion.json'; enriched['receipt_completion_sha256'] = _sha_file(completion_p)
            enriched['stdout_path'] = 'receipts/' + receipt_p.name + '/stdout'; enriched['stdout_sha256'] = _sha_bytes(stdout_b); enriched['stderr_path'] = 'receipts/' + receipt_p.name + '/stderr'; enriched['stderr_sha256'] = _sha_bytes(stderr_b)
            enriched['completion_receipt'] = completion; enriched['installed_tool_sha256_before'] = before_exe; enriched['installed_tool_sha256_after'] = _sha_file(cfg)
            _require(completion.get('rc') == enriched.get('rc') and completion.get('reason') == enriched.get('reason'), 'conversion_receipt_result_mismatch')
            return enriched
        return convert
    return factory
def detect_material(data):
    if data[:4] == RAP: return 'RAP'
    try:
        text = data.decode('utf-8')
        if all(ch.isprintable() or ch in '\r\n\t' for ch in text): return 'TEXT_SAMPLE'
    except UnicodeDecodeError: pass
    return 'UNKNOWN'
def _safe_local(out, virtual):
    _validate_raw_virtual(virtual); out = Path(out); _require(out.drive.lower() != 'p:', 'never_write_p')
    parts = _norm(virtual).split('/'); dest = out.joinpath('assets', *parts)
    _require(out.resolve() in dest.resolve().parents, 'safe_local_escape:' + str(virtual))
    cur = out
    _no_reparse(out)
    for part in ['assets'] + parts[:-1]:
        cur = cur / part
        if cur.exists(): _no_reparse(cur)
    return dest
def _flush(out, report, manifest, contract_sha):
    report['contract_sha256'] = contract_sha; manifest['contract_sha256'] = contract_sha; manifest['status'] = report['status']; manifest['build_ready'] = False
    _write_json(out / 'report.json', report); manifest['report_sha256'] = _sha_file(out / 'report.json'); _write_json(out / 'manifest.json', manifest)
def _extract(f, entry, dest, state, c):
    _require(entry['size'] <= c['limits']['resource_bytes'], 'resource_limit_exceeded'); _require(state['total'] + entry['size'] <= c['limits']['total_output_bytes'], 'total_limit_exceeded')
    _no_reparse(dest.parent); dest.parent.mkdir(parents=True, exist_ok=True); _no_reparse(dest.parent)
    f.seek(entry['offset']); h = hashlib.sha256(); left = entry['size']; first = b''
    with open(dest, 'wb') as w:
        while left:
            b = f.read(min(CHUNK, left)); _require(b, 'truncated_pbo_payload')
            if len(first) < 16: first += b[:16 - len(first)]
            h.update(b); w.write(b); left -= len(b)
        w.flush(); os.fsync(w.fileno())
    state['total'] += entry['size']
    return h.hexdigest(), first.hex()
def _process_pbo(path, pbo_table, expected_size=None):
    _no_reparse(path); p = Path(path); _require(p.is_file(), 'missing_pbo:' + str(p))
    sb = os.lstat(p); f = open(p, 'rb')
    try:
        fsb = os.fstat(f.fileno()); _require(_stat_id(sb) == _stat_id(fsb), 'pbo_stat_open_mismatch')
        size = fsb.st_size
        if expected_size is not None: _require(size == expected_size, 'pbo_size_mismatch:' + str(p))
        h1 = _hash_stream(f); f.seek(0); props, entries = pbo_table(f, size)
        return f, {'path': str(p), 'size': size, 'sha256_observed': h1, 'stat_before': _stat_id(fsb), 'properties': props, 'entries': entries}
    except Exception:
        f.close(); raise
def _finish_pbo(f, info):
    try:
        h2 = _hash_stream(f); fsb = os.fstat(f.fileno()); sa = os.lstat(info['path'])
        info['sha256_after'] = h2; info['stat_after'] = _stat_id(sa)
        _require(h2 == info['sha256_observed'], 'pbo_changed_during_read'); _require(_stat_id(fsb) == info['stat_before'] and _stat_id(sa) == info['stat_before'], 'pbo_stat_changed')
        info.pop('entries', None); info.pop('properties', None)
        return info
    finally: f.close()
def run_discovery(contract, contract_sha256, out, converter=None, converter_factory=None):
    start = time.monotonic(); out = Path(out)
    _require(not out.exists(), 'output_already_exists'); _require(out.drive.lower() != 'p:', 'never_write_p')
    c, data = _load_contract(contract, contract_sha256); contract_sha = contract_sha256.lower(); lim = c['limits']; deadline = start + lim['seconds']
    docs = _parse_sources(c); linkage = _linkage(docs, c['pins'], c); _bind_selected(c, docs); entry_by, model_by = _catalog(docs); refs, used = _all_lod_refs(c, model_by)
    _no_reparse(out); out.mkdir(parents=True); _no_reparse(out); (out / 'assets').mkdir(); state = {'out': out, 'total': 0, 'conversions': 0}
    report = {'schema': 'ROAD_INSTALLED_MATERIAL_PROBE_REPORT_V1', 'contract_sha256': contract_sha, 'status': 'INCONCLUSIVE_INITIAL_DISCOVERY', 'build_ready': False, 'dependency_closure': 'NOT_EVALUATED', 'pivot': 'UNKNOWN', 'width': 'UNKNOWN', 'accesses': 'UNKNOWN', 'assets': [], 'tables': {}, 'external': [], 'conversions': [], 'phases': [], 'linkage': linkage, 'all_lod_refs': refs, 'catalog_models_used': used}
    manifest = {'schema': MANIFEST_SCHEMA, 'contract_sha256': contract_sha, 'report_sha256': None, 'status': 'INCONCLUSIVE_INITIAL_DISCOVERY', 'build_ready': False, 'dependency_closure': 'NOT_EVALUATED', 'pivot': 'UNKNOWN', 'width': 'UNKNOWN', 'accesses': 'UNKNOWN', 'references_closed': False, 'assets': [], 'artifacts': [], 'evidence_artifacts': []}
    def save(phase): report['phases'].append(phase); _flush(out, report, manifest, contract_sha)
    stack = ExitStack()
    try:
        save('pins_and_bindings'); pbo_table = load_helper_pbo_table(c['helper'], c['pins']); prefix_norm = _norm(c['pbos']['roads']['prefix'])
        roads_f, roads = _process_pbo(c['pbos']['roads']['path'], pbo_table, c['pbos']['roads']['bytes']); stack.callback(roads_f.close)
        roads_entries = {_norm(e['name']): e for e in roads['entries']}; props = roads['properties']
        _require(roads['sha256_observed'] == c['pbos']['roads']['sha256'].lower(), 'roads_global_sha_mismatch'); _require(_norm(props.get('prefix', '')) == prefix_norm, 'roads_prefix_mismatch')
        report['tables']['roads'] = {'prefix': props.get('prefix'), 'entry_count': len(roads_entries), 'sha256_observed_now': roads['sha256_observed']}
        for en, e in entry_by.items():
            t = roads_entries.get(en); _require(t is not None and t['size'] == e['size'] and t['mime'] == e['mime'], 'catalog_entry_table_mismatch:' + en)
        save('roads_table')
        for s in c['selected']:
            _check_deadline(deadline); e = roads_entries.get(_norm(s['entry'])); _require(e is not None, 'selected_missing_in_roads:' + s['entry'])
            if e['mime'] != 0: report['assets'].append({'virtual_path': s['virtual_path'], 'kind': s['kind'], 'status': 'INCONCLUSIVE_UNSUPPORTED_COMPRESSION', 'mime': e['mime'], 'provider': 'roads'}); continue
            dest = _safe_local(out, s['virtual_path']); sha, pfx = _extract(roads_f, e, dest, state, c)
            _require(sha == s['sha256'].lower(), 'selected_sha_mismatch_vs_r0:' + s['virtual_path'])
            cat = entry_by.get(_norm(s['entry'])); _require(cat is not None and cat['sha256'].lower() == sha, 'selected_catalog_sha_mismatch')
            asset = {'virtual_path': s['virtual_path'], 'kind': s['kind'], 'local_path': dest.relative_to(out).as_posix(), 'sha256': sha, 'size': e['size'], 'prefix16': pfx, 'source_offset': e['offset'], 'mime': e['mime'], 'provider': 'roads', 'status': 'EXTRACTED'}
            report['assets'].append(asset); manifest['assets'].append(asset); manifest['artifacts'].append({'local_path': asset['local_path'], 'sha256': sha, 'size': e['size']})
        report['tables']['roads'].update(_finish_pbo(roads_f, roads)); save('selected_extracted')
        providers = []; prefix_unknown = False
        for name in ('surfaces', 'surfaces_bliss'):
            _check_deadline(deadline); info = c['pbos'][name]
            if not Path(info['path']).is_file(): report['tables'][name] = {'status': 'MISSING', 'observed_not_retroactive': True}; prefix_unknown = True; continue
            f, tab = _process_pbo(info['path'], pbo_table, info['bytes']); stack.callback(f.close)
            entries = {_norm(e['name']): e for e in tab['entries']}; prefix = tab['properties'].get('prefix')
            if not prefix: prefix_unknown = True
            report['tables'][name] = {'prefix': prefix, 'entry_count': len(entries), 'sha256_observed_now': tab['sha256_observed'], 'observed_not_retroactive': True, 'size': tab['size'], 'status': 'READ' if prefix else 'INCONCLUSIVE_PREFIX_UNKNOWN'}
            providers.append((name, f, tab, entries, prefix))
        ext = c['external'][0]; matches = []
        for name, f, tab, entries, prefix in providers:
            if not prefix: continue
            for en, e in entries.items():
                if _norm(prefix) + '/' + en == _norm(ext): matches.append((name, f, tab, e))
        ext_rec = {'virtual_path': ext, 'providers': [m[0] for m in matches], 'status': 'UNRESOLVED_EXTERNAL'}
        if prefix_unknown: ext_rec['status'] = 'INCONCLUSIVE_PREFIX_UNKNOWN'
        elif len(matches) > 1: ext_rec['status'] = 'AMBIGUOUS_PROVIDER'
        elif len(matches) == 1:
            name, f, tab, e = matches[0]
            if e['mime'] != 0: ext_rec['status'] = 'INCONCLUSIVE_UNSUPPORTED_COMPRESSION'; ext_rec['mime'] = e['mime']
            else:
                dest = _safe_local(out, ext); sha, pfx = _extract(f, e, dest, state, c)
                asset = {'virtual_path': ext, 'kind': 'texture', 'local_path': dest.relative_to(out).as_posix(), 'sha256': sha, 'size': e['size'], 'prefix16': pfx, 'source_offset': e['offset'], 'mime': e['mime'], 'provider': name, 'status': 'EXTRACTED'}
                ext_rec.update({'status': 'RESOLVED', 'sha256': sha, 'provider': name}); report['assets'].append(asset); manifest['assets'].append(asset); manifest['artifacts'].append({'local_path': asset['local_path'], 'sha256': sha, 'size': e['size']})
        report['external'].append(ext_rec)
        for name, f, tab, entries, prefix in providers: report['tables'][name].update(_finish_pbo(f, tab))
        save('external_checked')
        conv_factory = converter_factory or (_default_converter_factory(c, deadline, state) if converter is None else None); conv_instance = converter
        for asset in [a for a in report['assets'] if a.get('kind') == 'material' and a.get('status') == 'EXTRACTED']:
            data2 = (out / asset['local_path']).read_bytes(); kind = detect_material(data2); asset['material_detection'] = kind
            if kind == 'TEXT_SAMPLE': asset['material_status'] = 'TEXT_SAMPLE'
            elif kind == 'UNKNOWN': asset['material_status'] = 'UNKNOWN'
            elif kind == 'RAP':
                if state['conversions'] >= lim['conversions']: asset['material_status'] = 'CONVERSION_BUDGET_EXHAUSTED'; continue
                state['conversions'] += 1; original = out / asset['local_path']; decoded = out / 'decoded' / (_norm(asset['virtual_path']) + '.txt'); _no_reparse(decoded.parent); decoded.parent.mkdir(parents=True, exist_ok=True); _no_reparse(decoded.parent); _require(not decoded.exists(), 'conversion_output_not_fresh')
                receipt = out / 'receipts' / ('conversion_' + str(state['conversions']))
                if conv_instance is None: conv_instance = conv_factory()
                conv = conv_instance
                input_before = _sha_file(original); remaining = deadline - time.monotonic(); _require(remaining > 0, 'deadline_exceeded')
                result = conv(original, decoded, receipt, min(remaining, lim['conversion_seconds']), lim['rss_bytes'])
                _require(_sha_file(original) == input_before, 'mutation_bytes_after_extract')
                rec = {'virtual_path': asset['virtual_path'], 'result': result if isinstance(result, dict) else repr(result), 'input_sha256': input_before}
                if isinstance(result, dict):
                    for kk in ('receipt_completion_path', 'receipt_completion_sha256', 'receipt_running_path', 'receipt_running_sha256', 'installed_tool_sha256_before', 'installed_tool_sha256_after'):
                        if kk in result: rec[kk] = result[kk]
                report['conversions'].append(rec)
                if isinstance(result, dict):
                    for kk in ('stdout_path', 'stdout_sha256', 'stderr_path', 'stderr_sha256'):
                        if kk in result: rec[kk] = result[kk]
                    for pk, hk in (('receipt_running_path', 'receipt_running_sha256'), ('receipt_completion_path', 'receipt_completion_sha256'), ('stdout_path', 'stdout_sha256'), ('stderr_path', 'stderr_sha256')):
                        if pk in result and hk in result and (out / result[pk]).is_file(): manifest['evidence_artifacts'].append({'local_path': result[pk], 'sha256': result[hk], 'size': (out / result[pk]).stat().st_size})
                if not isinstance(result, dict): asset['material_status'] = 'CONVERSION_FAILED'
                elif result.get('reason') == 'TIMEOUT': asset['material_status'] = 'CONVERSION_TIMEOUT'
                elif result.get('reason') is not None or result.get('rc') != 0: asset['material_status'] = 'CONVERSION_FAILED'
                elif not decoded.is_file() or decoded.stat().st_size == 0: asset['material_status'] = 'CONVERSION_EMPTY'
                else:
                    _require(decoded.stat().st_size <= lim['resource_bytes'], 'resource_limit_exceeded'); _require(state['total'] + decoded.stat().st_size <= lim['total_output_bytes'], 'total_limit_exceeded'); state['total'] += decoded.stat().st_size
                    asset['material_status'] = 'DECODED_SAMPLE_ONLY'; asset['decoded_local_path'] = decoded.relative_to(out).as_posix(); manifest['artifacts'].append({'local_path': asset['decoded_local_path'], 'sha256': _sha_file(decoded), 'size': decoded.stat().st_size})
            else: asset['material_status'] = kind
        save('materials_classified')
        for path in [c['sources'][k] for k in SOURCE_FIELDS] + [c['helper'], c['runner'], c['cfgconvert']]: _require(_pin_for(c['pins'], path) == _sha_file(path), 'final_pin_mismatch:' + str(path))
        inconclusive = any(a.get('status', '').startswith('INCONCLUSIVE') or a.get('material_status') in ('UNKNOWN', 'CONVERSION_FAILED', 'CONVERSION_TIMEOUT', 'CONVERSION_EMPTY', 'CONVERSION_BUDGET_EXHAUSTED') or str(a.get('material_status', '')).startswith('INCONCLUSIVE') for a in report['assets']) or ext_rec['status'].startswith('INCONCLUSIVE') or ext_rec['status'] == 'AMBIGUOUS_PROVIDER'
        report['final_pin_check'] = 'OK'; report['status'] = 'INCONCLUSIVE_INITIAL_DISCOVERY' if inconclusive else 'INITIAL_DISCOVERY_ONLY'; report['total_output_bytes'] = state['total']; manifest['total_output_bytes'] = state['total']; save('complete_initial_discovery')
        return report
    except Exception as e:
        report['status'] = 'INCONCLUSIVE_INITIAL_DISCOVERY'; report['error'] = type(e).__name__ + ':' + str(e); manifest['status'] = 'INCONCLUSIVE_INITIAL_DISCOVERY'; manifest['error'] = report['error']
        try: _flush(out, report, manifest, contract_sha)
        except Exception: pass
        raise
    finally: stack.close()
def consume_saved_manifest(out, expected_manifest_sha, expected_contract_sha256):
    out = Path(out); _require(_is_sha(expected_manifest_sha), 'manifest_sha_required'); _require(_is_sha(expected_contract_sha256), 'contract_sha256_required')
    _require((out / 'manifest.json').is_file() and (out / 'report.json').is_file(), 'saved_output_missing'); _no_reparse(out / 'manifest.json'); _no_reparse(out / 'report.json')
    data = (out / 'manifest.json').read_bytes(); _require(_sha_bytes(data) == expected_manifest_sha.lower(), 'manifest_sha_mismatch'); m = strict_loads(data)
    report_data = (out / 'report.json').read_bytes(); rep = strict_loads(report_data)
    _require(m.get('schema') == MANIFEST_SCHEMA, 'bad_manifest_schema'); _require(m.get('contract_sha256') == expected_contract_sha256.lower(), 'manifest_contract_mismatch'); _require(rep.get('contract_sha256') == expected_contract_sha256.lower(), 'report_contract_mismatch')
    _require(m.get('report_sha256') == _sha_bytes(report_data), 'manifest_report_mismatch')
    _require(m.get('status') == 'INITIAL_DISCOVERY_ONLY' and rep.get('status') == 'INITIAL_DISCOVERY_ONLY', 'manifest_status_rejected:' + str(m.get('status')))
    _require(m.get('dependency_closure') == 'NOT_EVALUATED' and m.get('references_closed') is False, 'closure_claim_rejected'); _require(m.get('build_ready') is False and rep.get('build_ready') is False, 'build_ready_rejected')
    assets = m.get('assets'); artifacts = m.get('artifacts'); _require(isinstance(assets, list) and isinstance(artifacts, list), 'bad_manifest_assets')
    rep_assets = rep.get('assets'); _require(isinstance(rep_assets, list), 'bad_report_assets')
    extracted = [a for a in rep_assets if isinstance(a, dict) and a.get('status') == 'EXTRACTED']; _require(assets == extracted, 'manifest_assets_not_report_extracted')
    roads_kinds = {}
    for a in assets:
        _require(isinstance(a, dict) and _is_sha(a.get('sha256')) and isinstance(a.get('size'), int) and not isinstance(a.get('size'), bool) and isinstance(a.get('local_path'), str), 'bad_asset_binding')
        if a.get('provider') == 'roads': roads_kinds[a.get('kind')] = roads_kinds.get(a.get('kind'), 0) + 1
    _require(roads_kinds == {'model': 3, 'material': 2, 'texture': 2}, 'required_roads_assets_mismatch')
    exts = rep.get('external'); _require(isinstance(exts, list) and len(exts) == 1 and isinstance(exts[0], dict) and exts[0].get('status') == 'RESOLVED', 'external_not_resolved')
    _require(len([a for a in assets if a.get('virtual_path') == exts[0].get('virtual_path') and a.get('sha256') == exts[0].get('sha256') and a.get('provider') == exts[0].get('provider')]) == 1, 'external_asset_not_bound')
    expected = {}; decoded_paths = []
    for a in assets:
        _validate_raw_virtual(a['local_path']); _require(a['local_path'] not in expected, 'duplicate_asset_local_path'); expected[a['local_path']] = {'local_path': a['local_path'], 'sha256': a['sha256'].lower(), 'size': a['size']}
        if a.get('material_status') == 'DECODED_SAMPLE_ONLY':
            dp = a.get('decoded_local_path'); _require(isinstance(dp, str), 'decoded_path_missing'); _validate_raw_virtual(dp); _require(dp not in expected and dp not in decoded_paths, 'duplicate_decoded_local_path'); decoded_paths.append(dp)
    _require(len(artifacts) > 0 and len(artifacts) == len(expected) + len(decoded_paths), 'artifact_count_mismatch')
    artifact_by = {}
    for a in artifacts:
        _require(isinstance(a, dict) and set(a) == {'local_path', 'sha256', 'size'}, 'bad_artifact_fields'); _validate_raw_virtual(a['local_path']); _require(a['local_path'] not in artifact_by, 'duplicate_artifact'); artifact_by[a['local_path']] = a
        p = out.joinpath(*a['local_path'].split('/')); _no_reparse(p); _require(p.is_file(), 'artifact_missing:' + a['local_path']); _require(p.stat().st_size == a['size'] and _sha_file(p) == a['sha256'], 'artifact_hash_mismatch:' + a['local_path'])
    _require(set(artifact_by) == set(expected) | set(decoded_paths), 'artifact_set_mismatch')
    for lp, exp in expected.items(): _require(artifact_by[lp] == exp, 'artifact_asset_mismatch:' + lp)
    convs = rep.get('conversions'); _require(isinstance(convs, list), 'bad_report_conversions'); evidence = m.get('evidence_artifacts'); _require(isinstance(evidence, list), 'bad_evidence_artifacts')
    expected_evidence = {}
    for conv in convs:
        if isinstance(conv, dict):
            for pk, hk in (('receipt_running_path', 'receipt_running_sha256'), ('receipt_completion_path', 'receipt_completion_sha256'), ('stdout_path', 'stdout_sha256'), ('stderr_path', 'stderr_sha256')):
                if pk in conv: _require(conv[pk] not in expected_evidence, 'duplicate_evidence_path'); expected_evidence[conv[pk]] = conv.get(hk)
    evidence_by = {}
    for a in evidence:
        _require(isinstance(a, dict) and set(a) == {'local_path', 'sha256', 'size'}, 'bad_evidence_fields'); _validate_raw_virtual(a['local_path']); _require(a['local_path'] not in evidence_by, 'duplicate_evidence_artifact'); evidence_by[a['local_path']] = a
        p = out.joinpath(*a['local_path'].split('/')); _no_reparse(p); _require(p.is_file(), 'evidence_missing:' + a['local_path']); _require(p.stat().st_size == a['size'] and _sha_file(p) == a['sha256'], 'evidence_hash_mismatch:' + a['local_path'])
    _require(set(evidence_by) == set(expected_evidence), 'evidence_set_mismatch')
    for lp, h in expected_evidence.items(): _require(evidence_by[lp]['sha256'] == h, 'evidence_receipt_mismatch:' + lp)
    return m
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--contract', required=True); ap.add_argument('--contract-sha256', required=True); ap.add_argument('--out', required=True); a = ap.parse_args(argv)
    try: run_discovery(a.contract, a.contract_sha256, a.out); return 0
    except Exception as e: print('INCONCLUSIVE_INITIAL_DISCOVERY:' + str(e), file=sys.stderr); return 2
if __name__ == '__main__': raise SystemExit(main())
