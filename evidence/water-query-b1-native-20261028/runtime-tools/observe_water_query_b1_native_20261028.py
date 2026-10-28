from pathlib import Path
import sys,json,collections,statistics
R=Path(__file__).resolve().parent;O=R/'water-query-b1-native-20261028'
W=Path("C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c");sys.path.insert(0,str(W/'tools/quality'))
import water_query_native_b1_ev112 as b
doc=b.read(O/'result.json');b.verify(doc['inputs']);rows=doc['details']
def bounds(v):
 return dict(count=len(v),min=min(v),median=statistics.median(v),max=max(v),max_abs=max(map(abs,v)),within_original_water_005=sum(abs(x)<=.05 for x in v))
def group(rr):
 values={k:[] for k in ('nf_high','fake_high','nf_low','fake_low')}
 h01=[];h12=[];highlow=[];sea=[]
 for r in rr:
  for k in values:values[k].extend(r['depth_surface_residuals'][k])
  m=r['measured'];D=m['depths'];Y=[p[1] for p in m['depth_origins']]
  h01.append((D[0]-D[1])-(Y[1]-Y[0]));h12.append((D[1]-D[2])-(Y[2]-Y[1]))
  highlow.append(m['nf_high']-m['nf_low'])
  for ref in m['sea_refs']:sea.append(ref['depth']-(ref['fake']-ref['depth_origin'][1]))
 return dict(rows=len(rr),points=len({r['id'] for r in rr}),residuals={k:bounds(v) for k,v in values.items()},depth_origin_01=bounds(h01),depth_origin_12=bounds(h12),surface_high_minus_low=bounds(highlow),sea_fake_residue=bounds(sea),surface_classes={k:dict(collections.Counter(r['surface_classes'][k]['label'] for r in rr)) for k in values})
groups={}
for name,rr in [('all',rows),('original_water_fail',[r for r in rows if r['original_states']['water']=='FAIL']),('original_water_pass',[r for r in rows if r['original_states']['water']=='PASS']),('original_water_inconclusive',[r for r in rows if r['original_states']['water']=='INCONCLUSIVE']),('without_recorded_confounders',[r for r in rows if not r['confounders']])]:
 if rr:groups[name]=group(rr)
summary=dict(status='B1_OBSERVATIONS_NO_PRODUCT_ACCEPTANCE',run_id=doc['run_id'],native_verdict=doc['status'],rows=doc['rows'],points=len({r['id'] for r in rows}),reference_mismatches=doc['reference_mismatches'],confounders=dict(collections.Counter(x['reason'] for x in doc['confounders'])),groups=groups,selected_examples=[r for r in rows if r['id'] in (292,524,528,700,723) and r['round']==0],inputs={str(O/'result.json'):b.sha(O/'result.json'),str(Path(__file__).resolve()):b.sha(Path(__file__).resolve())},limits=['All observations retained. Subgroup without recorded confounders does not prove absent confounding.','Numeric agreement supports a hypothesis; does not identify surface/object or repair the original FAIL.'])
b.require(not (O/'observations.json').exists(),'fresh_observations')
(O/'observations.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs','selected_examples')},indent=2))
