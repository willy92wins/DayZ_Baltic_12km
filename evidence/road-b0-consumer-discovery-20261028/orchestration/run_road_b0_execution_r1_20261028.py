from pathlib import Path
import hashlib,json,sys,time
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');sys.path.insert(0,str(W/'tools/quality'))
import build_prism_b3e2_ev112 as runtime
import road_consumer_discovery_ev112 as discovery
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
A=R/'road-b0-r1-execution-approval-20261028.json';O=R/'road-b0-discovery-r1-20261028';log=R/'road-b0-execution-r1-driver-20261028.log'
exception=R/'road-b0-r1-driver-exception-20261028.json'
assert not any(p.exists() for p in (O,log,log.with_suffix('.receipt.json'),log.with_suffix('.running.json'),exception)),'already_started'
a=json.loads(A.read_bytes());assert a['schema']=='ROAD_B0_EXECUTION_V1' and a['status']=='REVIEW_ADJUDICATED_TESTS_PASS' and Path(a['output']).resolve()==O.resolve()
required=[W/'tools/quality/road_consumer_discovery_ev112.py',W/'tools/quality/test_road_consumer_discovery_ev112.py',W/'plans/ev112-road-consumer-discovery-b0-20261028.md',Path(__file__).resolve(),Path(a['tests']),Path(a['review_adjudication'])]
assert all(str(p) in a['pins'] for p in required)
for p,h in a['pins'].items():assert sha(p)==h,p
suite=json.loads(Path(a['tests']).read_bytes());assert suite['status']=='TESTS_PASS' and suite['seconds']<=120 and suite['tests']>0
for p in required[:2]:assert suite['postimages'][str(p)]==a['pins'][str(p)]
argv=[sys.executable,'-I',str(required[0]),str(O)];started_ns=time.time_ns()
try:
 receipt=runtime.base.run_tree(argv,W,log,120)
except RuntimeError as error:
 runtime.dump(exception,dict(error=str(error)))
 receipt=json.loads(log.with_suffix('.receipt.json').read_bytes())
assert receipt['stop_reason'] is None and receipt['seconds']<=120 and receipt['peak_sampled_tree_rss_bytes']<=2*1024**3
assert receipt['returncode'] in (0,2)
for p,h in a['pins'].items():assert sha(p)==h,p
report=json.loads((O/'report.json').read_bytes());assert 'error' not in report,report
assert log.with_suffix('.running.json').stat().st_mtime_ns>=started_ns and log.with_suffix('.receipt.json').stat().st_mtime_ns>=started_ns
discovery.bind_execution_receipt(receipt,json.loads(log.with_suffix('.running.json').read_bytes()),argv,report['measurement']['pid'])
discovery.accept_run_receipt(receipt,report)
runtime.dump(O/'completion.json',dict(status=report['status'],report_sha256=sha(O/'report.json'),approval_sha256=sha(A),receipt=receipt,no_dayz_or_placement=True))
print(json.dumps(dict(status=report['status'],report_sha256=sha(O/'report.json'),seconds=report['elapsed_s'])))
