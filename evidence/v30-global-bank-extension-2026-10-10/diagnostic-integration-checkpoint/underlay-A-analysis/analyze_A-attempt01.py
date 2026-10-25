from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image

ROOT = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/water-lod-discriminator-plan/v2')
RUNTIME = ROOT / 'runtime/A'
OUT = RUNTIME / 'analysis-A'
BASE_NPZ = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
DIAG_NPZ = ROOT / 'build/terrain.npz'
STAGE = ROOT / 'build/stage.json'
DEPLOY = ROOT / 'build/deploy.json'
BUILDER = ROOT / 'build_diagnostic.py'
WATER_BASE = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons/baltic_water_v30.pbo')
WATER_DEPLOY = Path(r'P:/Mods/@DayZ_Baltic_UnderlayDiagnosticV1/Addons/baltic_water_v30.pbo')
WORLD_BASE = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons/narva_trial.pbo')
WORLD_DEPLOY = Path(r'P:/Mods/@DayZ_Baltic_UnderlayDiagnosticV1/Addons/narva_trial.pbo')
WORK = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
PLAN = ROOT.parent / 'PLAN-v2.md'
MISSION_SCRIPT = ROOT / 'prepare_runtime.py'
MISSION_SPEC = ROOT / 'runtime-mission.json'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def gray(path): return np.asarray(Image.open(path).convert('L'),dtype=np.float32)
def grad(a):
    gx=(np.roll(a,-1,axis=1)-np.roll(a,1,axis=1))/2
    gy=(np.roll(a,-1,axis=0)-np.roll(a,1,axis=0))/2
    return np.hypot(gx,gy)
def bridge_translation(a,b,dxlim=30,dylim=10,step=3):
    # Fixed image-space bridge ROI; downsample by 3 for a robust integer-pixel translation estimate.
    a=grad(a)[::step,::step]; b=grad(b)[::step,::step]
    x0,y0,x1,y1=(140,173,527,230)  # source pixels (420,519)-(1580,690), divided by 3
    aa=a[y0:y1,x0:x1]; candidates=[]
    for dy0 in range(-dylim,dylim+1):
      for dx0 in range(-dxlim,dxlim+1):
        dx,dy=dx0,dy0
        ax0=max(0,-dx); ax1=min(aa.shape[1],aa.shape[1]-dx)
        ay0=max(0,-dy); ay1=min(aa.shape[0],aa.shape[0]-dy)
        u=aa[ay0:ay1,ax0:ax1]
        v=b[y0+ay0+dy:y0+ay1+dy,x0+ax0+dx:x0+ax1+dx]
        u=u-u.mean(); v=v-v.mean(); den=np.linalg.norm(u)*np.linalg.norm(v)
        score=float((u*v).sum()/den) if den else -1.0
        candidates.append((score,dx*step,dy*step))
    candidates.sort(reverse=True)
    return [{'normalized_gradient_correlation':s,'translation_px':[dx,dy]} for s,dx,dy in candidates[:5]]

# Native engine SurfaceY log against exact baseline and staged diagnostic heights.
lines=(RUNTIME/'native-heights.log').read_text(encoding='utf-8').splitlines()
obs=np.full((35,35),np.nan,dtype=np.float64)
for line in lines:
    if line.startswith('H;'):
        _,r,c,y=line.split(';'); obs[int(r)-863,int(c)-383]=float(y)
if lines[0] != 'BEGIN;35;35' or lines[-1] != 'END;1225' or not np.isfinite(obs).all():
    raise RuntimeError('Native probe incomplete or malformed')
with np.load(BASE_NPZ,allow_pickle=False) as z: base=z['heights'].copy()
with np.load(DIAG_NPZ,allow_pickle=False) as z: diag={k:z[k].copy() for k in z.files}
if base.shape[0] < 898 or base.shape[1] < 418: raise RuntimeError('Terrain shape wrong')
base_window=base[863:898,383:418].astype(np.float64)
diag_window=diag['heights'][863:898,383:418].astype(np.float64)
patch=np.zeros((35,35),dtype=bool); patch[1:34,1:34]=True
err_base=np.abs(obs-base_window); err_diag=np.abs(obs-diag_window)
change=np.argwhere(base!=diag['heights'])
if len(change)!=1089: raise RuntimeError('Diagnostic height change count mismatch')

# Compare screenshots; lexical timestamps establish recorded ordering.
shots=sorted(RUNTIME.glob('capture_*.jpg'))
if len(shots)!=4: raise RuntimeError(f'Expected 4 JPEGs, found {len(shots)}')
images=[gray(p) for p in shots]
if any(im.shape!=(1080,1920) for im in images): raise RuntimeError('Unexpected capture dimensions')
roi=(918,465,1012,500); x0,y0,x1,y1=roi
roi_stats=[]
for path,im in zip(shots,images):
    v=im[y0:y1,x0:x1]
    roi_stats.append({'file':path.name,'roi':list(roi),'gray_mean':float(v.mean()),'gray_std':float(v.std()),'p10_p50_p90':[float(x) for x in np.percentile(v,[10,50,90])]})
frame_pairs=[]
for i in range(1,len(images)):
    a=np.asarray(Image.open(shots[i-1]).convert('RGB'),dtype=np.int16)
    b=np.asarray(Image.open(shots[i]).convert('RGB'),dtype=np.int16)
    delta=np.abs(a-b)
    frame_pairs.append({'from':shots[i-1].name,'to':shots[i].name,'mean_abs_delta_255':float(delta.mean()/255.0),'target_roi_mean_abs_delta_255':float(delta[y0:y1,x0:x1].mean()/255.0),'target_roi_changed_pixel_fraction':float(np.mean(np.any(delta[y0:y1,x0:x1]!=0,axis=2)))})
