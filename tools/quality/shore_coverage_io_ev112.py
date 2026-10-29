#!/usr/bin/env python3
import hashlib, importlib.util, json, math, os, stat
from pathlib import Path
class Bad(Exception): pass
class Resource(Exception): pass
P = 48; SCALE = 1 << P; MAXBITS = 4096; QUERY_OPS = 100000; CHAIN_OPS = 4000000; MAXEDGES = 14000
REPARSE = 0x400
KNOWN_HELPERS = {'tools/quality/certified_shore_kernel_ev112.py': 'ef844931862c1aa2d181caa5000b4843a4b1587da7149fb033a8efa5248abe64', 'tools/quality/verify_certified_shore_kernel_ev112.py': 'ab1977bc1ed283d00cb9aedab56ad1b83d2596a17f49c3558825aeec3ec8f2ca', 'tools/quality/shore_numeric_discovery_ev112.py': '3264f82294a2411e4f1d902c42173a01ef1f72244d6b220bba91e49a4596b696', 'tools/quality/shore_prefix_pilot_ev112.py': '8154fbe98363a0ce987675178bd2f8084b9cb1e7b8a163559cb424b62cc3bf38', 'tools/quality/verify_shore_prefix_pilot_ev112.py': '98cdab4fe6e1cd4c1898cd1e44139a00a79e4fffe934193d4689523b6807c773'}
THR_RATIO = [3022314549036573, 302231454903657293676544]
SOURCE_KEYS = {'q02b0_report', 'q02a_summary', 'q02b2_report', 'q02b2_consumer', 'q02b1_contract', 'old_oracles', 'plan', 'derivation'}
def is_int(v): return type(v) is int
def is_hex64(v): return isinstance(v, str) and len(v) == 64 and all(c in '0123456789abcdef' for c in v)
def sha_bytes(d): return hashlib.sha256(d).hexdigest()
def is_reparse_stat(st):
 return bool(stat.S_ISLNK(st.st_mode) or (getattr(st, 'st_file_attributes', 0) & REPARSE))
def classify_stat(st):
 if is_reparse_stat(st): return 'link'
 if stat.S_ISDIR(st.st_mode): return 'dir'
 if stat.S_ISREG(st.st_mode): return 'file'
 return 'other'
def lstat_checked(path):
 p = Path(path)
 try: st = os.lstat(p)
 except FileNotFoundError: return None
 except Exception as e: raise Bad('stat:' + str(e))
 if classify_stat(st) == 'link': raise Bad('link:' + str(p))
 return st
def exists_nofollow(path): return lstat_checked(path) is not None
def require_dir(path):
 st = lstat_checked(path)
 if st is None or classify_stat(st) != 'dir': raise Bad('notdir:' + str(path))
 return Path(path)
def require_file(path):
 st = lstat_checked(path)
 if st is None or classify_stat(st) != 'file': raise Bad('notfile:' + str(path))
 return Path(path)
def check_ancestors(path):
 p = Path(path).absolute(); cur = Path(p.anchor)
 for part in p.parts[1:]:
  cur = cur / part
  st = lstat_checked(cur)
  if st is None: return
def list_entries(path):
 require_dir(path); out = {}
 try: entries = list(os.scandir(Path(path)))
 except Exception as e: raise Bad('list:' + str(e))
 for e in entries:
  st = lstat_checked(e.path); kind = classify_stat(st)
  if kind not in ('dir', 'file'): raise Bad('entrykind:' + e.name)
  out[e.name] = kind
 return out
def capture_total_bytes(path, limit):
 require_dir(path); total = 0; stack = [Path(path)]
 while stack:
  cur = stack.pop()
  for name, kind in list_entries(cur).items():
   child = cur / name
   if kind == 'dir': stack.append(child)
   else:
    total += os.lstat(child).st_size
    if total > limit: raise Bad('totalbytes')
 return total
def read_bounded(path, limit):
 p = require_file(path)
 try:
  with open(p, 'rb') as fh: d = fh.read(limit + 1)
 except Bad: raise
 except Exception as e: raise Bad('read:' + str(e))
 if len(d) > limit: raise Bad('large:' + str(p))
 return d
