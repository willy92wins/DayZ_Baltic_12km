"""Preserve the completed offline candidate without claiming native acceptance."""
from pathlib import Path
import hashlib, json, shutil

B = Path(__file__).parent
R = B.parent
G = R / 'v30-remaining-exact-dry-support-20261009'
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
surface = read(B / 'surface-verification.json')
mips = read(B / 'changed-mips.json')
deploy = read(B / 'deploy.json')
shape = read(G / 'verification.json')
coverage = read(G / 'compiled-coverage.json')
exposure = read(G / 'compiled-exposure.json')
accounting = read(G / 'layer-replay.json')
census = read(G / 'risk-census/census.json')
census_check = read(G / 'risk-census/verification.json')
probe = read(B / 'base-surface-fullwater-reference.json')
lint = read(B / 'probe-lint.json')
assert surface['status'] == 'PASS_COMPLETE_SURFACE_SOURCE_COMPILED'
assert mips['status'] == 'PASS_ALL_CHANGED_MIPS'
assert shape['status'] == 'PASS_STRICT_DRY_FLOOR_SOURCE'
assert coverage['status'] == 'PASS_GLOBAL_COMPILED_COVERAGE'
assert exposure['status'] == 'PASS_COMPILED_EXPOSURE'
assert accounting['status'] == 'PASS_EXACT_LAYER_AND_DRY_TARGET_ACCOUNTING'
assert census_check['status'] == 'PASS_GEOMETRIC_INDEX_ONLY'
assert lint['info']['files_scanned'] == 1 and not lint['errors']
assert sha(B / 'candidate/terrain.npz') == shape['candidate_sha256'] == deploy['terrain_sha256'] == probe['terrain_sha256']
assert all(sha(Path(deploy['mod']) / 'Addons' / name) == digest for name, digest in deploy['files'].items())
assert all(sha(Path(probe['mission']) / name) == digest for name, digest in probe['files'].items())
assert probe['pbo'] == deploy['files']

checks = [
    G / 'verification.json', G / 'compiled-coverage.json', G / 'compiled-exposure.json',
    G / 'layer-replay.json', G / 'risk-census/verification.json',
    B / 'surface-verification.json', B / 'changed-mips.json', B / 'probe-lint.json'
]
gate = dict(
    status='OFFLINE_PASS_NATIVE_PENDING', terrain_sha256=deploy['terrain_sha256'],
    pbo=deploy['files'], mod=deploy['mod'], mission=probe['mission'],
    runtime_vertices=4194304, runtime_points=len(probe['points']),
    runtime_water_probes=sum('expected_water' in q for q in probe['points']),
    checks=[dict(path=str(p), sha256=sha(p), status=read(p).get('status', 'SCRIPT_LINT_1_FILE')) for p in checks],
    native_run_id=None, native_pass=False, base_1_0_accepted=False,
    limits=['EV61 remains the last native-verified geometry.',
            'EV68 is a separate proposal with a pending policy exception; it is not included.',
            'Global graphical acceptance, remaining contour repairs, reserved lakes and TB/navmesh remain open.'])
(B / 'offline-gate.json').write_text(json.dumps(gate, indent=2) + '\n')

