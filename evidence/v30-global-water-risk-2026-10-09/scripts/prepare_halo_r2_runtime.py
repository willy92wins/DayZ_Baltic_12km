"""Fresh V2 missions: full-grid readback plus immutable 120-point temporal comparison."""
from pathlib import Path
import json,hashlib,shutil,sys,subprocess
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');H=B/'halo-fix-v3'
sys.path[:0]=[str(W/'tools/playtest'),str(W/'tools/terrain')]
from attach_navmesh import read_pbo
from v30_common import tri_sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=B/'measured-bank-bed-r1/terrain.npz';t=dict(np.load(source));h=t['heights'];cls=t['cls']
passed=json.loads((E/'targeted-pocket-removal-verification.json').read_text())
assert passed['status']=='PASS_OFFLINE_TARGETED_FLOOD_REMOVAL' and sha(source)==passed['terrain_sha256']
base=Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons/narva_trial.pbo')
assert sha(base)=='75adb673ed23ab5b656a162063d6a89cbb2e0a0d99aba82263bf2a54a31e8623'
_,pa,a=read_pbo(base);_,pb,b=read_pbo(H/'world/out/narva_trial.pbo')
assert pa==pb and set(a)==set(b)
changed=[k for k in a if a[k]!=b[k]];assert changed==['baltic_trial.wrp'] and b['baltic_trial.wrp'].startswith(b'OPRW')
dest=Path('P:/Mods/@DayZ_Baltic_HaloFixV2/Addons');dest.mkdir(parents=True,exist_ok=False)
for p in (H/'world/out/narva_trial.pbo',H/'water/packed/baltic_water_v30.pbo'):
    shutil.copyfile(p,dest/p.name);assert sha(p)==sha(dest/p.name)
files={p.name:sha(p) for p in dest.glob('*.pbo')}
(E/'halo-r2-deploy.json').write_text(json.dumps(dict(status='ISOLATED_R2_PREVIEW_NOT_ACCEPTED',destination=str(dest.parent),files=files,terrain_sha256=sha(source),changed_world_entries=changed),indent=2)+'\n')
server=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')
lintcmd=[sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py']
def finish(mission,ref,report):
    lint=subprocess.run(lintcmd+[str(mission)],capture_output=True,text=True);got=json.loads(lint.stdout)
    assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==1
    (E/(report+'-lint.json')).write_text(lint.stdout)
    deployed=server/mission.name;shutil.copytree(mission,deployed)
    ref.update(mission=str(deployed),files={p.name:sha(p) for p in mission.iterdir()},terrain_sha256=sha(source),pbo=files)
    assert all(sha(deployed/k)==v for k,v in ref['files'].items())
    (E/(report+'-reference.json')).write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(mission=str(deployed),lint='PASS',pbo=files)))
# Full-grid producer and verifier keep exactly the original query sequence.
old=B/'missions/BalticHaloFullWaterV1.BalticTrial';mission=B/'missions/BalticHaloFullWaterV2.BalticTrial';mission.mkdir(parents=True,exist_ok=False)
oldref=json.loads((E/'halo-fullwater-reference.json').read_text())
code=(old/'init.c').read_text().replace('baltic_halo_fullwater_v1','baltic_halo_fullwater_v2').replace(oldref['terrain_sha256'],sha(source))
code=code.replace(' protected int m_WetMissing;',' protected int m_WetMissing;\n protected int m_UnflaggedPositive;')
anchor='  if ((kind == 0 && (nominal || dynamic)) || missing)'
assert anchor in code
code=code.replace(anchor,'''  // Do not silently discard positive scalar queries when both presence flags are false.
  // These require classification: the height API can also return an object surface.
  if (kind == 0 && !sea && !pond && (plane > ground + 0.03 || depth > 0.02))
  {
   m_UnflaggedPositive++;
   string qrecord = "Q;" + row + ";" + column + ";" + kind;
   qrecord = qrecord + ";" + ground + ";" + sea + ";" + pond;
   qrecord = qrecord + ";" + plane + ";" + depth;
   Emit(qrecord);
  }
''' + anchor)
assert 'Emit(summary);return;' in code
code=code.replace('Emit(summary);return;','Emit("QUERY_END;" + m_UnflaggedPositive);\n   Emit(summary);return;')
(mission/'init.c').write_text(code);shutil.copyfile(old/'risks.csv',mission/'risks.csv')
with (mission/'grid.csv').open('w',newline='') as f:
    for r in range(2048):
        for c in range(0,2048,32):
            fields=[]
            for j in range(c,c+32):fields.extend([format(float(h[r,j]),'.9g'),str(int(cls[r,j]))])
            f.write(f'{r};{c};'+';'.join(fields)+'\n')
