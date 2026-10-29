#!/usr/bin/env python3
import argparse, math, sys
from fractions import Fraction
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shore_coverage_io_ev112 as IO
Bad = IO.Bad
class Resource(Exception): pass
SCALE = IO.SCALE; MAXBITS = 4096; THR = Fraction(3022314549036573, 302231454903657293676544)
V = None; TR = None
def bl(x): return abs(int(x)).bit_length()
def is_res(e):
 if isinstance(e, Resource): return True
 cap = getattr(V, 'Cap', None) if V is not None else None
 return isinstance(cap, type) and isinstance(e, cap)
def sealed_bad_types():
 out = []
 for m in (V,):
  c = getattr(m, 'Bad', None) if m is not None else None
  if isinstance(c, type): out.append(c)
 return tuple(out)
class CB:
 def __init__(self, limit): self.n = 0; self.limit = limit; self.events = None
 def tick(self, n=1):
  self.n += n
  if self.n > self.limit: raise Resource('ops')
 def need(self, *v):
  if sum(bl(x) for x in v) > MAXBITS: raise Resource('bits')
  self.tick()
 def need_sum(self, a, b):
  if max(bl(a), bl(b)) + 1 > MAXBITS: raise Resource('sumbits')
  self.tick()
def enc_iv(iv): return None if iv is None else [[iv[0].numerator, iv[0].denominator], [iv[1].numerator, iv[1].denominator]]
def enc_station(s): return None if s is None else {'segment': s['segment'], 'from_point': [[s['from'][0].numerator, s['from'][0].denominator], [s['from'][1].numerator, s['from'][1].denominator]], 'to_point': [[s['to'][0].numerator, s['to'][0].denominator], [s['to'][1].numerator, s['to'][1].denominator]], 't': enc_iv(s['t']), 'point': [enc_iv(s['point'][0]), enc_iv(s['point'][1])]}
def enc_field(f): return {'state': f['state'], 'interval': enc_iv(f['interval']), 'unit': f['unit'], 'width': [f['width'].numerator, f['width'].denominator] if f['width'] is not None else None}
def build_tree(leaves, budget):
 m = len(leaves)
 if m < 1 or m > 14000: raise Bad('edges')
 M = 1
 while M < m: M *= 2
 if M > 16384: raise Bad('treeM')
 tree = [(0, 0)] * (2 * M)
 for i, (lo, hi) in enumerate(leaves):
  if type(lo) is not int or type(hi) is not int or lo < 0 or hi < lo or hi - lo > 1: raise Bad('leaf')
  tree[M + i] = (lo, hi)
 for v in range(M - 1, 0, -1):
  a = tree[2 * v]; b = tree[2 * v + 1]; budget.need_sum(a[0], b[0]); budget.need_sum(a[1], b[1]); tree[v] = (a[0] + b[0], a[1] + b[1])
 return tree, M
def range_sum(tree, M, m, a, b, budget):
 if type(a) is not int or type(b) is not int or not (0 <= a <= b <= m): raise Bad('range')
 if a == b: return (0, 0)
 L = M + a; R = M + b; lo = 0; hi = 0
 while L < R:
  if L & 1:
   budget.need_sum(lo, tree[L][0]); budget.need_sum(hi, tree[L][1]); lo += tree[L][0]; hi += tree[L][1]; L += 1
  if R & 1:
   R -= 1; budget.need_sum(lo, tree[R][0]); budget.need_sum(hi, tree[R][1]); lo += tree[R][0]; hi += tree[R][1]
  L //= 2; R //= 2
 return (lo, hi)
class Prepared:
 __slots__ = ('pts', 'closed', 'edges', 'deg', 'tree', 'M', 'cache')
 def __init__(s, pts, closed, edges, deg, tree, M, cache): s.pts = pts; s.closed = closed; s.edges = edges; s.deg = deg; s.tree = tree; s.M = M; s.cache = cache
def frac_points(points):
 out = []
 for p in points:
  if isinstance(p[0], Fraction): out.append((p[0], p[1]))
  elif type(p[0]) is int: out.append((Fraction(p[0]), Fraction(p[1])))
  else:
   x = float(p[0]); z = float(p[1]); out.append((Fraction(x.as_integer_ratio()[0], x.as_integer_ratio()[1]), Fraction(z.as_integer_ratio()[0], z.as_integer_ratio()[1])))
 return out
def scaled_int(f, budget):
 budget.need(f.numerator, f.denominator)
 if f.denominator <= 0 or SCALE % f.denominator != 0: raise Bad('rootscale')
 factor = SCALE // f.denominator
 if bl(f.numerator) + bl(factor) > MAXBITS: raise Resource('rootbits')
 budget.tick(); return f.numerator * factor
