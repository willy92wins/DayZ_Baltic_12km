from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-current-satellite-2026-10-09';E.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);assert sha(source)==sha(target)
for name in ['plan.md','discover_and_check_inputs.py','compile_and_verify_surface.py','package_surface.py','preserve.py','inputs.json','surface-verification.json','deploy.json','filebank.log','runtime.json']:
    copy(B/name,E/name)
copy(W/'tools/terrain/build_surface_v30.py',E/'build_surface_v30.py')
for name in ['surface.json','preview_sat.png','preview_mask.png']:copy(B/'surface'/name,E/name)
for p in sorted((B/'captures').rglob('*.jpg')):copy(p,E/'frames'/p.parent.name/p.name)
for role,stamp in [('client','11-55-28'),('server','11-55-17')]:
    p=Path('P:/DayZ_MCP_dev')/('_'+role)/'profiles'/f'DayZDiag_x64_2026-10-09_{stamp}.RPT'
    text=p.read_text(errors='replace');assert '@DayZ_Baltic_CurrentSurfaceV1' in text and 'Termination successfully completed' in text
    copy(p,E/'logs'/(role+'.RPT'))
copy(Path('P:/DayZ_MCP_dev/_server/profiles/baltic_render_layer_v1.log'),E/'logs/baltic_render_layer_v1.log')
readme='''# EV28 — superficie completa actualizada

Preview @DayZ_Baltic_CurrentSurfaceV1. Las1024 teselas anteriores coincidian con v12. build_surface_v30.py admite ahora un campo de agua fisica verificado por SHA256, evitando reconstruir el agua congelada a partir de cls/level. No cambia paleta ni opciones aprobadas. Se regeneran satelite y mascara sobre terreno EV25 y plane.npy d59dcdb9.

Consumidor independiente de triangulos nativos:150.847.524 pixeles,35.772.061 mojados, cero superficie terrestre bajo agua en la fuente. Las2048 texturas se compilan y decodifican;34.445.765 pixeles interiores de agua sin mezcla terrestre. Los4.323 pixeles mezclados por DXT junto a la frontera se inventarian. Los3968 solapes (1984 por familia) coinciden exactamente. Error RGB medio de compresion0,68565/255, maximo25/255; no se pretende identidad fuente/PAA.

Cambian1.710.644 pixeles de satelite y212.250 de mascara, estos ultimos todos secos. Hay9 controles de entrada (incluye caso valido) y controles analiticos de triangulo y de corrupcion real de mascara. El paquete cambia754 satelites y712 mascaras; las5361 entradas restantes y todo el PBO de agua quedan exactos. WRP compilado cfcbbd0c, terreno fb36ec4c. No nuevo censo de alturas ni travesias: la identidad de sus archivos delimita el alcance reutilizable.

Run b690cc87-1c6f-465f-adba-ee070db236f4: texturas cargadas en puente/R1, R3 cercano/medio y tesela27,21 (mayor cambio) cercana/elevada. Sin foco manual. R3 lejano limitado por bruma: INCONCLUSO para aceptar distancia; el cercano tiene cabeza del jugador en parte de la imagen. Una primera camera_set fue rechazada por mezclar modo free con matriz, corregida a matrix antes de la captura. Todas las capturas guardadas presentan3 frames distintos; no hay A/B de mejora estetica. No se da por reparado el residual016 ni el fallo intermitente019.

Cliente/servidor cerrados orderly, lease liberado y banco vacio. Mundo b69265c5feb99d1bda7a5c9f02282818d0ffe4cd26f89f3a095c128e62d374f3, agua3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14. Los PNG/PAA completos siguen en E:/DayZ-Baltic-Build/v30-current-satellite-20261009/surface/layers y tienen hashes individuales en surface-verification.json. No promocion a TB/base1.0: forma restante, lagos, residual y pruebas finales siguen pendientes.
'''
(E/'README.md').write_text(readme,encoding='utf-8')
(E/'preservation.json').write_text(json.dumps({str(p.relative_to(E)):sha(p) for p in E.rglob('*') if p.is_file()},indent=2)+'\n')
print(json.dumps(dict(status='SURFACE_EVIDENCE_PRESERVED',files=sum(p.is_file() for p in E.rglob('*')),evidence=str(E))))
