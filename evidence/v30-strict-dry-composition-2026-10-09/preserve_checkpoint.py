from pathlib import Path
import ast,json,hashlib,shutil,io
import numpy as np
B=Path(__file__).parent;R=B.parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'v30-isolated-basin-repair-20261009/preserve_checkpoint.py';tree=ast.parse(old.read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)];exec(compile(ast.Module(body=defs,type_ignores=[]),str(old),'exec'))
save_layer()
jobs=[('v30-msta-dry-bank-solve-20261009',[]),('v30-volkhov-coupled-visible-20261009',[]),('v30-volkhov-stable-derivatives-20261009',['runtime/msta','runtime/msta-valid','runtime/volkhov']),('v30-native-water-flag-classification-20261009',[]),('v30-low-dry-domain-classification-20261009',[]),('v30-strict-dry-floor-20261009',[]),('v30-strict-dry-composition-20261009',['risk-census'])]
print(json.dumps({name:copy_set(R/name,W/'evidence'/name.replace('-20261009','-2026-10-09'),subs) for name,subs in jobs},indent=2))
