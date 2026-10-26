from pathlib import Path
import gzip,json,hashlib
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/restart-continuation-20261026'
E.mkdir(parents=True,exist_ok=True)
def save(src,name,compress=False):
 src=Path(src);assert src.is_file(),src
 raw=src.read_bytes();data=gzip.compress(raw,mtime=0) if compress else raw
 p=E/(name+'.gz' if compress else name);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==data,('Refuse overwriting evidence',p)
 else:p.write_bytes(data)
def small_folder(name,target):
 for p in sorted((R/name).iterdir()):
  if p.is_file() and p.suffix in ('.json','.jsonl','.log','.md') and p.stat().st_size<2000000:
   if p.name=='review-response.json' and p.stat().st_size==0:continue
   save(p,target+'/'+p.name)
for folder,dest in [('nav-c-data-preparation-20261026','nav/startup-rejected'),('nav-c-data-preparation-v2-20261026','nav/c-failed'),('nav-c-data-preparation-v2-20261026/observer','nav/c-failed/observer'),('c-nav-exit-diagnostic-20261026','nav/exit-diagnostic'),('nav-c-plan-review-v2','reviews/nav-plan'),('nav-c-code-review','reviews/nav-code'),('nav-c-postprocess-review','reviews/nav-postprocess'),('restart-final-review','reviews/final'),('river-kit7-a-run-20261026','rivers/kit7/diagnostics'),('river-kit7-saved-review-run-20261026','rivers/kit7/saved-review-process'),('river-kit7-saved-review-20261026','rivers/kit7/saved-review'),('river-kit7-visible-run-20261026','rivers/kit7/visible-review-process'),('patch-nav-c45','nav/c45-prepared')]:
 small_folder(folder,dest)
small_folder('restart-final-tests-20261026','tests')
for name in ['recovery.json','preflight.stdout.log','preflight.stderr.log','observer-tests.log','coordinator-control-flow.json']:
 save(R/'restart-recovery-20261026'/name,'recovery/'+name)
for name in ['tests229.json','tests229.stdout.log','tests229.stderr.log','windows-events.json','rpt-analysis.json','clock-binding-historical-control.json','retained-handle-smoke.json','shell-environment-discriminator.json','shell-environment-discriminator-v2.json']:
 save(R/'f-nav-exit-diagnostic-20261026'/name,'prior-F-diagnostic/'+name)
save(R/'f-nav-exit-diagnostic-20261026/query-scope.json','nav/query-scope.json')
save(R/'navmesh-c-v9-20261026/generation.json','nav/c-failed/generation.json')
save(R/'navmesh-c-v9-20261026/generator.stderr.log','nav/c-failed/generator.stderr.log',True)
for site in ['kit-7','10.0-0','38.0-0']:
 for n in ['bounds.npz','report.json']:save(R/'river-bounds-next-20261026'/site/n,'rivers/bounds/'+site+'/'+n)
for n in ['author-report.json','kit-7-surfaces.npz','visible-relief-review.json','visible-native-creases.csv']:
 save(R/'river-kit7-a-on-f-20261026'/n,'rivers/kit7/'+n)
save(R/'river-kit7-saved-review-20261026/pilot-preview.png','figures/kit7-pilot.png')
save(R/'river-kit7-candidate-plan.md','rivers/kit7/initial-plan-before-scope-correction.md')
for n in ['init.c','queries.csv']:
 save(Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticPatchNavC45.BalticTrial')/n,'nav/c45-prepared/mission/'+n)
sources=['recover_post_reboot_preflight.py','orchestrate_nav_c_generation.js','orchestrate_nav_c_generation_v2.js','test_nav_c_coordinator.cjs','record_nav_c_event.ps1','diagnose_c_nav_shutdown.py','prepare_c45_exact_queries.py','package_and_deploy_c_nav9.py','finish_c45_probe.py','orchestrate_c45_probe.js','test_c45_command_completion.cjs','accept_nav_c_postprocess_review.py','diagnose_next_river_bounds.py','run_river_kit7_candidate.py','audit_kit7_native_guards.py','diagnose_kit7_t_envelope.py','audit_kit7_layers_and_cover.py','run_kit7_saved_mesh_review.py','run_kit7_visible_review.py','run_restart_final_review.py','checkpoint_restart_continuation.py']
sources.append('run_restart_final_tests.py')
for n in sources:save(R/n,'source/'+n);save(R/n,'executed-source/'+n,True)
for n in ['tools/navigation/observe_owned_server_exit.ps1','tests/test_server_exit_observer.py','plans/ev112-c-navmesh-observed-generation-20261026.md','tools/water/continuous_stream_pilot_v31.py','tools/water/review_continuous_stream_pilot_v31.py','tools/terrain/review_visible_pilot_relief_v31.py']:
 save(W/n,'executed-source/'+n,True)
save(R/'nav-c-postprocess-review/tested-command-function.js','reviews/nav-postprocess/tested-command-function.js')
save(R/'c-nav-exit-diagnostic-20261026/read_shutdown_events.ps1','source/read_c_shutdown_events.ps1')
manifest={str(p.relative_to(E)).replace('\\','/'):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()),path=str(E))))
