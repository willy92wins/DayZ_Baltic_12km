"""Freeze a local shoreline camera and read-only dynamic water measurements."""
from pathlib import Path
import json,hashlib,sys,shutil,subprocess
import numpy as np
from scipy.ndimage import distance_transform_edt
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    old='visual_native_south_v4';new='outline_water_v1';prefix='baltic_foundation_'+new
    ev=ROOT/'evidence/foundation-followup-2026-10-01/outline-water-probe-v1'
    package=ROOT/'packages/foundation-outline-water-v1';stage=package/prefix
    mission=ROOT/'missions/BalticOutlineWaterV1.BalticTrial'
    deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
    mod=Path('P:/Mods/@BalticOutlineWaterV1')
    assert not any(p.exists() for p in [ev,package,mission,deployed,mod])
    original=ROOT/'packages/foundation-visual_native_south_v4'
    source=original/('baltic_foundation_'+old)/'scripts/5_Mission/BalticRenderProbe.c'
    assert sha(source)=='f2719dc065ee37bd2d6b04194647ee14fd1e696824b9ed0dccaa9d195a7e3bca'
    data=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');h=data['candidate']
    masks=np.load(ROOT/'evidence/foundation-followup-2026-10-01/outline-water-audit-v1/diagnostic-masks.npz')
    wet=masks['water'];distance=distance_transform_edt(~wet)*6
    center=np.array([8203.,10433.]);points=[];labels=[]
    risk=np.load(ROOT/'evidence/foundation-followup-2026-10-01/outline-water-audit-v1/dry-subcell-below-diagnostic-envelope.npy')
    risk=risk[np.linalg.norm(risk[:,:2]-center,axis=1)<85]
    for p in risk[np.argsort(risk[:,2])]:
        if all(np.linalg.norm(p[:2]-q)>=5 for q in points):points.append(p[:2]);labels.append('dry_shore_source')
        if len(points)==12:break
    rr,cc=np.indices(h.shape);local=(cc*6-center[0])**2+(12282-rr*6-center[1])**2<160**2
    wider=(cc*6-center[0])**2+(12282-rr*6-center[1])**2<600**2
    for name,mask in [('dry_low_interior',local&~wet&(h<1.6)&(distance>=12)),('dry_high_control',wider&~wet&(h>3)),('wet_control',local&wet&(h<0))]:
        coords=np.column_stack(np.nonzero(mask));count=0
        for r,c in coords[::max(1,len(coords)//100)]:
            p=np.array([c*6,12282-r*6],dtype=float)
            if all(np.linalg.norm(p-q)>=12 for q in points):points.append(p);labels.append(name);count+=1
            if count==4:break
        assert count==4,(name,count)
    points=np.array(points);heights=sample(h,points[:,0]+200000,points[:,1])
    safe=np.column_stack(np.nonzero(wider&~wet&(h>2)&(distance>12)))
    safe_xy=np.c_[safe[:,1]*6,12282-safe[:,0]*6];anchor=safe_xy[np.argmin(np.linalg.norm(safe_xy-center,axis=1))]
    code=source.read_text().replace(old,new).replace(old.upper(),new.upper()).replace('client_metrics_native_south_v4','client_metrics_outline_water_v1').replace('METRICS_NATIVE_SOUTH_V4','METRICS_OUTLINE_WATER_V1')
    code=code.replace('"5540 180 250", "5800 65 522", 6000, 10','"8175 24 10390", "8203 1 10433", 2500, 0.07')
    code=code.replace('m_BalticRenderTime >= 105','m_BalticRenderTime >= 195').replace('m_BalticRenderTime >= 108','m_BalticRenderTime >= 198')
    code=code.replace('    protected bool m_BalticNativeCaptureActive;','    protected bool m_BalticNativeCaptureActive;\n    protected ref array<vector> m_OutlineWaterPoints;\n    protected float m_OutlineWaterNext;\n    protected bool m_OutlineWaterClosed;')
    literal='\n'.join('        m_OutlineWaterPoints.Insert("'+f'{x:.9g} 0 {z:.9g}'+'");' for x,z in points)
    init='''        m_OutlineWaterPoints = new array<vector>();
POINTS
        FileHandle waterFile = OpenFile("$profile:baltic_outline_water_v1.log",FileMode.WRITE);
        if (waterFile) { FPrintln(waterFile,"BALTIC_OUTLINE_WATER_V1;" + GetGame().GetWorldName()); CloseFile(waterFile); }
'''.replace('POINTS',literal)
    code=code.replace('        BalticRenderRecord("START", true);',init+'        BalticRenderRecord("START", true);')
    code=code.replace('        BalticVisualMetrics();','        BalticVisualMetrics();\n        BalticOutlineWaterRead();')
    code=code.replace('            BalticRenderRecord("COMPLETE_RESTORED_SETTLED", false);','            FileHandle done = OpenFile("$profile:baltic_outline_water_v1.log",FileMode.APPEND);\n            if (done) { FPrintln(done,"COMPLETE;"+m_BalticRenderTime); CloseFile(done); }\n            BalticRenderRecord("COMPLETE_RESTORED_SETTLED", false);')
    method='''
    // Read-only client measurements, local loaded scene. No terrain/water mutation.
    protected void BalticOutlineWaterRead()
    {
        if (m_BalticRenderTime < 20 || m_BalticRenderTime > 190 || m_BalticRenderTime < m_OutlineWaterNext) return;
        m_OutlineWaterNext = m_BalticRenderTime + 0.25;
        FileHandle f = OpenFile("$profile:baltic_outline_water_v1.log",FileMode.APPEND);
        if (!f) return;
        string sea = "SEA;" + m_BalticRenderTime + ";" + GetGame().GetTickTime() + ";" + GetGame().SurfaceGetSeaLevelMin() + ";" + GetGame().SurfaceGetSeaLevelMax();
        sea = sea + ";" + GetGame().SurfaceGetSeaLevel() + ";" + GetGame().SurfaceGetSeaWaveMax() + ";" + GetGame().SurfaceGetSeaWaveCurrent();
        FPrintln(f,sea);
        for (int i=0; i<m_OutlineWaterPoints.Count(); i++)
        {
            vector p=m_OutlineWaterPoints[i];
            float ground=GetGame().SurfaceY(p[0],p[2]); p[1]=ground+10;
            string row="S;"+m_BalticRenderTime+";"+i+";"+p.ToString()+";"+ground;
            row=row+";"+GetGame().GetWaterSurfaceHeightNoFakeWave(p)+";"+GetGame().GetWaterSurfaceHeightWithFakeWave(p);
            row=row+";"+GetGame().GetWaterDepth(p)+";"+GetGame().SurfaceIsSea(p[0],p[2])+";"+GetGame().SurfaceIsPond(p[0],p[2]);
            FPrintln(f,row);
        }
        CloseFile(f);
    }
'''
    code=code.replace('    protected void BalticVisualMetrics()',method+'\n    protected void BalticVisualMetrics()')
    (stage/'scripts/5_Mission').mkdir(parents=True);ev.mkdir(parents=True);mission.mkdir(parents=True)
    script=stage/'scripts/5_Mission/BalticRenderProbe.c';script.write_text(code,encoding='utf-8')
    config=(original/'config.cpp').read_text().replace('baltic_foundation_'+old,prefix);(package/'config.cpp').write_text(config)
    init=(ROOT/'missions/BalticFoundationVisualNativeSouthV4.BalticTrial/init.c').read_text().replace('5540 0 250',f'{anchor[0]} 0 {anchor[1]}')
    (mission/'init.c').write_text(init)
    lint=subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(stage)],capture_output=True,text=True)
    (ev/'lint.json').write_text(lint.stdout);result=json.loads(lint.stdout);assert lint.returncode==0 and result['status']=='PASS' and result['info']['files_scanned']==1
    addons=package/'Addons';addons.mkdir();tools=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
    for i,args in enumerate([[tools/'CfgConvert/CfgConvert.exe','-bin','-dst',stage/'config.bin',package/'config.cpp'],[tools/'PboUtils/FileBank.exe','-property','prefix='+prefix,'-property','product=dayz ugc','-dst',addons,stage]]):
        r=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(package/f'command-{i}.log').write_bytes(r.stdout);assert r.returncode==0
    pbo=addons/(prefix+'.pbo');_,props,entries=read_pbo(pbo);assert props['prefix']==prefix and entries=={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    (mod/'Addons').mkdir(parents=True);shutil.copy2(pbo,mod/'Addons'/pbo.name);shutil.copytree(mission,deployed)
    ref=dict(status='FROZEN_DIAGNOSTIC_NOT_ACCEPTANCE',terrain_npz_sha256=sha(ROOT/'tests/regional_foundation_combined_v10/reference.npz'),world_pbo_sha256='d1008dd6c882193706f06c5e7b8495ee1a357f5819a8574118784f7e90f18577',probe_pbo_sha256=sha(pbo),script_sha256=sha(script),mission_sha256=sha(mission/'init.c'),points=[dict(index=i,xz=p.tolist(),kind=k,ground_m=float(y)) for i,(p,k,y) in enumerate(zip(points,labels,heights))],anchor_xz=anchor.tolist(),camera=[8175,24,10390],target=[8203,1,10433],nearplane=.07,view_distance=2500,measurement_window_s=[20,190],finish_s=198,deployed_mod=str(mod),deployed_mission=str(deployed),limits=['Read-only local client queries. Ocean/fake-wave time samples do not establish the global maximum.','Surface queries ignore terrain; compare against ground, sea/pond classification and visible scene.'])
    (ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n');print(json.dumps(dict(status=ref['status'],samples=len(points),anchor=anchor.tolist(),probe=sha(pbo))))

if __name__=='__main__':main()
