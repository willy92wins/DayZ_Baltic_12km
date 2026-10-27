"""Archive all six measured runs without changing or selecting benchmark data."""
from pathlib import Path
import gzip, hashlib, json, re

R = Path(__file__).parent
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D = R / 'kit7-navv9diag-ram-ab-20261027'
E = W / 'evidence/performance/kit7-navigation-12p5m-diagnostic-ab-20261027'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

assert not E.exists(), 'Fresh evidence directory required'
comparison = load(D / 'comparison.json')
assert comparison['status'] in ('PASS_EMPTY_SERVER_RAM_BUDGET', 'FAIL_EMPTY_SERVER_RAM_BUDGET', 'INCONCLUSIVE')
assert comparison['measurement_repeats'] == 0
assert comparison['acceptance_eligible'] is False and comparison['scope']=='DIAGNOSTIC_ONLY_ORIGINAL_FOUR_HEIGHT_FAILURES_PRESERVED'
assert comparison['order'] == ['BalticTrial', 'ChernarusPlus', 'ChernarusPlus', 'BalticTrial', 'BalticTrial', 'ChernarusPlus']
for name, digest in {**comparison['inputs'], **comparison['validation_sources']}.items():
    assert sha(name) == digest, name
assert len(comparison['inputs']) == 6
terminal=load(D/'session-final.json')
assert terminal['self']['state']=='none' and not any(terminal[k] for k in ('pending_commands','cleanup_degraded','own_runs_remaining'))
for n in range(1, 7):
    p = D / f'pass-{n:02}'
    result = load(p / 'result-revalidated.json')
    assert result['status'] == 'PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT'
    assert result['all_bound_files_rehashed']
    for name, digest in {**result['inputs'], **result['validation_sources']}.items():
        assert sha(name) == digest, name
    clean = load(p / 'cleanup.json')
    assert clean['close']['run_retired'] and clean['self']['state'] == 'none'
    assert not any(clean[k] for k in ('own_run_present', 'pending_commands', 'cleanup_degraded', 'error', 'cleanup_error'))

E.mkdir(parents=True, exist_ok=False)
def save(source, relative):
    raw = source.read_bytes()
    compressed = len(raw) > 250000
    dest = E / (relative + '.gz' if compressed else relative)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(gzip.compress(raw, mtime=0) if compressed else raw)
def write(relative, value):
    p = E / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

for name in ('comparison.json', 'background-activity-summary.json', 'missions.json', 'accepted.json', 'coordinator-controls.json','session-final.json'):
    save(D / name, name)
for n in range(1, 7):
    base = D / f'pass-{n:02}'
    prefix = f'pass-{n:02}/'
    run = load(base / 'run.json')
    for name in ('before.json', 'benchmark-gate.json', 'spec.json', 'timeline.jsonl',
                 'host.jsonl', 'host-identity.json', 'run.json', 'cleanup.json',
                 'rpt-binding.json', 'reference.json', 'result.json', 'result-revalidated.json',
                 'binding.stdout.log', 'binding.stderr.log', 'consumer.stdout.log', 'consumer.stderr.log'):
        save(base / name, prefix + name)
    save(base / run['profile_log'], prefix + run['profile_log'])
    save(Path(run['mission']) / 'init.c', prefix + 'mission/init.c')
    for p in (base / 'observer').rglob('*'):
        if p.is_file() and p.suffix in ('.json', '.jsonl', '.log'):
            save(p, prefix + 'observer/' + p.relative_to(base / 'observer').as_posix())
    launch = load(base / 'launch.json')
    assert launch['status'] == 'succeeded' and launch['run_id'] == run['run_id']
    write(prefix + 'launch-summary.json', dict(status=launch['status'], run_id=run['run_id'],
          raw_sha256=sha(base / 'launch.json'), full_receipt_retained_locally=True,
          arguments=run['launch_arguments']))
    rpt = base / 'server.RPT'
    count = warnings = errors = 0
    terminations = []
    with rpt.open(encoding='utf-8', errors='replace') as f:
        for line in f:
            count += 1
            low = line.lower()
            warnings += int('(w)' in low or 'warning' in low)
            errors += int(any(x in low for x in ('error', 'exception', "can't compile")))
            if 'termination successfully completed' in low:
                terminations.append(line.rstrip())
    write(prefix + 'rpt-summary.json', dict(sha256=sha(rpt), line_count=count,
          warning_lines=warnings, error_or_exception_lines=errors,
          termination_lines=terminations, full_rpt_retained_locally=True))

