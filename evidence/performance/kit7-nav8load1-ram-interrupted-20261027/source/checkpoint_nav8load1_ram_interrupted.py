from pathlib import Path
import hashlib,json,datetime,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav8load1-ram-ab-20261027';E=W/'evidence/performance/kit7-nav8load1-ram-interrupted-20261027'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,name):
 target=E/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
assert not E.exists() and not (D/'comparison.json').exists() and not (D/'block-result.json').exists()
gate=read(D/'accepted.json');assert all(sha(p)==h for p,h in gate['inputs'].items())
assert len(list(D.glob('pass-*')))==3 and len(list((D/'attempt-reservations').glob('*.json')))==3
launch=read(D/'pass-03/launch.json');assert launch['status']=='failed' and launch['run_id'] is None and launch['reason']=='port_in_use_foreign' and not launch['cleanup_degraded']
rows=[]
for n in (1,2):
 p=D/f'pass-{n:02d}';result=read(p/'result.json');clean=read(p/'cleanup.json');assert result['status']=='PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT'
 assert clean['close']['run_retired'] and clean['self']['state']=='none' and not clean['pending_commands'] and not clean['own_run_present'] and not clean['error'] and not clean['cleanup_error']
 rows.append(dict(order=n,run_id=clean['close']['run_id'],world=result['world'],working_set_mib=result['working_set_mib'],private_mib=result['private_mib']))
status=dict(status='INCONCLUSIVE_INTERRUPTED_RAM_BLOCK',acceptance_eligible=False,measured_passes=2,planned_passes=6,refused_pass=3,reason='port_in_use_foreign',launch_run_id=None,completed=rows,native_status='PASS_LOAD1_CONFIG_AND_NATIVE607',retries=0,remaining_passes_executed=False,limits=['No aggregate RAM verdict from two measurements.','No causal comparison with historical Nav8.','Original six-pass block is stopped and cannot resume; a new reviewed plan is required.'])
(D/'block-result.json').write_text(json.dumps(status,indent=2)+'\n')
receipt=dict(source='Observed MCP session_status after refused launch; selected fields only',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),self_state='none',owner=None,pending_commands=0,cleanup_degraded=[],own_run_present=False,queue_position=None,runs=[])
(D/'terminal-coordination-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
E.mkdir(parents=True)
for name in ['block-result.json','terminal-coordination-receipt.json','accepted.json','missions.json','mission-validation.json','joint-gate-controls.json','conditions-controls.json','command-flow-controls.json','coordinator-controls.json']:save(D/name,name)
for p in (D/'attempt-reservations').glob('*.json'):save(p,'attempt-reservations/'+p.name)
for n in (1,2):
 p=D/f'pass-{n:02d}'
 for name in ['result.json','reference.json','run.json','launch.json','host-identity.json','host.jsonl','before.json','spec.json','benchmark-gate.json','cleanup.json','timeline.jsonl','rpt-binding.json','binding.stdout.log','binding.stderr.log','consumer.stdout.log','consumer.stderr.log']:save(p/name,f'pass-{n:02d}/'+name)
 for name in ['attached.json','terminal.json']:save(p/'observer'/name,f'pass-{n:02d}/observer/'+name)
 save(p/read(p/'run.json')['profile_log'],f'pass-{n:02d}/engine.log')
sanitized={k:v for k,v in launch.items() if k not in ('mod','artifacts_paths')};sanitized['redactions']=['External mod names and local profiles directory omitted'];sanitized['raw_sha256']=sha(D/'pass-03/launch.json')
(E/'pass-03').mkdir();(E/'pass-03/launch-redacted.json').write_text(json.dumps(sanitized,indent=2)+'\n')
source_map={}
for i,(path,h) in enumerate(sorted(gate['inputs'].items())):
 name=f'frozen-inputs/{i:03d}-'+Path(path).name;save(Path(path),name);source_map[path]=dict(archive=name,sha256=h)
(E/'frozen-input-map.json').write_text(json.dumps(source_map,indent=2)+'\n')
for folder in ['kit7-nav8load1-ram-review-20261027','kit7-nav8load1-recovery-review-20261027']:
 v=R/folder
 for name in ['adjudication.json','completion.json','source-hashes.json']:save(v/name,'reviews/'+folder+'/'+name)
 (E/'reviews'/folder/'fable-review.md').write_text(read(v/'response.json')['result'],encoding='utf-8')
save(Path(__file__),'source/'+Path(__file__).name)
(E/'README.md').write_text('''# Nav8Load1: bloque RAM interrumpido, sin aceptación

**INCONCLUSIVE_INTERRUPTED_RAM_BLOCK.** Dos mediciones válidas y cerradas,
de las seis planificadas. La tercera no arrancó: MCP informó port_in_use_foreign,
run_id nulo. No se interrumpió ninguna sesión ajena. Después, session_status
confirmó lease propio ausente, cero comandos pendientes y ningún run propio.

Medianas descriptivas, sin comparador de aceptación:
- Baltic: residente4254,57MiB, privada4649,21MiB.
- Chernarus: residente3349,37MiB, privada3733,76MiB.

No se calcula un PASS/FAIL agregado con una sola muestra por mundo. Se conserva
el fallo de admisión y los dos resultados completos. No se ejecutaron pasadas4-6,
no hay repeticiones ni sustitución de una medida. El bloque original queda
cerrado como incompleto; no puede rellenarse posteriormente. Reanudar requiere
un plan revisado y un bloque íntegramente nuevo, conservando estos datos.

Los 80 controles de admisión verifican identidad conjunta, cobertura de fuentes,
hashes de revisión y reservas exclusivas. RAM1,10, dispersión5%, calentamiento30s
y medida120s permanecen. El PASS nativo de configuración y607 no cambia.
Las fuentes exactas usadas se conservan en frozen-inputs y frozen-input-map.json.
No se incluyen nombres de aplicaciones ajenas ni sus snapshots privados.
''',encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()};(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status=status['status'],archived_files=len(manifest))))
