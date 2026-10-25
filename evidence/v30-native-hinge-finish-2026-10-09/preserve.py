from pathlib import Path
import json,shutil,hashlib
B=Path(__file__).parent;A=Path('E:/DayZ-Baltic-Build/v30-surface-crease-audit-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for root,leaf in [(A,'v30-surface-crease-audit-2026-10-09'),(B,'v30-native-hinge-finish-2026-10-09')]:
    dest=W/'evidence'/leaf;dest.mkdir(exist_ok=True)
    for p in root.iterdir():
        if p.is_file() and p.suffix in ('.py','.ps1','.md','.json','.csv','.npz','.log'):
            target=dest/p.name
            if target.exists():assert target.read_bytes()==p.read_bytes(),target
            else:shutil.copyfile(p,target)
            assert sha(p)==sha(target)
    if root==B:
        shutil.copyfile(B/'package/world-addonbuilder.log',dest/'world-addonbuilder.log')
        frames=dest/'frames';frames.mkdir(exist_ok=True)
        for q in json.loads((B/'runtime.json').read_text())['views']:
            p=Path(q['fullres_path']);shutil.copyfile(p,frames/p.name);assert sha(p)==sha(frames/p.name)
        mission=B/'missions/BalticHingeSmoothFullWaterV1.BalticTrial'
        for name in ['init.c','risks.csv']:shutil.copyfile(mission/name,dest/('mission-'+name))
    print(str(dest))
