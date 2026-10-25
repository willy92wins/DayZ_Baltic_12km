"""Copy the verified P pilot into a fresh disposable mod and mission; no launch."""
import argparse,hashlib,json,shutil
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build');a=ap.parse_args();B=Path(a.build)
    pkg=B/'package-visual-probe-20261024-a';pilot=B/'visual-pilot-20261024-p';probe=B/'probe-visual-20261024-b'
    mod=Path('P:/Mods/@DayZ_Baltic_EV112_VisualProbeP')
    mission=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticVisualProbeV1.BalticTrial')
    assert not mod.exists() and not mission.exists(),'fresh destinations required'
    pr=json.loads((pkg/'verification.json').read_text());assert pr['status']=='OFFLINE_PACKAGE_PASS'
    br=json.loads((pilot/'binary-review.json').read_text());assert br['status']=='BINARY_PASS'
    sources={pkg/'Addons/narva_trial.pbo':pr['pbo_sha256'],pilot/'packed/baltic_stream_pilot.pbo':br['pbo_sha256'],
             Path('P:/Mods/@DayZ_Baltic_EV112_RuntimeMarginsV2/Addons/baltic_water_v30.pbo'):'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}
    for path,digest in sources.items():assert sha(path)==digest,str(path)
    points=json.loads((probe/'points.json').read_text());assert not points['diagnostics']
    srcmission=probe/mission.name
    for name in ('init.c','points.csv'):assert sha(srcmission/name)==points['inputs'][str(srcmission/name)]
    (mod/'Addons').mkdir(parents=True);mission.mkdir(parents=True)
    checks=[]
    for src,digest in sources.items():
        dest=mod/'Addons'/src.name;shutil.copy2(src,dest);actual=sha(dest);assert actual==digest
        checks.append(dict(path=str(dest),sha256=actual))
    for name in ('init.c','points.csv'):
        src=srcmission/name;dest=mission/name;shutil.copy2(src,dest);assert sha(src)==sha(dest)
        checks.append(dict(path=str(dest),sha256=sha(dest)))
    result=dict(status='DEPLOYED_ISOLATED_PROBE',mod=str(mod),mission=str(mission),checks=checks,points=len(points['points']),production_replaced=False,launched=False)
    (probe/'deploy-receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
