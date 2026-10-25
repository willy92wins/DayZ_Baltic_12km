from pathlib import Path
import csv,json,hashlib,shutil,math
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
ref=json.loads((B/'native-census-reference.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
log=Path('P:/DayZ_MCP_dev/_server/profiles/baltic_native_census_v1.log');text=log.read_text(encoding='utf-8-sig')
def judge(text,expected):
    lines=[s.split(';') for s in text.splitlines() if s];g=[];p=[];end=[];gridend=[];errors=[]
    if not lines or lines[0]!=['BALTIC_NATIVE_CENSUS_V1','BalticTrial',ref['terrain_sha256']]:errors.append('header')
    for f in lines:
        if f[0]=='FAIL':errors.append('mission_failure')
        if f[0]=='G':g.append(f)
        if f[0]=='P':p.append(f)
        if f[0]=='END':end.append(f)
        if f[0]=='GRID_END':gridend.append(f)
    if len(g)!=2048 or [int(f[1]) for f in g]!=list(range(2048)):errors.append('grid_coverage')
    if any(len(f)!=5 or int(f[2])!=2048 or int(f[3])!=0 or not math.isfinite(float(f[4])) or float(f[4])>.001 for f in g):errors.append('grid_comparison')
    if len(p)!=len(expected) or [int(f[1]) for f in p]!=list(range(len(expected))):errors.append('water_coverage')
    if len(gridend)!=1 or gridend[0][1:4]!=['4194304','0','true']:errors.append('grid_end_and_live_negative')
    if len(end)!=1 or end[0][1:4]!=['4194304','0',str(len(expected))]:errors.append('end')
    rows=[]
    for f,q in zip(p,expected):
        nums=[float(v) for v in [f[2],*f[5:]]]
        if not all(math.isfinite(v) for v in nums):errors.append('nonfinite');continue
        if abs(nums[0]-q['expected_ground'])>.001:errors.append('water_height_reference')
        rows.append(dict(**q,ground=nums[0],sea=f[3]=='true',pond=f[4]=='true',plane=nums[1],depth=nums[2],sea_now=nums[3],
                         wet_nominal=bool((f[3]=='true' or f[4]=='true') and nums[1]>nums[0]+.03),
                         wet_dynamic=bool((f[3]=='true' or f[4]=='true') and nums[2]>.02)))
    return dict(pass_gate=not errors,errors=sorted(set(errors)),rows=rows,grid=g,end=end)
r=judge(text,ref['points']);negative={}
lines=text.splitlines()
negative['row_missing']=not judge('\n'.join(s for s in lines if not s.startswith('G;42;')),ref['points'])['pass_gate']
negative['water_point_missing']=not judge('\n'.join(s for s in lines if not s.startswith('P;42;')),ref['points'])['pass_gate']
negative['missing_end']=not judge('\n'.join(s for s in lines if not s.startswith('END;')),ref['points'])['pass_gate']
mut=[dict(p) for p in ref['points']];mut[-7]['expected_ground']+=1
negative['wrong_reference']=not judge(text,mut)['pass_gate']
negative['live_wrong_height']=len(r['grid'])==2048 and 'GRID_END;4194304;0;true;' in text
assert all(negative.values()),negative
dry=[p for p in r['rows'] if p['cls']==0]
physical=[p for p in dry if p['wet_nominal'] or p['wet_dynamic']]
with (E/'native-water-positive-dry.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(r['rows'][0]));writer.writeheader();writer.writerows(physical)
shutil.copyfile(log,E/'native-census-runtime.log')
shutil.copyfile(Path(ref['mission'])/'risks.csv',E/'native-census-points.csv')
shutil.copyfile(Path('P:/DayZ_MCP_dev/_server/profiles/script_2026-10-09_02-50-17.log'),E/'native-census-script.log')
out=dict(status='PASS_NATIVE_GEOMETRY_AND_WATER_READBACK' if r['pass_gate'] else 'FAIL',errors=r['errors'],
    terrain_sha256=ref['terrain_sha256'],pbo=ref['pbo'],runtime_sha256=sha(log),vertices=4194304,
    max_vertex_error_m=max(float(f[4]) for f in r['grid']),water_points=len(r['rows']),
    dry_points=len(dry),nominally_wet_dry=sum(p['wet_nominal'] for p in dry),dynamically_wet_dry=sum(p['wet_dynamic'] for p in dry),
    calibrated=[p for p in r['rows'] if p['role'] not in ('low_dry_vertex','high_dry_control')],
    negative=negative,elapsed_mission_ms=int(r['end'][0][-1]) if r['end'] else None,
    limits=['PASS is for height agreement and complete readback, not absence of water/render bugs.',
    'Physical water readback covers all 30,668 empirical low dry vertices plus controls, not all 3,195,297 dry vertices.',
    'A nonfatal diagnostic-plugin stack trace is retained; the mission completed all rows and points.',
    'Compiled native height is not the rendered terrain LOD or visual wave envelope.'])
(E/'native-census-verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