def frac_scaled(pair, budget):
 budget.need(pair[0], SCALE); budget.need(pair[1], SCALE); return (Fraction(pair[0], SCALE), Fraction(pair[1], SCALE))
def prepare(points, closed, cache=None, budget=None):
 budget = budget or CB(IO.CHAIN_OPS); pts = frac_points(points); n = len(pts); m = n if closed else n - 1
 if type(closed) is not bool or m < 1 or m > 14000: raise Bad('edges')
 t2 = V.mul(budget, THR, THR); edges = []; deg = []
 for i in range(m):
  a1 = pts[i]; b1 = pts[(i + 1) % n]; dx = V.sub(budget, b1[0], a1[0]); dz = V.sub(budget, b1[1], a1[1]); q = V.add(budget, V.mul(budget, dx, dx), V.mul(budget, dz, dz)); iv = V.root_interval(budget, (q, q)); lo = scaled_int(iv[0], budget); hi = scaled_int(iv[1], budget)
  if hi - lo not in (0, 1): raise Bad('witness')
  edges.append((lo, hi, q))
  if V.cmpf(budget, q, t2) < 0: deg.append(i)
 if not deg and any(lo == 0 for lo, hi, q in edges): raise Bad('zero_lo_nondegenerate')
 tree, M = build_tree([(lo, hi) for lo, hi, q in edges], budget)
 return Prepared(pts, closed, edges, deg, tree, M, cache)
def dir_pref(prep, center, direction, k, budget):
 if k == 0: return (0, 0)
 m = len(prep.edges)
 def rs(a, b): return range_sum(prep.tree, prep.M, m, a, b, budget)
 if direction > 0:
  if not prep.closed or center + k <= m: v = rs(center, center + k)
  else:
   x = rs(center, m); y = rs(0, (center + k) % m); budget.need_sum(x[0], y[0]); budget.need_sum(x[1], y[1]); v = (x[0] + y[0], x[1] + y[1])
 else:
  if not prep.closed or center - k >= 0: v = rs(center - k, center) if not prep.closed else rs(center - k, center)
  else:
   x = rs(0, center); y = rs(m + (center - k), m); budget.need_sum(x[0], y[0]); budget.need_sum(x[1], y[1]); v = (x[0] + y[0], x[1] + y[1])
 return v
def edge_at(prep, center, direction, k):
 n = len(prep.pts)
 if prep.closed: frm = (center + direction * k) % n; to = (center + direction * (k + 1)) % n
 else: frm = center + direction * k; to = center + direction * (k + 1)
 ei = frm if direction > 0 else to
 if prep.closed: ei %= n
 return ei, frm, to
def make_station(budget, prep, seg, frm, to, t):
 pt = []
 for kk in (0, 1):
  d = V.sub(budget, prep.pts[to][kk], prep.pts[frm][kk]); pt.append(V.iadd(budget, (prep.pts[frm][kk], prep.pts[frm][kk]), V.imul(budget, t, (d, d))))
 return {'segment': seg, 'from': prep.pts[frm], 'to': prep.pts[to], 't': t, 'point': (pt[0], pt[1])}
def locate(prep, center, direction, h, budget):
 n = len(prep.pts); steps = n if prep.closed else (center if direction < 0 else n - 1 - center); cen = prep.pts[center]
 if steps == 0:
  return {'segment': None, 'from': cen, 'to': cen, 't': (Fraction(0), Fraction(0)), 'point': ((cen[0], cen[0]), (cen[1], cen[1]))} if V.cmpf(budget, h, Fraction(0)) == 0 else 'OUT_OF_RANGE'
 if V.cmpf(budget, h, Fraction(0)) == 0:
  ei, frm, to = edge_at(prep, center, direction, 0); return make_station(budget, prep, 0, frm, to, (Fraction(0), Fraction(0)))
 total_i = dir_pref(prep, center, direction, steps, budget); total = frac_scaled(total_i, budget)
 if not prep.closed and total[0] == total[1] and V.cmpf(budget, h, total[0]) == 0:
  ei, frm, to = edge_at(prep, center, direction, steps - 1); return make_station(budget, prep, steps - 1, frm, to, (Fraction(1), Fraction(1)))
 lo_i = 0; hi_i = steps
 while lo_i < hi_i:
  mid = (lo_i + hi_i) // 2; budget.tick(); pl = dir_pref(prep, center, direction, mid + 1, budget)
  if V.cmpf(budget, frac_scaled(pl, budget)[0], h) <= 0: lo_i = mid + 1
  else: hi_i = mid
 cand = lo_i
 if cand >= steps:
  return 'OUT_OF_RANGE' if V.cmpf(budget, h, total[1]) > 0 else 'BOUNDARY_UNCERTAIN'
 S = frac_scaled(dir_pref(prep, center, direction, cand, budget), budget); N = frac_scaled(dir_pref(prep, center, direction, cand + 1, budget), budget); ei, frm, to = edge_at(prep, center, direction, cand)
 if S[0] == S[1] and V.cmpf(budget, h, S[0]) == 0: return make_station(budget, prep, cand, frm, to, (Fraction(0), Fraction(0)))
 if V.cmpf(budget, S[1], h) < 0 and V.cmpf(budget, h, N[0]) < 0:
  lo, hi, q = prep.edges[ei]; L = frac_scaled((lo, hi), budget)
  try: t = V.idiv(budget, V.isub(budget, (h, h), S), L)
  except Exception as e:
   if is_res(e): raise
   if sealed_bad_types() and isinstance(e, sealed_bad_types()): raise Bad('t:' + str(e))
   raise Bad('t:' + str(e))
  if V.cmpf(budget, t[0], Fraction(0)) < 0 or V.cmpf(budget, t[1], Fraction(1)) > 0: return 'BOUNDARY_UNCERTAIN'
  return make_station(budget, prep, cand, frm, to, t)
 if V.cmpf(budget, h, total[1]) > 0: return 'OUT_OF_RANGE'
 return 'BOUNDARY_UNCERTAIN'
