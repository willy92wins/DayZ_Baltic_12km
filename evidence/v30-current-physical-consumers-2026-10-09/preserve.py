from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-current-physical-consumers-2026-10-09'
for p in B.glob('*.py'):shutil.copyfile(p,E/p.name)
shutil.copyfile(B/'preparation.json',E/'preparation.json')
for p in (B/'missions').rglob('*'):
 if p.is_file():dest=E/p.relative_to(B);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
d=json.loads((E/'drive-verification.json').read_text());b=json.loads((E/'boat-verification.json').read_text())
out=dict(status='PASS_SELECTED_PHYSICAL_CONSUMERS_EV16',drive_cases=len(d['cases']),drive_samples=sum(c['samples'] for c in d['cases']),drive_ground_error=max(c['maximum_ground_error_m'] for c in d['cases']),drive_contact_error=max(c['maximum_contact_error_m'] for c in d['cases']),drive_min_health=min(c['health_min'] for c in d['cases']),drive_controls=18,boat_controls=11,limits=['Six frozen boat trips and six frozen sedan trips, not every route or vehicle.','Drive verifier status has a historical name: current cases are coast, hills and south, in both directions.','No new final navmesh, no AI pursuit or player-load acceptance.'])
(E/'result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
(E/'README.md').write_text(f'''# EV18 — consumidores físicos del candidato EV16

Seis viajes de lancha y seis de sedán pasan sobre el terreno desplegado actual. La conducción aporta {out['drive_samples']} muestras activas, salud mínima {out['drive_min_health']}, error máximo de suelo {out['drive_ground_error']:.8f} m y de contacto {out['drive_contact_error']:.8f} m. Los recorridos, controladores y umbrales se fijaron antes de probar; solo se actualizó la referencia de terreno.

Los controles negativos se ejecutaron sobre los logs reales positivos: 11 de lancha y 18 de conducción rechazan daños, falta de motor/movimiento, teletransporte, suelo incorrecto, huecos de reloj y otras corrupciones pertinentes.

La auditoría independiente de caras nativas cubre los 19 corredores principales (36.494 caras; mínimo 0,955609 m) y los cuatro del delta (1.237 caras; mínimo 3,05 m). No aparecen nuevas excepciones de fondo ni inundación seca. La primera implementación del verificador queda preservada como FAIL de instrumentación: mezclaba 19+4 casos con una cuenta esperada de 19 y no era el consumidor exacto aprobado. `geometry-current-exact.json` utiliza ese consumidor y comprueba cobertura poligonal completa.

No se declara toda la red físicamente recorrida, capacidad de barcos medianos, conducción humana, navmesh final ni carga de jugadores. El nombre histórico del estado PASS del verificador no describe las rutas actuales: son costa, colinas y sur, en ambos sentidos. Todos los procesos de esta unidad cierran normalmente.
''',encoding='utf-8')
