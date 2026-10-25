"""Corrupt real V4 evidence; require rejection by independent physical invariants."""
import json
import rasterio
from verify_outline_chase import ROOT, verify, vector

base = ROOT / 'evidence/regional-outline-v3'
raw = (base/'runtime-chase-tile12p5-v4.log').read_text()
ref = json.loads((base/'chase-reference-v4.json').read_text())
with rasterio.open(ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc') as ds:
    heights = ds.read(1)
assert verify(raw, ref, heights)['status'].startswith('PASS')
lines = raw.splitlines()
controls = []


def rejected(name, changed, gate=None):
    try:
        result = verify('\n'.join(changed), ref, heights)
    except (ValueError, IndexError, KeyError):
        assert gate is None, f'{name}: parser rejected before intended gate'
    else:
        assert result['status'].startswith('FAIL'), name
        if gate:
            assert any(not s['checks'][gate] for s in result['stages']), name
    controls.append({'control': name, 'rejected': True})


rejected('truncated_completion', lines[:-2])
old = lines.copy(); old[0] = 'BALTIC_OUTLINE_CHASE_V3'
rejected('cannot_reclassify_old_v3_as_v4', old)
sample_indices = [i for i, line in enumerate(lines) if line.startswith('SAMPLE;') and line.split(';')[2] == '1']
assert len(sample_indices) > 10
middle = sample_indices[len(sample_indices)//2]

floating = lines.copy(); f = floating[middle].split(';'); f[4] = str(float(f[4]) + 1); floating[middle] = ';'.join(f)
rejected('actor_floating_above_native_ground', floating, 'physical_surface')

prey = lines.copy(); f = prey[middle+1].split(';'); pos = vector(f[3]); pos[0] += 5; f[3] = '<' + ','.join(map(str,pos)) + '>'; prey[middle+1] = ';'.join(f)
rejected('human_target_drift', prey, 'fixed_prey')

silent = lines.copy()
for i, line in enumerate(silent):
    f = line.split(';')
    if len(f) == 11 and f[0] in ('SPAWN','SAMPLE','NOISE','REACHED'):
        f[9] = '841311604' if f[0] == 'SPAWN' else '0'
        silent[i] = ';'.join(f)
rejected('invalid_spawn_mind_cannot_prove_stimulus', silent, 'responded_to_stimulus')

invalid = lines.copy(); f = invalid[middle].split(';'); f[9] = '841311604'; invalid[middle] = ';'.join(f)
rejected('invalid_settled_native_mind', invalid, 'known_mind_states_after_first_second')

missed = lines.copy()
end = next(i for i,line in enumerate(lines) if line.startswith('REACHED;') and line.split(';')[2] == '1')
f = missed[end].split(';'); f[3:8] = lines[sample_indices[0]].split(';')[3:8]; missed[end] = ';'.join(f)
rejected('false_reached_marker_without_goal', missed, 'reached_target_3d')

loop = lines.copy()
positions = [lines[sample_indices[0]].split(';')[3:8], lines[sample_indices[-1]].split(';')[3:8]]
for n,i in enumerate(sample_indices):
    f = loop[i].split(';'); f[3:8] = positions[n%2]; loop[i] = ';'.join(f)
rejected('excessive_travel_or_position_jumps', loop, 'bounded_path_length')

result = dict(status='PASS_REAL_CONSUMER_AND_NEGATIVE_CONTROLS', controls=controls,
              limits=['Corruption controls for this verifier, not additional in-game runs.'])
(base/'consumer-v4-controls.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
