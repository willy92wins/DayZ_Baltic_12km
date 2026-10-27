"""Reuse the frozen planning screen only where recorded native XZ samples agree."""
from pathlib import Path
import hashlib,json
R=Path(__file__).parent;O=R/'kit7-nav-after12-screen-20261027';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
old_path=R/'kit7-nav-consumer-20261026/runtime.log';new_path=R/'kit7-nav12-consumer-20261027/runtime.log'
def points(path):
    out={}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        f=line.split(';')
        if f[0]=='P':out[(f[1],int(f[2]))]=[[float(v) for v in a.strip('<>').split(',')] for a in f[3:]]
    return out
old=points(old_path);new=points(new_path)
known=['kit7_piece_124_right','kit7_piece_133_right','kit7_seam_124_right','kit7_seam_133_right','kit7_piece_116_left','kit7_piece_116_right','kit7_seam_116_right']
keys={k for k in new if k[0] in known};assert len(keys)==14
for k in keys:
    assert k in old and all(abs(old[k][0][i]-new[k][0][i])<1e-6 for i in (0,2)),k
    assert abs(old[k][2][1]-new[k][2][1])<1e-6,k
screen_path=R/'kit7-nav-budget-all-width-screen-20261027/result.json';screen=read(screen_path)
assert screen['status']=='PLANNING_ESTIMATE_ONLY'
rows=[]
for c in screen['candidates']:
    selected=[x for x in c['samples'] if (x['query'],x['index']) in keys]
    assert len(selected)==14
    rows.append(dict(tile_width=c['tile_width'],tile_count=c['tile_count'],maximum_known14_estimate_m=max(x['worst_error'] for x in selected),above_known14_estimate=sum(x['worst_error']>.801 for x in selected),maximum_all_estimate_m=c['maximum_error_m'],above_all_estimate=c['above_0801'],per_query={n:max(x['worst_error'] for x in selected if x['query']==n) for n in known}))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(status='PLANNING_ESTIMATE_ONLY',native_xz_and_physical_y_parity=True,known_queries=known,samples=14,candidates=rows,inputs={str(p):sha(p) for p in [Path(__file__),old_path,new_path,screen_path]},limits=['Predictions are not native heights or acceptance. 12m predicts 74 failures but actually has 3; 8m predicts 10 but actually has 0.','Same fourteen observed XZ points and physical heights; no changed queries, parameters or artifacts.','Candidate ranking only; another experiment requires a new reviewed plan.'])
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{k:v for k,v in row.items() if k!='per_query'} for row in rows],indent=2))
