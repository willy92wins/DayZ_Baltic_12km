from pathlib import Path
import hashlib, json, struct

root = Path(r'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\buldozer-auto-v1')
source = Path(r'P:\DayZ_Baltic_12km_dev\tests\buldozer-observer\baltic_water_observer')
pbo = root / 'Addons/baltic_water_observer.pbo'
data = pbo.read_bytes()
pos = 0
entries = []
properties = {}

def string():
    global pos
    end = data.index(b'\0', pos)
    result = data[pos:end].decode('utf-8')
    pos = end + 1
    return result

while True:
    name = string()
    mime, original, reserved, timestamp, size = struct.unpack_from('<5I', data, pos)
    pos += 20
    if not name:
        if mime == 0x56657273:
            while True:
                key = string()
                if not key:
                    break
                properties[key] = string()
            continue
        break
    assert mime == 0, 'Compressed content needs an actual decoder'
    entries.append((name, size))

blob = {}
for name, size in entries:
    key = name.replace('\\', '/').lower()
    assert key not in blob
    content = data[pos:pos + size]
    pos += size
    assert len(content) == size
    assert content == (root / 'temp/baltic_water_observer' / name.replace('\\', '/')).read_bytes()
    blob[key] = content

script_name = 'scripts/5_mission/balticwaterobserver.c'
assert set(blob) == {'config.bin', script_name}, list(blob)
assert blob['config.bin'].startswith(b'\0raP')
assert properties.get('prefix') == 'baltic_water_observer'
assert blob[script_name] == (source / 'scripts/5_Mission/BalticWaterObserver.c').read_bytes()
assert b'baltic_water_observer/scripts/5_Mission' in blob['config.bin']
assert b'missionScriptModule' in blob['config.bin']
assert b'DZ_Scripts' in blob['config.bin']
assert b'BALTIC_AUTO_OBSERVER_V1_COMPLETE_441' in blob[script_name]

result = {
    'status': 'PASS_PACKED_OBSERVER_CONTENT_ONLY',
    'pbo_bytes': len(data),
    'pbo_sha256': hashlib.sha256(data).hexdigest(),
    'properties': properties,
    'entries': [{'name': n, 'bytes': len(c), 'sha256': hashlib.sha256(c).hexdigest()} for n, c in blob.items()],
    'actual_compiled_tree_and_source_parity': True,
    'limits': ['No engine Enforce compilation, module-load or water result yet.'],
}
(root / 'package-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