def query_prepared(prep, center, h):
 budget = CB(IO.QUERY_OPS)
 if type(center) is not int or not (0 <= center < len(prep.pts)): return {'state': 'INVALID_QUERY', 'stations': None, 'features': None, 'support': None, 'ops': 0}
 hh = h if isinstance(h, Fraction) else Fraction(h)
 if V.cmpf(budget, hh, Fraction(0)) < 0: return {'state': 'INVALID_QUERY', 'stations': None, 'features': None, 'support': None, 'ops': 0}
 if prep.deg: return {'state': 'DEGENERATE', 'stations': None, 'features': None, 'support': None, 'ops': 0}
 m = len(prep.edges)
 if prep.closed:
  per = frac_scaled(range_sum(prep.tree, prep.M, m, 0, m, budget), budget); support = {'perimeter': per, 'backward': per, 'forward': per}; two = V.mul(budget, Fraction(2), hh)
  if per[0] == per[1]: supp = 'SUPPORTED' if V.cmpf(budget, two, per[0]) < 0 else 'INSUFFICIENT_SUPPORT'
  elif V.cmpf(budget, two, per[1]) >= 0: supp = 'INSUFFICIENT_SUPPORT'
  elif V.cmpf(budget, two, per[0]) < 0: supp = 'SUPPORTED'
  else: supp = 'SUPPORT_UNCERTAIN'
 else:
  back = frac_scaled(range_sum(prep.tree, prep.M, m, 0, center, budget), budget); fwd = frac_scaled(range_sum(prep.tree, prep.M, m, center, m, budget), budget); support = {'perimeter': None, 'backward': back, 'forward': fwd}; supp = 'SUPPORTED'
  for dist in (back, fwd):
   cur = 'SUPPORTED' if V.cmpf(budget, dist[0], hh) >= 0 else ('INSUFFICIENT_SUPPORT' if V.cmpf(budget, dist[1], hh) < 0 else 'SUPPORT_UNCERTAIN')
   if cur == 'INSUFFICIENT_SUPPORT': supp = cur
   elif cur == 'SUPPORT_UNCERTAIN' and supp == 'SUPPORTED': supp = cur
 sup_enc = {'perimeter': enc_iv(support['perimeter']), 'backward': enc_iv(support['backward']), 'forward': enc_iv(support['forward']), 'state': supp}
 if supp != 'SUPPORTED': return {'state': supp, 'stations': None, 'features': None, 'support': sup_enc, 'ops': budget.n}
 A = locate(prep, center, -1, hh, budget)
 if isinstance(A, str): return {'state': A, 'stations': None, 'features': None, 'support': sup_enc, 'ops': budget.n}
 C = locate(prep, center, 1, hh, budget)
 if isinstance(C, str): return {'state': C, 'stations': None, 'features': None, 'support': sup_enc, 'ops': budget.n}
 cen = prep.pts[center]; B = {'segment': None, 'from': cen, 'to': cen, 't': (Fraction(0), Fraction(0)), 'point': ((cen[0], cen[0]), (cen[1], cen[1]))}; feats = V.features(budget, A, B, C, hh); state = 'UNDEFINED_ZERO_CHORD' if feats['chord_ac']['interval'] == (Fraction(0), Fraction(0)) else 'DEFINED'
 return {'state': state, 'stations': {'A': enc_station(A), 'B': enc_station(B), 'C': enc_station(C)}, 'features': {k: enc_field(v) for k, v in feats.items()}, 'support': sup_enc, 'ops': budget.n}
def query_from_points(points, closed, center, h):
 prep = prepare(points, closed, None, CB(IO.CHAIN_OPS)); return query_prepared(prep, center, h)
