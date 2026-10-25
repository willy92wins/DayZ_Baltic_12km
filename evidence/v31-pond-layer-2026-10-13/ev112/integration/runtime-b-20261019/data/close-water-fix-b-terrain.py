from pathlib import Path
import numpy as np,json,hashlib
O=Path(__file__).parent;D=O/'water-fix-b';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=np.load(O/'fp-ev112-c/footprint.npz');newpath=D/'bury-work/fp0/footprint.npz';new=np.load(newpath)
same={k:bool(np.array_equal(old[k],new[k],equal_nan=old[k].dtype.kind=='f')) for k in old.files};assert set(old.files)==set(new.files) and all(same.values())
t=np.load(O/'terrain-ev112-c.npz');n=np.load(D/'terrain.npz');ch=t['heights']!=n['heights'];rr,cc=np.nonzero(ch)
sites={'c2':(10235,9398),'c3':(8568,10414),'c4':(10417,9426),'c5':(8227,10468),'c6':(3588,6867),'c7':(9678,2661)}
outside={name:bool(((abs(cc*6-x)>156)|(abs(12282-rr*6-z)>156)).all()) for name,(x,z) in sites.items()};assert all(outside.values())
checks=dict(footprint_arrays_identical=all(same.values()),bury_zero_changes=json.loads((D/'bury-report.json').read_text())['changed_vs_input']==0,native_delta_audit=json.loads((D/'delta-audit.json').read_text())['status']=='PASS',c2_c7_domains_unchanged=all(outside.values()),forest_g1=json.loads((D/'forest-g1-resume-execution.json').read_text())['rc']==0,forest_g4=json.loads((D/'forest-g4-execution.json').read_text())['rc']==0,phase_g9_g11_identical=all(x['all_measurements_identical'] for x in json.loads((D/'phase-gate-comparison.json').read_text())),exact_replay=json.loads((D/'replay-controls.json').read_text())['status']=='PASS')
for gate in (2,3,4,7,10):
 r=json.loads((D/f'kit/gate-g{gate}.json').read_text());checks[f'kit_g{gate}']=all(x['passed'] is True for x in r.values()) if gate in (2,3,4) else r['passed'] is True
evidence={str(p):sha(p) for p in [D/'delta-audit.json',D/'candidate.json',D/'phase-gate-comparison.json',D/'forest-origin-audit.json',D/'forest-g1.json',D/'forest-g4.log',D/'replay-controls.json',D/'bury-report.json',newpath]}
out=dict(status='PASS_AFFECTED_OFFLINE_TERRAIN_CONSUMERS' if all(checks.values()) else 'FAIL',checks=checks,terrain_sha256=sha(D/'terrain.npz'),original_terrain_sha256=sha(O/'terrain-ev112-c.npz'),footprint_arrays=same,regenerated_footprint_sha256=sha(newpath),original_footprint_sha256=sha(O/'fp-ev112-c/footprint.npz'),c2_c7_domains_unchanged=outside,evidence=evidence,limits='Not package, runtime or visual acceptance. G9/G11 raw FAIL retained with exact baseline equality; no additional phase waiver. Original pond/sea topology and c2-c7 evidence are transferred only through exact sign/domain identities. Forest record bytes unchanged; G1/G4 remeasured on final candidate.')
(D/'terrain-closure.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],checks=checks,footprint_arrays=same)));assert all(checks.values())
