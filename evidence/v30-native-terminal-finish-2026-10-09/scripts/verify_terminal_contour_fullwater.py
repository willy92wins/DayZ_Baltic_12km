from pathlib import Path
import csv,json,hashlib,math,shutil
import numpy as np
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-native-terminal-finish-2026-10-09'
ref=json.loads((E/'terminal-contour-fullwater-reference.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz');assert sha(source)==ref['terrain_sha256']
t=dict(np.load(source));h=t['heights'];cls=t['cls']
log=Path('P:/DayZ_MCP_dev/_server/profiles/baltic_terminal_contour_fullwater_v1.log');content=log.read_text(encoding='utf-8-sig')
def judge(text):
    f=[s.split(';') for s in text.splitlines() if s];errors=[]
    if not f or f[0]!=['BALTIC_TERMINAL_CONTOUR_FULLWATER_V1','BalticTrial',ref['terrain_sha256']]:errors.append('header')
    if any(v[0]=='FAIL' for v in f):errors.append('mission_failure')
    grid=[v for v in f if v[0]=='G'];a=[v for v in f if v[0]=='A'];p=[v for v in f if v[0]=='P'];end=[v for v in f if v[0]=='END'];ge=[v for v in f if v[0]=='GRID_END']
    if len(grid)!=2048 or [int(v[1]) for v in grid]!=list(range(2048)):errors.append('grid_coverage')
    if any(len(v)!=5 or v[2:4]!=['2048','0'] or not math.isfinite(float(v[4])) or float(v[4])>.001 for v in grid):errors.append('height_comparison')
    if len(ge)!=1 or ge[0][1:4]!=['4194304','0','true']:errors.append('grid_end')
    if len(end)!=1 or end[0][1:4]!=['4194304','0','7'] or end[0][5:7]!=[str(ref['dry']),str(ref['wet'])]:errors.append('fullwater_coverage')
    if len(p)!=7 or [v[1] for v in p]!=[str(i) for i in range(7)]:errors.append('calibrated_coverage')
    for v,q in zip(p,ref['points']):
        if not math.isfinite(float(v[2])) or abs(float(v[2])-q['expected_ground'])>.001:errors.append('calibrated_height')
    qs=[v for v in f if v[0]=='Q'];qe=[v for v in f if v[0]=='QUERY_END'];qseen=set()
    if len(qe)!=1 or len(qe[0])!=2 or int(qe[0][1])!=len(qs):errors.append('unflagged_query_count')
    for q in qs:
        if len(q)!=9:errors.append('unflagged_schema');continue
        r,c=int(q[1]),int(q[2])
        if not(0<=r<2048 and 0<=c<2048) or (r,c) in qseen:errors.append('unflagged_identity');continue
        qseen.add((r,c))
        g,lev,dep=map(float,(q[4],q[7],q[8]))
        if q[3]!='0' or q[5:7]!=['false','false'] or int(cls[r,c])!=0 or abs(g-float(h[r,c]))>.001 or not all(math.isfinite(z) for z in (g,lev,dep)) or not(lev>g+.0299 or dep>.0199):errors.append('unflagged_content')
    rows=[];seen=set()
    for v in a:
        if len(v)!=10:errors.append('anomaly_schema');continue
        r,c,kind=map(int,v[1:4]);ground,plane,depth,sea_now=map(float,[v[4],v[7],v[8],v[9]])
        if (r,c) in seen:errors.append('duplicate_anomaly')
        seen.add((r,c))
        if not (0<=r<2048 and 0<=c<2048):errors.append('anomaly_bounds');continue
        if int(cls[r,c])!=kind or not all(math.isfinite(x) for x in (ground,plane,depth,sea_now)) or abs(ground-float(h[r,c]))>.001:errors.append('anomaly_reference')
        sea=v[5]=='true';pond=v[6]=='true';has=sea or pond
        nominal=has and plane>ground+.03;dynamic=has and depth>.02
        near_nominal=has and abs(plane-ground-.03)<.0001;near_dynamic=has and abs(depth-.02)<.0001
        if kind>0 and has:errors.append('invalid_missing_water')
        if kind==0 and not(nominal or dynamic or near_nominal or near_dynamic):errors.append('invalid_dry_water')
        rows.append(dict(row=r,col=c,x=c*6,z=12282-r*6,cls=kind,ground=ground,sea=sea,pond=pond,plane=plane,
            depth=depth,sea_now=sea_now,nominal=bool(nominal),dynamic=bool(dynamic),near_nominal=bool(near_nominal),near_dynamic=bool(near_dynamic),
            reserve=bool(t['reserve'][r,c]),platform=bool(t['platform'][r,c]),beach=bool(t['beach'][r,c])))
    if end:
        for index,key,uncertain in [(7,'nominal','near_nominal'),(8,'dynamic','near_dynamic')]:
            dry=[q for q in rows if q['cls']==0];count=sum(q[key] for q in dry);margin=sum(q[uncertain] for q in dry)
            if abs(count-int(end[0][index]))>margin:errors.append('anomaly_count_'+key)
        if sum(q['cls']>0 for q in rows)!=int(end[0][9]):errors.append('missing_water_count')
    return dict(pass_gate=not errors,errors=sorted(set(errors)),rows=rows,end=end,grid=grid)
r=judge(content);lines=content.splitlines();negative={}
for name,prefix in [('missing_grid_row','G;42;'),('missing_end','END;'),('missing_calibrated_point','P;0;'),('missing_scalar_diagnostic_end','QUERY_END;')]:
    negative[name]=not judge('\n'.join(s for s in lines if not s.startswith(prefix)))['pass_gate']
anomaly=next((s for s in lines if s.startswith('A;')),None)
if anomaly:negative['duplicate_anomaly']=not judge(content+'\n'+anomaly)['pass_gate']
negative['height_mismatch']=not judge(content.replace('G;42;2048;0;','G;42;2048;1;',1))['pass_gate']
assert all(negative.values()),negative
rows=r['rows'];dry=[q for q in rows if q['cls']==0];wet=[q for q in rows if q['cls']>0]
with (E/'terminal-contour-physical-anomalies.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['row']);writer.writeheader();writer.writerows(rows)
(E/'terminal-contour-unflagged-scalar-queries.csv').write_text('row;col;cls;ground;sea;pond;plane;depth\n'+'\n'.join(s[2:] for s in content.splitlines() if s.startswith('Q;'))+'\n')
shutil.copyfile(log,E/'terminal-contour-fullwater-runtime.log')
out=dict(status='PASS_COMPLETE_NATIVE_READBACK' if r['pass_gate'] else 'FAIL',errors=r['errors'],terrain_sha256=ref['terrain_sha256'],pbo=ref['pbo'],
    runtime_sha256=sha(log),vertices=4194304,dry_vertices=ref['dry'],wet_vertices=ref['wet'],
    max_ground_error_m=max(float(v[4]) for v in r['grid']),physical_anomalies=len(rows),
    unflagged_positive_scalar_queries=sum(s.startswith('Q;') for s in content.splitlines()),dry_anomalies=len(dry),nominal_water_on_dry=int(r['end'][0][7]),dynamic_water_on_dry=int(r['end'][0][8]),
    design_water_without_presence=len(wet),missing_by_class={int(k):sum(q['cls']==k for q in wet) for k in sorted(set(q['cls'] for q in wet))},
    dry_nominal_over_1_8=sum(q['nominal'] and q['ground']>1.8 for q in dry),
    dry_by_protection={k:sum(q[k] for q in dry) for k in ('reserve','platform','beach')},
    negatives=negative,elapsed_mission_ms=int(r['end'][0][4]),
    limits=['Complete runtime water queries at every native vertex; subcell continuity and render LOD remain separate.',
    'Anomalies are differences against source class, requiring classification of intentional coast/shore transitions.',
    'Dynamic water is sampled at current wave phase, not every tide/wind envelope.','No visual defect is closed by this physical readback.'])
(E/'terminal-contour-fullwater-verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
