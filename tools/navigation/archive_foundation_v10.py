"""Archive the persisted editable foundation, dependencies and identified runtime package."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,shutil,sys,zipfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from attach_navmesh import read_pbo
from package_native_checkpoint import tree,sha
from verify_native_persistence import inspect

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--world-pbo',type=Path,required=True)
    ap.add_argument('--world-sha256',required=True);ap.add_argument('--water-pbo',type=Path,required=True)
    ap.add_argument('--generation-receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh archive required')
    source=ROOT/'tb/regional_foundation_v10';first=source/'01_native_v10.wrp';reopened=source/'02_reopened_v10.wrp'
    persistence=inspect(first,reopened)
    if persistence['status']!='PASS_EXACT_NATIVE_PERSISTENCE':raise ValueError('Reopen persistence failed')
    if sha(a.world_pbo)!=a.world_sha256:raise ValueError('Selected world changed')
    if sha(a.water_pbo)!='f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3':raise ValueError('Water dependency changed')
    _,_,entries=read_pbo(a.world_pbo);generation=json.loads(a.generation_receipt.read_text(encoding='utf-8-sig'))
    wrp_sha=hashlib.sha256(entries['baltic_trial.wrp']).hexdigest();nm_sha=hashlib.sha256(entries['navmesh/baltic_trial.nm']).hexdigest()
    if generation['compiled_wrp_sha256']!=wrp_sha or generation['navmesh_sha256']!=nm_sha or not generation['saved']:
        raise ValueError('Generation receipt does not bind this world/navmesh')
    folders=['tb/regional_foundation_v10','tests/regional_foundation_combined_v10','tests/narva_bridge_v10',
             'derived/outline-v3','build-temp/regional_water_assets_v2/baltic_water',
             'packages/baltic-foundation-v10-native/source/BalticTrialWorld',
             'tools/navigation','tools/playtest']
    paths={p for folder in folders for p in tree(ROOT/folder) if p.suffix!='.tmp'}
    for name in ('tests/regional_outline_v1/biome_reservation.tif','evidence/recorte-v0.kml','evidence/aprobacion.json'):
        p=ROOT/name
        if p.is_file():paths.add(p)
    biome=ROOT/'tests/regional_outline_v1/biome_reservation.tif'
    if biome not in paths:raise ValueError('Reserved biome layer missing')
    water_mount=Path('P:/baltic_water')
    water_source=ROOT/'build-temp/regional_water_assets_v2/baltic_water'
    if water_mount.resolve()!=water_source.resolve():raise ValueError('Native water model mount differs')
    # The editable has historical absolute imports. Preserve existing local
    # inputs explicitly; do not rewrite the binary project or copy vanilla.
    refs=[];raw=(source/'narva_trial.tv4p').read_bytes()
    pattern=rb'(?i)[a-z]:[\\/][ -~]*?\.(?:asc|png|v4w|cfg|xml|tif|lbt)(?=[^a-z0-9]|[A-Z])'
    # Printable ALB1 strings sometimes end immediately in a binary tag letter.
    for m in re.finditer(pattern,raw):
        name=m.group().decode('ascii');p=Path(name)
        try:relative=p.resolve().relative_to(ROOT.resolve())
        except ValueError:refs.append(dict(path=name,status='EXTERNAL_NOT_COPIED'));continue
        if p.is_file():paths.add(ROOT/relative);refs.append(dict(path=name,status='INCLUDED',archive_path=relative.as_posix()))
        else:refs.append(dict(path=name,status='HISTORICAL_REFERENCE_ABSENT'))
    if not refs:raise ValueError('Dependency parser found no references; inspect binary project')
    for p in paths:
        if p.is_symlink() or p.is_junction():raise ValueError('Unexpected link: '+str(p))
    records=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)]
    a.out.mkdir(parents=True);archive=a.out/'terrain-builder-foundation-v10.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for record in records:z.write(ROOT/record['path'],record['path'])
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist())!=len(records):raise ValueError('Archive count differs')
        for record in records:
            with z.open(record['path']) as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
            if digest!=record['sha256'] or sha(ROOT/record['path'])!=digest:raise ValueError('Archive/source changed during capture')
    mod=a.out/'@DayZ_Baltic_Foundation/Addons';mod.mkdir(parents=True)
    for src in (a.world_pbo,a.water_pbo):
        dst=mod/src.name;shutil.copy2(src,dst)
        if sha(dst)!=sha(src):raise ValueError('Copied addon mismatch')
    mission=ROOT/'missions/BalticNativeBasic.BalticTrial'
    shutil.copytree(mission,a.out/'mpmissions'/mission.name)
    report=dict(status='PASS_ARCHIVE_BYTES_NOT_WHOLE_MAP_ACCEPTANCE',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                native_persistence=persistence,world_pbo_sha256=a.world_sha256,water_pbo_sha256=sha(a.water_pbo),
                compiled_wrp_sha256=wrp_sha,navmesh_sha256=nm_sha,generation_receipt_sha256=sha(a.generation_receipt),
                archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,files=records,editable_references=refs,
                workdrive_mappings=[dict(path='P:/baltic_water',source='build-temp/regional_water_assets_v2/baltic_water',
                                        purpose='Terrain Builder Baltic_Water_V2 template model paths')],
                mission_files={p.relative_to(mission).as_posix():sha(p) for p in tree(mission)},
                limits=['Local checkpoint retaining original P:/DayZ_Baltic_12km_dev paths; restore there or remap in Terrain Builder.',
                        'Vanilla DZ/bin/core data are external prerequisites and not included.',
                        'Before opening the editable, recreate P:/baltic_water from the recorded workdrive_mappings; do not overwrite an existing unrelated path.',
                        'Historical native exports retained; selected native is tb/regional_foundation_v10/02_reopened_v10.wrp.',
                        'Source staging contains explicitly stale bootstrap NM; use runtime Addons and the generation receipt for current NM.',
                        'No placed settlements/forests/road pieces, final CE or 80-100-player capacity acceptance.'])
    (a.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    (a.out/'README.md').write_text('# Base regional Baltic V10 — checkpoint local\n\nEditable y paquete identificados en manifest.json. El manifiesto verifica cada\narchivo del ZIP y sus fuentes después de comprimir. Ver el handoff vigente para\nlos resultados físicos, visuales y de carga; este archivo no declara mapa1.0.\n\n'+ '\n'.join('- '+x for x in report['limits'])+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','editable_references')},indent=2))

if __name__=='__main__':main()
