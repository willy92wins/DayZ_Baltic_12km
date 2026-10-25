from pathlib import Path
import json,shutil,hashlib
B=Path(__file__).parent;R=B.parent;OLD=R/'v30-isolated-basin-repair-20261009';S=R/'v30-strict-dry-composition-20261009';SURFACE=R/'v30-surface-aligned-20261009'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
code=(OLD/'stage_and_deploy.py').read_text()
code=code.replace("OLD=Path('E:/DayZ-Baltic-Build/v30-coupled-native-shore-corrected-20261009')",f"OLD=Path('{S.as_posix()}')")
code=code.replace('@DayZ_Baltic_CurrentSurfaceV1','@DayZ_Baltic_SurfaceAlignedV2')
code=code.replace("result['status']=='PASS_INDEPENDENT_BASIN_GEOMETRY'","result['status']=='PASS_GEOMETRIC_PROPOSAL_POLICY_PENDING'\n    assert json.loads((B/'compiled-exposure.json').read_text())['status']=='PASS_COMPILED_EXPOSURE'")
code=code.replace('444d8c80cfc58b17c71863378e4f5f4449ddd9ee3b35ce8474ecb5298d3d3bc9','931dd215fcb211bf233e18dd4e7fd0ce7a64f772d7294d28abbc5b1a6fbd3107')
code=code.replace("sha(original)=='b69265c5feb99d1bda7a5c9f02282818d0ffe4cd26f89f3a095c128e62d374f3'",f"sha(original)==json.loads(Path('{(SURFACE/'deploy.json').as_posix()}').read_text())['files']['narva_trial.pbo']")
code=code.replace('@DayZ_Baltic_IsolatedBasinsV1','@DayZ_Baltic_VolkhovBedProposalV1')
code=code.replace('STAGED_ISOLATED_BASIN_WORLD','STAGED_VOLKHOV_PROPOSAL_POLICY_PENDING').replace('DEPLOYED_ISOLATED_BASIN_PREVIEW','DEPLOYED_VOLKHOV_PROPOSAL_POLICY_PENDING')
code=code.replace("expected[10]+=shift.get(old['id'],0)","expected[10]=np.float32(float(old['matrix'][10])+shift.get(old['id'],0))")
code=code.replace('EV28 textures retained provisionally; Nazia shoreline needs final texture regeneration; basin shapes conserved.','EV67 textures retained provisionally over the same wet footprints; local shore apron semantics need final regeneration if accepted.')
(B/'stage_and_deploy.py').write_text(code)
shutil.copyfile(R/'v30-volkhov-stable-derivatives-20261009/audit_coverage.py',B/'audit_coverage.py')
packed=B/'package/water/packed';packed.mkdir(parents=True,exist_ok=False);water=Path('P:/Mods/@DayZ_Baltic_StrictDryFloorV1/Addons/baltic_water_v30.pbo');assert sha(water)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14';shutil.copyfile(water,packed/water.name)
print('Prepared package scripts; source remains EV61, preview textures EV67.')
