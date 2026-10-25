from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).parent;R=B.parent;OLD=R/'v30-surface-aligned-20261009';S=R/'v30-remaining-exact-dry-support-20261009/candidate'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={'terrain.npz':'b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36','plane.npy':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0','visible-field.npy':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'}
assert all(sha(S/n)==v for n,v in hashes.items())
generator=W/'tools/terrain/build_surface_v30.py';prior=json.loads((OLD/'inputs.json').read_text());assert sha(generator)==prior['generator_sha256']
code=(OLD/'compile_and_verify_surface.py').read_text().replace('v30-strict-dry-composition-20261009/candidate','v30-remaining-exact-dry-support-20261009/candidate').replace('7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990',hashes['terrain.npz'])
(B/'compile_and_verify_surface.py').write_text(code)
(B/'check_changed_mips.py').write_text((OLD/'check_changed_mips.py').read_text())
(B/'inputs.json').write_text(json.dumps(dict(status='VERIFIED_EV71_GEOMETRY_SAME_GENERATOR',inputs={str(S/n):v for n,v in hashes.items()},generator_sha256=sha(generator),prior_inputs_sha256=sha(OLD/'inputs.json'),consumer_source_sha256=sha(OLD/'compile_and_verify_surface.py')),indent=2)+'\n')
dest=B/'candidate';dest.mkdir(exist_ok=False)
for name,expected in hashes.items():shutil.copyfile(S/name,dest/name);assert sha(dest/name)==expected
print('EV72_CURRENT_GEOMETRY_AND_SURFACE_CONSUMER_PREPARED')
