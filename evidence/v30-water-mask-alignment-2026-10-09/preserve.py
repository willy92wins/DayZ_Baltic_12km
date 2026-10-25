from pathlib import Path
import shutil,json,zipfile,hashlib
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-water-mask-alignment-2026-10-09';E.mkdir(exist_ok=False)
for p in B.iterdir():
 if p.is_file() and p.suffix in ('.py','.md','.json','.log'):shutil.copyfile(p,E/p.name)
for p in (B/'views').rglob('*.jpg'):
 dest=E/p.relative_to(B);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
receipt=json.loads((B/'deploy-receipt.json').read_text());wanted=set(Path(k).name.lower() for k in receipt['changed_entries'])
files=list((B/'layers').glob('*.png'))+[B/'layers'/name for name in sorted(wanted)]
archive=E/'mask-overrides.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):
  info=zipfile.ZipInfo(p.name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
with zipfile.ZipFile(archive) as z:
 assert len(z.namelist())==1024+642
 for p in files:assert z.read(p.name)==p.read_bytes()
(E/'preservation.json').write_text(json.dumps(dict(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),entries=len(files),size_bytes=archive.stat().st_size),indent=2)+'\n')
(E/'README.md').write_text('''# EV23 — máscaras alineadas con el agua compilada

Preview `@DayZ_Baltic_AlignedMaskV1`. Corrige55.958 píxeles de un metro que usaban superficies terrestres bajo agua nominal. Se comprueba toda la fuente:35.772.220 píxeles mojados, cero errores; ningún píxel seco ni alpha cambia. Los1.984 solapes entre tiles coinciden exactamente.

Las1.024 máscaras se recompilan y vuelven a decodificar. En34.445.894 píxeles interiores, a4m o más de la frontera, no queda mezcla terrestre. Persisten4.354 píxeles mezclados junto al borde por compresión DXT; se inventarían y no se venden como cero mezcla en todas las muestras. Negativos sobre píxeles reales interiores son rechazados.

Se reemplazan642 PAA en el PBO y los otros6.185 archivos son byte por byte idénticos a EV16: WRP, configuración, satélite, materiales, puentes y navmesh. El PBO de agua es idéntico. Por esa identidad geométrica se conservan el censo EV16, los corredores y los doce viajes físicos EV18, sin fingir que se repitieron.

Mundo `6c9becaa2be8345402eb4863f2c48938860a8a0bb8238ea0acecf31dd8188104`; agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`. Terreno `70f74c9334620c458880f728d3ff15cec7867ffe2bd8bd2e9d5135e1692b7ed5`.

Run `f3f2f091-7205-4a90-a7ea-e3c75415c63c`: carga correcta en R1 y cerca de uno de los grupos más afectados, sin recuperar foco manual. Las consultas SurfaceGetType y un rayo por debajo del agua devuelven fresh_water_ext: confirman agua, pero ocultan la superficie del fondo y no prueban por sí solas el tipo de máscara. El control seco conserva cp_conifer_common1 y altura1,520454m. No se atribuye al cambio una mejora no comparada de vegetación ni el arreglo de BALTIC-016.

Cliente/servidor cierran normally, lease libre, cero runs. El archivo ZIP conserva las1.024 fuentes y las642 PAA cambiadas. Esta unidad no congela geometría ni cierra lagos, remates, residual, distancias, TB o navmesh final.
''',encoding='utf-8')
print(str(E))
