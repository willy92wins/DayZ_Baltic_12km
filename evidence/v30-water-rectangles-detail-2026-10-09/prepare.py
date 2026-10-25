from pathlib import Path
import json,hashlib
E=Path(__file__).parent
files={'world':Path('P:/Mods/@DayZ_Baltic_BaseSurfacePreviewV1/Addons/narva_trial.pbo'),'water':Path('P:/Mods/@DayZ_Baltic_BaseSurfacePreviewV1/Addons/baltic_water_v30.pbo'),'probe':Path('P:/Mods/@BalticDetailProbeV1/Addons/baltic_detail_probe_v1.pbo'),'profile':Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile')}
hashes={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()}
assert hashes['world']=='a08b96a1f952edca98e525221ed48790051291b8fcc9db7cc7661ea8bacc1335'
assert hashes['water']=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
assert hashes['probe']=='cd0939d9ae0be441cba22eaf7a321a1e8d648022ed40c65f894d4666d16e32b4'
(E/'profile-before.DayZProfile').write_bytes(files['profile'].read_bytes())
p=Path('P:/DayZ_MCP_dev/_client/profiles/baltic_detail_probe_v1.phase')
previous=p.read_text() if p.exists() else None
p.write_text('EV32-20261009\n0\n4\n')
(E/'preflight.json').write_text(json.dumps(dict(hashes=hashes,paths={k:str(p) for k,p in files.items()},phase_previous=previous,phase_reset=p.read_text()),indent=2)+'\n')
print(json.dumps(hashes))
