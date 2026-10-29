"""Single fresh B3G2 pair, pinned sources and isolated deployment folders.

No launcher call. Approval SHA is supplied by the independent integration step.
Only new directories are created; no shared addon is overwritten.
"""
from pathlib import Path
import argparse,json,shutil,time
import contact_pair_b3g_binding_ev112 as b
import contact_b3g2_native_ev112 as current
W=Path(__file__).resolve().parents[2];R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
SOURCE=R/'b3g-source-discovery-20261029'
ROOT=R/'contact-b3g2-native-20261029'
MISSION=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticContactB3G2.BalticTrial')
PROOF=R/'prism-b3f-package-20261028/consumer/report.json'
PROOF_SHA='e62ed4709f9e5815740479aa60f16a2f4d4e003e9a070b4dd4886d0d95101a95'
MANIFEST=R/'prism-b3f-package-20261028/manifest.json'
MANIFEST_SHA='d34b3ecd5c4cccc239a3b86bbfd763e181dc22731b0b7eb86a34375df84572df'

def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def prepare(approval,approval_sha):
    started=time.monotonic();b.require(b.sha(approval)==approval_sha,'approval_pin');a=b.read(approval)
    b.require(a['status']=='REVIEWED_B3G2_COORDINATOR_READY','review_required');b.verify(a['inputs'])
    required=[Path(__file__),W/'tools/quality/contact_pair_b3g_ev112.py',W/'tools/quality/contact_pair_b3g_binding_ev112.py',W/'missions/BalticContactB3G2.BalticTrial/init.c',SOURCE/'files.json']
    required += [W/'tools/quality'/n for n in ('capture_contact_b3g2_identity.ps1','observe_contact_b3g2_ev112.py','contact_b3g2_native_ev112.py','contact_pair_b3g1_receipts_ev112.py','run_contact_b3g2.js','contact_b3g2_tools.js')]
    required += [W/'evidence/collision-native-b2-20261028/native/deployment.json', W/'tools/quality/shared_log_b3g2_ev112.py', W/'tools/quality/contact_b3g1_native_ev112.py', R/'b3g2-observer-inputs-20261029/golden.json']
    b.require(all(str(p) in a['inputs'] for p in required),'approval_scope')
    b.verify({str(PROOF):PROOF_SHA,str(MANIFEST):MANIFEST_SHA})
    rows=b.read(SOURCE/'files.json');pins={r['path']:r['sha256'] for r in rows};b.verify(pins)
    # R0's earlier B2 consumer hash is not an executable dependency; current row
    # digest is explicitly bound by the published replay and the new approval.
    d=b.read(W/'evidence/collision-native-b2-20261028/native/deployment.json')
    points=b.contract(b.read(d['frozen']),b.read(d['original']));csv=b.wire.csv_for(points)
    b.require(csv== (SOURCE/'points.csv').read_text(encoding='ascii'),'fixed_csv')
    mods={arm:Path('P:/Mods')/('@DayZ_Baltic_B3G2_'+arm+'_20261029') for arm in ('control','candidate')}
    b.require(len(d['packages'])==4 and {Path(p).name.lower() for p in d['packages']}==b.OWN,'source_mod_names')
    b.require(len([p for p in d['static_packages'] if Path(p).name.lower() in b.VANILLA])==5,'source_vanilla_count')
    bridge=next(Path(p) for p in d['packages'] if Path(p).name.lower()=='dayz_mcp.pbo')
    b.require(list(bridge.parent.glob('*.pbo'))==[bridge],'unlisted_bridge_pbo')
    b.require(not ROOT.exists() and not MISSION.exists() and all(not p.exists() for p in mods.values()),'fresh_destinations')
    ROOT.mkdir();MISSION.mkdir();shutil.copyfile(W/'missions/BalticContactB3G2.BalticTrial/init.c',MISSION/'init.c')
    (MISSION/'points.csv').write_text(csv,encoding='ascii',newline='')
    engine=d['engine'];scripts=str(Path(engine).parent/'dta/scripts.pbo');vanilla={p:h for p,h in d['static_packages'].items() if Path(p).name.lower() in b.VANILLA}
    for arm,mod in mods.items():
        output=ROOT/arm;output.mkdir();(mod/'Addons').mkdir(parents=True);packages={}
        for old,h in d['packages'].items():
            name=Path(old).name
            if name.lower()=='dayz_mcp.pbo':packages[old]=h;continue
            src=Path(old)
            if name=='baltic_stream_pilot.pbo':src=R/('dry-road-final-package-20261028' if arm=='control' else 'prism-b3f-package-20261028')/'Addons'/name;h=b.CONTROL if arm=='control' else b.CANDIDATE
            b.require(b.sha(src)==h,'source_changed');dest=mod/'Addons'/name;shutil.copyfile(src,dest);b.require(b.sha(dest)==h,'copy_changed');packages[str(dest)]=h
        input_pins={**pins,**a['inputs'],**packages,**vanilla,str(approval):approval_sha,str(PROOF):PROOF_SHA,str(MANIFEST):MANIFEST_SHA}
        for p in (MISSION/'init.c',MISSION/'points.csv'):input_pins[str(p)]=b.sha(p)
        deployed=dict(golden=str(R/'b3g2-observer-inputs-20261029/golden.json'),arm=arm,mission=str(MISSION),mod=mod.name,producer=str(MISSION/'init.c'),csv=str(MISSION/'points.csv'),
                      original=d['original'],frozen=d['frozen'],wrp=d['wrp'],engine=engine,scripts=scripts,scripts_sha256=b.sha(scripts),
                      packages=packages,vanilla=vanilla,inputs=input_pins,status='PREPARED_NOT_ADMITTED')
        b.verify(input_pins);dump(output/'deployment.json',deployed)
        dump(output/'accepted.json',dict(status='B3G_NATIVE_READY',inputs={str(output/'deployment.json'):b.sha(output/'deployment.json')}))
        seal=b.sha(output/'accepted.json');b.gate(output,seal)
        dump(output/'preparation.json',dict(status='PRE_FIFO_GATE_PASS',accepted_sha256=seal,arm=arm))
    b.require(time.monotonic()-started<120,'preparation_budget')
    dump(ROOT/'prepared.json',dict(status='PREPARED_PAIR_NOT_ADMITTED',seconds=time.monotonic()-started,order=['control','candidate']))
    return b.read(ROOT/'prepared.json')

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','gate','consume','compare']);p.add_argument('--approval',type=Path);p.add_argument('--sha');p.add_argument('--arm',choices=['control','candidate']);a=p.parse_args()
    if a.action=='prepare':result=prepare(a.approval,a.sha)
    elif a.action in ('gate','consume'):
        b.require(a.arm is not None and a.sha is not None,'arm_and_seal_required');root=ROOT/a.arm
        result=b.gate(root,a.sha) if a.action=='gate' else current.consume_bound(root,a.sha)
        if a.action=='consume':dump(root/'result.json',result)
    else:
        b.require(not (ROOT/'comparison.json').exists(),'comparison_consumed');data=[];deploy=[]
        for arm in ('control','candidate'):
            root=ROOT/arm;seal=b.read(root/'preparation.json')['accepted_sha256'];d=b.files(root,seal);r=b.read(root/'result.json')
            b.require(r['deployment_sha256']==b.sha(root/'deployment.json'),'result_deployment');b.verify(r['inputs']);data.append(r);deploy.append(d)
        result=b.pair_bound(*data,*deploy);dump(ROOT/'comparison.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='details'}))

if __name__=='__main__':main()
