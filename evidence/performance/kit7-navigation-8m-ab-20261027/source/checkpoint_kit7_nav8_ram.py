"""Archive all six measured runs without changing or selecting benchmark data."""
from pathlib import Path
import gzip, hashlib, json, re

R = Path(__file__).parent
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D = R / 'kit7-nav8-ram-ab-20261027'
E = W / 'evidence/performance/kit7-navigation-8m-ab-20261027'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

assert not E.exists(), 'Fresh evidence directory required'
comparison = load(D / 'comparison.json')
assert comparison['status'] in ('PASS_EMPTY_SERVER_RAM_BUDGET', 'FAIL_EMPTY_SERVER_RAM_BUDGET', 'INCONCLUSIVE')
assert comparison['measurement_repeats'] == 0
assert comparison['order'] == ['BalticTrial', 'ChernarusPlus', 'ChernarusPlus', 'BalticTrial', 'BalticTrial', 'ChernarusPlus']
for name, digest in {**comparison['inputs'], **comparison['validation_sources']}.items():
    assert sha(name) == digest, name
assert len(comparison['inputs']) == 6
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

for name in ('comparison.json', 'background-activity-summary.json', 'missions.json', 'accepted.json', 'coordinator-controls.json'):
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
for name in ('screen_kit7_nav_budget_widths.py', 'screen_kit7_nav_budget_all_widths.py'):
    save(R / name, 'diagnostics/' + name)
for name in ('kit7-nav-budget-width-screen-20261027', 'kit7-nav-budget-all-width-screen-20261027'):
    save(R / name / 'result.json', 'diagnostics/' + name + '.json')
save(R / 'kit7-nav-budget-planning-summary-20261027.json', 'diagnostics/planning-summary.json')
m = comparison['metrics']
rows = []
for key, label in [('working_set_mib', 'RAM residente'), ('private_mib', 'RAM privada')]:
    value = m[key]
    rows.append(f"| {label} | {value['baltic_median']:.2f} | {value['chernarus_median']:.2f} | {value['ratio']:.5f} | {value['status']} |")
text = '''# RAM del kit7 con navegación de 8 m frente a Chernarus

Resultado: **STATUS**. Se conservan las seis pasadas nuevas en orden
A-B-B-A-A-B, tres por mapa, sin repeticiones ni selección de resultados.
Cada misión tiene 30 s de calentamiento y 120 s de medición. Se mantienen
el presupuesto de RAM de 1,10 y la dispersión máxima del 5 %.

| Mediana por mapa | Baltic (MiB) | Chernarus (MiB) | Cociente | Resultado |
|---|---:|---:|---:|---|
ROWS

Las seis mediciones están vinculadas a proceso y creación, misión, ejecutable,
configuración y paquetes por SHA-256. El lector se volvió a ejecutar sobre las
seis capturas antes de comparar. Los observadores y cierres oficiales de cada
servidor propio están archivados. El muestreo comienza antes del calentamiento;
los hashes posteriores se calculan fuera de la ventana de medición.

Esto mide RAM del proceso servidor vacío, sin CE, AI, jugadores ni cliente.
CPU se conserva como dato descriptivo. No acredita FPS, VRAM, capacidad para
80–100 jugadores ni aceptación visual o global del mapa. Los resúmenes de
actividad del equipo no prueban ausencia de carga ajena; los nombres de las
aplicaciones y los RPT completos permanecen locales.

La corrección funcional se mantiene separada: las 607 consultas nativas del
kit7 pasan con máximo 0,711963 m y límite intacto de 0,801 m. Véase
../../v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-navigation-8m-functional-20261027/README.md.
La receta, revisiones independientes y controles de preparación están en ese
checkpoint. Los archivos binarios del mapa y de vanilla no se publican en Git.

Los diagnósticos adjuntos exploran otros tamaños de tesela sin modificar el
mapa. Son estimaciones para priorizar experimentos: 12 m estima 0,715 m en los
ocho puntos originales, pero predice 74 excesos en el conjunto amplio. El mismo
método predice 10 excesos para 8 m, que pasa realmente en el motor, y 125 para
12,5 m, que falla en cuatro. No sirve como gate de aceptación. Cualquier nueva
variante necesita una generación propia, las mismas 607 consultas y otra
comparación de RAM completa antes de ser promovida.
'''.replace('STATUS', comparison['status']).replace('ROWS', '\n'.join(rows))
if comparison['status'] != 'PASS_EMPTY_SERVER_RAM_BUDGET':
    text += '\nEsta variante no se promueve como optimizada: el presupuesto de RAM no ha\nsuperado la aceptación. Se conserva el éxito funcional y se requiere una\nalternativa motivada antes de otra generación. No se cambian los límites.\n'
