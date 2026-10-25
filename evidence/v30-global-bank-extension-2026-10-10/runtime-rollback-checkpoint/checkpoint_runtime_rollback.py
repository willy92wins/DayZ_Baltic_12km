from pathlib import Path
import hashlib,json,shutil
G=Path(__file__).resolve().parent
R=G.parent
P=G/'global-operator-prototype'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OUT=W/'evidence/v30-global-bank-extension-2026-10-10/runtime-rollback-checkpoint'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
groups={
'recovery':(P/'global-dry-rollback-frozen-recovery',['PLAN.md','rollback_core.py','rollback_once.py','test_rollback_core.py','test_rollback_once_fixture.py','fixture-report.json','independent-review.json','recovery-provenance.json','run-01/receipt.json']),
'anomalies':(G/'build-wide-slope/anomaly-classification',['classification.json','classification.csv','README.md']),
'subcell':(G/'build-wide-slope/subcell-flag-probe',['PLAN.md','prepare_points.py','selection.json','probe-manifest.json','native-probe-lint.json','mission/BalticEV95SubcellFlagsV1.BalticTrial/init.c','mission/BalticEV95SubcellFlagsV1.BalticTrial/points.csv','prepare_compile_safe_v2.py','runtime-v2/preparation.json','runtime-v2/lint.json','runtime-v2/stage.json','runtime-v2/runtime-receipt.json','runtime-v2/native-snapshot.log','runtime-v2/BalticEV95SubcellFlagsV2.BalticTrial/init.c','runtime-v2/BalticEV95SubcellFlagsV2.BalticTrial/points.csv']),
'shadow-v4':(R/'v30-water-render-discriminator-20261010/shadow-runtime-plan/v4-probe',['PLAN.md','preparation.json','package_probe.py','prepare_ids.py','package-receipt.json','lint-root.json','baltic_shadow_probe_v4/config.cpp','baltic_shadow_probe_v4/scripts/5_Mission/BalticShadowProbeV4.c','runtime/diag-registry-crosswalk.json','runtime/probe.log','runtime/runtime-receipt.json','runtime/analysis/compare_captures.py','runtime/analysis/pixel-difference-analysis.json','runtime/analysis/runtime-difference-review.md']),
'remaining':(G/'G/base10-remaining-audit',['base10-remaining-audit.md','evidence.json'])
}
for folder,files in groups.values():
 for name in files:
  if not (folder/name).is_file():raise FileNotFoundError(folder/name)
OUT.mkdir(parents=True,exist_ok=False)
records=[]
for prefix,(folder,files) in groups.items():
 for name in files:
  src=folder/name;dst=OUT/prefix/name;digest=sha(src)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  assert sha(src)==digest and sha(dst)==digest
  records.append({'source':str(src),'copy':str(dst.relative_to(OUT)),'sha256':digest,'bytes':src.stat().st_size})
refs=[]
sources=[P/'global-dry-rollback-frozen-recovery/run-01/candidate-terrain.npz']
sources+=sorted((R/'v30-water-render-discriminator-20261010/shadow-runtime-plan/v4-probe/runtime').glob('capture_*.jpg'))
for src in sources:refs.append({'path':str(src),'sha256':sha(src),'bytes':src.stat().st_size})
(OUT/'manifest.json').write_text(json.dumps({'copied':records,'external':refs},indent=2)+'\n',encoding='utf-8')
(OUT/'README.md').write_text("""# Recovery candidate and isolated runtime evidence

No BASE 1.0 acceptance or terrain promotion. The frozen recovery produced candidate 1bd6b67d with 2,502,853 changed dry vertices and original objective 69,217.203→68,784.240. Author D8/face/new-30 checks pass; the complete independent consumer is separate and still pending.

V4 shadow probe compiled and completed run 2f277c6b with setting 160 at 0→1→0, control 163 unchanged, restoration read back, then orderly close and lease release. Rectangles remain visible, but weak temporal activity and absence of a confirmed positive shadow control prevent causal exclusion. The independent pixel review keeps this INCONCLUSIVE.

EV95 subcell run 1afd534d executed 279 points × 7 phases (1,953 readings,30.012 seconds), then orderly close and release. Source v2 only splits seven long log expressions, preserving v1 and sampling logic. Its 11 anomaly centers and four controls are bound to the prior compiled-face classification. Interpretation of the new snapshot is separate; the snapshot alone does not close gaps or dynamic-water defects.

All copied artifacts are byte-exact; big terrain and images remain external SHA-pinned references. No push.
""",encoding='utf-8')
shutil.copyfile(Path(__file__),OUT/Path(__file__).name)
print(json.dumps({'copies':len(records),'references':len(refs),'out':str(OUT)}))

