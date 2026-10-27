"""Bind the known failing original candidate for diagnosis, never acceptance."""
from pathlib import Path
import hashlib,json
HEIGHT_SHA='e086af218bc393476256cbfc17a540964d2daf53735dd9587585ae15eb9f7041'
NAMES={'kit7_piece_124_right/1','kit7_piece_133_right/1','kit7_seam_124_right/0','kit7_seam_133_right/0'}
PACKAGES={'narva_trial.pbo':'a2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c','baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6','baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43','DayZ_MCP.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'}
def validate_fields(height,dep):
    assert height['status']=='FAIL_KIT7_NATIVE_GRAPH' and len(height['cases'])==607 and not height['local_failures']
    assert len(height['height_issues'])==4 and {x.split(':')[0] for x in height['height_issues']}==NAMES
    assert dep['status']=='RESTORED_EXACT_ORIGINAL_PACKAGES_DIAGNOSTIC_ONLY' and dep['acceptance_eligible'] is False
    assert dep['height_result_sha256']==HEIGHT_SHA
    assert len(dep['packages'])==4 and {Path(p).name:h for p,h in dep['packages'].items()}==PACKAGES
def validate_diagnostic(result_path,deployment_path):
    raw=Path(result_path).read_bytes();assert hashlib.sha256(raw).hexdigest()==HEIGHT_SHA
    dep=json.loads(Path(deployment_path).read_text());validate_fields(json.loads(raw),dep)
    for p,h in {**dep['inputs'],**dep['packages']}.items():
        with Path(p).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
    return {'status':'DIAGNOSTIC_ONLY','acceptance_eligible':False,'height_failures_preserved':4}