(E / 'README.md').write_text(text, encoding='utf-8')
handoff = W / 'HANDOFF.md'
old = handoff.read_text(encoding='utf-8')
(D / 'handoff-before-ram-checkpoint.md').write_text(old, encoding='utf-8')
ws, private = m['working_set_mib'], m['private_mib']
updates = {
    'updated': '2026-10-27 (kit7: cuatro alturas corregidas, 607 PASS; comparación RAM de 8 m terminada)',
    'plan': 'Corrección del kit7 y comparación RAM propia completadas según plans/ev112-kit7-nav-height-refinement-20261027.md; tolerancias intactas. Visual, locomoción y otros sectores siguen pendientes.',
    'blocker': 'Los cuatro fallos de altura del kit7 están cerrados: 607 consultas nativas PASS, máximo 0,711963 m frente a 0,801 m. RAM 8 m: ' + comparison['status'] + '. Visual, locomoción y aceptación global siguen pendientes; se conservan protecciones y censo abiertos.',
    'performance': f"{comparison['status']} sobre kit7 Nav8: 6 pasadas nuevas ABBAAB, 3 por mapa, 0 repeticiones. Residente {ws['baltic_median']:.2f}/{ws['chernarus_median']:.2f} MiB (ratio {ws['ratio']:.5f}); privada {private['baltic_median']:.2f}/{private['chernarus_median']:.2f} MiB (ratio {private['ratio']:.5f}). Presupuesto 1.10 y dispersión 5% intactos. CPU descriptiva; no FPS/VRAM/capacidad. Evidencia " + E.relative_to(W).as_posix() + '.',
    'cleanup': 'Generación, sonda 607 y seis pasadas RAM propias cerradas oficialmente; sin cliente, leases liberados y recibos terminales conservados. Automatización anterior PAUSED; nuevos lanzamientos por FIFO.',
    'next': ('Revisión visual y locomoción conjunta del kit7; después otros sectores y censo global.' if comparison['status'] == 'PASS_EMPTY_SERVER_RAM_BUDGET' else 'Replantear el coste de navegación de 8 m antes de promoverlo como optimizado; conservar el éxito funcional y las seis mediciones. Revisar una alternativa motivada antes de otra generación.') + ' No heredar aceptación global de los resultados locales.',
    'handoff': E.relative_to(W).as_posix() + '/README.md y checkpoint funcional kit7-navigation-8m-functional-20261027; evidencia de RAM y geometría separadas.',
    'deployed': 'P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8: mundo ac088ccbaff34ef7a5cbfe03b6e016fb6941895b9b253786f99b57578cf6d4ff, piloto 3d9550bf, agua 97edcafe. Copias anteriores conservadas. Grafo 607 PASS; RAM ' + comparison['status'] + '; visual pendiente.'
}
new = old
for key, value in updates.items():
    new, count = re.subn('^' + key + ':.*$', lambda match: key + ': ' + value, new, count=1, flags=re.M)
    assert count == 1, key
assert handoff.read_text(encoding='utf-8') == old, 'Preserve concurrent handoff edits'
handoff.write_text(new, encoding='utf-8')
manifest = {p.relative_to(E).as_posix(): dict(sha256=sha(p), bytes=p.stat().st_size)
            for p in sorted(E.rglob('*')) if p.is_file()}
write('MANIFEST.json', manifest)
print(json.dumps(dict(status='KIT7_NAV8_RAM_CHECKPOINT', verdict=comparison['status'], files=len(manifest))))
