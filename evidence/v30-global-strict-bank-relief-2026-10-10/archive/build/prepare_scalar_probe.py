"""Prepare one diagnostic time series, no geometry/model edits and no new acceptance claim."""
from pathlib import Path
import csv,json,hashlib,subprocess,sys
import numpy as np
R=Path(__file__).parent;D=R/'scalar-probe';D.mkdir(exist_ok=False)
B=R.parents[1]/'v30-mixed-bank-incremental-fixed-20261010'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(R/'candidate/terrain.npz')=='8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b'
assert sha(B/'candidate/terrain.npz')=='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
H=np.load(R/'candidate/terrain.npz')['heights'];HB=np.load(B/'candidate/terrain.npz')['heights'];P=np.load(R/'candidate/plane.npy')
lev=np.full(H.shape,.85);v=np.where(np.isfinite(P),P,-np.inf)
for dr,dc in ((0,0),(0,1),(1,0),(1,1)):np.maximum(lev[dr:dr+2047,dc:dc+2047],v,out=lev[dr:dr+2047,dc:dc+2047])
coords=[tuple(x) for x in np.argwhere((H!=HB)&(H>lev)&(H-lev<.25))]
assert len(coords)==162
points=[{'id':i,'row':int(r),'col':int(c),'x':int(c*6),'z':int(12282-r*6),'H':float(H[r,c]),'B':float(HB[r,c]),'P_max':float(lev[r,c]),'role':'all_changed_clearance_under_25cm'} for i,(r,c) in enumerate(coords)]
# Predetermined positive/negative controls share the same diagnostic classifier.
for r,c in coords[:8]:
 for dr,dc in ((0,1),(1,0)):
  rr,cc=r+dr,c+dc
  if (rr,cc) in coords:continue
  points.append({'id':len(points),'row':int(rr),'col':int(cc),'x':int(cc*6),'z':int(12282-rr*6),'H':float(H[rr,cc]),'B':float(HB[rr,cc]),'P_max':float(lev[rr,cc]),'role':'adjacent_control'})
mission_name='BalticScalarMarginV1.BalticTrial';local=D/mission_name
server=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission_name
assert not local.exists() and not server.exists();local.mkdir()
weather=(R/'missions/BalticStrictBankFullWaterV1.BalticTrial/init.c').read_text().split('class BalticStrictBankFullWaterMission')[0]
code=weather+'''
class BalticScalarMarginMission : MissionServer
{
 protected ref array<vector> m_Points = new array<vector>;
 protected ref array<float> m_B = new array<float>;
 protected FileHandle m_Log;
 protected int m_Next;
 protected int m_Sample;
 protected bool m_Done;
 override void OnInit()
 {
  super.OnInit();
  if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") { m_Done=true;return; }
  m_Log=OpenFile("$profile:baltic_scalar_margin_v1.log",FileMode.WRITE);
  if (!m_Log) { m_Done=true;return; }
  FPrintln(m_Log,"BALTIC_SCALAR_MARGIN_V1;8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b");
'''
for p in points:
 code+=f'  m_Points.Insert(Vector({p["x"]}, {p["H"]:.9g}, {p["z"]})); m_B.Insert({p["B"]:.9g});\n'
code+='''
  m_Next=GetGame().GetTime()+5000;
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  GetGame().GetWeather().SetWindSpeed(20);
  if (m_Done || GetGame().GetTime()<m_Next) return;
  m_Next=GetGame().GetTime()+250;
  int now=GetGame().GetTime();
  FPrintln(m_Log,"T;"+m_Sample+";"+now+";"+GetGame().GetWeather().GetWindSpeed()+";"+GetGame().SurfaceGetSeaLevel()+";"+GetGame().SurfaceGetSeaWaveMax());
  for (int i=0;i<m_Points.Count();i++)
  {
   vector point=m_Points[i];float ground=GetGame().SurfaceY(point[0],point[2]);
   vector above=Vector(point[0],ground+100,point[2]);
   bool sea=GetGame().SurfaceIsSea(point[0],point[2]);bool pond=GetGame().SurfaceIsPond(point[0],point[2]);
   float nominal=GetGame().GetWaterSurfaceHeightNoFakeWave(above);
   float fake=GetGame().GetWaterSurfaceHeightWithFakeWave(above);
   float depthH=GetGame().GetWaterDepth(Vector(point[0],ground+0.01,point[2]));
   float depthB=GetGame().GetWaterDepth(Vector(point[0],m_B[i]+0.01,point[2]));
   FPrintln(m_Log,"P;"+m_Sample+";"+i+";"+ground+";"+sea+";"+pond+";"+nominal+";"+fake+";"+depthH+";"+depthB);
  }
  m_Sample++;
  if (m_Sample==241)
  {
   FPrintln(m_Log,"END;"+m_Sample+";"+m_Points.Count());CloseFile(m_Log);m_Log=null;m_Done=true;
  }
 }
}
Mission CreateCustomMission(string path) { return new BalticScalarMarginMission(); }
'''
(local/'init.c').write_text(code,encoding='utf-8')
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
lint=subprocess.run([sys.executable,str(validator),str(local)],capture_output=True,text=True)
obj=json.loads(lint.stdout);assert lint.returncode==0 and obj['info']['files_scanned']==1 and not obj['errors'],obj
(D/'lint.json').write_text(json.dumps(obj,indent=2)+'\n')
import shutil
shutil.copytree(local,server)
assert sha(local/'init.c')==sha(server/'init.c')
deploy=json.loads((R/'deploy.json').read_text())
for name,digest in deploy['files'].items():assert sha(Path(deploy['mod'])/'Addons'/name)==digest
ref={'status':'PREPARED_DIAGNOSTIC_NOT_RUN','mission':str(server),'mod':deploy['mod'],'pbo':deploy['files'],
 'files':{'init.c':sha(local/'init.c')},'points':points,'samples':241,'interval_ms':250,'wind_m_s':20,
 'scope':'All 162 changed vertices with nominal clearance under25cm plus predetermined adjacent controls.',
 'limits':['Query at old B height on current H is an input-height discriminator, not a second B world run.',
 '60s observed envelope at wind20 is not an all-weather proof; scalar APIs do not prove rendered pixels.',
 'No terrain/model changes or new acceptance threshold from this diagnostic.']}
(D/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':ref['status'],'points':len(points),'mission':str(server),'script_sha256':ref['files']['init.c']}))