def is_ratio(v): return IO.is_ratio(v)
def is_interval(v):
 if not isinstance(v, list) or len(v) != 2 or not is_ratio(v[0]) or not is_ratio(v[1]): return False
 return v[0][0] * v[1][1] <= v[1][0] * v[0][1]
def is_point_enc(v): return isinstance(v, list) and len(v) == 2 and all(is_ratio(x) for x in v)
def validate_cache_form(cache, meta_expected, closed, points):
 IO.keys(cache, {'meta', 'closed', 'points', 'edges', 'pref_lo', 'pref_hi', 'degenerate_indices', 'counters'}, 'cachekeys')
 if not IO.strict_eq(cache['meta'], meta_expected) or type(cache['closed']) is not bool or cache['closed'] != closed: raise Bad('cachemeta')
 pts = frac_points(points); enc = [[[c.numerator, c.denominator] for c in p] for p in pts]
 if not isinstance(cache['points'], list) or len(cache['points']) != len(enc): raise Bad('cachepoints')
 for p in cache['points']:
  if not isinstance(p, list) or len(p) != 2 or not all(is_ratio(c) for c in p): raise Bad('cachepoints')
 if not IO.strict_eq(cache['points'], enc): raise Bad('cachepoints')
 m = len(pts) if closed else len(pts) - 1
 if not isinstance(cache['edges'], list) or len(cache['edges']) != m: raise Bad('edgecount')
 for e in cache['edges']:
  IO.keys(e, {'q', 'lo', 'hi'}, 'edge')
  if not is_ratio(e['q']) or not IO.is_int(e['lo']) or not IO.is_int(e['hi']) or e['lo'] < 0 or e['hi'] < e['lo'] or e['hi'] - e['lo'] > 1: raise Bad('edgeform')
 for name in ('pref_lo', 'pref_hi'):
  v = cache[name]
  if not isinstance(v, list) or len(v) != m + 1 or any(not IO.is_int(x) or x < 0 for x in v): raise Bad(name + 'form')
 deg = cache['degenerate_indices']
 if not isinstance(deg, list) or any(not IO.is_int(x) or not (0 <= x < m) for x in deg) or deg != sorted(set(deg)): raise Bad('degform')
 c = cache['counters']; IO.keys(c, {'edges', 'ops', 'max_bits'}, 'counters')
 if not IO.is_int(c['edges']) or c['edges'] != m or not IO.is_int(c['ops']) or not (0 <= c['ops'] <= IO.CHAIN_OPS) or not IO.is_int(c['max_bits']) or not (0 <= c['max_bits'] <= 4096): raise Bad('counters')
 return m
def verify_cache(cache, points, closed, meta_expected, budget, prep=None):
 m = validate_cache_form(cache, meta_expected, closed, points)
 if prep is None: prep = prepare(points, closed, cache, budget)
 if len(prep.edges) != m: raise Bad('edgecount')
 pl = [0]; ph = [0]
 for i, e in enumerate(cache['edges']):
  lo, hi, q = prep.edges[i]
  if not IO.strict_eq(e['q'], [q.numerator, q.denominator]) or e['lo'] != lo or e['hi'] != hi: raise Bad('edge')
  budget.need_sum(pl[-1], lo); budget.need_sum(ph[-1], hi); pl.append(pl[-1] + lo); ph.append(ph[-1] + hi)
 if not IO.strict_eq(cache['pref_lo'], pl) or not IO.strict_eq(cache['pref_hi'], ph): raise Bad('prefix')
 if not IO.strict_eq(cache['degenerate_indices'], prep.deg): raise Bad('degenerate')
 return prep
UNITS = {'cross': 'm^2', 'dot': 'm^2', 'chord_ba': 'm', 'chord_bc': 'm', 'chord_ac': 'm', 'deficit': '1', 'deviation': 'm', 'curvature': '1/m', 'angle': 'rad'}
def validate_station_enc(s):
 IO.keys(s, {'segment', 'from_point', 'to_point', 't', 'point'}, 'station')
 if not (s['segment'] is None or (IO.is_int(s['segment']) and s['segment'] >= 0)): raise Bad('stationsegment')
 if not is_point_enc(s['from_point']) or not is_point_enc(s['to_point']) or not is_interval(s['t']): raise Bad('stationform')
 if not isinstance(s['point'], list) or len(s['point']) != 2 or not all(is_interval(x) for x in s['point']): raise Bad('stationpoint')
