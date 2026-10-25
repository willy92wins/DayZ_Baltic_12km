"""Carry the complete candidate-terrain coverage across exact WRP object parity."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
B=Path(__file__).parent;parent=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009')
sys.path.insert(0,str(Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')));from discover_native_turns import W,sha
sys.path.insert(0,str(W/'tools/terrain'));from wrp0wzd import read
audit=json.loads((B/'initial-coverage.json').read_text());stage=json.loads((B/'stage.json').read_text())
assert audit['status']=='PASS_GLOBAL_COMPILED_COVERAGE' and not audit['uncovered_cells']
old=parent/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';new=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
assert sha(old)==audit['world_source_sha256']==stage['old_world_source_sha256']
assert sha(new)==stage['world_source_sha256']
assert sha(B/'candidate/terrain.npz')==audit['terrain_sha256']==stage['terrain_sha256']
a,b=read(old),read(new);assert [o['bytes'] for o in a['objects']]==[o['bytes'] for o in b['objects']]
assert np.array_equal(b['heights'],np.load(B/'candidate/terrain.npz')['heights'][::-1])
water=parent/'package/water/packed/baltic_water_v30.pbo';assert sha(water)==audit['water_sha256']==stage['water_sha256']
audit.update(world_source_sha256=sha(new),coverage_input_world_source_sha256=sha(old),coverage_reuse_proof='Candidate terrain was already the audited input. Every WRP object byte is identical and the compiled water archive hash is exact; only WRP heights changed to that candidate.',object_record_parity_sha256=hashlib.sha256(b''.join(o['bytes'] for o in b['objects'])).hexdigest(),source_audit_sha256=sha(B/'initial-coverage.json'))
(B/'final-coverage.json').write_text(json.dumps(audit,indent=2)+'\n')
package=dict(status='TERMINAL_WORLD_WITH_UNCHANGED_COMPILED_WATER',terrain_sha256=stage['terrain_sha256'],water_sha256=sha(water),world_source_sha256=sha(new),original_objects_exact=True,added_objects=0,objects=len(b['objects']),old_water_contents_exact=True,source_water_build=str(parent/'package/water'),limits=['Water build is an immutable junction reference; never delete recursively through it.', 'Coverage reuse follows identical object bytes, archive hash and the same candidate terrain input.'])
(B/'package-seams.json').write_text(json.dumps(package,indent=2)+'\n');print(json.dumps(package,indent=2))