def sha_file(path, limit): return sha_bytes(read_bounded(path, limit))
def strict_parse(data, label='json'):
 def nodup(pairs):
  o = {}
  for k, v in pairs:
   if k in o: raise Bad(label + 'dup')
   o[k] = v
  return o
 def badc(v): raise Bad(label + 'const')
 try: return json.loads(data.decode('utf-8'), object_pairs_hook=nodup, parse_constant=badc)
 except Bad: raise
 except Exception as e: raise Bad(label + ':' + str(e))
def canon(obj):
 try: return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
 except Exception as e: raise Bad('canon:' + str(e))
def selector_sha(sel): return sha_bytes(canon(sel))
def strict_eq(a, b):
 if type(a) != type(b): return False
 if isinstance(a, dict): return set(a) == set(b) and all(strict_eq(a[k], b[k]) for k in a)
 if isinstance(a, list): return len(a) == len(b) and all(strict_eq(x, y) for x, y in zip(a, b))
 return a == b
def is_ratio(v):
 return isinstance(v, list) and len(v) == 2 and is_int(v[0]) and is_int(v[1]) and v[1] > 0 and math.gcd(abs(v[0]), v[1]) == 1
def keys(o, s, label='keys'):
 if not isinstance(o, dict) or set(o) != set(s): raise Bad(label)
def resolve(root, p):
 q = Path(p); return q if q.is_absolute() else Path(root) / q
def load_sealed(root, rel, expected, prefix):
 p = Path(root) / rel; d = read_bounded(p, 17 * 1024 * 1024)
 if sha_bytes(d) != expected: raise Bad('helperpin:' + rel)
 spec = importlib.util.spec_from_file_location(prefix + expected[:12], str(p)); m = importlib.util.module_from_spec(spec); m.__file__ = str(p); exec(compile(d, str(p), 'exec'), m.__dict__); return m
def verify_helpers(root, helpers):
 if not isinstance(helpers, dict) or helpers != KNOWN_HELPERS: raise Bad('helpers')
 for rel, sha in KNOWN_HELPERS.items():
  if sha_file(Path(root) / rel, 17 * 1024 * 1024) != sha: raise Bad('helperfile:' + rel)
def claims(contract): return {'human_cases': contract['human_cases'], 'controls': contract['controls'], 'c1': contract['c1'], 'natural_positive_count': contract['natural_positive_count'], 'calibration_ready': contract['calibration_ready'], 'angle_state': contract['angle_state'], 'map_repaired': contract['map_repaired']}
def _check_limits(c):
 keys(c['read_limits'], {'archive_bytes', 'required_uncompressed_bytes', 'header_bytes', 'members'}, 'read_limits'); keys(c['output_limits'], {'cache_bytes', 'shard_bytes', 'query_bytes', 'terminal_bytes', 'manifest_bytes', 'total_bytes'}, 'output_limits'); keys(c['budgets'], {'author_s', 'code_review_s', 'suite_s', 'capture_s', 'consumer_s', 'rss_bytes'}, 'budgets')
 caps_r = {'archive_bytes': 67108864, 'required_uncompressed_bytes': 8388608, 'header_bytes': 16384, 'members': 32}; caps_o = {'cache_bytes': 16777216, 'shard_bytes': 16777216, 'query_bytes': 262144, 'terminal_bytes': 1048576, 'manifest_bytes': 1048576, 'total_bytes': 2147483648}
 for k, v in caps_r.items():
  if not is_int(c['read_limits'][k]) or not (0 < c['read_limits'][k] <= v): raise Bad('readlimit')
 for k, v in caps_o.items():
  if not is_int(c['output_limits'][k]) or not (0 < c['output_limits'][k] <= v): raise Bad('outlimit')
 for v in c['budgets'].values():
  if not is_int(v) or v <= 0: raise Bad('budget')
 if c['budgets']['rss_bytes'] > 536870912: raise Bad('rss')
