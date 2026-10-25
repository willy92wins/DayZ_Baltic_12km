"""Freeze the verified regional baseline and native inputs, excluding probes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()
expected = 'ebc60f4f089b3e125426263b456d1f9662bc828c506993bbabbf0e43023a06d4'
if sha(a.baseline.read_bytes()) != expected or a.output.exists():
    raise ValueError('Exact baseline and fresh output required')
native = a.repo/'tb/regional_clearance_v1'
paths = sorted(native.rglob('*'))
if any(x.is_symlink() or x.is_junction() for x in paths):
    raise ValueError('Native archive must not traverse reparse points')
native_files = [x for x in paths if x.is_file()]
if len(native_files) != 8934:
    raise ValueError('Native source set changed; review before freezing')
a.output.mkdir(parents=True)
mod = a.output/'@DayZ_Baltic_12km/Addons'
mod.mkdir(parents=True)
shutil.copyfile(a.baseline, mod/'narva_trial.pbo')
shutil.copytree(a.repo/'missions/BalticBasic.BalticTrial', a.output/'mpmissions/BalticBasic.BalticTrial',
                ignore=shutil.ignore_patterns('storage*', '*.log', '*.RPT'))
archive = a.output/'terrain-builder-regional.zip'
records = {}
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for source in native_files:
        name = 'regional_clearance_v1/'+source.relative_to(native).as_posix()
        data = source.read_bytes()
        z.writestr(name, data)
        records[name] = sha(data)
    for name in ('baltic_regional_clearance_v1.asc', 'delta.npz', 'manifest.json'):
        source = a.repo/'tests/regional_clearance_v1'/name
        data = source.read_bytes()
        entry = 'candidate-source/'+name
        z.writestr(entry, data)
        records[entry] = sha(data)
with zipfile.ZipFile(archive) as z:
    if set(z.namelist()) != set(records):
        raise ValueError('Archive entry set mismatch')
    for entry, digest in records.items():
        if sha(z.read(entry)) != digest:
            raise ValueError('Archive verification failed: '+entry)
if sha((mod/'narva_trial.pbo').read_bytes()) != expected:
    raise ValueError('PBO copy changed')
manifest = dict(status='PASS_FROZEN_TECHNICAL_CANDIDATE_NOT_FULL_MAP_RELEASE',
                map_sha256=expected, map_bytes=(mod/'narva_trial.pbo').stat().st_size,
                navmesh_sha256='0fc26281e3cf2908b9f95f937521d758808007a83f9f837e4e81a034a5b161fe',
                wrp_sha256='d12ae049599b804c46df91a7bac46e8a530c7ade1ad149188524aed768479d5c',
                native_zip_sha256=sha(archive.read_bytes()), native_entries=len(records),
                native_entries_sha256=records, probes_in_addons=False,
                mission='BalticBasic.BalticTrial',
                mission_sha256={p.relative_to(a.output).as_posix(): sha(p.read_bytes())
                                for p in (a.output/'mpmissions').rglob('*') if p.is_file()},
                limitations=['Absolute native P: paths remain; this is not a portable installer.',
                             'Editable TB export needs the documented exact object-pose normalization.',
                             'Cities, regional physical roads, elevated lakes, CE, live AI and80-100 unaccepted.'])
(a.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k!='native_entries_sha256'}, indent=2))
