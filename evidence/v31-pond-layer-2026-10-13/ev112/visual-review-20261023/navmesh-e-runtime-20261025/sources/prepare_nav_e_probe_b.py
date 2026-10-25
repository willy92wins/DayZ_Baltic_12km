from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).parent
src=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticGuardedENavV9.BalticTrial')
dst=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticGuardedENavV9B.BalticTrial');dst.mkdir(exist_ok=False)
out=R/'navmesh-guarded-e-v9-probe-b';out.mkdir(exist_ok=False)
s=(src/'init.c').read_text(encoding='utf-8')
s=s.replace('$profile:baltic_ev112_nav_v9.log','$profile:baltic_ev112_nav_v9_b.log')
s=s.replace('        AIWorld ai=', '        FileHandle diagnostic=OpenFile("$profile:baltic_ev112_nav_v9_diag.log",FileMode.WRITE);\n        if (!diagnostic) { CloseFile(input);CloseFile(output);return; }\n        AIWorld ai=')
old='''                vector p=path[i];
                vector groundSample=Vector(p[0],GetGame().SurfaceY(p[0],p[2]),p[2]);
                vector roadSample=Vector(p[0],GetGame().SurfaceRoadY(p[0],p[2]),p[2]);
                FPrintln(output,"P;"+fields[0]+";"+i+";"+p.ToString()+";"+groundSample.ToString()+";"+roadSample.ToString());'''
new='''                vector p=path[i];
                vector legacyGround=Vector(p[0],GetGame().SurfaceY(p[0],p[2]),p[2]);
                vector legacyRoad=Vector(p[0],GetGame().SurfaceRoadY(p[0],p[2]),p[2]);
                float legacyX=legacyRoad[0];
                float legacyZ=legacyRoad[2];
                float pointX=p[0];
                float pointZ=p[2];
                float groundY=GetGame().SurfaceY(pointX,pointZ);
                float roadY=GetGame().SurfaceRoadY(pointX,pointZ);
                vector groundSample=Vector(pointX,groundY,pointZ);
                vector roadSample=Vector(pointX,roadY,pointZ);
                string pointText=p.ToString();
                string groundText=groundSample.ToString();
                string roadText=roadSample.ToString();
                string legacyText=legacyRoad.ToString();
                string diagnosticRow="D;"+fields[0]+";"+i+";"+pointX+";"+pointZ+";"+legacyX+";"+legacyZ;
                diagnosticRow=diagnosticRow+";"+legacyText+";"+roadText;
                FPrintln(diagnostic,diagnosticRow);
                FPrintln(output,"P;"+fields[0]+";"+i+";"+pointText+";"+groundText+";"+roadText);'''
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('        CloseFile(input);CloseFile(output);','        CloseFile(input);CloseFile(output);CloseFile(diagnostic);')
(dst/'init.c').write_bytes(s.encode('utf-8'));shutil.copyfile(src/'queries.csv',dst/'queries.csv')
shutil.copyfile(R/'navmesh-guarded-e-v9-probe/reference.json',out/'reference.json')
launch=json.loads((R/'navmesh-guarded-e-v9-probe/launch-server.json').read_text());launch['mission']=str(dst)
(out/'launch-server.json').write_text(json.dumps(launch,indent=2)+'\n',encoding='utf-8')
oldreceipt=json.loads((R/'navmesh-guarded-e-v9-probe/deployment.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(status='DIAGNOSTIC_PROBE_PREPARED_NOT_RUN',deployed=oldreceipt['deployed'],mission=str(dst),inputs={str(p):sha(p) for p in (dst/'init.c',dst/'queries.csv',out/'reference.json',Path(__file__))},limits=['Same navmesh, query endpoints, heights and acceptance thresholds. Diagnostic contrasts nested constructor with scalar temporaries; no consumer tolerance changes.'])
for p,digest in receipt['deployed'].items():assert sha(Path(p))==digest
receipt['inputs'].update(receipt['deployed'])
(out/'deployment.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(mission=str(dst),source_sha256=sha(dst/'init.c'),queries_sha256=sha(dst/'queries.csv')),indent=2))
