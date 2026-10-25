"""Reuse the proven full-grid native consumer with a fresh terminal-preview identity."""
from pathlib import Path
import ast,json,subprocess,sys
B=Path(__file__).parent;parent=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009')
s=(parent/'prepare_fullwater_regression.py').read_text()
s=s.replace('v30-global-contour-pass-2026-10-09','v30-native-terminal-finish-2026-10-09').replace('candidate-repaired/terrain.npz','candidate/terrain.npz')
s=s.replace('GlobalContourFullWater','TerminalContourFullWater').replace('global_contour_fullwater','terminal_contour_fullwater').replace('GLOBAL_CONTOUR_FULLWATER','TERMINAL_CONTOUR_FULLWATER')
s=s.replace('global-contour-fullwater','terminal-contour-fullwater').replace('global-contour-physical','terminal-contour-physical').replace('global-contour-unflagged','terminal-contour-unflagged')
ast.parse(s);dest=B/'prepare_terminal_fullwater.py';assert not dest.exists();dest.write_text(s)
print('Prepared generator; run after deploy.json exists.')
