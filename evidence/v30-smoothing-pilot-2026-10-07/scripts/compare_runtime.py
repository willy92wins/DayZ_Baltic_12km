"""Verify independent engine readbacks and make matched screenshots reviewable."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

EV=Path(__file__).resolve().parents[1]
base=json.loads((EV/'reports/runtime-dry-v12.json').read_text(encoding='utf8'))
preview=json.loads((EV/'reports/runtime-dry-preview.json').read_text(encoding='utf8'))
ref=json.loads((EV/'reports/runtime-height-reference.json').read_text(encoding='utf8'))
checks={}
samples=[]
for i,p in enumerate(ref):
    old=base['heights_and_time'][i]
    new=preview['heights_and_time'][i]
    checks[f'v12_sample_{i}']=old['ok']==1 and abs(old['y']-p['v12_y'])<1e-4
    checks[f'preview_sample_{i}']=new['ok']==1 and abs(new['y']-p['preview_y'])<1e-4
    checks[f'stale_v12_rejected_{i}']=abs(old['y']-p['preview_y'])>.9
    samples.append({**p,'v12_engine_y':old['y'],'preview_engine_y':new['y'],'engine_delta_m':new['y']-old['y']})
for k in ['camera','low_camera']:
    checks[k+'_matrix_same']=base[k]['camera']['matrix']==preview[k]['camera']['matrix']
for k in ['frame','low_frame']:
    dims=lambda d:(d[k]['effective_surface']['native_width'],d[k]['effective_surface']['native_height'])
    checks[k+'_viewport_same']=dims(base)==dims(preview)==(1920,1080)
noon={'year':2026,'month':10,'day':2,'hour':12,'minute':0}
checks['fixed_clock_samples']=all(d['heights_and_time'][2]['world_time']==noon and d['end_time']['world_time']==noon for d in [base,preview])
checks['orderly_close']=all(d['close']['graceful'] and d['close']['run_retired'] for d in [base,preview])
assert all(checks.values()), checks
report={'status':'PASS_DEPLOYED_HEIGHT_AND_MATCHED_POSE_ONLY','checks':checks,'samples':samples,'limits':['Two changed terrain samples do not certify the whole map.', 'FOV request identical; camera_get returns zero, so native FOV readback is unavailable.', 'Visual improvement is moderate with a 1m cap; no user acceptance implied.', 'Boat navigation, navmesh, shore candidates and all-distance material acceptance remain open.']}
(EV/'reports/runtime-comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
fig,axs=plt.subplots(2,2,figsize=(15,9),layout='constrained')
for row,k in enumerate(['frame','low_frame']):
    for col,(d,label) in enumerate([(base,'V12'),(preview,'Preview · smoothing 18 m')]):
        im=np.asarray(Image.open(d[k]['fullres_path']))
        # Identical crop; removes excess sky and a Steam toast below y=1000.
        axs[row,col].imshow(im[240:970,:]);axs[row,col].set_axis_off()
        axs[row,col].set_title(label+(' · vista alta' if row==0 else ' · vista de ladera'))
fig.suptitle('Comparación en DayZ · cámara, viewport y mediodía iguales\nCambio acotado a 1 m; las dos alturas leídas en motor coinciden exactamente con los candidatos',fontsize=15)
fig.savefig(EV/'figures/relieve-en-dayz.png',dpi=135);plt.close(fig)
print(json.dumps(report,indent=2))
