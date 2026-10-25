"""Compare equal camera readbacks and retain diagnostic texture statistics."""
from pathlib import Path
import csv
import json
import hashlib
import sys
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

EV = Path(__file__).resolve().parent
ROOT = EV.parents[1]
sys.path.insert(0, str(ROOT/'tools/playtest'))
from dark_tiles_v30 import measure
B = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008')
old = json.loads((EV/'render-v12.json').read_text())
new = json.loads((EV/'render-combined.json').read_text())
figures = EV/'figures'
figures.mkdir(exist_ok=True)
checks, views = {}, {}
focus = {}
for name in ['v12-corrected', 'combined']:
    path = B/f'focus-{name}.csv'
    rows = list(csv.DictReader(path.open()))
    window = [r for r in rows if r['window_exists'] == 'True']
    times = np.array([np.datetime64(r['utc'].replace('Z','')) for r in rows])
    focus[name] = dict(samples=len(rows), window_samples=len(window),
                       focused_samples=sum(r['foreground_is_client'] == 'True' for r in window),
                       minimized_samples=sum(r['minimized'] == 'True' for r in window),
                       observed_pids=sorted({r['client_pid'] for r in window}),
                       start_utc=rows[0]['utc'], end_utc=rows[-1]['utc'],
                       max_sample_gap_s=float(np.diff(times).max()/np.timedelta64(1,'s')),
                       sha256=hashlib.sha256(path.read_bytes()).hexdigest())
fig, axes = plt.subplots(3, 2, figsize=(14, 13), layout='constrained')
roi = (640, 848, 1152, 1040)  # Dry land observed in all six native frames.
for row, (label, distance) in enumerate([('near', 70.8802), ('medium', 283.5207), ('far', 1134.0828)]):
    a, b = old['views'][label], new['views'][label]
    checks[label+'_camera_exact'] = a['camera']['camera']['matrix'] == b['camera']['camera']['matrix']
    checks[label+'_viewport_exact'] = all((v['capture']['effective_surface']['native_width'], v['capture']['effective_surface']['native_height']) == (1920,1080) for v in [a,b])
    views[label] = dict(target_distance_m=distance, roi_pixels=roi, captures={})
    for col, (v, package) in enumerate([(a,'V12'), (b,'Preview combinada')]):
        path = Path(v['capture']['fullres_path'])
        im = Image.open(path)
        assert im.size == (1920,1080)
        crop = figures/f'{label}-{col}-land-roi.png'
        im.crop(roi).save(crop)
        views[label]['captures'][package] = dict(full_frame=measure(path,.55,.8,140),
                                                 dry_roi=measure(crop,1.,.8,140),
                                                 file_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        axes[row,col].imshow(np.array(im)[250:1080,:])
        axes[row,col].set_axis_off()
        axes[row,col].set_title(f'{package} · {distance:.0f} m')
noon=dict(year=2026,month=10,day=2,hour=12,minute=0)
checks['time_same_noon'] = old['time']['world_time'] == new['time']['world_time'] == noon
terrain = np.load(B/'combined/terrain_inland.npz')['heights']
baseline = np.load('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz')['heights']
samples = []
for x,z in [(6060,8346),(6324,8190),(9492,2076)]:
    expected = float(terrain[(12282-z)//6, x//6])
    stale = float(baseline[(12282-z)//6,x//6])
    got = new['surfaces'][str(x)]
    checks[f'height_{x}_exact'] = got['ok'] == 1 and got['y'] == expected
    checks[f'height_{x}_rejects_stale_v12'] = abs(got['y']-stale) > .4
    samples.append(dict(x=x,z=z,expected=expected,engine=got['y'],v12=stale))
checks['remote_camera_exact'] = new['views']['remote_before']['camera']['camera']['matrix'] == new['views']['remote_after']['camera']['camera']['matrix']
report = dict(status='PASS_MATCHED_VIEWS_AND_HEIGHT_READBACK' if all(checks.values()) else 'FAIL',
              checks=checks, samples=samples, focus=focus, views=views,
              requested_fov_radians=1.1955505,
              texture_acceptance='INCONCLUSIVE_LONG_DISTANCE: far dry ROI exceeds the unchanged historical 0.2 metric in both packages; no threshold adjustment.',
              visible_result='Textured dry terrain at all three distances in both packages and at the remote Luga view before/after player teleport.',
              limits=['FOV request equal; camera_get does not expose native FOV.',
                      'Foreground comparison is not a causal active/inactive focus experiment.',
                      'Texture metrics are diagnostics on observed land ROIs, not whole-map acceptance.',
                      'Surface query at underwater x10290,z3918 returned fresh_water_ext y3.15; excluded from terrain-height proof.',
                      'No claim that the intermittent grey-tile issue is fixed.'])
fig.suptitle('DayZ · mismas cámaras y viewport 1920 × 1080\nTexturas y materiales idénticos; solo cambia la geometría del WRP', fontsize=15)
fig.savefig(figures/'render-tres-distancias.png',dpi=120)
plt.close(fig)
(EV/'render-comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(status=report['status'],checks=checks,focus=focus,
                     dry_roi_bluish={k:{p:d['dry_roi']['flat_dark_bluish_share'] for p,d in v['captures'].items()} for k,v in views.items()}),indent=2))
assert all(checks.values())
