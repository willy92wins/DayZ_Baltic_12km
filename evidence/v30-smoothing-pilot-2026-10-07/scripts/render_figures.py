"""Read-only figure of native engine captures; no synthetic terrain imagery.

The texture metric is diagnostic local contrast in a documented visible land ROI,
not an acceptance score or a measurement of all distance bands.
"""
from pathlib import Path
import json
import csv
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

W=Path(__file__).resolve().parents[3]
EV=W/'evidence/v30-smoothing-pilot-2026-10-07'
B=Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007/runtime-v12')
captures=[('nav85','21:29:29 · llegada'),('nav85-unfocused-5min','21:33:47 · +4 min 18 s'),('nav85-unfocused-10min','21:38:25 · +8 min 56 s')]
fig,axs=plt.subplots(1,3,figsize=(16,4.6),layout='constrained')
report=[]
for ax,(folder,label) in zip(axs,captures):
    path=sorted((B/folder).glob('capture_*.jpg'))[-1]
    rgb=np.asarray(Image.open(path))
    height,width=rgb.shape[:2]
    # Fixed crop removes the overlay/sky. The full native files remain on E:.
    crop=rgb[int(height*.45):,:]
    ax.imshow(crop);ax.set_title(label);ax.set_axis_off()
    roi=rgb[int(height*.65):int(height*.92),int(width*.55):int(width*.85)].astype(float).mean(2)
    dx=np.diff(roi,axis=1);dy=np.diff(roi,axis=0)
    report.append({'path':str(path),'label':label,'width':width,'height':height,'roi_fraction_xyxy':[.55,.65,.85,.92],'diagnostic_mean_absolute_adjacent_pixel_delta':float((np.abs(dx).mean()+np.abs(dy).mean())/2)})
fig.suptitle('V12 · misma cámara · carga parcial de teselas sin foco registrado\nCapturas del motor; recorte de tierra. BALTIC-019 sigue abierto.',fontsize=15)
fig.savefig(EV/'figures/render-v12-unfocused.png',dpi=145);plt.close(fig)
focus=[]
for folder in ['focus-nav85','focus-nav85-retry']:
    with (B/folder/'log.csv').open() as f:
        rows=[r for r in csv.DictReader(f) if r.get('focused') in ('True','False')]
    focus.append({'folder':folder,'samples':len(rows),'focused_samples':sum(r['focused']=='True' for r in rows),'first':rows[0]['time'],'last':rows[-1]['time']})
(EV/'reports/render-v12-unfocused.json').write_text(json.dumps({'captures':report,'focus':focus,'status':'PARTIAL_TEXTURE_LOADING_OBSERVED_BACKGROUND; FOCUS_CAUSAL_TEST_INCONCLUSIVE','continuous_probe_frames':['figures/focus-213421_508_U.jpg','figures/focus-213825_380_U.jpg'],'limits':['Clock progressed from noon; geometry and camera fixed.', 'Some texture loading without focus does not prove focus has no effect.', 'Diagnostic ROI selected on visible dry ground; no near/mid/far acceptance.', 'Focus sampling gap21:32:23-21:34:21; the continuous second interval brackets gray and textured frames with593 unfocused samples.']},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'captures':report,'focus':focus},indent=2))