save(Path(__file__), 'source/' + Path(__file__).name)
save(R/'compare_kit7_ram_block_conditions.py','source/compare_kit7_ram_block_conditions.py')
save(R/'kit7-ram-cross-block-conditions-20261027.json','cross-block-conditions.json')
save(R/'screen_kit7_nav_fine_widths.py','source/screen_kit7_nav_fine_widths.py')
save(R/'kit7-nav-fine-width-diagnostic-20261027/result.json','diagnostics/fine-width-screen.json')
for name in ('setup_navv9diag_ram.py','prepare_navv9diag_ram_files.py','navv9diag_gate.py','prepare_navv9diag_ram_pass.py','finish_navv9diag_ram_pass.py','finalize_navv9diag_ram_ab.py','orchestrate_navv9diag_ram.js','test_navv9diag_gate.py','test_navv9diag_ram_conditions.py','test_navv9diag_ram_flow.cjs','test_navv9diag_ram_command.cjs','review_navv9diag_ram.py','seal_navv9diag_ram.py'):
    save(R/name,'source/'+name)
for name in ('deployment.json','restore.json','mission-validation.json','diagnostic-gate-controls.json','conditions-controls.json','command-flow-controls.json'):
    save(D/name,'preparation/'+name)
for name in ('fable-review.md','adjudication.md','source-hashes.json','completion.json'):
    save(R/'kit7-navv9diag-ram-review-20261027'/name,'review/'+name)
m=comparison['metrics'];ws=m['working_set_mib'];private=m['private_mib']
rows=[]
for key,label in [('working_set_mib','Residente'),('private_mib','Privada')]:
    v=m[key];rows.append(f"|{label}|{v['baltic_median']:.2f}|{v['chernarus_median']:.2f}|{v['ratio']:.6f}|{v['status']}|")
(E/'README.md').write_text(f'''# Control diagnóstico de RAM del kit7 original de 12,5 m

Resultado RAM: **{comparison['status']}**. Elegibilidad funcional: **NO**.
El paquete conserva sus cuatro fallos de altura; esta medición no lo acepta.
Seis pasadas nuevas ABBAAB, tres por mapa, cero repeticiones. Mismos 30 s de
calentamiento y 120 s de medición; presupuesto 1,10 y dispersión 5% intactos.

|Memoria|Baltic MiB|Chernarus MiB|Cociente|Resultado|
|---|---:|---:|---:|---|
'''+ '\n'.join(rows)+'''

Identidades, hashes, cierre oficial y liberación del lease comprobados en cada
pasada. El lector se vuelve a ejecutar sobre las seis capturas antes de
comparar. PBOs originales restaurados exactamente, archivo previo conservado.
No hay generación nueva ni cambio de terreno, modelos, agua o consultas.

Nav8 mantiene 607 PASS con máximo 0,711963 m y FAIL de RAM 1,265913/1,241333.
Nav12 sigue rechazado por tres alturas nuevas y no se midió su RAM.
Un resultado favorable aquí no predice RAM ni aceptación de otra variante.
Un resultado desfavorable tampoco aislaría una causa exclusiva del kit.

Solo servidor vacío, sin CE, AI, jugadores o cliente. CPU descriptiva. No prueba
FPS, VRAM ni capacidad de jugadores. Los RPT completos y nombres de aplicaciones
permanecen privados; se publican sus hashes, resúmenes y evidencia de cierre.
''',encoding='utf-8')
handoff=W/'HANDOFF.md';old=handoff.read_text(encoding='utf-8');new=old
updates={
'updated':'2026-10-27 (Nav8 funcional publicado; Nav12 rechazado; control RAM12,5 completado)',
'performance':f"Control kit7original de 12,5 DIAGNOSTIC_ONLY: {comparison['status']}, seis ABBAAB nuevas,sin repeticiones. Residente {ws['baltic_median']:.2f}/{ws['chernarus_median']:.2f}MiB ratio{ws['ratio']:.6f}; privada {private['baltic_median']:.2f}/{private['chernarus_median']:.2f}MiB ratio{private['ratio']:.6f}. Conserva4FAILaltura. Nav8funcional conservaFAILRAM1.265913/1.241333. SinFPS/capacidad.",
'cleanup':'Los seis runs propios del control RAM12,5 cerrados oficialmente y leases liberados. Generación/sonda Nav12 y Nav8 también cerrados. Automatización anterior PAUSED; siguientes lanzamientos por FIFO.',
'next':'Replantear una única variante funcional motivada con el control RAM12,5 ya medido; no generar otro ancho por el estimador de dos diagonales. Mantener607consultas y tolerancias0.801/0.011/2.1; nuevo paquete necesitará su propio RAMABBAAB. No aceptación global.',
'handoff':E.relative_to(W).as_posix()+'/README.md; Nav12FAIL en evidence/navigation/kit7-nav12-rejected-20261027; Nav8funcional y RAMFAIL intactos.'}
for key,value in updates.items():
    new,count=re.subn('^'+key+':.*$',lambda match:key+': '+value,new,count=1,flags=re.M);assert count==1,key
assert handoff.read_text(encoding='utf-8')==old
handoff.write_text(new,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
write('MANIFEST.json',manifest)
print(json.dumps(dict(status='DIAGNOSTIC_RAM_CHECKPOINT',verdict=comparison['status'],acceptance_eligible=False,files=len(manifest))))
