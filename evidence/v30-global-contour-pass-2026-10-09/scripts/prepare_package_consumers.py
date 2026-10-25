"""Parameter-only reuse of the EV13 package parity and isolated deployment consumers."""
from pathlib import Path
import json,hashlib
B=Path(__file__).parent;B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')


def once(text,old,new):
    assert text.count(old)==1,(old,text.count(old));return text.replace(old,new)


text=(B13/'package_native_seams.py').read_text()
text=once(text,'from discover_native_turns import B,B12,W,sha',
          f"sys.path.insert(0,r'{B13.as_posix()}')\nfrom discover_native_turns import B12,W,sha\nB=Path(r'{B.as_posix()}')\nB13=Path(r'{B13.as_posix()}')")
text=once(text,"oldwater=B12/'final/water/packed/baltic_water_v30.pbo'","oldwater=B13/'package/water/packed/baltic_water_v30.pbo'")
start=text.index("compiler=B/'compile_native_world.ps1'");end=text.index("compiler.write_text(code)",start)+len('compiler.write_text(code)')
text=text[:start]+"assert str(B/'package/water/temp/baltic_water_v30') in (B/'compile_native_world.ps1').read_text()"+text[end:]
text=text.replace('NATIVE_CONTOUR_WITH_EXACT_SEAMS_STAGED','GLOBAL_CONTOUR_WITH_EXACT_SEAMS_STAGED')
text=text.replace('models=len(got)-1','packed_model_entries=sum(k.endswith(\'.p3d\') for k in got)')
(B/'package_global_seams.py').write_text(text)

text=(B13/'deploy_native_preview.py').read_text()
text=once(text,'from discover_native_turns import B,B12,sha',
          f"sys.path.insert(0,r'{B13.as_posix()}')\nfrom discover_native_turns import B12,sha\nB=Path(r'{B.as_posix()}')\nB13=Path(r'{B13.as_posix()}')")
text=once(text,"B/'candidate-feasible-verification.json'","B/'candidate-repaired-verification.json'")
text=once(text,"B/'candidate-feasible-final-coverage.json'","B/'final-coverage.json'")
text=once(text,"source['status']=='PASS_SOURCE_TERRAIN'","source['status']=='PASS_GLOBAL_SOURCE'")
text=once(text,"B12/'final/world/out/narva_trial.pbo'","B13/'package/world/out/narva_trial.pbo'")
text=text.replace('@DayZ_Baltic_NativeContourV1','@DayZ_Baltic_GlobalContourV1').replace('ISOLATED_NATIVE_CONTOUR_PREVIEW_NOT_RUNTIME_ACCEPTED','ISOLATED_GLOBAL_CONTOUR_PREVIEW_NOT_RUNTIME_ACCEPTED')
text=text.replace("runtime_status='NOT_RUN_PORT_ATTRIBUTION_UNKNOWN'","runtime_status='NOT_RUN'")
text=text.replace('261 terrain vertices and two extra seam instances; earlier preview retained.','53,853 terrain vertices and 96 extra seam instances; earlier preview retained.')
(B/'deploy_global_preview.py').write_text(text)
report=dict(status='PARAMETER_REUSE_PREPARED',scripts={name:hashlib.sha256((B/name).read_bytes()).hexdigest() for name in ('package_global_seams.py','deploy_global_preview.py')},
            source_scripts={name:hashlib.sha256((B13/name).read_bytes()).hexdigest() for name in ('package_native_seams.py','deploy_native_preview.py')})
(B/'package-consumer-reuse.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