def load_contract(root, contract_path, contract_sha):
 root = Path(root)
 if not is_hex64(contract_sha) or contract_sha != contract_sha.lower(): raise Bad('contractshaarg')
 cp = resolve(root, contract_path); data = read_bounded(cp, 16 * 1024 * 1024); csha = sha_bytes(data)
 if csha != contract_sha: raise Bad('contractsha')
 c = strict_parse(data, 'contract')
 keys(c, {'schema', 'scope', 'npz_path', 'npz_sha256', 'selectors', 'oracles', 'sources', 'helpers', 'h', 'expected', 'p', 'threshold_ratio', 'max_bits', 'query_ops', 'chain_ops', 'max_edges', 'read_limits', 'output_limits', 'human_cases', 'controls', 'c1', 'natural_positive_count', 'calibration_ready', 'angle_state', 'budgets', 'schema_document', 'schema_document_sha256', 'map_repaired', 'roles'}, 'contractkeys')
 if c['schema'] != 'q02b3.v1' or c['scope'] != 'NUMERIC_COVERAGE_ONLY': raise Bad('schema')
 if not is_int(c['p']) or c['p'] != 48 or not is_ratio(c['threshold_ratio']) or c['threshold_ratio'] != THR_RATIO or not is_int(c['max_bits']) or c['max_bits'] != 4096 or not is_int(c['query_ops']) or c['query_ops'] != QUERY_OPS or not is_int(c['chain_ops']) or c['chain_ops'] != CHAIN_OPS or not is_int(c['max_edges']) or c['max_edges'] != MAXEDGES: raise Bad('numericcaps')
 if not isinstance(c['h'], list) or strict_eq(c['h'], [6, 12, 24, 48, 96]) is not True: raise Bad('h')
 if not is_hex64(c['npz_sha256']) or not isinstance(c['npz_path'], str) or not c['npz_path']: raise Bad('npzpin')
 if not strict_eq(c['human_cases'], {'count': 9, 'state': 'GEOMETRY_UNBOUND', 'resolved': 0}) or not is_int(c['controls']) or c['controls'] != 4 or c['c1'] != 'NOT_REVIEWED' or not is_int(c['natural_positive_count']) or c['natural_positive_count'] != 0 or c['calibration_ready'] is not False or c['angle_state'] != 'PENDING_CERTIFIED_ANGLE' or c['map_repaired'] is not False: raise Bad('claims')
 _check_limits(c); verify_helpers(root, c['helpers'])
 if not is_hex64(c['schema_document_sha256']) or not isinstance(c['schema_document'], str): raise Bad('schemadoc')
 if sha_file(resolve(root, c['schema_document']), 16 * 1024 * 1024) != c['schema_document_sha256']: raise Bad('schemadocsha')
 keys(c['roles'], {'producer_imports', 'consumer_imports', 'regression_only'}, 'roles')
 if c['roles'] != {'producer_imports': ['tools/quality/shore_prefix_pilot_ev112.py', 'tools/quality/certified_shore_kernel_ev112.py', 'tools/quality/shore_numeric_discovery_ev112.py'], 'consumer_imports': ['tools/quality/verify_certified_shore_kernel_ev112.py', 'tools/quality/shore_numeric_discovery_ev112.py'], 'regression_only': ['tools/quality/verify_shore_prefix_pilot_ev112.py']}: raise Bad('roles')
 for sec in ('selectors', 'oracles'):
  keys(c[sec], {'path', 'sha256'}, sec)
  if not isinstance(c[sec]['path'], str) or not is_hex64(c[sec]['sha256']): raise Bad(sec + 'sha')
 if not isinstance(c['sources'], dict) or set(c['sources']) != SOURCE_KEYS: raise Bad('sources')
 for name, src in c['sources'].items():
  keys(src, {'path', 'sha256'}, 'source')
  if not isinstance(src['path'], str) or not is_hex64(src['sha256']): raise Bad('sourcesha')
  if sha_file(resolve(root, src['path']), 64 * 1024 * 1024) != src['sha256']: raise Bad('sourcefile:' + name)
 sel_data = read_bounded(resolve(root, c['selectors']['path']), 16 * 1024 * 1024)
 if sha_bytes(sel_data) != c['selectors']['sha256']: raise Bad('selectorsha')
 selectors = strict_parse(sel_data, 'selectors')
 keys(selectors, {'schema', 'npz_sha256', 'universe', 'chains'}, 'selectors')
 if selectors['schema'] != 'q02b3-selectors.v1' or selectors['npz_sha256'] != c['npz_sha256'] or not is_int(selectors['universe']): raise Bad('selectorsmeta')
 ora_data = read_bounded(resolve(root, c['oracles']['path']), 16 * 1024 * 1024)
 if sha_bytes(ora_data) != c['oracles']['sha256']: raise Bad('oraclesha')
 oracles = strict_parse(ora_data, 'oracles')
 keys(oracles, {'schema', 'natural_positive_count', 'calibration_ready', 'tree_integer_reduction_only', 'sqrt2', 'threshold', 'station_literals', 'required_negatives', 'station_convention'}, 'oracles')
 if oracles['schema'] != 'q02b3-literal-oracles.v1' or not is_int(oracles['natural_positive_count']) or oracles['natural_positive_count'] != 0 or oracles['calibration_ready'] is not False: raise Bad('oraclesmeta')
 chs = selectors['chains']
 if not isinstance(chs, list) or not chs: raise Bad('chains')
 tot_core = 0; tot_edges = 0; closed_n = 0; maxcore = 0; maxedges = 0
 for i, s in enumerate(chs):
  keys(s, {'chain_id', 'closed', 'point_offset', 'segment_offset', 'core_count', 'core_float64_le_sha256', 'centers'}, 'selector')
  if not is_int(s['chain_id']) or s['chain_id'] != i or type(s['closed']) is not bool or not is_int(s['core_count']) or s['core_count'] < 1: raise Bad('selectorid')
  for off in (s['point_offset'], s['segment_offset']):
   if not isinstance(off, list) or len(off) != 2 or any(not is_int(x) for x in off) or not (0 <= off[0] < off[1]): raise Bad('offset')
  pd = s['point_offset'][1] - s['point_offset'][0]; sd = s['segment_offset'][1] - s['segment_offset'][0]
  if sd != pd - 1 or s['core_count'] != pd - (1 if s['closed'] else 0): raise Bad('corecount')
  if not is_hex64(s['core_float64_le_sha256']): raise Bad('corehash')
  if not strict_eq(s['centers'], {'start': 0, 'stop': s['core_count'], 'step': 1}): raise Bad('centers')
  e = s['core_count'] if s['closed'] else s['core_count'] - 1
  if e < 1 or e > MAXEDGES: raise Bad('edgesdomain')
  tot_core += s['core_count']; tot_edges += e; closed_n += 1 if s['closed'] else 0; maxcore = max(maxcore, s['core_count']); maxedges = max(maxedges, e)
 if selectors['universe'] != tot_core * 5: raise Bad('universe')
 keys(c['expected'], {'chains', 'closed_chains', 'core_vertices', 'edges', 'universe', 'open_chains', 'max_core_count', 'max_edges_observed', 'degenerate_chains', 'degenerate_chain_ids'}, 'expected')
 exp = {'chains': len(chs), 'closed_chains': closed_n, 'core_vertices': tot_core, 'edges': tot_edges, 'universe': tot_core * 5, 'open_chains': len(chs) - closed_n, 'max_core_count': maxcore, 'max_edges_observed': maxedges}
 for k, v in exp.items():
  if not is_int(c['expected'][k]) or c['expected'][k] != v: raise Bad('expected:' + k)
 degids = c['expected']['degenerate_chain_ids']
 if not is_int(c['expected']['degenerate_chains']) or not isinstance(degids, list) or c['expected']['degenerate_chains'] != len(degids) or any(not is_int(x) for x in degids) or degids != sorted(set(degids)) or any(not (0 <= x < len(chs)) for x in degids): raise Bad('expecteddeg')
 if sha_file(Path(c['npz_path']), c['read_limits']['archive_bytes']) != c['npz_sha256']: raise Bad('npzsha')
 return c, csha, selectors, oracles