finish(mission,oldref,'halo-r2-fullwater')
verify=(B/'verify_halo_fullwater.py').read_text().replace('halo-fullwater','halo-r2-fullwater').replace('baltic_halo_fullwater_v1','baltic_halo_fullwater_v2').replace('halo-physical-anomalies','halo-r2-physical-anomalies')
verify=verify.replace('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz',str(source).replace('\\','/'))
anchor='    rows=[];seen=set()'
assert anchor in verify
verify=verify.replace(anchor,'''    qs=[v for v in f if v[0]=='Q'];qe=[v for v in f if v[0]=='QUERY_END'];qseen=set()
    if len(qe)!=1 or len(qe[0])!=2 or int(qe[0][1])!=len(qs):errors.append('unflagged_query_count')
    for q in qs:
        if len(q)!=9:errors.append('unflagged_schema');continue
        r,c=int(q[1]),int(q[2])
        if not(0<=r<2048 and 0<=c<2048) or (r,c) in qseen:errors.append('unflagged_identity');continue
        qseen.add((r,c))
        g,lev,dep=map(float,(q[4],q[7],q[8]))
        if q[3]!='0' or q[5:7]!=['false','false'] or int(cls[r,c])!=0 or abs(g-float(h[r,c]))>.001 or not all(math.isfinite(z) for z in (g,lev,dep)) or not(lev>g+.0299 or dep>.0199):errors.append('unflagged_content')
''' + anchor)
verify=verify.replace("('missing_calibrated_point','P;0;')","('missing_calibrated_point','P;0;'),('missing_scalar_diagnostic_end','QUERY_END;')")
verify=verify.replace("dry_anomalies=len(dry),","unflagged_positive_scalar_queries=sum(s.startswith('Q;') for s in content.splitlines()),dry_anomalies=len(dry),")
verify=verify.replace("shutil.copyfile(log,E/'halo-r2-fullwater-runtime.log')","(E/'halo-r2-unflagged-scalar-queries.csv').write_text('row;col;cls;ground;sea;pond;plane;depth\\n'+'\\n'.join(s[2:] for s in content.splitlines() if s.startswith('Q;'))+'\\n')\nshutil.copyfile(log,E/'halo-r2-fullwater-runtime.log')")
(B/'verify_halo_r2_fullwater.py').write_text(verify)
# Same locations as V1, with the nine bank heights and one bed height updated.
old=B/'missions/BalticHaloConsumersV1.BalticTrial';mission=B/'missions/BalticHaloConsumersV2.BalticTrial';mission.mkdir(parents=True,exist_ok=False)
ref=json.loads((E/'halo-consumers-reference.json').read_text())
assert len(ref['points'])==120
for p in ref['points']:
    p['expected_ground_m']=float(tri_sample(h,p['x'],p['z']))
    if p.get('case')=='remaining_dry':p['role']='dry_bank'
(mission/'init.c').write_text((old/'init.c').read_text().replace('halo_consumers_v1','halo_consumers_v2').replace('halo_consumers_order_v1','halo_consumers_order_v2'))
shutil.copyfile(old/'points.csv',mission/'points.csv')
ref['deployed']={str(p):sha(p) for p in dest.glob('*.pbo')}
finish(mission,ref,'halo-r2-consumers')
verify=(B/'verify_halo_consumers.py').read_text().replace('halo-consumers','halo-r2-consumers').replace('halo_consumers_v1','halo_consumers_v2').replace('halo_consumers_order_v1','halo_consumers_order_v2')
verify=verify.replace('60 diagnostic remaining dry points','60 repaired dry-bank neighbourhood points')
(B/'verify_halo_r2_consumers.py').write_text(verify)
audit=(B/'audit_global_water_domains.py').read_text().replace('halo-fix-v2','halo-fix-v3').replace('@DayZ_Baltic_HaloFixV1','@DayZ_Baltic_HaloFixV2').replace('halo-deploy.json','halo-r2-deploy.json').replace('halo-fix-authoring.json','halo-fix-r2-authoring.json').replace("suffix='halo'","suffix='halo-r2'")
(B/'audit_global_water_domains_r2.py').write_text(audit)