gtext = f'''# EV71 — cierre de los bajos secos editables

Estado: fuente y modelos compilados PASS; sin ejecución nueva en DayZ.

Se completan los 164 objetivos editables que quedaban después de EV70. Esta pasada cambia 5.202 vértices; la composición EV70+71 cambia {accounting['changed_since_ev61']:,} respecto de EV61, con elevación acumulada máxima de {accounting['max_cumulative_uplift_m']:.7f} m. P/F, carreteras, plataformas y todos los apoyos de triángulos realmente mojados se conservan. Las 18.033 instancias del WRP permanecen exactas.

La lista EV59 queda contada completamente: 2.615 de 2.760 puntos alcanzan 1,80 m (tolerancia 1e-6); los 145 restantes están protegidos, 59 en bancos de grandes lagos y 91 en el borde, con 5 comunes. Ningún objetivo editable de esa lista queda pendiente. No equivale a eliminar todo defecto gráfico del mapa.

El consumidor independiente de normales mide reducción del 15,98 % de energía angular en las 22.689 aristas incidentes, y los pliegues >30 grados bajan de 89 a 50. En los bancos naturales completos, p99 pasa de 16,70260 a 16,69000 grados. Cuatro sectores empeoran localmente; `sectors.json` conserva su detalle. No hay aceptación artística.

La exposición de los 500 objetos compilados afectados se conserva exactamente: 11.197 caras físicas y 30.141 visibles sin área nueva u oculta. La cobertura completa de 404.484 celdas pasa, sin hueco físico; residuo visible 3,8464e-12 m². El control negativo de hueco de un centímetro falla como debe.

El índice global recorre 8.380.418 triángulos: 408 zonas >=1 m² y {census['area_m2']:.2f} m² en la banda de riesgo. Su consumidor independiente pasa 91.937 caras analíticas, 320 comparaciones GEOS y 423 puntos secos. Es un índice geométrico, no 408 defectos de render confirmados.

`terrain-delta.npz` reconstruye byte a byte el candidato desde EV70; `layer-replay.json` verifica también los 145 protegidos. Terreno `{deploy['terrain_sha256']}`. El paquete final con las texturas nuevas es EV72; no usar las texturas provisionales de ExactDrySupportV2 para aceptación gráfica.
'''
(G / 'README.md').write_text(gtext)
text = f'''# EV72 — superficie completa sobre el terreno EV71

Estado: **OFFLINE_PASS_NATIVE_PENDING**. Base 1.0 incompleta. EV61 sigue siendo la última geometría comprobada dentro del motor.

Paquete preparado: `{deploy['mod']}`.

- Mundo: `{deploy['files']['narva_trial.pbo']}`.
- Agua: `{deploy['files']['baltic_water_v30.pbo']}`.
- Terreno: `{deploy['terrain_sha256']}`.
- WRP compilado: `{deploy['compiled_wrp_sha256']}`.

Las 1.024 teselas se regeneran desde el terreno actual y P verificado. El consumidor independiente revisa {surface['counts']['pixels']:,} píxeles y 3.968 solapes. Ningún píxel fuente mojado usa otra superficie que grava; los interiores compilados también pasan. Las {surface['counts']['compiled_wet_non_gravel']:,} mezclas DXT de borde se inventarían explícitamente.

Frente a las texturas EV67 cambian {deploy['changed_satellites']} satélites y {deploy['changed_masks']} máscaras. Todas las demás entradas de paquete son exactas respecto a EV71; el WRP no cambia en este paso. Se decodifican los {mips['changed_mips']} mipmaps nuevos y se contrastan con controles del conversor nativo. La truncación del payload se rechaza. Esto comprueba archivos, no la residencia de texturas en la GPU ni el fallo de streaming 019.

La misión `{Path(probe['mission']).name}` queda instalada, con 4.194.304 vértices, {len(probe['points'])} puntos y {gate['runtime_water_probes']} planos de agua. Lint: un archivo, cero errores. **No se ha ejecutado.** `offline-gate.json` enlaza los informes exactos y verifica de nuevo paquete y misión desplegados.

Continuación: recuperar herramientas publicadas de dayz-mcp, consultar ocupación y adquirir lease según el runbook, revalidar hashes y lanzar esta misión; ejecutar `verify_native.py` sobre el log nuevo. Después comparar vistas cargadas de puente, Msta, Volkhov y distancia. No aceptar una captura gris como referencia. Cerrar el run propio ordenadamente y liberar el lease. EV68/Volkhov se prueba aparte y requiere resolver su excepción 647/651 antes de promoción.

Pendientes del objetivo completo: reflejos residuales sin mecanismo cerrado, contornos todavía poligonales, grandes lagos reservados, 45 cruces de reserva vial, streaming, Terrain Builder y después navmesh/IA. El índice de bajos secos no convierte riesgos en defectos confirmados. El ticket de foco ya existe: `fb-20261008-233507-8b1c`.

Entorno: la UI indica conectado sin errores, pero `connector-availability.json` registra cero herramientas dayz-mcp disponibles para este turno. Sin nuevo run, lease ni bypass. El estado actual del banco compartido no se puede certificar.
'''
(B / 'README.md').write_text(text)

parent = W / 'evidence/v30-volkhov-float-consistent-2026-10-09/evidence-manifest.json'
assert all(sha(W / row['path']) == row['sha256'] for row in read(parent))
manifest = dict(status='PRESERVED_OFFLINE_NATIVE_PENDING', parent_manifest=dict(path=parent.relative_to(W).as_posix(), sha256=sha(parent)), files=[])
for number, src, name in [(71, G, 'v30-remaining-exact-dry-support-2026-10-09'), (72, B, 'v30-complete-dry-surface-2026-10-09')]:
    dest = W / 'evidence' / name
    dest.mkdir(exist_ok=False)
    files = [p for p in src.iterdir() if p.is_file() and p.suffix in {'.py', '.json', '.md', '.npz', '.log', '.ps1', '.csv'}]
    for child in ['risk-census', 'native-controls']:
        if (src / child).is_dir():
            files += [p for p in (src / child).iterdir() if p.is_file()]
    for p in files:
        out = dest / p.relative_to(src)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out)
        assert sha(p) == sha(out)
        manifest['files'].append(dict(evidence=number, path=out.relative_to(W).as_posix(), sha256=sha(out), bytes=out.stat().st_size))
    if number == 72:
        out = dest / 'probe-init.c'
        shutil.copyfile(Path(probe['mission']) / 'init.c', out)
        manifest['files'].append(dict(evidence=number, path=out.relative_to(W).as_posix(), sha256=sha(out), bytes=out.stat().st_size))
dest = W / 'evidence/v30-complete-dry-surface-2026-10-09'
(dest / 'evidence-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
assert len({r['path'] for r in manifest['files']}) == len(manifest['files'])
assert all(sha(W / row['path']) == row['sha256'] for row in manifest['files'])
print(json.dumps(dict(status=manifest['status'], files=len(manifest['files']), bytes=sum(row['bytes'] for row in manifest['files']), candidate=deploy['mod']), indent=2))
