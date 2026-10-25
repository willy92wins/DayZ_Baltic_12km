"""Freeze a separate transmission experiment; does not modify the terrain."""
from pathlib import Path
import json
import shutil
from waterway_common import ROOT, sha, read_base, sample
import numpy as np

destination=ROOT/'missions/BalticBoatCalibration.BalticTrial'
if destination.exists():
    raise ValueError('Fresh calibration mission required')
x,z=np.meshgrid(np.arange(1880,2121,6)+200000,np.arange(11080,11321,6))
heights=sample(read_base(),x,z)
if float(heights.max()) > -3:
    raise ValueError('Open-water reference not sufficiently deep')
shutil.copytree(ROOT/'missions/BalticBasic.BalticTrial',destination,
                ignore=shutil.ignore_patterns('storage*','*.log','*.RPT'))
source=ROOT/'tools/navigation/boat_calibration_init.c'
shutil.copyfile(source,destination/'init.c')
out=ROOT/'evidence/navigation/calibration-v1'
out.mkdir(exist_ok=False)
(out/'fixture.json').write_text(json.dumps({
    'mission':str(destination),'init_sha256':sha(destination/'init.c'),
    'reference_game_xz':[2000,11200],'offline_box_half_width_m':120,
    'offline_max_ground_m':float(heights.max()),
    'pbo_sha256':'ee93a4c4a00a81e246ea81fbd3d83b25ba642b24d650cbb738ecf26b022eb67d',
    'purpose':'Control calibration only; not river or crew clearance acceptance',
    'max_seconds':85,'distance_stop_m':90},indent=2)+'\n',encoding='utf-8')
print('Created isolated calibration mission and frozen fixture.')
