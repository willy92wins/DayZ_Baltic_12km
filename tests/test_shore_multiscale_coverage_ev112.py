import hashlib, importlib.util, json, math, os, shutil, stat, subprocess, sys, tempfile, unittest
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
def load(name, rel):
 spec = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
IO = load('io_t', 'tools/quality/shore_coverage_io_ev112.py'); CONS = load('cons_t', 'tools/quality/verify_shore_multiscale_coverage_ev112.py'); CONS.V = IO.load_sealed(ROOT, 'tools/quality/verify_certified_shore_kernel_ev112.py', IO.KNOWN_HELPERS['tools/quality/verify_certified_shore_kernel_ev112.py'], 'vt_')
def sha(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o, sort_keys=True, separators=(',', ':')).encode()
CHAINS = [[[-2.0, 0.0], [0.0, 0.0], [2.0, 0.0]], [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]], [[0.0, 0.0], [1e-9, 0.0], [1.0, 0.0]]]
CLOSED = [False, True, False]
SOURCE_NAMES = ['q02b0_report', 'q02a_summary', 'q02b2_report', 'q02b2_consumer', 'q02b1_contract', 'old_oracles', 'plan', 'derivation']
def build_fixture(base, closed_repeat_signed=False, total_bytes=2147483648):
 base = Path(base); npz = base / 'fixture.npz'; po = [0]; co = [0]; pts = []; closed = []
 for i, stored in enumerate(CHAINS):
  st = [list(x) for x in stored]
  if closed_repeat_signed and i == 1: st[-1] = [-0.0, 0.0]
  pts.extend(st); po.append(len(pts)); co.append(co[-1] + len(st) - 1); closed.append(CLOSED[i])
 np.savez(npz, point_offsets=np.array(po, dtype=np.int64), chain_offsets=np.array(co, dtype=np.int64), chain_points=np.array(pts, dtype=np.float64), closed=np.array(closed, dtype=bool))
 npzsha = sha(npz.read_bytes()); chains = []; core_tot = 0; edge_tot = 0
 for i, stored in enumerate(CHAINS):
  core = stored[:-1] if CLOSED[i] else stored; core_tot += len(core); e = len(core) if CLOSED[i] else len(core) - 1; edge_tot += e
  arr = np.array(core, dtype='<f8'); chains.append({'chain_id': i, 'closed': CLOSED[i], 'point_offset': [po[i], po[i + 1]], 'segment_offset': [co[i], co[i + 1]], 'core_count': len(core), 'core_float64_le_sha256': sha(arr.tobytes()), 'centers': {'start': 0, 'stop': len(core), 'step': 1}})
 sel = {'schema': 'q02b3-selectors.v1', 'npz_sha256': npzsha, 'universe': core_tot * 5, 'chains': chains}; selp = base / 'selectors.json'; selp.write_bytes(canon(sel))
 ora = {'schema': 'q02b3-literal-oracles.v1', 'natural_positive_count': 0, 'calibration_ready': False, 'tree_integer_reduction_only': {'leaves': [[3, 4], [5, 5], [7, 8], [11, 12], [13, 13]], 'leaf_slots': 8, 'useful_nodes': 15, 'padding': [[0, 0]] * 3, 'ranges': [], 'directed': [], 'invalid_ranges': []}, 'sqrt2': {'q': [2, 1], 'p': 48, 'lo': 398065729532860, 'hi': 398065729532861}, 'threshold': {'binary_ratio': [3022314549036573, 302231454903657293676544], 'floor_scaled': 2814749, 'comparison': 'q < THR^2'}, 'station_literals': [], 'required_negatives': ['swap_leaf_preserve_total', 'forged_full_manifest'], 'station_convention': {'segment': 'local'}}; orap = base / 'oracles.json'; orap.write_bytes(canon(ora))
 doc = base / 'doc.md'; doc.write_text('# fixture doc\n')
 sources = {}
 for name in SOURCE_NAMES:
  p = base / ('source-' + name + '.json'); p.write_bytes(canon({'fixture_source_literal': name})); sources[name] = {'path': str(p), 'sha256': sha(p.read_bytes())}
 helpers = {rel: sha((ROOT / rel).read_bytes()) for rel in IO.KNOWN_HELPERS}
 contract = {'schema': 'q02b3.v1', 'scope': 'NUMERIC_COVERAGE_ONLY', 'npz_path': str(npz), 'npz_sha256': npzsha, 'selectors': {'path': str(selp), 'sha256': sha(selp.read_bytes())}, 'oracles': {'path': str(orap), 'sha256': sha(orap.read_bytes())}, 'sources': sources, 'helpers': helpers, 'h': [6, 12, 24, 48, 96], 'expected': {'chains': 3, 'closed_chains': 1, 'core_vertices': core_tot, 'edges': edge_tot, 'universe': core_tot * 5, 'open_chains': 2, 'max_core_count': 4, 'max_edges_observed': 4, 'degenerate_chains': 1, 'degenerate_chain_ids': [2]}, 'p': 48, 'threshold_ratio': [3022314549036573, 302231454903657293676544], 'max_bits': 4096, 'query_ops': 100000, 'chain_ops': 4000000, 'max_edges': 14000, 'read_limits': {'archive_bytes': 67108864, 'required_uncompressed_bytes': 8388608, 'header_bytes': 16384, 'members': 32}, 'output_limits': {'cache_bytes': 16777216, 'shard_bytes': 16777216, 'query_bytes': 262144, 'terminal_bytes': 1048576, 'manifest_bytes': 1048576, 'total_bytes': total_bytes}, 'human_cases': {'count': 9, 'state': 'GEOMETRY_UNBOUND', 'resolved': 0}, 'controls': 4, 'c1': 'NOT_REVIEWED', 'natural_positive_count': 0, 'calibration_ready': False, 'angle_state': 'PENDING_CERTIFIED_ANGLE', 'budgets': {'author_s': 300, 'code_review_s': 240, 'suite_s': 180, 'capture_s': 600, 'consumer_s': 900, 'rss_bytes': 536870912}, 'schema_document': str(doc), 'schema_document_sha256': sha(doc.read_bytes()), 'map_repaired': False, 'roles': {'producer_imports': ['tools/quality/shore_prefix_pilot_ev112.py', 'tools/quality/certified_shore_kernel_ev112.py', 'tools/quality/shore_numeric_discovery_ev112.py'], 'consumer_imports': ['tools/quality/verify_certified_shore_kernel_ev112.py', 'tools/quality/shore_numeric_discovery_ev112.py'], 'regression_only': ['tools/quality/verify_shore_prefix_pilot_ev112.py']}}
 cp = base / 'contract.json'; cp.write_bytes(canon(contract)); return cp, sha(cp.read_bytes())
