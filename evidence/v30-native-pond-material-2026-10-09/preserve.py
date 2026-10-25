from pathlib import Path
import hashlib,json,shutil,re
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-native-pond-material-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b);assert sha(a)==sha(b)
ref=json.loads((B/'reference.json').read_text());runtime=json.loads((B/'runtime.json').read_text())
profile=Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile')
# Window was enlarged during startup before the baseline. Record profile truth, never force it.
settings={k:float(re.search(r'^'+k+r'=([^;]+);',profile.read_text(),re.M).group(1)) for k in ref['settings']}
assert settings==ref['settings']
maps={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons').glob('*.pbo')};assert maps==ref['map_files']
cp(Path('P:/DayZ_MCP_dev/_client/profiles/baltic_pond_material_probe_v1.log'),B/'native-pond.log')
cp(Path('P:/DayZ_MCP_dev/_server/profiles/baltic_render_layer_v1.log'),B/'native-sea.log')
phases=[s for s in (B/'native-pond.log').read_text().splitlines() if s.startswith('PHASE;')]
assert [int(s.split(';')[1]) for s in phases]==[0,1,2,3,4] and 'untouched' in phases[0]
assert all('set_return=true' in phases[i] for i in (1,3))
for label in ['baseline','wetfloor0','restored']:
 rows=[r for r in runtime['captures'] if r['phase']==label];assert len(rows)==6 and all(r['frame_stale'] is False for r in rows)
assert len({(r['client_surface']['rect_window']['width'],r['client_surface']['rect_window']['height']) for r in runtime['captures']})==1
report=dict(status='NO_STABLE_RESIDUAL_SUPPRESSION_BINDING_NOT_ISOLATED',phases=phases,settings_after=settings,settings_identical=True,profile_byte_identical=sha(profile)==ref['profile_sha256'],profile_hash_after=sha(profile),map_hashes_after=maps,pixel_series=json.loads((B/'pixel-series.json').read_text()),run_id=runtime['run_id'],close=runtime['close'],final_state=runtime['final'],limits=['GetMaterial and indices are valid; SetParam true is not a readback or proof that this resource shades the observed pixels.','NormalPower control is not unambiguous amid sea foam. No whole-map exclusion of a pond-material contribution.','Six frames per A/B/A phase cover waves but are not phase synchronized.','No geometry, level or production material changed; no fix promoted.'])
(B/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
E.mkdir(exist_ok=False)
for name in ['plan.md','build_probe.py','set_phase.py','preserve.py','measure_series.py','reference.json','runtime.json','runtime-working.json','summary.json','pixel-series.json','phase-writes.jsonl','native-pond.log','native-sea.log','lint.json','cfgconvert.log','filebank.log']:cp(B/name,E/name)
for p in (B/'baltic_pond_material_probe_v1').rglob('*'):
 if p.is_file():cp(p,E/'source'/p.relative_to(B/'baltic_pond_material_probe_v1'))
for p in (B/'captures').rglob('*.jpg'):cp(p,E/'frames'/p.relative_to(B/'captures'))
for src in [Path('P:/DayZ_MCP_dev/_client/profiles'),Path('P:/DayZ_MCP_dev/_server/profiles')]:
 files=sorted(src.glob('*.RPT'),key=lambda p:p.stat().st_mtime)
 if files:cp(files[-1],E/'logs'/src.parent.name/files[-1].name)
for p in [Path('P:/Graphics/materials/water/pond_moss_1.emat'),Path('P:/DZ/water/ponds/data/pond_moss_1.rvmat')]:cp(p,E/'references'/p.name)
(E/'README.md').write_text('''# EV33 — material de charca, sin supresion estable

La sonda cambia solo WetFloor de graphics/materials/water/pond_moss_1, mientras EV17 habia cambiado el material del oceano. Obtiene handle, indices validos y respuestastrue; baseline inicial intacta. Series0/1/2 de seis capturas cada una, mas controlNormalPower0 y reset. Camara y ventana2891x1648 estables durante las series. El parametro vuelve al valor por defecto mediante ResetParam; la API no permite leer el valor anterior.

La aparente limpieza en algunas capturas no supera con claridad las variaciones naturales. Centro seco: cambio mediano2.400RGB frente2.302 entre referencias. Conjunto de charcas3.062 frente2.930. Solo13pixeles de525673 superan todos los originales/restaurados por5niveles. No suprime espuma/halos de forma demostrada. NormalPower no ofrece control inequivoco con espuma del mar superpuesta; no afirmar que este handle sea el consumidor de los pixeles observados, ni descartar todos los shaders de charca. La ruta requiere comprobar el enlace del RVMAT CalmWater al recurso nativo antes de mas parametros.

No se altera produccion. Ajustes de render del perfil iguales; resumen conserva verdad del hash completo. Mapa y agua exactos. Cierre orderly cliente/servidor, lease liberado y banco libre. Sin cierre016/018 ni base1.0.
''',encoding='utf-8')
(E/'preservation.json').write_text(json.dumps({str(p.relative_to(E)):sha(p) for p in E.rglob('*') if p.is_file()},indent=2)+'\n')
print(json.dumps(dict(status=report['status'],profile_byte_identical=report['profile_byte_identical'],evidence=str(E))))
