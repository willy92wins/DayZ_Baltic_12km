"""Reproduce logical satisfiability only. The observations are SYNTHETIC, not native."""
from pathlib import Path
import hashlib,json,sys
repo=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(repo/'tools/quality'))
from dry_road_native_consumer_ev112 import evaluate
data=json.loads(Path(__file__).with_name('unsat-counterexample.json').read_bytes())
source=repo/'tools/quality/dry_road_native_consumer_ev112.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='9613ed035eaa64cc58dfaf2e7a9baaa441c30e90f225b91567507b62660ff0b4'
results=[evaluate([c['unchanged_expectation']],{c['id']:c['SYNTHETIC_measured']},{'margin_m':.03999144638858333}) for c in data['cases_detail']]
assert len(results)==41
assert all(r['rows'][0]['states']['water']=='PASS' and r['rows'][0]['states']['roadway']=='PASS' for r in results)
assert sum(r['status']=='SERVER_PROBE_PASS' for r in results)==40
print(json.dumps(dict(status='SYNTHETIC_COUNTEREXAMPLE_REPRODUCED_NOT_NATIVE',cases=41,water_pass=41,roadway_pass=41,full_synthetic_pass=40)))
