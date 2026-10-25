from pathlib import Path
import shutil,json,hashlib
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
R=Path('E:/DayZ-Baltic-Build')
D=W/'evidence/v30-water-cause-investigation-2026-10-10'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
roots={
 'census':R/'v30-subsea-interior-census-20261009',
 'optical-ray':R/'v30-water-pixel-spatial-review-20261009',
 'rejected-narva':R/'v30-narva-bed-discriminator-20261009',
 'projection':R/'v30-water-pixel-calibration-20261010',
 'object-boundaries':R/'v30-water-object-boundaries-20261010',
}
manifest=[]
for label,source in roots.items():
    assert source.is_dir(), source
    for p in sorted(source.rglob('*')):
        assert not p.is_symlink(), p
        if not p.is_file() or p.suffix.lower() not in {'.md','.json','.py','.c','.cpp','.csv','.log','.jpg','.png'}:continue
        rel=Path(label)/p.relative_to(source);dst=D/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dst);assert sha(p)==sha(dst)
        manifest.append(dict(path=rel.as_posix(),bytes=dst.stat().st_size,sha256=sha(dst)))
for name in ['2026-10-09-luna-water-evidence-review.md','2026-10-09-luna-water-geometry-audit.md']:
    p=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions')/name;dst=D/'reviews'/name;dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,dst);assert sha(p)==sha(dst)
    manifest.append(dict(path=dst.relative_to(D).as_posix(),bytes=dst.stat().st_size,sha256=sha(dst)))
(D/'preservation.json').write_text(json.dumps(dict(status='PRESERVED_EXACT_FILES',files=manifest,limits=['Generated terrain npz stays outside Git; source and output hashes are in candidate/report.json.','DayZ PBO files remain deployed and hashed; no rejected terrain was deployed.']),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(files=len(manifest),bytes=sum(r['bytes'] for r in manifest),destination=str(D))))