def run(*args): return subprocess.run([sys.executable] + list(args), cwd=str(ROOT), text=True, capture_output=True, timeout=60)
def refresh_capture(cap):
 cap = Path(cap); terms = []
 for i in range(3):
  td = (cap / ('chain-%04d' % i) / 'terminal.json').read_bytes(); terms.append({'chain_id': i, 'bytes': len(td), 'sha256': sha(td)})
 mp = cap / 'manifest.json'
 if mp.exists():
  m = json.loads(mp.read_text()); m['terminals'] = terms; mp.write_bytes(canon(m))
def refresh_shard_term(cap, ci):
 cap = Path(cap); cdir = cap / ('chain-%04d' % ci); term = json.loads((cdir / 'terminal.json').read_text()); shards = []; sc = {}; unver = 0
 for sh in term['shards']:
  data = (cdir / sh['name']).read_bytes(); recs = [json.loads(x) for x in data.decode().splitlines()]; shards.append({'name': sh['name'], 'bytes': len(data), 'sha256': sha(data), 'queries': len(recs)})
  for r in recs: sc[r['result']['state']] = sc.get(r['result']['state'], 0) + 1; unver += r['result']['state'] == 'RESOURCE_INCONCLUSIVE'
 term['shards'] = shards; term['state_counts'] = sc; term['unverified_numeric_count'] = unver
 if term['classification'] == 'NUMERIC': term['query_count'] = sum(x['queries'] for x in shards)
 (cdir / 'terminal.json').write_bytes(canon(term)); refresh_capture(cap)
 if (cap / 'manifest.json').exists():
  m = json.loads((cap / 'manifest.json').read_text()); allsc = {}; tq = 0; tu = 0; te = 0
  for i in range(3):
   t = json.loads((cap / ('chain-%04d' % i) / 'terminal.json').read_text()); tq += t['query_count']; tu += t['unverified_numeric_count']; te += t['excluded_count']
   for k, v in t['state_counts'].items(): allsc[k] = allsc.get(k, 0) + v
  m.update({'query_count': tq, 'unverified_numeric_count': tu, 'state_counts': allsc, 'excluded_count': te}); (cap / 'manifest.json').write_bytes(canon(m)); refresh_capture(cap)