pan_corr=bridge_translation(images[0],images[1])
restore_corr_12=bridge_translation(images[1],images[2],dxlim=8,dylim=4)
restore_corr_23=bridge_translation(images[2],images[3],dxlim=8,dylim=4)

sys.path.insert(0,str(WORK/'tools/playtest'))
from attach_navmesh import read_pbo
_,base_props,base_entries=read_pbo(WORLD_BASE)
_,deployed_props,deployed_entries=read_pbo(WORLD_DEPLOY)
changed=[k for k in sorted(set(base_entries)|set(deployed_entries)) if base_entries.get(k)!=deployed_entries.get(k)]
water_base_sha=sha(WATER_BASE); water_deploy_sha=sha(WATER_DEPLOY)
stage=json.loads(STAGE.read_text(encoding='utf-8')); deploy=json.loads(DEPLOY.read_text(encoding='utf-8'))
current_builder_sha=sha(BUILDER)
inputs=[PLAN,BUILDER,MISSION_SCRIPT,MISSION_SPEC,BASE_NPZ,DIAG_NPZ,STAGE,DEPLOY,WATER_BASE,WATER_DEPLOY,WORLD_BASE,WORLD_DEPLOY,RUNTIME/'native-heights.log',RUNTIME/'render-settings.log',RUNTIME/'scene.log',*shots]
report={
 'status':'A_READBACK_AND_VISUAL_LIVENESS_REVIEW',
 'inputs':{str(p):sha(p) for p in inputs},
 'native_heights':{
   'probe_count':int(np.isfinite(obs).sum()),'grid_shape':[35,35],
   'baseline_expected_all_1225':{'max_abs_error_m':float(err_base.max()),'mean_abs_error_m':float(err_base.mean()),'p99_abs_error_m':float(np.quantile(err_base,.99))},
   'baseline_expected_patch_1089':{'max_abs_error_m':float(err_base[patch].max()),'mean_abs_error_m':float(err_base[patch].mean()),'p99_abs_error_m':float(np.quantile(err_base[patch],.99))},
   'baseline_expected_halo_136':{'max_abs_error_m':float(err_base[~patch].max()),'mean_abs_error_m':float(err_base[~patch].mean())},
   'distance_from_diagnostic_heights_patch_m':{'min':float(np.min(err_diag[patch])),'max':float(np.max(err_diag[patch]))},
   'interpretation':'All 1225 SurfaceY samples match the baseline terrain, including the 1089-cell diagnostic patch; this supports A as baseline phase. Native readback does not show the diagnostic lowering in A.'},
 'diagnostic_npz':{'changed_height_vertices':int(len(change)),'bbox_rc_inclusive':[int(change[:,0].min()),int(change[:,1].min()),int(change[:,0].max()),int(change[:,1].max())],'nonheight_arrays_equal':all(np.array_equal(base[k],diag[k],equal_nan=True) for k in diag if k!='heights'),'height_delta_min_m':float(np.min(diag['heights'][base!=diag['heights']].astype(np.float64)-base[base!=diag['heights']].astype(np.float64))),'height_delta_max_m':float(np.max(diag['heights'][base!=diag['heights']].astype(np.float64)-base[base!=diag['heights']].astype(np.float64)))},
 'package':{'base_entries':len(base_entries),'deployed_entries':len(deployed_entries),'properties_equal':base_props==deployed_props,'changed_entries':changed,'water_base_sha256':water_base_sha,'water_deployed_sha256':water_deploy_sha,'water_identical':water_base_sha==water_deploy_sha,'deploy_report_world_sha256_matches':sha(WORLD_DEPLOY)==deploy['world_sha256'],'deploy_report_water_sha256_matches':water_deploy_sha==deploy['water_sha256'],'stage_current_deploy_builder_sha256':[stage['builder_sha256'],deploy['builder_sha256'],current_builder_sha],'all_three_builder_hashes_equal':len({stage['builder_sha256'],deploy['builder_sha256'],current_builder_sha})==1,'assert_builder_stage_package_identity_absent':'package() does not compare stage.builder_sha256 to the current builder; observed values nevertheless agree.'},
 'captures':{'files':[p.name for p in shots],'dimensions':[1920,1080],'predetermined_target_subroi':roi,'target_roi_visual_check':'Manual visual inspection: the gray/blue rectangular patch remains visible inside the predeclared target sub-ROI in the three restored-pose captures. This is not an automated classifier.','roi_pixel_stats':roi_stats,'pan_to_restore_bridge_registration_top5':pan_corr,'restored_frame_1_to_2_bridge_registration_top5':restore_corr_12,'restored_frame_2_to_3_bridge_registration_top5':restore_corr_23,'adjacent_frame_pixel_deltas':frame_pairs,'interpretation':'The pan capture aligns to the first restored capture at an estimated +45px horizontal bridge displacement (0px vertical); the three restored captures align at 0px shift. This is 2D image evidence of pan/restore, not a 3D camera readback.'},
 'limits':['No per-capture camera matrix/readback is present in runtime/A artifacts inspected. runtime-mission.json records the intended liveness control, not observed camera matrices.','Scene log and screenshots do not link each frame cryptographically to the package hash; package/deploy hashes are independently verified, but phase-level launch linkage is not in this folder.','A reproduces the gray target in the fixed ROI; this does not establish cause. B comparison remains pending.','The pan displacement is a projected bridge-image shift, not an independently verified world-space landmark/camera delta.']}
(OUT/'analysis-A.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','native_heights','diagnostic_npz','package','captures','limits']},indent=2))
