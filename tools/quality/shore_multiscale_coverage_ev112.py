#!/usr/bin/env python3
import argparse, hashlib, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shore_coverage_io_ev112 as IO
Bad = IO.Bad; Resource = IO.Resource
PILOT = None
def is_resource(e):
 if isinstance(e, IO.Resource): return True
 if PILOT is not None:
  for cls in (getattr(PILOT, 'Resource', None), getattr(getattr(PILOT, 'K', None), 'Res', None)):
   if isinstance(cls, type) and isinstance(e, cls): return True
 return False
def main(argv=None):
 ap = argparse.ArgumentParser(); ap.add_argument('--root', required=True); ap.add_argument('--contract', required=True); ap.add_argument('--contract-sha', required=True); ap.add_argument('--output-dir', required=True); a = ap.parse_args(argv)
 try:
  root = Path(a.root); contract, csha, selectors, oracles = IO.load_contract(root, a.contract, a.contract_sha)
  arrays = IO.load_npz(root, contract); chains = IO.source_chains(arrays, selectors)
  global PILOT; PILOT = IO.load_sealed(root, 'tools/quality/shore_prefix_pilot_ev112.py', IO.KNOWN_HELPERS['tools/quality/shore_prefix_pilot_ev112.py'], 'pilot_'); PILOT.load_helpers(root)
  out = Path(a.output_dir); IO.check_ancestors(out)
  if IO.exists_nofollow(out): raise Bad('outputexists')
  out.mkdir(parents=True); IO.require_dir(out)
  total = 0; total_cap = contract['output_limits']['total_bytes']
  def reserve(n):
   nonlocal total; total += n
   if total > total_cap: raise Bad('totalbytes')
  header = {'schema': 'q02b3.v1', 'kind': 'header', 'contract_sha256': csha, 'npz_sha256': contract['npz_sha256'], 'helpers': contract['helpers'], 'universe': selectors['universe'], 'claims': IO.claims(contract)}
  hb = IO.canon(header); reserve(len(hb)); IO.atomic_new(out / 'header.json', hb)
  terminals = []; g_query = 0; g_excluded = 0; g_unverified = 0; g_states = {}
  for ch in chains:
   s = ch['selector']; cid = s['chain_id']; univ = s['core_count'] * 5; cdir = out / IO.chain_dir(cid); cdir.mkdir(); IO.require_dir(cdir)
   meta = {'chain_id': cid, 'point_offset': s['point_offset'], 'segment_offset': s['segment_offset'], 'core_count': s['core_count'], 'core_float64_le_sha256': s['core_float64_le_sha256'], 'npz_sha256': contract['npz_sha256'], 'contract_sha256': csha}
   cache = None; cache_info = None; shards = []; classification = None; qcount = 0; excluded = 0; unverified = 0; states = {}
   try: cache = PILOT.build_cache(ch['points'], ch['closed'], meta)
   except Exception as e:
    if is_resource(e): classification = 'RESOURCE_INCONCLUSIVE'
    else: raise Bad('buildcache:' + str(e))
   if classification == 'RESOURCE_INCONCLUSIVE':
    excluded = univ; unverified = univ; states = {'RESOURCE_INCONCLUSIVE': univ}
   else:
    cb = IO.canon(cache)
    if len(cb) > contract['output_limits']['cache_bytes']: raise Bad('cachebytes')
    reserve(len(cb)); IO.atomic_new(cdir / 'cache.json', cb); cache_info = {'name': 'cache.json', 'bytes': len(cb), 'sha256': IO.sha_bytes(cb)}
    prepared = PILOT._Prepared(cache, PILOT._points_frac(cache['points']))
    if cache['degenerate_indices']:
     classification = 'DEGENERATE'; excluded = univ; states = {'DEGENERATE': univ}
    else:
     classification = 'NUMERIC'; shard_idx = 0; cur = None; cur_bytes = 0; cur_queries = 0; hasher = None
     def close_shard():
      nonlocal cur, cur_bytes, cur_queries, shard_idx, hasher
      if cur is None: return
      cur.flush(); os.fsync(cur.fileno()); cur.close(); cur = None
      if cur_bytes == 0: raise Bad('emptyshard')
      shards.append({'name': IO.shard_name(shard_idx), 'bytes': cur_bytes, 'sha256': hasher.hexdigest(), 'queries': cur_queries}); shard_idx += 1; cur_bytes = 0; cur_queries = 0; hasher = None
     try:
      for center in range(s['core_count']):
       for h in contract['h']:
        try: r = PILOT.query(prepared, center, h)
        except Exception as e:
         if is_resource(e): r = {'state': 'RESOURCE_INCONCLUSIVE', 'stations': None, 'features': None, 'support': None, 'ops': None, 'reason': 'query_budget'}
         else: raise
        if not isinstance(r, dict) or 'state' not in r: raise Bad('queryresult')
        if r['state'] == 'RESOURCE_INCONCLUSIVE' and set(r) != {'state', 'stations', 'features', 'support', 'ops', 'reason'}: r = {'state': 'RESOURCE_INCONCLUSIVE', 'stations': None, 'features': None, 'support': None, 'ops': None, 'reason': 'query_budget'}
        rec = {'kind': 'query', 'chain_id': cid, 'center': center, 'h': h, 'result': r}; line = IO.canon(rec) + b'\n'
        if len(line) > contract['output_limits']['query_bytes']: raise Bad('querybytes')
        if cur is not None and cur_bytes + len(line) > contract['output_limits']['shard_bytes']: close_shard()
        if cur is None:
         reserve(len(line)); cur = open(cdir / IO.shard_name(shard_idx), 'xb'); hasher = hashlib.sha256()
        else: reserve(len(line))
        cur.write(line); hasher.update(line); cur_bytes += len(line); cur_queries += 1; qcount += 1; states[r['state']] = states.get(r['state'], 0) + 1
        if r['state'] == 'RESOURCE_INCONCLUSIVE': unverified += 1
      close_shard()
     finally:
      if cur is not None:
       try: cur.close()
       except Exception: pass
   term = {'kind': 'chain_terminal', 'chain_id': cid, 'contract_sha256': csha, 'selector_sha256': IO.selector_sha(s), 'classification': classification, 'universe': univ, 'query_count': qcount, 'excluded_count': excluded, 'state_counts': states, 'cache': cache_info, 'shards': shards, 'unverified_numeric_count': unverified}
   tb = IO.canon(term)
   if len(tb) > contract['output_limits']['terminal_bytes']: raise Bad('terminalbytes')
   reserve(len(tb)); IO.atomic_new(cdir / 'terminal.json', tb); terminals.append({'chain_id': cid, 'bytes': len(tb), 'sha256': IO.sha_bytes(tb)}); g_query += qcount; g_excluded += excluded; g_unverified += unverified
   for k, v in states.items(): g_states[k] = g_states.get(k, 0) + v
  manifest = {'kind': 'manifest', 'schema': 'q02b3.v1', 'contract_sha256': csha, 'npz_sha256': contract['npz_sha256'], 'chain_count': len(chains), 'universe': selectors['universe'], 'query_count': g_query, 'excluded_count': g_excluded, 'state_counts': g_states, 'unverified_numeric_count': g_unverified, 'terminals': terminals}
  mb = IO.canon(manifest)
  if len(mb) > contract['output_limits']['manifest_bytes']: raise Bad('manifestbytes')
  reserve(len(mb)); IO.atomic_new(out / 'manifest.json', mb)
  print('RESOURCE_INCONCLUSIVE' if g_unverified else 'COMPLETE')
  return 2 if g_unverified else 0
 except Bad as e: print('REJECTED:' + str(e), file=sys.stderr); return 1
 except Exception as e:
  if is_resource(e): print('INCONCLUSIVE_RESOURCE:' + str(e), file=sys.stderr); return 2
  print('REJECTED:' + str(e), file=sys.stderr); return 1
if __name__ == '__main__': raise SystemExit(main())
