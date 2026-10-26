"""Geometric feasibility of frozen proposals against the decoded shipped mesh."""
from pathlib import Path
import json,hashlib
from shapely.geometry import LineString,shape
from shapely.ops import unary_union
R=Path(__file__).parent;D=R/'kit7-nav-route-discovery-20261026'
read=lambda p:json.loads(p.read_text())
proposed=read(D/'proposals.json');packed=read(R/'kit7-packed-nav-discovery-20261026/geometry.json')
profiles={x['name']:x['profile'] for x in proposed['screen']};models=packed['models']
dry={k:shape(v['dry']) for k,v in models.items()};water={k:shape(v['water']) for k,v in models.items()};allwater=unary_union(list(water.values()))
queries=proposed['queries']+packed['cap_queries'];results=[]
for q in queries:
    coords=q.get('centerline') or [[x['x'],x['z']] for x in profiles[q['name']]]
    line=LineString(coords);base=unary_union([dry[k] for k in q['models']]);wet=unary_union([water[k] for k in q['models']]);full=base.union(wet)
    exterior=line.buffer(2.1).difference(full) if q['kind']=='cap_to_land' else None
    allowed=base if exterior is None else base.union(exterior)
    covered={k:line.intersection(dry[k]).length for k in q['models']}
    record=dict(name=q['name'],length=line.length,uncovered_length=line.difference(allowed.buffer(.01)).length,water_overlap_length=line.intersection(allwater).length,covered_by_model=covered,exterior_length=0 if exterior is None else line.difference(full).length)
    record['screen_pass']=record['uncovered_length']<1e-8 and record['water_overlap_length']<1e-8 and all(v>=.5 for v in covered.values()) and (exterior is None or record['exterior_length']>=.5)
    results.append(record)
assert len(results)==562
paths=[Path(__file__),D/'proposals.json',R/'kit7-packed-nav-discovery-20261026/geometry.json']
report=dict(status='GEOMETRIC_CORRIDOR_SCREEN_ONLY',cases=results,failures=[r for r in results if not r['screen_pass']],inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},limits=['Screening proposed centre lines, no native FindPath result.','Horizontal coverage only; no actor motion or whole-segment height acceptance.'])
out=D/'packed-corridor-screen.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(queries=len(results),failures=report['failures']),indent=2))