def refresh_cache_term(cap, ci):
 cap = Path(cap); cdir = cap / ('chain-%04d' % ci); term = json.loads((cdir / 'terminal.json').read_text()); data = (cdir / 'cache.json').read_bytes(); term['cache'] = {'name': 'cache.json', 'bytes': len(data), 'sha256': sha(data)}; (cdir / 'terminal.json').write_bytes(canon(term)); refresh_capture(cap)
def radical_sign(a, b, rad):
 # Exact sign of a + b*sqrt(rad), by signs and squared rational magnitudes.
 sign = lambda x: (x > 0) - (x < 0)
 if not b: return sign(a)
 if not a: return sign(b)
 if sign(a) == sign(b): return sign(a)
 return sign(a) * sign(a*a - b*b*rad)

def interval_contains(enc, terms):
 a = Fraction(0); b = Fraction(0); rad = None
 for t in terms:
  v = Fraction(t['num'], t['den'])
  if t['radicand'] == 1: a += v
  elif v:
   if rad is not None and rad != t['radicand']: raise AssertionError('oracle domain')
   rad = t['radicand']; b += v
 lo = Fraction(*enc[0]); hi = Fraction(*enc[1])
 return radical_sign(a-lo,b,rad or 1) >= 0 and radical_sign(hi-a,-b,rad or 1) >= 0