def validate_result_form(r):
 if not isinstance(r, dict): raise Bad('result')
 if r.get('state') == 'RESOURCE_INCONCLUSIVE':
  if set(r) != {'state', 'stations', 'features', 'support', 'ops', 'reason'} or r['stations'] is not None or r['features'] is not None or r['support'] is not None or r['ops'] is not None or r['reason'] != 'query_budget': raise Bad('resourceform')
  return
 if set(r) != {'state', 'stations', 'features', 'support', 'ops'} or not IO.is_int(r['ops']) or not (0 <= r['ops'] <= IO.QUERY_OPS): raise Bad('resultform')
 if r['state'] not in ('DEFINED', 'UNDEFINED_ZERO_CHORD', 'INSUFFICIENT_SUPPORT', 'SUPPORT_UNCERTAIN', 'BOUNDARY_UNCERTAIN', 'OUT_OF_RANGE'): raise Bad('state')
 sup = r['support']; IO.keys(sup, {'perimeter', 'backward', 'forward', 'state'}, 'support')
 if sup['state'] not in ('SUPPORTED', 'INSUFFICIENT_SUPPORT', 'SUPPORT_UNCERTAIN'): raise Bad('supportstate')
 for k in ('perimeter', 'backward', 'forward'):
  if sup[k] is not None and not is_interval(sup[k]): raise Bad('supportform')
 if r['state'] in ('DEFINED', 'UNDEFINED_ZERO_CHORD'):
  IO.keys(r['stations'], {'A', 'B', 'C'}, 'stations')
  for s in r['stations'].values(): validate_station_enc(s)
  feats = r['features']; IO.keys(feats, set(UNITS), 'features')
  for k, f in feats.items():
   IO.keys(f, {'state', 'interval', 'unit', 'width'}, 'field')
   if f['unit'] != UNITS[k] or not isinstance(f['state'], str): raise Bad('fieldform')
   if (f['interval'] is None) != (f['width'] is None): raise Bad('fieldform')
   if f['interval'] is not None and (not is_interval(f['interval']) or not is_ratio(f['width'])): raise Bad('fieldform')
 else:
  if r['stations'] is not None or r['features'] is not None: raise Bad('resultnulls')
def validate_state_counts(v):
 if not isinstance(v, dict) or any(not isinstance(k, str) or not IO.is_int(x) or x < 0 for k, x in v.items()): raise Bad('statecounts')
def validate_terminal(term, cid, csha, sel_sha, univ):
 IO.keys(term, {'kind', 'chain_id', 'contract_sha256', 'selector_sha256', 'classification', 'universe', 'query_count', 'excluded_count', 'state_counts', 'cache', 'shards', 'unverified_numeric_count'}, 'terminal')
 if term['kind'] != 'chain_terminal' or not IO.is_int(term['chain_id']) or term['chain_id'] != cid or term['contract_sha256'] != csha or term['selector_sha256'] != sel_sha: raise Bad('terminalbind')
 if term['classification'] not in ('NUMERIC', 'DEGENERATE', 'RESOURCE_INCONCLUSIVE'): raise Bad('classification')
 for k in ('universe', 'query_count', 'excluded_count', 'unverified_numeric_count'):
  if not IO.is_int(term[k]) or term[k] < 0: raise Bad('terminalint')
 if term['universe'] != univ: raise Bad('terminalbind')
 validate_state_counts(term['state_counts'])
 if term['cache'] is not None:
  IO.keys(term['cache'], {'name', 'bytes', 'sha256'}, 'cacheentry')
  if term['cache']['name'] != 'cache.json' or not IO.is_int(term['cache']['bytes']) or term['cache']['bytes'] < 0 or not IO.is_hex64(term['cache']['sha256']): raise Bad('cacheentry')
 if not isinstance(term['shards'], list): raise Bad('shards')
 for i, sh in enumerate(term['shards']):
  IO.keys(sh, {'name', 'bytes', 'sha256', 'queries'}, 'shard')
  if sh['name'] != IO.shard_name(i) or not IO.is_int(sh['bytes']) or sh['bytes'] < 0 or not IO.is_hex64(sh['sha256']) or not IO.is_int(sh['queries']) or sh['queries'] < 0: raise Bad('shardform')
def validate_manifest(man, csha, npz_sha, nchains, universe):
 IO.keys(man, {'kind', 'schema', 'contract_sha256', 'npz_sha256', 'chain_count', 'universe', 'query_count', 'excluded_count', 'state_counts', 'unverified_numeric_count', 'terminals'}, 'manifest')
 if man['kind'] != 'manifest' or man['schema'] != 'q02b3.v1' or man['contract_sha256'] != csha or man['npz_sha256'] != npz_sha: raise Bad('manifest')
 for k in ('chain_count', 'universe', 'query_count', 'excluded_count', 'unverified_numeric_count'):
  if not IO.is_int(man[k]) or man[k] < 0: raise Bad('manifestint')
 if man['chain_count'] != nchains or man['universe'] != universe: raise Bad('manifest')
 validate_state_counts(man['state_counts'])
 if not isinstance(man['terminals'], list) or len(man['terminals']) != nchains: raise Bad('manifestterminals')
 for i, t in enumerate(man['terminals']):
  IO.keys(t, {'chain_id', 'bytes', 'sha256'}, 'manifestterminal')
  if not IO.is_int(t['chain_id']) or t['chain_id'] != i or not IO.is_int(t['bytes']) or t['bytes'] < 0 or not IO.is_hex64(t['sha256']): raise Bad('manifestterminal')
