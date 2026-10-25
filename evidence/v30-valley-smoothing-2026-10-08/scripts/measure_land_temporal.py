"""Image-data diagnostic, not a visual acceptance test: same-camera temporal energy."""
from pathlib import Path
import json,numpy as np
from PIL import Image
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
E=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-valley-smoothing-2026-10-08')
groups={'baseline':list((B/'land160-visual/baseline-loaded').glob('*.jpg')),'land160':list((B/'land160-visual/land160-loaded').glob('*.jpg')),'land180':list((B/'land180-visual/loaded').glob('*.jpg'))+list((B/'land180-visual/initial').glob('*.jpg'))}
rois={'west_field':[130,400,500,800],'east_field':[1020,310,1250,590],'river_positive_control':[945,500,970,570],'static_field_control':[1460,780,1630,890]}
report={}
for group,files in groups.items():
    stack=np.array([np.asarray(Image.open(p).convert('RGB'),dtype=np.float32).mean(axis=2) for p in sorted(files)])
    assert stack.shape[1:]==(1080,1920)
    report[group]=dict(frames=len(files),files=[str(p) for p in sorted(files)],regions={})
    for name,(x0,y0,x1,y1) in rois.items():
        a=stack[:,y0:y1,x0:x1];span=np.ptp(a,axis=0)
        report[group]['regions'][name]=dict(median_span=float(np.median(span)),p95_span=float(np.percentile(span,95)),p99_span=float(np.percentile(span,99)),share_span_over12=float(np.mean(span>12)))
out=dict(status='DIAGNOSTIC_ONLY',rois_pixels_xyxy=rois,groups=report,limits=['Temporal pixel variation is not a semantic water detector. Unequal sampling times and JPEG noise prevent a universal PASS threshold.','All included frames have loaded terrain and the same R1_far matrix. River ROI is a positive live-render control.'])
(E/'land-temporal-image-data.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v['regions'] for k,v in report.items()},indent=2))