class TreeTests(unittest.TestCase):
 def test_tree_external_oracles_and_negatives(self):
  ora = json.loads((ROOT / 'tests/fixtures/q02b3/oracles-r1.json').read_text()); tree_o = ora['tree_integer_reduction_only']; leaves = [tuple(x) for x in tree_o['leaves']]; tree, M = CONS.build_tree(leaves, CONS.CB(4000000)); self.assertEqual(M, tree_o['leaf_slots']); self.assertEqual(len(tree) - 1, tree_o['useful_nodes']); self.assertEqual(tree[M + 5:M + 8], [tuple(x) for x in tree_o['padding']])
  for r in tree_o['ranges']: self.assertEqual(CONS.range_sum(tree, M, 5, r['a'], r['b'], CONS.CB(100000)), tuple(r['sum']))
  with self.assertRaises(CONS.Bad): CONS.range_sum(tree, M, 5, 5, 8, CONS.CB(100000))
  prep = CONS.Prepared([(Fraction(i), Fraction(0)) for i in range(5)], True, [(lo, hi, Fraction(0)) for lo, hi in leaves], [], tree, M, None)
  for d in tree_o['directed']: self.assertEqual(CONS.dir_pref(prep, d['center'], d['direction'], d['steps'], CONS.CB(100000)), tuple(d['sum']))
  swapped = [leaves[1], leaves[0]] + leaves[2:]; t2, M2 = CONS.build_tree(swapped, CONS.CB(4000000)); self.assertEqual(CONS.range_sum(t2, M2, 5, 0, 5, CONS.CB(100000)), (39, 42)); self.assertNotEqual(CONS.range_sum(t2, M2, 5, 0, 1, CONS.CB(100000)), (3, 4))
  bad = list(leaves); bad[0] = (4, 4); tb, Mb = CONS.build_tree(bad, CONS.CB(4000000)); self.assertNotEqual(CONS.range_sum(tb, Mb, 5, 0, 2, CONS.CB(100000)), CONS.range_sum(tree, M, 5, 0, 2, CONS.CB(100000)))
 def test_sqrt_threshold_and_station_external_oracles(self):
  ora = json.loads((ROOT / 'tests/fixtures/q02b3/oracles-r1.json').read_text()); prep = CONS.prepare([[0, 0], [1, 1]], False, None, CONS.CB(4000000)); self.assertEqual((prep.edges[0][0], prep.edges[0][1]), (ora['sqrt2']['lo'], ora['sqrt2']['hi']))
  self.assertEqual(ora['threshold']['floor_scaled'], (CONS.THR.numerator * (1 << 48)) // CONS.THR.denominator)
  for lit in ora['station_literals']:
   r = CONS.query_from_points(lit['points'], lit['closed'], lit['center'], Fraction(lit['h'][0], lit['h'][1])); self.assertEqual(r['state'], lit['state'], lit['id'])
   for key, segk, tk, fk, tok, ek in (('A', 'a_segment', 'a_t', 'a_from', 'a_to', 'a_exact'), ('C', 'c_segment', 'c_t', 'c_from', 'c_to', 'c_exact')):
    st = r['stations'][key]; self.assertEqual(st['segment'], lit[segk], lit['id']); self.assertEqual(st['from_point'], [[lit[fk][0], 1], [lit[fk][1], 1]]); self.assertEqual(st['to_point'], [[lit[tok][0], 1], [lit[tok][1], 1]]); self.assertEqual(st['t'], [[lit[tk][0], lit[tk][1]], [lit[tk][0], lit[tk][1]]]); self.assertEqual(st['point'], [[[lit[ek][0], 1], [lit[ek][0], 1]], [[lit[ek][1], 1], [lit[ek][1], 1]]])
 def test_station_h0_exact_zero_chord(self):
  r = CONS.query_from_points([[-2, 0], [0, 0], [2, 0]], False, 1, Fraction(0)); self.assertEqual(r['state'], 'UNDEFINED_ZERO_CHORD'); self.assertEqual(r['stations']['A']['from_point'], [[0, 1], [0, 1]]); self.assertEqual(r['stations']['A']['to_point'], [[-2, 1], [0, 1]])
 def test_old_30_oracles_regression(self):
  raw = (ROOT / 'tests/fixtures/q02b0/oracles.json').read_bytes(); self.assertEqual(sha(raw), '083334300732b33b994dd6d97d063a19db08dd58e64a92cffea806848c4bde1b'); data = json.loads(raw); count = 0
  for f in data['fixtures']:
   for q in f['queries']:
    count += 1; r = CONS.query_from_points(f['points'], f['closed'], f['center_index'], q['h']); expected = 'UNDEFINED_ZERO_CHORD' if q['state'] == 'COINCIDENT_SUPPORT' else q['state']; self.assertEqual(r['state'], expected, (f['id'], q['h']))
    if q['a_exact'] is not None:
     self.assertTrue(interval_contains(r['stations']['A']['point'][0], q['a_exact'][0])); self.assertTrue(interval_contains(r['stations']['A']['point'][1], q['a_exact'][1])); self.assertTrue(interval_contains(r['stations']['C']['point'][0], q['c_exact'][0])); self.assertTrue(interval_contains(r['stations']['C']['point'][1], q['c_exact'][1]))
  self.assertEqual(count, 30)
 def test_saved_q02b2_54_queries_by_hash(self):
  contract = json.loads((ROOT / 'tests/fixtures/q02b3/contract.json').read_text()); src = contract['sources']['q02b2_report']; p = Path(src['path'])
  self.assertTrue(p.is_file(), 'required frozen Q02B2 evidence missing')
  raw = p.read_bytes(); self.assertEqual(sha(raw), src['sha256']); recs = [json.loads(x) for x in raw.decode().splitlines() if x.strip()]; queries = [r for r in recs if r.get('kind') == 'query']; self.assertEqual(len(queries), 54)
  prepared = {}
  for r in recs:
   if r.get('kind') == 'cache':
    c = r['cache']; points = [[Fraction(*v) for v in pt] for pt in c['points']]
    prepared[r['chain_id']] = CONS.prepare(points, c['closed'], None, CONS.CB(4000000))
  for r in queries:
   CONS.validate_result_form(r['result'])
   expected = CONS.query_prepared(prepared[r['chain_id']], r['center_index'], r['h'])
   self.assertTrue(IO.strict_eq({k:v for k,v in r['result'].items() if k != 'ops'}, {k:v for k,v in expected.items() if k != 'ops'}), (r['chain_id'],r['center_index'],r['h']))
 def test_consumer_imports_and_reparse_stat_simulated(self):
  import ast; tree = ast.parse((ROOT / 'tools/quality/verify_shore_multiscale_coverage_ev112.py').read_text()); mods = []
  for n in ast.walk(tree):
   if isinstance(n, ast.Import): mods += [x.name for x in n.names]
   if isinstance(n, ast.ImportFrom) and n.module: mods.append(n.module)
  self.assertFalse(any('shore_prefix_pilot' in m or m.endswith('certified_shore_kernel_ev112') or 'shore_multiscale_coverage' in m for m in mods))
  self.assertTrue(IO.is_reparse_stat(type('S', (), {'st_mode': stat.S_IFLNK | 0o777, 'st_file_attributes': 0})()))
  self.assertTrue(IO.is_reparse_stat(type('S', (), {'st_mode': stat.S_IFREG, 'st_file_attributes': 0x400})()))
  self.assertFalse(IO.is_reparse_stat(type('S', (), {'st_mode': stat.S_IFREG, 'st_file_attributes': 0})()))
  with self.assertRaises(CONS.Resource): CONS.CB(0).tick()
class CliTests(unittest.TestCase):
 def setUp(self): self.td = tempfile.TemporaryDirectory(); self.base = Path(self.td.name); self.cp, self.csha = build_fixture(self.base); self.cap = self.base / 'capture'; self.assertEqual(self.produce().returncode, 0)
 def tearDown(self): self.td.cleanup()
 def produce(self): return run('tools/quality/shore_multiscale_coverage_ev112.py', '--root', str(ROOT), '--contract', str(self.cp), '--contract-sha', self.csha, '--output-dir', str(self.cap))
 def consume(self, cap, out): return run('tools/quality/verify_shore_multiscale_coverage_ev112.py', '--root', str(ROOT), '--contract', str(self.cp), '--contract-sha', self.csha, '--capture-dir', str(cap), '--output', str(out))
 def copy(self, name): dst = self.base / name; shutil.copytree(self.cap, dst); return dst
 def expect_reject(self, cap, name): out = self.base / (name + '.json'); c = self.consume(cap, out); self.assertEqual(c.returncode, 1, c.stderr + c.stdout); self.assertEqual(json.loads(out.read_text())['state'], 'REJECTED')
 def test_full_cli(self):
  out = self.base / 'consumer.json'; c = self.consume(self.cap, out); self.assertEqual(c.returncode, 0, c.stderr + c.stdout); rep = json.loads(out.read_text()); self.assertEqual(rep['state'], 'VERIFIED_FULL_NUMERIC_COVERAGE_ONLY'); self.assertTrue(rep['coverage_complete']); self.assertEqual((rep['completed_chains'], rep['covered_universe']), (3, 50))
 def test_partial_first_gap_only_and_invalid_terminal(self):
  cap2 = self.copy('cap2'); os.remove(cap2 / 'manifest.json'); os.remove(cap2 / 'chain-0002' / 'terminal.json'); out = self.base / 'c2.json'; c = self.consume(cap2, out); self.assertEqual(c.returncode, 2); self.assertEqual(json.loads(out.read_text())['state'], 'VERIFIED_PARTIAL_NUMERIC_COVERAGE')
  cap3 = self.copy('cap3'); os.remove(cap3 / 'manifest.json'); os.remove(cap3 / 'chain-0001' / 'terminal.json'); shutil.rmtree(cap3 / 'chain-0002'); (cap3 / 'chain-0002').mkdir(); (cap3 / 'chain-0002' / 'cache.json').write_bytes(b'{}'); self.expect_reject(cap3, 'aftergap')
  cap4 = self.copy('cap4'); (cap4 / 'chain-0001' / 'terminal.json').write_bytes(b'{bad'); refresh_capture(cap4); self.expect_reject(cap4, 'badterm')
 def test_forged_manifest_duplicate_and_extra(self):
  cap = self.copy('capm'); m = json.loads((cap / 'manifest.json').read_text()); m['chain_count'] = 999; (cap / 'manifest.json').write_bytes(canon(m)); self.expect_reject(cap, 'forged')
  cap = self.copy('capdup'); m = json.loads((cap / 'manifest.json').read_text()); m['terminals'] = m['terminals'] + [m['terminals'][0]]; (cap / 'manifest.json').write_bytes(canon(m)); self.expect_reject(cap, 'dupterm')
  cap = self.copy('capextra'); (cap / 'chain-0003').mkdir(); self.expect_reject(cap, 'extrachain')
 def test_query_mutation_negatives(self):
  cases = []
  cap = self.copy('missing'); p = cap / 'chain-0000' / 'queries-0000.ndjson'; lines = p.read_text().splitlines(); del lines[0]; p.write_text('\n'.join(lines) + '\n'); refresh_shard_term(cap, 0); cases.append(cap)
  cap = self.copy('dupq'); p = cap / 'chain-0000' / 'queries-0000.ndjson'; lines = p.read_text().splitlines(); lines.insert(1, lines[0]); p.write_text('\n'.join(lines) + '\n'); refresh_shard_term(cap, 0); cases.append(cap)
  cap = self.copy('changedh'); p = cap / 'chain-0000' / 'queries-0000.ndjson'; lines = p.read_text().splitlines(); r = json.loads(lines[0]); r['h'] = 12; lines[0] = json.dumps(r, sort_keys=True, separators=(',', ':')); p.write_text('\n'.join(lines) + '\n'); refresh_shard_term(cap, 0); cases.append(cap)
  cap = self.copy('reorder'); p = cap / 'chain-0000' / 'queries-0000.ndjson'; lines = p.read_text().splitlines(); lines[0], lines[1] = lines[1], lines[0]; p.write_text('\n'.join(lines) + '\n'); refresh_shard_term(cap, 0); cases.append(cap)
  cap = self.copy('trunc'); p = cap / 'chain-0000' / 'queries-0000.ndjson'; p.write_bytes(p.read_bytes()[:-3]); refresh_shard_term(cap, 0) if False else None; cases.append(cap)
  cap = self.copy('extrashard'); termp = cap / 'chain-0000' / 'terminal.json'; t = json.loads(termp.read_text()); (cap / 'chain-0000' / 'queries-0001.ndjson').write_bytes((cap / 'chain-0000' / 'queries-0000.ndjson').read_bytes()[:2]); t['shards'].append({'name': 'queries-0001.ndjson', 'bytes': 2, 'sha256': sha(b'{}\n'[:2]), 'queries': 0}); termp.write_bytes(canon(t)); refresh_capture(cap); cases.append(cap)
  for i, c in enumerate(cases): self.expect_reject(c, 'qneg%d' % i)
 def test_bool_and_cache_comutation_negatives(self):
  cap = self.copy('boolterm'); t = json.loads((cap / 'chain-0001' / 'terminal.json').read_text()); t['chain_id'] = True; (cap / 'chain-0001' / 'terminal.json').write_bytes(canon(t)); refresh_capture(cap); self.expect_reject(cap, 'boolterm')
  cap = self.copy('boolcount'); t = json.loads((cap / 'chain-0000' / 'terminal.json').read_text()); t['query_count'] = False; (cap / 'chain-0000' / 'terminal.json').write_bytes(canon(t)); refresh_capture(cap); self.expect_reject(cap, 'boolcount')
  cap = self.copy('boolshard'); p = cap / 'chain-0000' / 'queries-0000.ndjson'; lines = p.read_text().splitlines(); r = json.loads(lines[0]); r['center'] = True; lines[0] = json.dumps(r, sort_keys=True, separators=(',', ':')); p.write_text('\n'.join(lines) + '\n'); refresh_shard_term(cap, 0); self.expect_reject(cap, 'boolshard')
  cap = self.copy('comut'); cachep = cap / 'chain-0000' / 'cache.json'; cache = json.loads(cachep.read_text()); cache['points'][0] = [[999, 1], [0, 1]]; cachep.write_bytes(canon(cache)); refresh_cache_term(cap, 0); self.expect_reject(cap, 'comut')
  cap = self.copy('prefmut'); cachep = cap / 'chain-0000' / 'cache.json'; cache = json.loads(cachep.read_text()); cache['edges'][0]['lo'] += 1; cache['pref_lo'] = [x + (1 if i > 0 else 0) for i, x in enumerate(cache['pref_lo'])]; cachep.write_bytes(canon(cache)); refresh_cache_term(cap, 0); self.expect_reject(cap, 'prefmut')
  cap = self.copy('swapleaf'); cachep = cap / 'chain-0001' / 'cache.json'; cache = json.loads(cachep.read_text()); cache['edges'][0] = {'q': [121, 1], 'lo': 11 * (1 << 48), 'hi': 11 * (1 << 48)}; cache['edges'][1] = {'q': [81, 1], 'lo': 9 * (1 << 48), 'hi': 9 * (1 << 48)}; pl = [0]; ph = [0]
  for e in cache['edges']: pl.append(pl[-1] + e['lo']); ph.append(ph[-1] + e['hi'])
  cache['pref_lo'] = pl; cache['pref_hi'] = ph; cachep.write_bytes(canon(cache)); refresh_cache_term(cap, 1); self.expect_reject(cap, 'swapleaf')
 def test_resource_record_not_full_and_producer_cap(self):
  cap = self.copy('capr'); sh = cap / 'chain-0000' / 'queries-0000.ndjson'; lines = sh.read_text().splitlines(); r = json.loads(lines[0]); r['result'] = {'state': 'RESOURCE_INCONCLUSIVE', 'stations': None, 'features': None, 'support': None, 'ops': None, 'reason': 'query_budget'}; lines[0] = json.dumps(r, sort_keys=True, separators=(',', ':')); sh.write_text('\n'.join(lines) + '\n'); refresh_shard_term(cap, 0); out = self.base / 'cr.json'; c = self.consume(cap, out); self.assertEqual(c.returncode, 2); self.assertEqual(json.loads(out.read_text())['state'], 'NUMERIC_RESOURCE_INCONCLUSIVE')
  base2 = self.base / 'smallcap'; base2.mkdir(); cp2, sha2 = build_fixture(base2, total_bytes=10); outdir = base2 / 'out'; p = run('tools/quality/shore_multiscale_coverage_ev112.py', '--root', str(ROOT), '--contract', str(cp2), '--contract-sha', sha2, '--output-dir', str(outdir)); self.assertEqual(p.returncode, 1); total = sum(x.stat().st_size for x in outdir.rglob('*') if x.is_file()) if outdir.exists() else 0; self.assertLessEqual(total, 10)
 def test_signed_zero_and_symlink_if_permitted(self):
  base2 = self.base / 'sz'; base2.mkdir(); cp2, sha2 = build_fixture(base2, True); p = run('tools/quality/shore_multiscale_coverage_ev112.py', '--root', str(ROOT), '--contract', str(cp2), '--contract-sha', sha2, '--output-dir', str(base2 / 'out')); self.assertEqual(p.returncode, 1, p.stderr)
  cap = self.copy('linkcap'); target = cap / 'chain-0000' / 'cache.json'; link = cap / 'chain-0000' / 'cache-link.json'
  try: os.symlink(target, link)
  except (OSError, NotImplementedError): return
  self.expect_reject(cap, 'linkcap')
 def test_own_consumer_resource_keeps_structural_coverage(self):
  from unittest.mock import patch
  for method in ('query_prepared', 'prepare'):
   out = self.base / ('own-resource-' + method + '.json')
   argv = ['--root', str(ROOT), '--contract', str(self.cp), '--contract-sha', self.csha, '--capture-dir', str(self.cap), '--output', str(out)]
   with patch.object(CONS, method, side_effect=CONS.Resource('test-own-budget')):
    rc = CONS.main(argv)
   r = json.loads(out.read_bytes()); self.assertEqual(rc, 2); self.assertEqual(r['state'], 'NUMERIC_RESOURCE_INCONCLUSIVE'); self.assertTrue(r['coverage_complete']); self.assertEqual(r['completed_chains'],3); self.assertGreater(r['unverified_numeric_count'],0)
 def test_temporary_manifest_cap_and_ancestor_guard(self):
  cap = self.copy('tmpcap'); (cap / 'manifest.json').unlink(); (cap / 'chain-0002' / 'terminal.json').unlink(); (cap / 'manifest.json.tmp').write_bytes(b'x' * (1048576+1)); self.expect_reject(cap,'tmpcap')
  from unittest.mock import patch
  target = str(self.cap)
  real = CONS.IO.check_ancestors
  def blocked(path):
   if str(path) == target: raise CONS.Bad('test-reparse-ancestor')
   return real(path)
  out = self.base / 'ancestor.json'
  with patch.object(CONS.IO,'check_ancestors',side_effect=blocked):
   rc = CONS.main(['--root',str(ROOT),'--contract',str(self.cp),'--contract-sha',self.csha,'--capture-dir',str(self.cap),'--output',str(out)])
  self.assertEqual(rc,1); self.assertEqual(json.loads(out.read_bytes())['errors'],['test-reparse-ancestor'])
if __name__ == '__main__': unittest.main()