def tail_cap(name, limits):
 if name in ('cache.json', 'cache.json.tmp'): return limits['cache_bytes']
 if name in ('terminal.json', 'terminal.json.tmp'): return limits['terminal_bytes']
 return limits['shard_bytes']
def main(argv=None):
 ap = argparse.ArgumentParser(); ap.add_argument('--root', required=True); ap.add_argument('--contract', required=True); ap.add_argument('--contract-sha', required=True); ap.add_argument('--capture-dir', required=True); ap.add_argument('--output', required=True); a = ap.parse_args(argv)
 report = {'schema': 'q02b3-consumer.v1', 'state': 'REJECTED', 'coverage_complete': False, 'completed_chains': 0, 'covered_universe': 0, 'universe': 0, 'query_count': 0, 'excluded_count': 0, 'state_counts': {}, 'unverified_numeric_count': 0, 'unverified_tail': None, 'claims': None, 'bindings': {}, 'errors': []}
 rc = 1; completed = 0; covered = 0; gq = 0; gex = 0; gu = 0; gp = 0; gst = {}; observed_deg = []
 try:
  root = Path(a.root); contract, csha, selectors, oracles = IO.load_contract(root, a.contract, a.contract_sha); report['claims'] = IO.claims(contract); report['universe'] = selectors['universe']; report['bindings'] = {'contract_sha256': csha, 'npz_sha256': contract['npz_sha256'], 'selectors_sha256': contract['selectors']['sha256'], 'oracles_sha256': contract['oracles']['sha256']}
  global V; V = IO.load_sealed(root, 'tools/quality/verify_certified_shore_kernel_ev112.py', contract['helpers']['tools/quality/verify_certified_shore_kernel_ev112.py'], 'vc_')
  arrays = IO.load_npz(root, contract); chains = IO.source_chains(arrays, selectors); cap = Path(a.capture_dir); IO.check_ancestors(cap); IO.require_dir(cap)
  top = IO.list_entries(cap)
  expected_top = {'header.json', 'manifest.json', 'manifest.json.tmp'} | {IO.chain_dir(i) for i in range(len(chains))}
  if not set(top) <= expected_top: raise Bad('extra_top')
  for name, kind in top.items():
   if name.startswith('chain-') and kind != 'dir': raise Bad('topkind')
   if not name.startswith('chain-') and kind != 'file': raise Bad('topkind')
  if 'header.json' not in top: raise Bad('header')
  hdata = IO.read_bounded(cap / 'header.json', contract['output_limits']['terminal_bytes']); header = IO.strict_parse(hdata, 'header'); exp_header = {'schema': 'q02b3.v1', 'kind': 'header', 'contract_sha256': csha, 'npz_sha256': contract['npz_sha256'], 'helpers': contract['helpers'], 'universe': selectors['universe'], 'claims': IO.claims(contract)}
  if not IO.strict_eq(header, exp_header): raise Bad('header')
  IO.capture_total_bytes(cap, contract['output_limits']['total_bytes'])
  if 'manifest.json.tmp' in top: IO.read_bounded(cap / 'manifest.json.tmp', contract['output_limits']['manifest_bytes'])
  first_gap = None; tail = None; any_consumer_resource = False
  for idx, ch in enumerate(chains):
   s = ch['selector']; cid = s['chain_id']; univ = s['core_count'] * 5; cdir = cap / IO.chain_dir(cid); tpath = cdir / 'terminal.json'
   if not IO.exists_nofollow(tpath):
    first_gap = cid
    if IO.exists_nofollow(cdir):
     entries = IO.list_entries(cdir); names = sorted(entries)
     if any(k != 'file' for k in entries.values()): raise Bad('tailkind')
     if not IO.capture_names_ok(names): raise Bad('tailnames')
     for name in names:
      if IO.exists_nofollow(cdir / name) and len(IO.read_bounded(cdir / name, tail_cap(name, contract['output_limits']))) > tail_cap(name, contract['output_limits']): raise Bad('tailcap')
     tail = {'chain_id': cid, 'files': names}
    else: tail = {'chain_id': cid, 'files': []}
    break
   IO.require_file(tpath); IO.require_dir(cdir)
   tdata = IO.read_bounded(tpath, contract['output_limits']['terminal_bytes']); term = IO.strict_parse(tdata, 'terminal'); validate_terminal(term, cid, csha, IO.selector_sha(s), univ)
   entries = IO.list_entries(cdir)
   if any(k != 'file' for k in entries.values()): raise Bad('chainkind')
   names = set(entries); budget = CB(contract['chain_ops']); consumer_resource = False; prep = None; local_unver = term['unverified_numeric_count']
   meta = {'chain_id': cid, 'point_offset': s['point_offset'], 'segment_offset': s['segment_offset'], 'core_count': s['core_count'], 'core_float64_le_sha256': s['core_float64_le_sha256'], 'npz_sha256': contract['npz_sha256'], 'contract_sha256': csha}
   if term['classification'] == 'RESOURCE_INCONCLUSIVE':
    if term['cache'] is not None or term['shards'] != [] or term['query_count'] != 0 or term['excluded_count'] != univ or term['state_counts'] != {'RESOURCE_INCONCLUSIVE': univ} or term['unverified_numeric_count'] != univ: raise Bad('resterm')
    if names != {'terminal.json'}: raise Bad('resfiles')
   elif term['classification'] in ('DEGENERATE', 'NUMERIC'):
    if term['cache'] is None: raise Bad('cachemissing')
    cdata = IO.read_bounded(cdir / 'cache.json', contract['output_limits']['cache_bytes'])
    if not IO.strict_eq(term['cache'], {'name': 'cache.json', 'bytes': len(cdata), 'sha256': IO.sha_bytes(cdata)}): raise Bad('cachebind')
    cache = IO.strict_parse(cdata, 'cache'); validate_cache_form(cache, meta, ch['closed'], ch['points'])
    if term['classification'] == 'DEGENERATE':
     if term['shards'] != [] or term['query_count'] != 0 or term['excluded_count'] != univ or term['state_counts'] != {'DEGENERATE': univ} or term['unverified_numeric_count'] != 0: raise Bad('degterm')
     if names != {'cache.json', 'terminal.json'}: raise Bad('degfiles')
    else:
     if term['excluded_count'] != 0: raise Bad('numterm')
     if not term['shards']: raise Bad('shards')
     maxshards = -(-univ * contract['output_limits']['query_bytes'] // max(1, contract['output_limits']['shard_bytes'] - contract['output_limits']['query_bytes'])) + 1
     if len(term['shards']) > maxshards: raise Bad('shardcount')
     exp_names = {'cache.json', 'terminal.json'} | {sh['name'] for sh in term['shards']}
     if names != exp_names: raise Bad('chainfiles')
     qi = 0; local_states = {}; prod_unver = 0; shard_first = []; shard_sizes = []
     for si, sh in enumerate(term['shards']):
      data = IO.read_bounded(cdir / sh['name'], contract['output_limits']['shard_bytes'])
      if len(data) != sh['bytes'] or IO.sha_bytes(data) != sh['sha256'] or not data.endswith(b'\n'): raise Bad('shardbind')
      raw = data.split(b'\n')[:-1]
      if not raw or sh['queries'] != len(raw): raise Bad('shardqueries')
      shard_first.append(raw[0] + b'\n'); shard_sizes.append(len(data))
      for line in raw:
       if len(line) + 1 > contract['output_limits']['query_bytes']: raise Bad('querybytes')
       rec = IO.strict_parse(line, 'query'); IO.keys(rec, {'kind', 'chain_id', 'center', 'h', 'result'}, 'query')
       ec = qi // len(contract['h']); eh = contract['h'][qi % len(contract['h'])]
       if rec['kind'] != 'query' or not IO.is_int(rec['chain_id']) or rec['chain_id'] != cid or not IO.is_int(rec['center']) or rec['center'] != ec or not IO.is_int(rec['h']) or rec['h'] != eh: raise Bad('queryorder')
       try: validate_result_form(rec['result'])
       except Exception as e:
        if is_res(e): consumer_resource = True
        else: raise
       qi += 1; local_states[rec['result']['state']] = local_states.get(rec['result']['state'], 0) + 1
       if rec['result']['state'] == 'RESOURCE_INCONCLUSIVE': prod_unver += 1
     for si in range(len(shard_sizes) - 1):
      if shard_sizes[si] + len(shard_first[si + 1]) <= contract['output_limits']['shard_bytes']: raise Bad('shardpacking')
     if qi != univ or term['query_count'] != qi or not IO.strict_eq(term['state_counts'], local_states) or term['unverified_numeric_count'] != prod_unver: raise Bad('termcounts')
     local_unver = prod_unver
    try:
     prep = prepare(ch['points'], ch['closed'], None, budget)
     if prep.deg: observed_deg.append(cid)
     prep = verify_cache(cache, ch['points'], ch['closed'], meta, budget, prep=prep)
    except Exception as e:
     if is_res(e): consumer_resource = True; prep = prep
     else: raise
    if not consumer_resource and prep is not None:
     isdeg = bool(prep.deg)
     if term['classification'] == 'DEGENERATE' and not isdeg: raise Bad('degclass')
     if term['classification'] == 'NUMERIC':
      if isdeg: raise Bad('numdeg')
      qi2 = 0; stop = False
      for si, sh in enumerate(term['shards']):
       if stop: break
       data = IO.read_bounded(cdir / sh['name'], contract['output_limits']['shard_bytes']); raw = data.split(b'\n')[:-1]
       for line in raw:
        rec = IO.strict_parse(line, 'query'); ec = qi2 // len(contract['h']); eh = contract['h'][qi2 % len(contract['h'])]; qi2 += 1
        if rec['result']['state'] == 'RESOURCE_INCONCLUSIVE': continue
        try: exp = query_prepared(prep, ec, eh)
        except Exception as e:
         if is_res(e): consumer_resource = True; stop = True; break
         raise
        if not IO.strict_eq({k: v for k, v in rec['result'].items() if k != 'ops'}, {k: v for k, v in exp.items() if k != 'ops'}): raise Bad('querymismatch')
   else: raise Bad('classification')
   if consumer_resource: any_consumer_resource = True; local_unver = univ
   completed += 1; covered += univ; gq += term['query_count']; gex += term['excluded_count']; gu += local_unver; gp += term['unverified_numeric_count']
   for k, v in term['state_counts'].items(): gst[k] = gst.get(k, 0) + v
  if first_gap is not None:
   for cid in range(first_gap + 1, len(chains)):
    if IO.exists_nofollow(cap / IO.chain_dir(cid)): raise Bad('chainaftergap')
   if IO.exists_nofollow(cap / 'manifest.json'): raise Bad('manifestpartial')
   report.update({'coverage_complete': False, 'completed_chains': completed, 'covered_universe': covered, 'query_count': gq, 'excluded_count': gex, 'state_counts': gst, 'unverified_numeric_count': gu, 'unverified_tail': tail})
   report['state'] = 'NUMERIC_RESOURCE_INCONCLUSIVE' if (gu or any_consumer_resource) else 'VERIFIED_PARTIAL_NUMERIC_COVERAGE'; rc = 2
  else:
   mpath = cap / 'manifest.json'
   if not IO.exists_nofollow(mpath): raise Bad('manifest')
   IO.require_file(mpath)
   if IO.exists_nofollow(cap / 'manifest.json.tmp'): raise Bad('manifesttmpfull')
   mdata = IO.read_bounded(mpath, contract['output_limits']['manifest_bytes']); man = IO.strict_parse(mdata, 'manifest'); validate_manifest(man, csha, contract['npz_sha256'], len(chains), selectors['universe'])
   terms = []
   for idx in range(len(chains)):
    td = IO.read_bounded(cap / IO.chain_dir(idx) / 'terminal.json', contract['output_limits']['terminal_bytes']); terms.append({'chain_id': idx, 'bytes': len(td), 'sha256': IO.sha_bytes(td)})
   if not IO.is_int(man['query_count']) or man['query_count'] != gq or man['excluded_count'] != gex or not IO.strict_eq(man['state_counts'], gst) or man['unverified_numeric_count'] != gp or not IO.strict_eq(man['terminals'], terms): raise Bad('manifest')
   report.update({'coverage_complete': True, 'completed_chains': completed, 'covered_universe': covered, 'query_count': gq, 'excluded_count': gex, 'state_counts': gst, 'unverified_numeric_count': gu, 'unverified_tail': None})
   deg_mismatch = observed_deg != contract['expected']['degenerate_chain_ids']
   if deg_mismatch and not (gu or any_consumer_resource): report['errors'] = ['degenerate_expected_mismatch']
   if gu or any_consumer_resource or deg_mismatch: report['state'] = 'NUMERIC_RESOURCE_INCONCLUSIVE'; rc = 2
   else: report['state'] = 'VERIFIED_FULL_NUMERIC_COVERAGE_ONLY'; rc = 0
 except Bad as e: report['state'] = 'REJECTED'; report['errors'] = [str(e)]; rc = 1
 except Exception as e:
  report.update({'completed_chains': completed, 'covered_universe': covered, 'query_count': gq, 'excluded_count': gex, 'state_counts': gst, 'unverified_numeric_count': gu})
  if is_res(e): report['state'] = 'NUMERIC_RESOURCE_INCONCLUSIVE'; report['errors'] = [str(e)]; rc = 2
  else: report['state'] = 'REJECTED'; report['errors'] = [str(e)]; rc = 1
 try: IO.write_exclusive(a.output, IO.canon(report) + b'\n')
 except Exception as e: print(str(e), file=sys.stderr); return 1
 print(report['state']); return rc
if __name__ == '__main__': raise SystemExit(main())
