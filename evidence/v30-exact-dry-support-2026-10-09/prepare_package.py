from pathlib import Path
import json
B=Path(__file__).parent;R=B.parent;OLD=R/'v30-volkhov-float-consistent-20261009'
v=json.loads((B/'verification.json').read_text());assert v['status']=='PASS_STRICT_DRY_FLOOR_SOURCE'
code=(OLD/'audit_exposure.py').read_text();needle="shifts={int(k):z for k,z in json.loads((B/'authoring.json').read_text())['object_translations'].items()}";assert needle in code
(B/'audit_exposure.py').write_text(code.replace(needle,"shifts={} # EV70 changes no water object or water plane."))
code=(OLD/'stage_and_deploy.py').read_text()
code=code.replace("'PASS_GEOMETRIC_PROPOSAL_POLICY_PENDING'","'PASS_STRICT_DRY_FLOOR_SOURCE'").replace("result['terrain_sha256']","result['candidate_sha256']")
needle="shift={int(k):v for k,v in json.loads((B/'authoring.json').read_text())['object_translations'].items()}";assert needle in code
code=code.replace(needle,'shift={} # Water object records stay byte-exact.')
code=code.replace('STAGED_VOLKHOV_PROPOSAL_POLICY_PENDING','STAGED_EXACT_DRY_SOURCE_PASS').replace('DEPLOYED_VOLKHOV_PROPOSAL_POLICY_PENDING','DEPLOYED_EXACT_DRY_PREVIEW')
code=code.replace('@DayZ_Baltic_VolkhovBedProposalV1','@DayZ_Baltic_ExactDrySupportV1')
code=code.replace('EV67 textures retained provisionally over the same wet footprints; local shore apron semantics need final regeneration if accepted.','EV67 textures retained provisionally over the same wet footprints; dry shore palette must be regenerated over the final geometry.')
(B/'stage_and_deploy.py').write_text(code)
(B/'audit_coverage.py').write_text((OLD/'audit_coverage.py').read_text())
print('PREPARED_EXPOSURE_AND_PACKAGE_EV70')
