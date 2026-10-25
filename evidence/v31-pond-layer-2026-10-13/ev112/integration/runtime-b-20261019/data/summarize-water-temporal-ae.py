from pathlib import Path
import collections,json,statistics,hashlib
O=Path(__file__).parent;D=O/'water-temporal-ae'
proposal=json.loads((D/'proposal.json').read_text());stat=collections.Counter((p['family'],p['kind']) for p in proposal['proposed_failures'])
rejection=dict(status='REJECTED_NOT_IMPLEMENTED',reason='Sea/Pond flags and NoFakeWave query from 100m do not agree with positive depth for numerous sloped kit faces; cannot replace the complete consumer with this rule.',proposed_failures=len(proposal['proposed_failures']),by_kind={str(k):v for k,v in stat.items()},proposal_sha256=hashlib.sha256((D/'proposal.json').read_bytes()).hexdigest())
(D/'proposal-rejection.json').write_text(json.dumps(rejection,indent=2)+'\n');print(json.dumps(rejection))
rs=collections.defaultdict(list)
for line in (D/'baltic_water_temporal_ev112.log').read_text().splitlines():
 a=line.split(';')
 if a[0]=='P':rs[int(a[3])].append(float(a[8]))
diagnosis=json.loads((D/'diagnosis.json').read_text());out=[]
for pid in (2733,3807,3808,3836):
 d=diagnosis['points'][str(pid)];entry=dict(id=pid,family_id=d['family_id'],kind=d['kind'],expected=d['expect'],minimum=min(rs[pid]),mean=statistics.mean(rs[pid]),maximum=max(rs[pid]),positive_samples=d['positive_depths'],samples=30,ground=d['ground_range'][0],nofake_range=d['nofake_range'],wave_relation_max_error=d['max_depth_minus_withfake_query_error']);out.append(entry)
summary=dict(status='USER_DECISION_REQUIRED_NO_EXCEPTION_APPLIED',strict_server_verdict='FAIL',points=out,proposed_scope='Exactly these four probe coordinates, no other point or tolerance. Retain raw strict FAIL and min/max/intermittency. Concrete lips/joints remain the existing plan section5 pending issue. No terrain, gate, package or coordinate changes.',alternative='Continue a physical terrain correction, rebuild and revalidate affected offline/runtime scope; no permission inferred to broaden topology/protected changes.',limits='One minute and fixed weather; does not establish player wetness, all-weather behavior, visual or FPS acceptance.')
(D/'four-point-decision.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
