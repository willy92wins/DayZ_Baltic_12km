from pathlib import Path
import json,hashlib
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'road-c1b-plan-review-20261029';D.mkdir(exist_ok=False)
plan=W/'plans/ev112-road-c1b-isolated-stage-20261029.md'
raw=plan.read_bytes();(D/'plan-reviewed.md').write_bytes(raw)
cfg=R/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/config.cpp'
cb=cfg.read_bytes()
brief='''REVISOR independiente Muse Wonder1.0, CLI nativo. SOLO lectura de esta capsula, sin herramientas, codigo ni archivos. Codex planner/integrator y executor local explicitamente asignado al corte si se aprueba. Revisar el plan concreto antes de implementarlo: seguridad/rutas/contrato/cotas/dos ramas/consumidor. No repetir council ni investigacion. Presupuesto dictamen180s, max1200palabras. Entrega final SOUND / SOUND-with-fixes / NEEDS-WORK, hallazgos concretos con ancla y correccion, limites. No exigir certificacion de compilacion para una copia por bytes que declara build_ready=false. Si alcance imposible explica mecanismo. No inventes APIs ni lectura de binarios. Esta capsula no contiene geometria vanilla.\n\nPLAN:\n'''+raw.decode('utf-8')+'\n\nCONFIG HISTORICO PROPIO (se propone literal nuevo, no editar original):\n'+''.join(f'{i}: {l}\n' for i,l in enumerate(cb.decode('utf-8').splitlines(),1))
brief+='\nHECHOS GUARDADOS: C1A1 4775RVMAT 10052971B;2048PNG metadata140323829B;8PAA metadata40711646B. B4A3 8assets+4leaves, virtual_path y SHA individuales. Core metadata observada este turno:58entradas/41files/9717421B; no reparse observado. No identidades de payload PNG/PAA/core todavia; se fijan en contrato antes del codigo. Dos stages unas450MB previstos, cap1GiB. Referencias OutsideTerrain son outside_sat_co.paa y cp_grass_nopx.paa/cp_grass_ca.paa; midDetail middle_sat_mco.paa; lista exacta se extrae de config historico, no basename. Plan dice dos texturas exteriores de addon mas cuatroRVMAT, las otras PAA pueden estar en8PAA; requerir reconciliacion exacta. P:/DZ puede tener junctions historicos: guardas deben fallar sin asumir la causa, sin tocarP:.\n'
(D/'brief.md').write_text(brief,encoding='utf-8')
exe='C:/Users/guill/AppData/Local/Programs/muse/muse-bin-1.4.14-R7309.1.exe'
job={'id':'road-c1b-plan','command':[exe,'exec','--json','--model','muse-wonder-1.0','--contributor-mode','off','--reasoning-effort','high','--workspace',str(R/'council-expanded-20261029'),'--disable-write','--disable-shell','--disable-web-tools','--disable-reminders','--disable-request-user-input','--no-foreign-personal-context','--no-session-log','--max-model-steps','4','--prompt-file',str(D/'brief.md')],'cwd':str(W),'out':str(D/'native'),'seconds':180,'max_bytes':2*1024**3,'input_file':str(D/'brief.md')}
(D/'job.json').write_text(json.dumps({'parallel':1,'jobs':[job]},indent=2),encoding='utf-8')
(D/'pins.json').write_text(json.dumps({str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in [plan,cfg,D/'brief.md',Path(exe)]},indent=2),encoding='utf-8')
print(D)
