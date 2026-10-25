from pathlib import Path
import hashlib,json
R=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
A=R/'navmesh-guarded-e-v9-probe';B=R/'navmesh-guarded-e-v9-probe-b'
for folder in (A,B):
    receipt=json.loads((folder/'deployment.json').read_text())
    for path,digest in receipt['inputs'].items():assert sha(Path(path))==digest,('input changed',path)
    host=json.loads((folder/'host-identity.json').read_text());mcp=json.loads((folder/'mcp-identity.json').read_text())
    assert host['pid']==mcp['process']['pid'] and host['run_id']==mcp['run_id'] and mcp['server_binding']=='BOUND' and mcp['client_started'] is False
    for path,digest in host['package_hashes'].items():assert sha(Path(path))==digest
    assert sha(Path(host['executable']))==host['executable_file_sha256']
    src=Path(receipt['mission'])/'init.c';(folder/'mission-source.c').write_bytes(src.read_bytes())
    (folder/'post-run-bindings.json').write_text(json.dumps(dict(status='INPUTS_AND_RUN_IDENTITY_VERIFIED',inputs_unchanged=True,actual_executable_file_sha256=host['executable_file_sha256'],host_identity_sha256=sha(folder/'host-identity.json'),mcp_identity_sha256=sha(folder/'mcp-identity.json'),log_sha256=sha(folder/'runtime.log'),mission_source_sha256=sha(src)),indent=2)+'\n',encoding='utf-8')
def points(path):
    return {(f[1],int(f[2])):f[3:] for line in path.read_text().splitlines() if (f:=line.split(';'))[0]=='P'}
def vector(text):return [float(x) for x in text.strip('<>').split(',')]
a=points(A/'runtime.log');b=points(B/'runtime.log');assert set(a)==set(b)
rows=[x.split(';') for x in (B/'diagnostic.log').read_text().splitlines()]
assert len(rows)==len(b)==108
legacy_bad=[];corrected_bad=[]
for f in rows:
    key=(f[1],int(f[2]));px,pz,lx,lz=map(float,f[3:7]);legacy,corrected=map(vector,f[7:9])
    assert abs(lx-legacy[0])<=.001 and abs(lz-legacy[2])<=.001
    assert vector(b[key][2])==corrected
    assert vector(a[key][0])==vector(b[key][0]),'Navigation changed between runs'
    assert vector(a[key][1])==vector(b[key][1]),'Native terrain samples changed'
    assert abs(legacy[1]-corrected[1])<=1e-6,'Returned native height changed'
    if abs(px-lx)>.011 or abs(pz-lz)>.011:legacy_bad.append([*key,lx,lz])
    if abs(px-corrected[0])>.011 or abs(pz-corrected[2])>.011:corrected_bad.append(list(key))
assert len(legacy_bad)==13 and not corrected_bad
report=dict(status='REPRODUCED_NESTED_VECTOR_COORDINATE_FAILURE',waypoints=108,legacy_direct_coordinate_failures=13,scalar_temporaries_coordinate_failures=0,navigation_and_native_ground_samples_identical=True,native_road_y_identical=True,legacy_failures=legacy_bad,
 inputs={str(p):sha(p) for p in (A/'runtime.log',B/'runtime.log',B/'diagnostic.log',Path(__file__))},
 limits=['Direct legacy vector components are already wrong before ToString. This isolates the nested construction form as failing in this probe.','The internal engine/compiler mechanism is not established. No navigation, terrain or consumer thresholds changed.','Final clean canonical-source probe C still required before source closure.'])
(B/'diagnostic-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('legacy_failures','inputs')},indent=2))
