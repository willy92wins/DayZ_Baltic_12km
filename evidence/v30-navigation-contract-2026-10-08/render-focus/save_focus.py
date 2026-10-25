"""Freeze observed focus/render evidence without changing captures or the game."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
from datetime import datetime
import numpy as np
from PIL import Image

W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B = Path(r'E:/DayZ-Baltic-Build/v30-navigation-contract-20261008')
E = W/'evidence/v30-navigation-contract-2026-10-08/render-focus'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(s, d):
    assert not d.exists(), d
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(s, d)
    assert sha(s) == sha(d)
    return {'source': str(s), 'saved': str(d.relative_to(E)), 'sha256': sha(d)}
record=json.loads((E/'record.json').read_text())
files=[]
for name, cap in record['captures'].items():
    if name in ('focusNear','focusNearCamera'): continue
    files.append(copy(Path(cap['fullres_path']), E/'views'/(name+'.jpg')))
spans={}
for folder in ('focus-probe','focus-probe2'):
    files.append(copy(B/folder/'log.csv', E/(folder+'.csv')))
    rows=[r for r in csv.DictReader((B/folder/'log.csv').open()) if r.get('file')]
    intervals=[]
    for r in rows:
        if not intervals or intervals[-1]['focused'] != (r['focused']=='True'):
            intervals.append(dict(start=r['time'],end=r['time'],focused=r['focused']=='True',samples=1))
        else:
            intervals[-1]['end']=r['time']; intervals[-1]['samples']+=1
    spans[folder]=intervals
rows=[r for r in csv.DictReader((B/'focus-probe2/log.csv').open()) if r.get('file')]
selected=[r for r in rows if '12:51:17'<=r['time']<='12:51:34']
pixels=[]
for r in selected:
    p=B/'focus-probe2'/r['file']
    a=np.asarray(Image.open(p).convert('RGB'), dtype=float)[360:510,120:220]
    pixels.append(dict(time=r['time'],focused=r['focused']=='True',mean_rgb=a.mean((0,1)).tolist(),
                       green_exceeds_blue_2=float((a[:,:,1]>a[:,:,2]+2).mean())))
    if r['time'].startswith(('12:51:20','12:51:21','12:51:22','12:51:27','12:51:32')):
        files.append(copy(p,E/'transition'/p.name))
cams=record['cameras']
assert cams['focusFixedSet']['camera']['matrix']==cams['focusFixedAfterCamera']['camera']['matrix']
assert cams['focusReserveSet']['camera']['matrix']==cams['focusReserveForegroundCamera']['camera']['matrix']
assert record['close']['graceful'] and record['close']['run_retired']
assert record['final']==dict(owner=None,occupied=False,runs=[],pending_commands=0)
files.append(copy(Path(r'P:/DayZ_MCP_dev/_client/profiles/DayZDiag_x64_2026-10-08_12-43-35.RPT'),E/'client.RPT'))
result={
 'status':'FOCUS_ASSOCIATED_RECOVERY_OBSERVED_NOT_NATIVE_CAUSE_ISOLATED',
 'actual_focus_intervals':spans,
 'fixed_camera_exact':True,
 'last_unfocused_grey':'12:51:20.552',
 'first_focused_textured':'12:51:21.574',
 'sampling_interval_seconds':1.022,
 'reserve_first_capture':'12:48:59.427',
 'partial_background_load_capture':'12:50:07.353',
 'resident_fixed_captures_seconds':68.546,
 'roi_half_size_window_xyxy':[120,360,220,510],
 'roi_purpose':'Descriptive change measurement only, not texture-residency acceptance',
 'roi_measurements':pixels,
 'limits':[
  'Native mechanism and full-engine correction not demonstrated.',
  'Background does load some tiles; foreground is not a necessary condition for all loading.',
  'Foreground was intermittent after the first seven samples, not a continuous 20-second hold.',
  'Initial client launch was already focused; no same-run unfocused-startup control.',
  'Reserve view shows the sampled sector only, not visual acceptance of the whole reserve.',
  'Record contains FOV setter echo, not a trustworthy native FOV readback.',
  'Focus probe gap 12:47:01.590 to 12:47:34.865 is explicit; no focus inferred in that gap.'
 ],
 'files':files,
}
(E/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','fixed_camera_exact','last_unfocused_grey','first_focused_textured','sampling_interval_seconds')}))
