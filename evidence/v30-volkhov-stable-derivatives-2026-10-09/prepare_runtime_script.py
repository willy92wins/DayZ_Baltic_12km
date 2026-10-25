from pathlib import Path
B=Path(__file__).parent;old=B.parent/'v30-isolated-basin-repair-20261009'
s=(old/'prepare_probe.py').read_text()
s=s.replace('BalticIsolatedBasinsFullWaterV1','BalticTerminalSmoothFullWaterV1').replace('BalticIsolatedBasinsFullWaterMission','BalticTerminalSmoothFullWaterMission')
s=s.replace('baltic_isolated_basins_fullwater_v1','baltic_terminal_smooth_fullwater_v1').replace('BALTIC_ISOLATED_BASINS_FULLWATER_V1','BALTIC_TERMINAL_SMOOTH_FULLWATER_V1')
s=s.replace('basins-fullwater','terminal-fullwater').replace('basins-physical','terminal-physical').replace('basins-unflagged','terminal-unflagged')
(B/'prepare_probe.py').write_text(s)
