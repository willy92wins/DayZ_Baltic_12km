from pathlib import Path
import json,hashlib,shutil,subprocess,sys
import numpy as np
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),str(R/'v30-native-terminal-finish-20261009')]
from v30_common import tri_sample
from audit_candidate_coverage import wet_shape
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
oldrefpath=W/'evidence/v30-native-hinge-finish-2026-10-09/hinge-smooth-fullwater-reference.json';ref=json.loads(oldrefpath.read_text());old=Path(ref['mission'])
assert all(sha(old/n)==s for n,s in ref['files'].items())
t=np.load(B/'candidate/terrain.npz');h=t['heights'];cls=t['cls'];p=np.load(B/'candidate/plane.npy');original=np.load(R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy');terrain_hash=sha(B/'candidate/terrain.npz')
name='BalticIsolatedBasinsFullWaterV1.BalticTrial';mission=B/'missions'/name;mission.mkdir(parents=True,exist_ok=False)
code=(old/'init.c').read_text().replace('BalticHingeSmoothFullWaterMission','BalticIsolatedBasinsFullWaterMission').replace('baltic_hinge_smooth_fullwater_v1','baltic_isolated_basins_fullwater_v1').replace('BALTIC_HINGE_SMOOTH_FULLWATER_V1','BALTIC_ISOLATED_BASINS_FULLWATER_V1').replace(ref['terrain_sha256'],terrain_hash)
main=(old.parent/'BalticRenderLayerProbeV1.BalticTrial/init.c').read_text().split('class BalticRenderLayerProbeV1Mission')[0]
code=code.replace('void main() {}',main)
needle=' protected FileHandle m_Grid;';insert=''' protected int m_WeatherTick;
 override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
 {
  pos="2682 0 6850";pos[1]=GetGame().SurfaceY(pos[0],pos[2])+0.2;
  return super.CreateCharacter(identity,pos,ctx,characterName);
 }
''';assert code.count(needle)==1;code=code.replace(needle,insert+needle)
needle='  super.OnUpdate(timeslice);';insert='''
  // Native declaration weather.c:251; force each update, log the actual value.
  GetGame().GetWeather().SetWindSpeed(20);
  if (GetGame().GetTime()>=m_WeatherTick)
  {
   m_WeatherTick=GetGame().GetTime()+250;
   Emit("W;"+GetGame().GetTime()+";"+GetGame().GetWeather().GetWindSpeed()+";"+GetGame().SurfaceGetSeaLevel());
  }
''';assert code.count(needle)==1;code=code.replace(needle,needle+insert);(mission/'init.c').write_text(code)
with (mission/'grid.csv').open('w',newline='') as stream:
    for r in range(2048):
        for c in range(0,2048,32):
            fields=[]
            for j in range(c,c+32):fields.extend([format(float(h[r,j]),'.9g'),str(int(cls[r,j]))])
            stream.write(f'{r};{c};'+';'.join(fields)+'\n')
points=[]
for previous in ref['points']:points.append(previous|dict(expected_ground=float(tri_sample(h,previous['x'],previous['z']))))
omitted=[]
for r,c in zip(*np.nonzero(np.isfinite(p)&(p!=original))):
    poly=wet_shape(r,c,h,np.repeat(p[r,c],4))
    if poly.is_empty:omitted.append([int(r),int(c),'dry_support']);continue
    at=poly.representative_point();x,z=at.x,at.y;ground=float(tri_sample(h,x,z));depth=float(p[r,c]-ground)
    if depth<.03:omitted.append([int(r),int(c),'sub3cm_sliver']);continue
    points.append(dict(x=x,z=z,expected_ground=ground,expected_water=float(p[r,c]),cls=int(cls[r,c]),role='translated_cell',row=int(r),col=int(c)))
(mission/'risks.csv').write_text(''.join(f"{i};{v['x']:.8f};{v['z']:.8f};{v['expected_ground']:.9g};{v['cls']}\n" for i,v in enumerate(points)))
validator='C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py';done=subprocess.run([sys.executable,validator,str(mission)],capture_output=True,text=True);lint=json.loads(done.stdout);(B/'probe-lint.json').write_text(done.stdout);assert done.returncode==0 and lint['info']['files_scanned']==1 and not lint['errors']
destination=old.parent/name;shutil.copytree(mission,destination)
deploy=json.loads((B/'deploy.json').read_text());mods=Path(deploy['destination'])/'Addons';assert all(sha(mods/n)==s for n,s in deploy['files'].items())
newref=ref|dict(mission=str(destination),terrain_sha256=terrain_hash,points=points,omitted_cells=omitted,files={p.name:sha(p) for p in mission.iterdir()},pbo=deploy['files'],deployed={str(mods/n):s for n,s in deploy['files'].items()},source_runtime_reference_sha256=sha(oldrefpath))
(B/'basins-fullwater-reference.json').write_text(json.dumps(newref,indent=2)+'\n')
verifier=(R/'v30-native-hinge-finish-20261009/verify_hinge_smooth_fullwater.py').read_text()
verifier=verifier.replace("E=W/'evidence/v30-native-hinge-finish-2026-10-09'","E=Path(__file__).parent")
verifier=verifier.replace('hinge-smooth-fullwater','basins-fullwater').replace('hinge-smooth-physical','basins-physical').replace('hinge-smooth-unflagged','basins-unflagged').replace('baltic_hinge_smooth_fullwater_v1','baltic_isolated_basins_fullwater_v1').replace('BALTIC_HINGE_SMOOTH_FULLWATER_V1','BALTIC_ISOLATED_BASINS_FULLWATER_V1')
verifier=verifier.replace("Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')",f"Path('{(B/'candidate/terrain.npz').as_posix()}')")
verifier=verifier.replace("['4194304','0','7']","['4194304','0',str(len(ref['points']))]").replace("len(p)!=7","len(p)!=len(ref['points'])").replace("range(7)","range(len(ref['points']))")
needle="        if not math.isfinite(float(v[2])) or abs(float(v[2])-q['expected_ground'])>.001:errors.append('calibrated_height')";assert needle in verifier
verifier=verifier.replace(needle,needle+"\n        if 'expected_water' in q and (v[4]!='true' or abs(float(v[5])-q['expected_water'])>.001):errors.append('translated_water_plane')")
verifier=verifier.replace("r=judge(content);lines=content.splitlines();negative={}","r=judge(content);lines=content.splitlines();negative={}\nwet_index=next(i for i,q in enumerate(ref['points']) if 'expected_water' in q)\noriginal=next(s for s in lines if s.startswith(f'P;{wet_index};'));mutant=original.split(';');mutant[5]=str(float(mutant[5])+.1)\nnegative['wrong_translated_water_plane']=not judge(content.replace(original,';'.join(mutant),1))['pass_gate']")
verifier=verifier.replace("out=dict(status=", "out=dict(translated_water_probes=sum('expected_water' in q for q in ref['points']),status=")
(B/'verify_native.py').write_text(verifier)
print(json.dumps(dict(status='PREPARED_NOT_RUN',mission=str(destination),points=len(points),water_probes=sum('expected_water' in q for q in points),omitted_cells=len(omitted),files=newref['files']),indent=2))
