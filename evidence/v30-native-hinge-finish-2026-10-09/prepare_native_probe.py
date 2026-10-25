from pathlib import Path
import ast,json,sys
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-native-hinge-finish-2026-10-09';E.mkdir(parents=True,exist_ok=True)
source=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/prepare_terminal_fullwater.py')
s=source.read_text().replace('v30-native-terminal-finish-2026-10-09','v30-native-hinge-finish-2026-10-09')
s=s.replace('TerminalContour','HingeSmooth').replace('TERMINAL_CONTOUR','HINGE_SMOOTH').replace('terminal_contour','hinge_smooth').replace('terminal-contour','hinge-smooth')
ast.parse(s);target=B/'prepare_hinge_fullwater.py';assert not target.exists();target.write_text(s)
print(str(target))
