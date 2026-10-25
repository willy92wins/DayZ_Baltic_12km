"""Adapt the established exact-centre seam author/consumer to two newly exposed gaps."""
from pathlib import Path
import json,hashlib
B=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
OLD=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
report=json.loads((B/'candidate-feasible-coverage.json').read_text())
assert report['status']=='FAIL_GLOBAL_COMPILED_COVERAGE' and len(report['uncovered_cells'])==2
def replace_once(text,old,new):
    assert text.count(old)==1,(old,text.count(old));return text.replace(old,new)
receipts=[]
for name in ('author_exact_seams.py','verify_exact_seams.py'):
    text=(OLD/name).read_text()
    text=replace_once(text,"B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')",f"B=Path('{B.as_posix()}')\nBASE=Path('{OLD.as_posix()}')")
    text=replace_once(text,'sys.path.insert(0,str(B))','sys.path.insert(0,str(BASE))')
    text=text.replace("B/'preserved-field.npy'","BASE/'preserved-field.npy'")
    text=replace_once(text,"np.load('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/measured-bank-bed-r2/terrain.npz')","np.load(B/'candidate-feasible/terrain.npz')")
    if name.startswith('author'):
        text=replace_once(text,"B/'compile/source/baltic_water_v30'","BASE/'compile/source/baltic_water_v30'")
        text=text.replace("B/'global-coverage.json'","B/'candidate-feasible-coverage.json'")
        text=replace_once(text,"wp=B/'world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';assert sha(wp)==report['world_source_sha256']",
                          "wp=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';stage=json.loads((B/'stage.json').read_text());assert sha(wp)==stage['world_source_sha256'] and stage['old_world_source_sha256']==report['world_source_sha256']")
        text=replace_once(text,"name=f'seamfix_{r:04}_{c:04}.p3d'","name=f'nativeseam_{r:04}_{c:04}.p3d'")
    else:text=replace_once(text,"B/'compile-r2/out/baltic_water_v30.pbo'","BASE/'compile-r2/out/baltic_water_v30.pbo'")
    target=B/name;assert not target.exists();target.write_text(text)
    receipts.append(dict(source=str(OLD/name),source_sha256=hashlib.sha256((OLD/name).read_bytes()).hexdigest(),target=str(target),target_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
text=(OLD/'compile_exact_seams.ps1').read_text()
text=replace_once(text,"$buildRoot='E:\\DayZ-Baltic-Build\\v30-frozen-water-stitch-20261009'","$buildRoot='E:\\DayZ-Baltic-Build\\v30-native-turn-optimizer-20261009'")
(B/'compile_exact_seams.ps1').write_text(text)
(B/'seam-reuse.json').write_text(json.dumps(dict(status='SAME_SEAM_GEOMETRY_CONSUMER_NEW_TERRAIN_AND_OUTPUT',copies=receipts),indent=2)+'\n')
print(json.dumps(dict(copies=len(receipts),gap_cells=[(r['row'],r['col']) for r in report['uncovered_cells']])))
