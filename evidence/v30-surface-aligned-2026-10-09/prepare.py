from pathlib import Path
import hashlib,json

B=Path(__file__).parent; R=B.parent; OLD=R/'v30-current-satellite-20261009'; S=R/'v30-strict-dry-composition-20261009/candidate'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={'terrain.npz':'7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990','plane.npy':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0','visible-field.npy':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'}
assert all(sha(S/n)==v for n,v in hashes.items())
inputs=json.loads((OLD/'inputs.json').read_text());generator=W/'tools/terrain/build_surface_v30.py'
assert sha(generator)==next(v for k,v in inputs['inputs'].items() if k.endswith('build_surface_v30.py'))
code=(OLD/'compile_and_verify_surface.py').read_text()
code=code.replace("T=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')",f"T=Path('{(S/'terrain.npz').as_posix()}')")
code=code.replace("P=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')",f"P=Path('{(S/'plane.npy').as_posix()}')")
code=code.replace("OLD=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/data/layers')",f"OLD=Path('{(OLD/'surface/layers').as_posix()}')")
code=code.replace("MASK=Path('E:/DayZ-Baltic-Build/v30-water-mask-alignment-20261009/layers')",'MASK=OLD')
code=code.replace('fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6',hashes['terrain.npz']).replace('d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803',hashes['plane.npy'])
(B/'compile_and_verify_surface.py').write_text(code)
code=(OLD/'package_surface.py').read_text().replace('@DayZ_Baltic_HingeSmoothV1','@DayZ_Baltic_StrictDryFloorV1').replace('9eb9f4006c55e3ed3f73461816bed0272e8ab5fdc2f0ca58e214687ef0b82ee5','1423f25da029ab0524a9d7861c2fbd1b2cda5f97b2244aa27e2a3fc03e3b5580').replace('fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6',hashes['terrain.npz']).replace('cfcbbd0c70b75a8e82824343905b16c4d43431ecca32b4fe9b722ac802c38fab','1b6fcff311b7de44b032a1e50eb4a0ae478d0035d2a5066b2d9e59a2b9f9788f').replace('@DayZ_Baltic_CurrentSurfaceV1','@DayZ_Baltic_SurfaceAlignedV2').replace('EV25 terrain/objects','EV61 terrain/objects')
(B/'package_surface.py').write_text(code)
(B/'inputs.json').write_text(json.dumps(dict(status='VERIFIED_CURRENT_INPUTS',inputs={str(S/n):v for n,v in hashes.items()},generator_sha256=sha(generator),input_controls_inherited_sha256=sha(OLD/'inputs.json'),independent_consumer_source_sha256=sha(OLD/'compile_and_verify_surface.py')),indent=2)+'\n')
print('Prepared same generator and independent full-map consumer against EV61.')