def load_npz(root, contract):
 tr = load_sealed(root, 'tools/quality/shore_numeric_discovery_ev112.py', KNOWN_HELPERS['tools/quality/shore_numeric_discovery_ev112.py'], 'tr_')
 tc = {'npz_path': contract['npz_path'], 'npz_sha256': contract['npz_sha256'], 'limits': contract['read_limits']}
 try: arrays, meta, other, before, after = tr._read_npz(tc)
 except Exception as e: raise Bad('npz:' + str(e))
 if set(arrays) != {'point_offsets', 'chain_offsets', 'chain_points', 'closed'}: raise Bad('arrays')
 return arrays
def source_chains(arrays, selectors):
 po = arrays['point_offsets']; co = arrays['chain_offsets']; cp = arrays['chain_points']; cl = arrays['closed']
 pol = po.tolist(); col = co.tolist(); cll = cl.tolist()
 if str(po.dtype) not in ('int64', '<i8') or str(co.dtype) not in ('int64', '<i8') or str(cp.dtype) not in ('<f8', 'float64') or str(cl.dtype) != 'bool': raise Bad('dtypes')
 if len(cp.shape) != 2 or cp.shape[1] != 2 or len(pol) != len(cll) + 1 or len(col) != len(cll) + 1 or pol[0] != 0 or col[0] != 0 or pol[-1] != cp.shape[0] or pol != sorted(pol) or col != sorted(col): raise Bad('offsets')
 if any(col[i + 1] - col[i] != pol[i + 1] - pol[i] - 1 for i in range(len(cll))): raise Bad('segmentoffsets')
 chs = selectors['chains']
 if not isinstance(chs, list) or len(chs) != len(cll): raise Bad('selectorcoverage')
 if [s['chain_id'] for s in chs] != list(range(len(cll))): raise Bad('selectorids')
 pcur = 0; scur = 0
 for s in chs:
  if s['point_offset'][0] != pcur or s['segment_offset'][0] != scur: raise Bad('selectorcoverage')
  pcur = s['point_offset'][1]; scur = s['segment_offset'][1]
 if pcur != pol[-1] or scur != col[-1]: raise Bad('selectorcoverage')
 out = []
 for s in chs:
  ci = s['chain_id']
  if pol[ci] != s['point_offset'][0] or pol[ci + 1] != s['point_offset'][1] or col[ci] != s['segment_offset'][0] or col[ci + 1] != s['segment_offset'][1] or bool(cll[ci]) != s['closed']: raise Bad('selectorbind')
  sub = cp[s['point_offset'][0]:s['point_offset'][1]]; core = sub[:-1] if s['closed'] else sub
  if s['closed'] and (len(sub) < 2 or sub[-1].astype('<f8').tobytes() != sub[0].astype('<f8').tobytes()): raise Bad('closedrepeat')
  if sha_bytes(core.astype('<f8').tobytes()) != s['core_float64_le_sha256']: raise Bad('corehash')
  pts = []
  for row in core.tolist():
   x = float(row[0]); z = float(row[1])
   if not math.isfinite(x) or not math.isfinite(z): raise Bad('finite')
   pts.append([x, z])
  out.append({'selector': s, 'points': pts, 'closed': s['closed']})
 return out
