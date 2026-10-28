"""Outer 300s/2GiB observed-tree cap; internal 60/120/120 phase caps still apply."""
from pathlib import Path
import sys,json
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');sys.path.insert(0,str(W/'tools/quality'))
import build_prism_b3e2_ev112 as runtime
log=R/'b3f-execution-driver-20261028.log';out=R/'prism-b3f-package-20261028'
if log.exists() or out.exists():raise RuntimeError('execution_already_started')
r=runtime.run_process([sys.executable,'-I',str(W/'tools/quality/prism_b3f_package_ev112.py'),'execute',str(R/'b3f-execution-approval-20261028.json'),str(out)],log,300)
print(json.dumps(r))
