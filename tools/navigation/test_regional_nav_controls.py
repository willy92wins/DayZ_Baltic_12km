"""Parser controls only, separate from the retained real-engine FAIL."""
import json
from verify_regional_nav import ROOT, REFERENCE, check

ref = json.loads(REFERENCE.read_text())
raw = (ROOT/'evidence/regional-outline-v3/runtime-nav-v1.log').read_text()
result = check(raw, ref)
assert result['status'] == 'FAIL' and result['gates']['heights'] and len(result['sample_failures']) == 26
assert result['gates']['negative_filter'] and sum(p['passed'] for p in result['routes']) == 2
lines = raw.splitlines()
d = next(i for i,v in enumerate(lines) if v.startswith('D;0;'))

def rejected(name, changed):
    try:
        r = check('\n'.join(changed), ref)
    except (ValueError, IndexError, KeyError):
        return {'control': name, 'rejected': True}
    raise AssertionError('Malformed evidence accepted: '+name)

controls = []
controls.append(rejected('no_footer', lines[:-1]))
controls.append(rejected('duplicate_point', lines[:d]+[lines[d]]+lines[d:]))
controls.append(rejected('missing_point', lines[:d]+lines[d+1:]))
bad = lines.copy(); bad[2] = 'flags=65535;0'
controls.append(rejected('wrong_filter', bad))
bad = lines.copy(); bad[d] = 'D;0;<4896,nan,11994>;true;<4896,12,11994>'
controls.append(rejected('nonfinite_position', bad))
bad = lines.copy(); bad[d] = 'D;0;<4897,12.4709,11994>;true;<4897,12.4709,11994>'
controls.append(rejected('moved_reference_point', bad))
bad = lines.copy(); bad[d] = 'D;0;<4896,50,11994>;true;<4896,50,11994>'
assert not check('\n'.join(bad), ref)['gates']['heights']
controls.append({'control':'wrong_terrain_height','rejected':True})
bad = lines.copy(); bad[-2] = 'Q;negative;true;true;true;0'
assert not check('\n'.join(bad), ref)['gates']['negative_filter']
controls.append({'control':'negative_filter_found_path','rejected':True})
out = dict(status='PASS_VERIFIER_CONTROLS_REAL_RUNTIME_STILL_FAIL', real_sample_failures=26, controls=controls)
(ROOT/'evidence/regional-outline-v3/nav-verifier-controls.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