def chain_dir(i): return 'chain-%04d' % i
def shard_name(i): return 'queries-%04d.ndjson' % i
def atomic_new(path, data):
 path = Path(path); check_ancestors(path.parent)
 if path.parent.exists(): require_dir(path.parent)
 if exists_nofollow(path): raise Bad('exists:' + path.name)
 tmp = path.with_name(path.name + '.tmp')
 if exists_nofollow(tmp): raise Bad('tmpexists')
 with open(tmp, 'xb') as fh: fh.write(data); fh.flush(); os.fsync(fh.fileno())
 if exists_nofollow(path):
  tmp.unlink(); raise Bad('exists:' + path.name)
 os.replace(tmp, path)
def write_exclusive(path, data):
 path = Path(path); check_ancestors(path.parent)
 if path.parent.exists(): require_dir(path.parent)
 if exists_nofollow(path): raise Bad('exists:' + str(path))
 with open(path, 'xb') as fh: fh.write(data); fh.flush(); os.fsync(fh.fileno())
def valid_shard_name(n): return isinstance(n, str) and n.startswith('queries-') and n.endswith('.ndjson') and len(n) == 19 and n[8:12].isdigit()
def capture_names_ok(names):
 allowed = {'cache.json', 'cache.json.tmp', 'terminal.json', 'terminal.json.tmp'}
 return all((n in allowed or valid_shard_name(n) or (n.endswith('.tmp') and valid_shard_name(n[:-4]))) for n in names)
