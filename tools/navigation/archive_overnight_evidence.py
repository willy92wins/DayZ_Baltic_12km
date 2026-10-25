"""Archive the night evidence and recipes after its runs stop; no map acceptance claim."""
from pathlib import Path
import argparse,datetime,hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--session-note',type=Path,required=True)
    ap.add_argument('--inventory-only',action='store_true',help='Read-only inventory; does not produce or accept an archive.')
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh archive directory required')
    night=ROOT/'evidence/overnight-2026-10-01';state=json.loads((night/'state.json').read_text())
    if state['status']!='SESSION_CLOSED' and not a.inventory_only:raise ValueError('Close runs, lease and session first')
    suffixes={'.json','.jsonl','.log','.rpt','.md','.txt','.png','.jpg','.c','.csv','.ps1','.py','.geojson','.dayzprofile'}
    selected={};excluded=[]
    visual_review=night/'visual-review.json'
    excluded_captures=set()
    if visual_review.exists():
        for relative in json.loads(visual_review.read_text(encoding='utf-8'))['excluded_other_window_images']:
            path=(night/relative).resolve()
            if not path.is_relative_to(night.resolve()) or not path.is_file():
                raise ValueError('Invalid excluded capture path')
            excluded_captures.add(path)
    def include(path,name=None):
        if not path.is_file():raise ValueError('Missing required evidence: '+str(path))
        key=name or path.relative_to(ROOT).as_posix()
        if key in selected and selected[key]!=path:raise ValueError('Ambiguous archive path')
        selected[key]=path
    for path in night.rglob('*'):
        if path.is_file():
            if path.resolve() in excluded_captures:
                excluded.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path),reason='Wrong application pixels; excluded from map evidence companion.'))
            elif 'memory-edits' in path.parts and path.name.endswith('.md'):
                excluded.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path),reason='Working Markdown backup kept locally; some shared-vault backups contain unrelated projects.'))
            elif path.suffix.lower() in suffixes:include(path)
            else:excluded.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path),reason='Binary editor/control fixture or dump remains in original project; not needed to read evidence.'))
    for path in (ROOT/'tools/navigation').iterdir():
        if path.is_file() and path.suffix in ('.py','.c','.ps1'):include(path)
    for name in ('attach_navmesh.py','verify_texture_grid_change.py'):include(ROOT/'tools/playtest'/name)
    for name in ('HANDOFF.md','PROJECT-MAP.md','product-spec.md','bugs.md','CLAUDE.md'):include(ROOT/name)
    include(ROOT/'packages/baltic-foundation-v10-native/README.md')
    # Small frozen geometry inputs required by the final consumer verifiers/plots.
    for relative in ('tests/regional_outline_v3/reference.npz',
        'tests/regional_foundation_roads_v6/reference.npz',
        'tests/regional_foundation_combined_v10/reference.npz',
        'tests/regional_foundation_combined_v10/solve.json',
        'evidence/regional-foundation-v1/fairways-main-game.json',
        'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson',
        'evidence/regional-foundation-v1/ocean-game.json',
        'evidence/regional-foundation-v1/road-grade-chains-v6.json',
        'evidence/regional-foundation-v1/road-network-selection.json',
        'evidence/regional-foundation-v1/combined-protected-area-review-v10.json',
        'evidence/narva/evidence/bridge-roadway.json'):
        include(ROOT/relative)
    for path in (ROOT/'plans').glob('*.md'):include(path)
    # Include only project-owned mission sources actually named by a night reference.
    mission_dirs=set()
    for rp in night.rglob('reference*.json'):
        ref=json.loads(rp.read_text(encoding='utf-8-sig'))
        named_mission=ref.get('mission',{})
        for key in (named_mission if isinstance(named_mission,dict) else {}):
            p=Path(key).resolve()
            if p.is_file() and p.is_relative_to(ROOT/'missions'):mission_dirs.add(p.parent)
        target=ref.get('deployed_mission')
        if target:
            p=ROOT/'missions'/Path(target).name
            if p.is_dir():mission_dirs.add(p)
    for folder in mission_dirs:
        for p in folder.rglob('*'):
            if p.is_file():include(p)
    for folder in (ROOT/'packages').iterdir():
        if folder.is_dir() and (folder.name.startswith('foundation-visual_g_') or folder.name in ('continuous-pursuit-v1','continuous-pursuit-v2','bridge-human-control-v1','foundation-drive-v1','boat-input-v2','boat-input-v2b')):
            for p in folder.rglob('*'):
                if p.is_file():include(p)
    skill=Path('C:/Users/guill/.codex/skills/dayz-terrain-workflow')
    for p in skill.rglob('*'):
        if p.is_file() and p.suffix in ('.md','.py','.yaml'):
            include(p,'skill-snapshot/dayz-terrain-workflow/'+p.relative_to(skill).as_posix())
    include(a.session_note,'session-note/'+a.session_note.name)
    records=[dict(path=k,source=str(p),bytes=p.stat().st_size,sha256=sha(p)) for k,p in sorted(selected.items())]
    if a.inventory_only:
        print(json.dumps(dict(status='INVENTORY_ONLY_NOT_ARCHIVE_ACCEPTANCE',members=len(records),bytes=sum(x['bytes'] for x in records),excluded=len(excluded))))
        return
    a.out.mkdir(parents=True);target=a.out/'overnight-evidence-and-recipes.zip'
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for row in records:z.write(row['source'],row['path'])
    with zipfile.ZipFile(target) as z:
        assert set(z.namelist())==set(selected)
        for row in records:
            if hashlib.sha256(z.read(row['path'])).hexdigest()!=row['sha256']:raise ValueError('Archive changed member')
            if sha(Path(row['source']))!=row['sha256']:raise ValueError('Source changed while archiving')
    report=dict(status='PASS_ARCHIVE_BYTES_NOT_WHOLE_MAP_ACCEPTANCE',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        archive_sha256=sha(target),archive_bytes=target.stat().st_size,files=records,excluded=excluded,
        base_checkpoint='packages/baltic-foundation-v10-native-checkpoint/terrain-builder-foundation-v10.zip',
        base_checkpoint_sha256='f96d3d5c11da9c7debcbfe35b8edad3e9ffcf9fbc8d194d999a751762ee3903f',
        limits=['Evidence companion; requires the base checkpoint, vanilla data and local tools.','No publication or external transfer.','Excluded binary artifacts remain on disk at their recorded paths.'])
    (a.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],members=len(records),bytes=report['archive_bytes'],sha256=report['archive_sha256'])))

if __name__=='__main__':main()
