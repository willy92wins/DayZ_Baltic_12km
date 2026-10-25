"""Pixel-preserving crop contact sheet for the one calibrated A/B/A experiment."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
E=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-global-water-risk-2026-10-09')
phases=['medium-before','extreme','extreme-settled','medium-return','medium-return-settled']
canvas=Image.new('RGB',(600,180*len(phases)),(245,245,245));draw=ImageDraw.Draw(canvas);manifest=[]
for i,phase in enumerate(phases):
 p=next((B/'terrain-detail'/phase).glob('*.jpg'));im=Image.open(p)
 assert im.size==(1920,1080),im.size
 roi=im.crop((240,60,420,130))
 draw.text((8,i*180+6),phase,fill=(0,0,0));canvas.paste(roi.resize((540,140),Image.Resampling.NEAREST),(8,i*180+29))
 manifest.append(dict(phase=phase,file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),roi=[240,60,420,130]))
canvas.save(B/'terrain-detail/registered-roi.png')
(E/'terrain-detail-frames.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(str(B/'terrain-detail/registered-roi.png'))
