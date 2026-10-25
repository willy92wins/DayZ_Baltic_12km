"""Deploy a new isolated technical candidate and immutable server mission."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
proof=R/'package-combined/verification.json';rep=json.loads(proof.read_text());assert rep['status']=='OBJECTS_AND_PAYLOAD_VERIFIED_BOUNDARY_PENDING'
mod=Path('P:/Mods/@DayZ_Baltic_EV112_ShapeRepairT');mission=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticShapeRepairT.BalticTrial');out=R/'runtime-combined'
assert not any(p.exists() for p in (mod,mission,out))
sources={R/'package-combined/Addons/narva_trial.pbo':rep['pbo_sha256'],R/'combined-pilot/packed/baltic_stream_pilot.pbo':'988354f4488c0a31c6ab57b3768b24447879aa815e0afdb056864dac2435423f',Path('P:/Mods/@DayZ_Baltic_EV112_VisualReviewR/Addons/baltic_water_v30.pbo'):'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}
for p,h in sources.items():assert sha(p)==h
points=R/'probe-combined/points.json';doc=json.loads(points.read_text());assert len(doc['points'])==2823
for p,h in doc['inputs'].items():assert sha(p)==h
(mod/'Addons').mkdir(parents=True);out.mkdir();mission.mkdir();checks=[]
for p,h in sources.items():
    dest=mod/'Addons'/p.name;shutil.copy2(p,dest);assert sha(dest)==h;checks.append(dict(path=str(dest),sha256=h,bytes=dest.stat().st_size))
for name in ('init.c','points.csv'):
    source=R/'probe-combined/BalticVisualProbeV1.BalticTrial'/name;shutil.copy2(source,mission/name);assert sha(mission/name)==sha(source)
shutil.copy2(points,out/'points.json')
launch=dict(project='DayZ_MCP',mode='server',mission=str(mission),extra_mods=[mod.name],base_mods=[],no_base_mods=True,no_file_patching=True,build=False,takeover=False,wait_for_box_s=0)
(out/'launch-server.json').write_text(json.dumps(launch,indent=2))
receipt=dict(status='DEPLOYED_ISOLATED_PENDING_RUNTIME',checks=checks,mission=str(mission),mission_files={n:sha(mission/n) for n in ('init.c','points.csv')},points=2823,points_sha256=sha(out/'points.json'),package_report_sha256=sha(proof),terrain_sha256=doc['inputs'][str(R/'combined-merged/terrain-buried.npz')],production_replaced=False,previous_mod_preserved=True,server_probe='NOT_RUN',navigation='UNCHANGED_NOT_ACCEPTED')
(out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
