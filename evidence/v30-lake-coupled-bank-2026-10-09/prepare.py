from pathlib import Path
B=Path(__file__).parent;old=Path('E:/DayZ-Baltic-Build/v30-lake-native-bank-finish-20261009')
plan='''# EV40 — liberar apoyos secos de orilla, niveles conservados

Cambio de mecanismo explícito tras EV19/39: la banda terrestre exterior no contiene la cresta completa. EV39 reduce la curvatura solo3,98%/2,43%; no se promueve ni se prolonga su solver. La máscara heredada de soporte de agua no es una prohibición del usuario. Este lote permite bajar sus vértices SECOS, siguiendo la petición de suavizar orillas y terraplenes, y conserva todos los mojados.

PLAN: rumbo §3 niveles reservados, §4 línea de agua medida, §7 física/visual. Niveles y fondos exactos. Carreteras, plataformas, corredores de navegación y periferia intactos. Celdas con distintos planos físicos incidentes protegidas para no cambiar contactos entre masas.

Una solución,60barridos/600s, una reparación de implementación. Mismo método de caras nativas EV25, descenso≤1,5m. Suelo exterior EV39; los apoyos secos pueden bajar hasta max(1,8m, todos los planos P/F incidentes+0,0501m), sin rebajar una excepción existente. Signos húmedo/seco de cada vértice/triángulo exactos. No se cambia clase, nivel ni lecho. Desplazamiento máximo de cruces≤4,1m, mismo límite EV16. Cada banco: curvatura≥10% menor, p90cresta no mayor, RMSde quiebros nativos menor. Contorno local medido para evitar dientes nuevos. Ningún signo/topología podrá esconderse por reclasificación.

Después de fuente PASS: comprobar cobertura compilada de todas las celdas alteradas y completar piezas mínimas solo si faltan, siguiendo EV16; satélite/máscara afectados recalculados; terreno/objetos reales leídos en motor. No aceptación de niveles nuevos ni de base completa. FAIL no admite otra variación de radio/peso.
'''
(B/'plan.md').write_text(plan,encoding='utf-8')
s=(old/'author.py').read_text().replace("'one lake-bank candidate'","'one coupled-bank candidate'")
s=s.replace("fixed=np.load(FIXED)['fixed']|water_support|t['water']|t['beach']|(t['cls']!=0)","""f=np.load('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy')
 pmax=np.full(h.shape,-np.inf);pmin=np.full(h.shape,np.inf);fmax=np.full(h.shape,-np.inf)
 for slot,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
  valid=np.isfinite(p);sl=np.s_[dr:dr+2047,dc:dc+2047]
  pmax[sl]=np.maximum(pmax[sl],np.where(valid,p,-np.inf));pmin[sl]=np.minimum(pmin[sl],np.where(valid,p,np.inf))
  fmax[sl]=np.maximum(fmax[sl],np.where(valid,f[:,:,slot],-np.inf))
 maxwater=np.maximum(pmax,fmax);dry_support=water_support&(h>maxwater)
 mixed_planes=water_support&((pmax-pmin)>1e-5)
 fixed=np.load(FIXED)['fixed']|(water_support&~dry_support)|mixed_planes|t['water']|t['beach']|(t['cls']!=0)""")
s=s.replace("minimum[scope]=np.minimum(original[scope],np.maximum(original[scope]-1.5*fade[scope],floor))", """local_floor=np.full(h.shape,floor)
  local_floor[dry_support]=np.maximum(1.8,maxwater[dry_support]+.0501)
  minimum[scope]=np.minimum(original[scope],np.maximum(original[scope]-1.5*fade[scope],local_floor[scope]))""")
s=s.replace("water_support=water_support,minimum=minimum", "water_support=water_support,dry_support=dry_support,mixed_planes=mixed_planes,minimum=minimum")
(B/'author.py').write_text(s)
print(B/'plan.md')
