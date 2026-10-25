"""Reject damaged copies of the real completed engine baseline."""
import json
from pathlib import Path
from verify_terrain_perf import verify

root = Path(__file__).resolve().parents[2]
text = (root/'evidence/performance/native-baseline-v1/engine.log').read_text(encoding='utf-8-sig')
assert verify(text)['samples'] == 120
lines = text.splitlines()
cases = {'missing_end':'\n'.join(lines[:-1]),
         'wrong_world':text.replace(';BalticTrial;', ';ChernarusPlus;', 1),
         'missing_sample':'\n'.join(lines[:7]+lines[8:]),
         'duplicate_sample':'\n'.join(lines[:7]+[lines[6]]+lines[8:]),
         'wrong_columns':text.replace('max_timeslice','min_timeslice',1)}
for name, field, value in [('nonfinite_clock',2,'nan'),('clock_backwards',2,'0'),
                          ('zero_updates',5,'0'),('invalid_fps',9,'0'),('fractional_over50',8,'0.5')]:
    altered = lines.copy(); row = altered[4].split(';'); row[field] = value
    altered[4] = ';'.join(row); cases[name] = '\n'.join(altered)
result = {}
for name, invalid in cases.items():
    try:
        verify(invalid)
    except (ValueError,IndexError):
        result[name] = 'REJECTED'
    else:
        raise AssertionError(f'False PASS: {name}')
out = root/'evidence/performance/native-baseline-v1/negative-controls.json'
out.write_text(json.dumps({'status':'PASS_EVIDENCE_REJECTION_CONTROLS','controls':result},indent=2)+'\n')
print(json.dumps(result,indent=2))
