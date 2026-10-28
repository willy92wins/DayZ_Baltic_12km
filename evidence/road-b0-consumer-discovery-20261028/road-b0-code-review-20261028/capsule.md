Delegar JUICIO codigo RoadB0, una lane Fable5.1 CLI nativo medido hoy2.1.310, reviews con modelUsage confirmado. Codex executor/integrator adjudica. Read-only sin tools/hijos/escrituras/git. <=180s700palabras, SOUND/SOUND-with-fixes/NEEDS-WORK, lineas/fix/casos falsosPASS. FIN_REVISION. Plan revisado77.828s adjunto y adjudicacion acota una extraccion120s2GiB, 3piezas asf1_25/asf2_25/asf1_10 100 instaladas del catalogoA; sin leerWRP ni colocar.14tests inicialesPASS1.093s. Primitivas reales: cat.read_pbo Path devuelve raw,props,entries dict; cat.model_metadata exige strict todosLOD/rawvertices exactos yfaceindices, roles por resolucion ymeta materias/centros; cat.sections exige particion total sin duplicados, indices validados; cat.loaded_reader_binding verifica5modulosdelectorpath. odol_reader.py488 lee bounding_center,662 b_center,717-720 verticesrawfloat32 sin desplazamiento. Nuevooffset0 describe sololector, pivotUNKNOWN. No alteranhelperssellados. CfgConvert -txt -dst dest original es firma verificada en build_outside_material_variant.py:49, hash instalado4c4f fijado; solo decodificacion nueva en salida local, nunca build/mod. run_process selladoB3E2 observaPIDbirthimagen, RSSpropio+descendientes, presupuestos yretorno0, cierra soloidentidadespropias enagotamiento; base.run_tree permite recibo rc2 ypadrelointerpreta como descubrimiento incompleto si3modelos ynoerror, noPASSmapa. CLI meter.bounded youter120s2GiB totalincluyelectura/decoder, decodermax60sconrestante. PBO501entradas/265modelos yselectedhashes leidoscatalogoA, no repetirCLIcatalogo. Camposconsumer/pivot/width/shoulder/crossingsUNKNOWN deliberados, no consumer demostrado porclasesconfig. LocalcaraspoligonosWKT soloRprivado, publicararesumen/recibos sinvanillageometria. Configclasesobservaciones no acepta runtime. Fixture curvaenLareas32bbox80demuestraunionnoancho; RoadwayausenteUNKNOWN. Cruces marginales/nodos faltanporquenoseimplementancruces; respetaralcance. Buscar fallosconcretos representacion/indices/normalizacion/materiales/proyecciones/consumidor/sello; no exigirPASScompleto. ReceptorindependienteCodex verificaadjudica; B3F yahecho peronoobjetoactual.

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\quality\road_consumer_discovery_ev112.py
1: """Bounded RoadB0 subset: local full faces/materials, not placement or driving."""
2: import time
3: START=time.monotonic()
4: from pathlib import Path
5: import argparse,importlib,json,math,struct,sys,traceback
6: HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
7: import road_asset_catalog_ev112 as cat
8: import build_prism_b3e2_ev112 as runtime
9: from deployed_surface_inventory_ev112 import sections
10: from shapely import Polygon,union_all
11: meter=cat.meter;sha=meter.sha;dump=meter.dump
12: CFG=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe')
13: CFG_SHA='4c4fc15ef9773b42b4191155d4e243d8c95d3156cf7b6f24e7d84dea7cd15a4c'
14: SELECTED={'Parts/asf1_25.p3d':'d72224ed23c03e2cc2d265aba895d534af4b5a8039adc192b783ef856984d69b','Parts/asf2_25.p3d':'4ce4b0a76b017d023b2c26e05dc144d26aae5b0272314790cae214746c1257ca','Parts/asf1_10 100.p3d':'2d52f9e5123d74d27ec91fe2f52dacf13e863e4a149c94e460ce675fcfd480ec'}
15: CONFIG_SHA='1c7aad19b4a2a92adbc4c46ddc6a1eda5a83aac33c81478fa4dfbc31f80f068c'
16: CAT_SHA='fb8ac8972e834c21084b2f22c6dd7409daeb052c6c466d97a6ea4929ad5f0427'
17: require=cat.require
18: 
19: def faces(lod):
20:     points=[cat.xyz(p) for p in lod.vertices]
21:     require(list(struct.iter_unpack('<fff',lod.vertex_raw))==[tuple(p) for p in points],'raw_decoded_vertices')
22:     assignment,materials=sections(lod);rows=[];polygons=[];by_material={}
23:     for fi,face in enumerate(lod.faces):
24:         ids=list(face.vertex_indices);require(len(ids) in (3,4) and all(0<=i<len(points) for i in ids),'face_indices')
25:         xyz=[points[i] for i in ids];poly=Polygon([(p[0],p[2]) for p in xyz]);si=int(assignment[fi]);section=materials[si]
26:         # Retain every source face, including vertical/degenerate projections.
27:         state='AREA' if poly.is_valid and poly.area>0 else 'DEGENERATE_OR_INVALID'
28:         rows.append(dict(face=fi,vertex_indices=ids,xyz=xyz,section=si,material=section['material'],texture=section['texture'],projection=state))
29:         if state=='AREA':polygons.append(poly);by_material.setdefault((section['material'],section['texture']),[]).append(poly)
30:     footprint=union_all(polygons)
31:     return dict(faces=rows,face_count=len(rows),bbox=cat.bbox(points),sections=materials,
32:                 projection_area_m2=float(footprint.area),projection_wkt=footprint.wkt,
33:                 material_masks=[dict(material=k[0],texture=k[1],area_m2=float((g:=union_all(v)).area),wkt=g.wkt) for k,v in by_material.items()],
34:                 degenerate_projection_faces=sum(r['projection']!='AREA' for r in rows))
35: 
36: def discovery_fields(roadway):
37:     require(isinstance(roadway,bool),'roadway_not_boolean')
38:     return dict(consumer_observed='UNKNOWN',pivot_convention='UNKNOWN',usable_width='UNKNOWN',shoulder_material='UNKNOWN',roadway_present=roadway,crossings_exact='UNKNOWN')
39: 
40: def status(rows):
41:     required=('consumer_observed','pivot_convention','usable_width','shoulder_material','roadway_present','crossings_exact')
42:     require(bool(rows),'empty_discovery')
43:     for row in rows:
44:         require(all(k in row for k in required),'missing_discovery_field')
45:         require(isinstance(row['roadway_present'],bool),'roadway_not_boolean')
46:         require(row['usable_width']=='UNKNOWN' or (isinstance(row['usable_width'],(int,float)) and math.isfinite(row['usable_width']) and row['usable_width']>0),'invalid_width')
47:     return 'INCONCLUSIVE_DISCOVERY' if any(row[k]=='UNKNOWN' for row in rows for k in required) else 'DISCOVERY_COMPLETE_NOT_PLACEMENT'
48: 
49: def run(output):
50:     pins={str(cat.PBO):cat.PBO_SHA,str(CFG):CFG_SHA,str(HERE/'road_asset_catalog_ev112.py'):CAT_SHA,
51:           **{str(cat.READER/n):h for n,h in cat.READER_PINS.items()},**{str((HERE/n).resolve()):h for n,h in cat.HELPER_PINS.items()},
52:           **{str(p):h for p,h in runtime.HELPERS.items()},str(HERE/'build_prism_b3e2_ev112.py'):'b131794d75a2748f40dfdd87e5e01389cf6434ca2f9b160253f70f241f538cbb'}
53:     cat.check_pins(pins);dump(output/'inputs.json',pins)
54:     raw,props,entries=cat.read_pbo(cat.PBO);require(cat.digest(raw)==cat.PBO_SHA,'pbo_changed');del raw
55:     require(props.get('prefix')=='dz\\structures\\roads' or props.get('prefix')=='dz/structures/roads','prefix')
56:     require(cat.digest(entries['config.bin'])==CONFIG_SHA,'config_changed')
57:     for name,h in SELECTED.items():require(cat.digest(entries[name])==h,'selected_changed:'+name)
58:     (output/'installed-config.bin').write_bytes(entries['config.bin'])
59:     runtime.run_process([str(CFG),'-txt','-dst',str(output/'installed-config.cpp'),str(output/'installed-config.bin')],output/'decode.log',min(60,max(1,120-(time.monotonic()-START))))
60:     cpp=(output/'installed-config.cpp').read_text(encoding='utf-8-sig');require(bool(cpp.strip()),'empty_decoded_config')
61:     # This is source evidence only: declarations do not imply WRP instances.
62:     source_lines=[dict(line=i+1,text=s.strip()) for i,s in enumerate(cpp.splitlines()) if 'StaticObj_Roads_Partasf' in s or any(n[6:-4] in s for n in SELECTED)]
63:     dump(output/'config-source-observations.json',dict(config_bin_sha256=CONFIG_SHA,decoded_sha256=sha(output/'installed-config.cpp'),lines=source_lines,consumer_observed='UNKNOWN',limit='Declarations only; no WRP/RoadNetwork/runtime consumer attested.'))
64:     sys.path.insert(0,str(cat.READER));backend=importlib.import_module('odol_reader');cat.loaded_reader_binding();summaries=[]
65:     for number,(name,h) in enumerate(SELECTED.items()):
66:         od=backend.ODOL.from_bytes(entries[name],strict=True);meta=cat.model_metadata(od);local=[]
67:         for li,lod in enumerate(od.lods):
68:             role=meta['lods'][li]['role']
69:             if role not in ('Visual','Roadway'):continue
70:             local.append(dict(lod=li,role=role,resolution=float(lod.resolution),stored_center=cat.xyz(lod.b_center),reader_applied_offset=[0,0,0],**faces(lod)))
71:         path=output/('local-faces-'+str(number)+'.json');dump(path,dict(model=name,sha256=h,bounding_center=meta['bounding_center'],lods=local,space='stored_local_raw',pivot_convention='UNKNOWN'))
72:         summaries.append(dict(model=name,sha256=h,local_geometry_sha256=sha(path),bounding_center=meta['bounding_center'],lods=[{k:v for k,v in row.items() if k not in ('faces','projection_wkt','material_masks')} for row in local],**discovery_fields(meta['roadway_present'])))
73:     del entries;cat.check_pins(pins);measurement=meter.memory()
74:     require(measurement['seconds']<=120 and max(measurement['peak_resident_bytes'],measurement['peak_commit_bytes'])<=2*1024**3,'resource_budget')
75:     return dict(status=status(summaries),models=summaries,sources=pins,config_bin_sha256=CONFIG_SHA,decoded_config_sha256=sha(output/'installed-config.cpp'),coverage=dict(selected=3,catalog_models=265,wrp_instances='NOT_READ',crossings='NOT_EVALUATED',all_visual_lods_and_roadway=True),elapsed_s=measurement['seconds'],peak_bytes=max(measurement['peak_resident_bytes'],measurement['peak_commit_bytes']),measurement=measurement,no_placement_build_or_dayz=True,limits=['Local geometry and config declarations only.','No native pivot/width/material friction proof.','World/crossing/access footprint remains unmeasured.','No vanilla coordinates or binaries for public release.'])
76: 
77: def main():
78:     ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
79:     meter.STARTED=START;meter.MAX_SECONDS=120;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
80:     try:r=run(a.output);dump(a.output/'report.json',r);return 0 if r['status']=='DISCOVERY_COMPLETE_NOT_PLACEMENT' else 2
81:     except Exception as e:dump(a.output/'report.json',dict(status='INCONCLUSIVE_DISCOVERY',error=type(e).__name__+':'+str(e),traceback=traceback.format_exc(),measurement=meter.memory()));return 2
82:     finally:stop.set()
83: 
84: if __name__=='__main__':raise SystemExit(main())

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\quality\test_road_consumer_discovery_ev112.py
1: from pathlib import Path
2: import math,struct,sys,unittest
3: from types import SimpleNamespace as NS
4: sys.path.insert(0,str(Path(__file__).resolve().parent))
5: import road_consumer_discovery_ev112 as d
6: 
7: def lod(points,faces,assignments=None,material_names=('asphalt','gravel')):
8:     assignments=assignments or [list(range(len(faces)))];sections=[]
9:     for i,ids in enumerate(assignments):sections.append(NS(texture_index=-1,material_index=i,mat_name='',get_face_indices=lambda fs,ids=ids:ids))
10:     raw=b''.join(struct.pack('<fff',*p) for p in points)
11:     return NS(vertices=[NS(x=p[0],y=p[1],z=p[2]) for p in points],vertex_raw=raw,faces=[NS(vertex_indices=f) for f in faces],sections=sections,textures=[],materials=[NS(material_name=n) for n in material_names])
12: 
13: class TestRoadB0(unittest.TestCase):
14:     def test_two_material_strip(self):
15:         l=lod([(0,0,0),(4,0,0),(4,0,10),(0,0,10),(6,0,0),(6,0,10)],[[0,1,2,3],[1,4,5,2]],[[0],[1]])
16:         r=d.faces(l);self.assertEqual(r['face_count'],2);self.assertEqual(r['projection_area_m2'],60);self.assertEqual([m['area_m2'] for m in r['material_masks']],[40,20]);self.assertEqual(r['faces'][1]['material'],'gravel')
17:     def test_curve_bbox_is_not_width(self):
18:         l=lod([(0,0,0),(2,0,0),(2,0,8),(8,0,8),(8,0,10),(0,0,10)],[[0,1,2],[0,2,5],[2,3,4,5]])
19:         r=d.faces(l);self.assertEqual(r['projection_area_m2'],32);self.assertNotIn('usable_width',r);self.assertEqual(d.discovery_fields(True)['usable_width'],'UNKNOWN')
20:     def test_shifted_pivot_raw_preserved(self):
21:         l=lod([(100,3,0),(104,3,0),(104,3,10),(100,3,10)],[[0,1,2,3]])
22:         r=d.faces(l);self.assertEqual(r['faces'][0]['xyz'][0],[100,3,0]);self.assertEqual(d.discovery_fields(True)['pivot_convention'],'UNKNOWN')
23:     def test_vertical_face_retained(self):
24:         l=lod([(0,0,0),(0,3,0),(0,3,4),(0,0,4)],[[0,1,2,3]])
25:         r=d.faces(l);self.assertEqual(r['face_count'],1);self.assertEqual(r['degenerate_projection_faces'],1);self.assertEqual(r['projection_area_m2'],0)
26:     def test_overlap_union_not_sum(self):
27:         l=lod([(0,0,0),(4,0,0),(4,0,10),(0,0,10)],[[0,1,2,3],[0,1,2,3]])
28:         self.assertEqual(d.faces(l)['projection_area_m2'],40)
29:     def test_raw_mismatch(self):
30:         l=lod([(0,0,0),(1,0,0),(0,0,1)],[[0,1,2]]);l.vertices[0].x=1
31:         with self.assertRaisesRegex(ValueError,'raw_decoded'):d.faces(l)
32:     def test_missing_section(self):
33:         l=lod([(0,0,0),(1,0,0),(0,0,1)],[[0,1,2]]);l.sections=[]
34:         with self.assertRaisesRegex(ValueError,'unassigned'):d.faces(l)
35:     def test_duplicate_assignment(self):
36:         l=lod([(0,0,0),(1,0,0),(0,0,1)],[[0,1,2]],[[0],[0]])
37:         with self.assertRaisesRegex(ValueError,'overlapping'):d.faces(l)
38:     def test_bad_index(self):
39:         l=lod([(0,0,0),(1,0,0),(0,0,1)],[[0,1,3]])
40:         with self.assertRaisesRegex(ValueError,'face_indices'):d.faces(l)
41:     def test_nonfinite(self):
42:         l=lod([(math.nan,0,0),(1,0,0),(0,0,1)],[[0,1,2]])
43:         with self.assertRaisesRegex(ValueError,'nonfinite'):d.faces(l)
44:     def test_missing_roadway(self):
45:         r=d.discovery_fields(False);self.assertIs(r['roadway_present'],False);self.assertEqual(r['usable_width'],'UNKNOWN');self.assertEqual(d.status([r]),'INCONCLUSIVE_DISCOVERY')
46:     def test_unknown_and_missing_field(self):
47:         r=d.discovery_fields(True);self.assertEqual(d.status([r]),'INCONCLUSIVE_DISCOVERY');del r['consumer_observed']
48:         with self.assertRaisesRegex(ValueError,'missing_discovery'):d.status([r])
49:     def test_no_default_zero_width(self):
50:         r=d.discovery_fields(True);r['usable_width']=0
51:         with self.assertRaisesRegex(ValueError,'invalid_width'):d.status([r])
52:     def test_empty_and_nonbool(self):
53:         with self.assertRaisesRegex(ValueError,'empty'):d.status([])
54:         with self.assertRaisesRegex(ValueError,'boolean'):d.discovery_fields(None)
55: 
56: if __name__=='__main__':unittest.main()

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\plans\ev112-road-consumer-discovery-b0-20261028.md
1: # Carreteras B0 — consumidor, pivotes y huella completa antes del piloto
2: 
3: Estado: REVISADO_PARA_IMPLEMENTAR. Preparación offline, sin colocación,
4: compilación, despliegue o DayZ. Continúa A; no repite catálogo501/265.
5: 
6: P5/P6/P9/P10/P11: reservar vías lisas y pasos navegables ahora, respetando P10
7: antes de mapeado global. La petición de preparar carreteras no modifica el agua,
8: extremos, islas ni la protección015-45. No asumir aceptación de conducción.
9: 
10: ## Referentes recuperados
11: 
12: [EXACT] evidence/road-preparation-receipts-20261028/recovery.json liga decisionP9
13: d510af67cc4016a0ba7192aa01c070d314b9bc7e49b6256ca6ffaf64fc05b843 al blob
14: histórico público; fondo1m/calado0.95m/corredor24m, excepciones bajos/Narva y
15: sin envolvente máxima de oleaje. No es ancho de carretera.
16: Bed-report23.95666642052773m²: cobertura histórica de8m, no de12/9m. No repetir
17: el discriminador ni convertir ese dato en superficie reparada por B3E2.
18: Catálogo instalado34c1cabe: asf1/asf2 con extensión12/9m; ancho útil UNDETERMINED.
19: 
20: ## Descubrimiento antes de diseñar poses
21: 
22: [DESIGN] Una unidad de lectura con fuentes instaladas/compiladas fijadas:
23: 1. Localizar y leer configuración de roads y consumidor real del terreno:
24:    objetos WRP, red vial y/o importador TerrainBuilder. No decidir objetos sueltos
25:    por el TXT FTT histórico. Registrar definiciones verificadas path:line/hash y
26:    ejemplos vanilla comparables; si sólo hay evidencia nominal, INCONCLUSIVE.
27: 2. Sobre asf1_25/asf2_25 y variantes candidatas documentadas, extraer de ODOL
28:    guardado Visual y Roadway: caras completas, materiales/texturas, selecciones,
29:    límites de superficie de apoyo y puntos de empalme. Espacio local/centro de
30:    bounding box/pivote real distintos. Comparar transformaciones con poses WRP
31:    conocidas y soporte nativo leído; no declarar convención por bbox solamente.
32: 3. Separar pavimento visible, arcén y superficie útil inferida del material.
33:    Material no prueba adherencia ni ancho transitable. Si falta regla de ancho,
34:    presentar dos alternativas concretas con huella y conflictos; no asignarla
35:    al azar ni pedir aprobación sin evidencia.
36: 4. Preparar cuatro corredores de revisión: seco49(5296,6000), cruce49/301 cerca
37:    de(4789.51465,5516.52197), Narva71 y kit118/cadena76. Coordenadas del personaje
38:    sólo seleccionan contexto; posición real de cruce viene de intersecciones
39:    exactas. La tabla de puentes no participa como oráculo de cruces ausentes.
40: 
41: Entregable: inventario de fuentes consumidoras, incertidumbres, máscaras de
42: Visual/Roadway en espacio local y propuestas de corredor con cobertura completa
43: de ancho y accesos; todo borrador sin poses autorizadas. Ríos/mar/lagunas por
44: superficies geométricas independientes; conservar extremos/nodos/contactos de
45: área pequeña y casos positivos diseñados. No buffer8m como prueba de huella12m.
46: Si agua/material/pivote no tienen referente suficiente, marcar ámbito desconocido
47: y seguir con fuentes independientes; ningún PASS global por ausencia de datos.
48: 
49: ## Validación y límites
50: 
51: Planreview180s, codereview180s/suite120s si se necesita extractor nuevo; una
52: extracción offline120s/2GiB. Geometría/arrays vanilla sólo locales, no Git público.
53: Fixtures independientes: tira con arcén de material distinto, curva con bbox
54: mayor que ancho útil, pivot desplazado, Roadway ausente, intersección marginal,
55: cruce en nodo y hueco de puente. Campos faltantes conservados, no defaultsPASS.
56: Cierre permitido DISCOVERY_COMPLETE_NOT_PLACEMENT o INCONCLUSIVE_DISCOVERY.
57: 
58: Después: plan B de piloto seco con tolerancias justificadas por consumidor;
59: mantener cross0.03m/grade0.065/chord0.03m existentes. Las exclusiones antiguas
60: 48m agua/470m Narva/18m extremos quedan NO EVALUADAS y necesitan puertas propias.
61: C: prueba de tablero/apoyos/accesos/agua y tránsito real en plan nativo separado,
62: después de hipótesis y revisión. Ni puente por cercanía ni pavimentado global.
63: 
64: ## Adjudicación de Fable5.1 — 77.828s
65: 
66: SOUND-with-fixes, entradas intactas, en evidence/road-b0-plan-review-20261028.
67: Codex verifica y adjudica antes de implementación:
68: 
69: - Se conserva UNA extracción120s/2GiB; no se acepta multiplicar presupuestos
70:   por WRP/ODOL/corredores. La primera extracción se acota a asf1_25, asf2_25
71:   y una curva identificada en el catálogo A, configuración instalada y metadatos
72:   disponibles. No decodificar un WRP entero como efecto lateral. Si no cabe o
73:   falta referente, guardar alcance parcial y campos UNKNOWN. Las ampliaciones
74:   requieren hipótesis y plan propios; no reiniciar el catálogo A.
75: - Fuente de piezas: PBO instalado structures_roads.pbo34c1cabe y sus entradas
76:   fijadas por A. P:/DZ/structures/roads/config.cpp es sólo fuente nominal;
77:   FTT TXT y verify_ftt_pilot.py NO prueban consumidor del motor. Config binaria
78:   instalada exige lectura/decodificación con identidad trazada antes de afirmar
79:   sus clases. Vanilla worlds_chernarusplus.pbo instalado existe; su identidad y
80:   entradas deben descubrirse antes de usarlo, sin asumir equivalencia con P:.
81: - consumer_observed = WRP_OBJECT / WRP_ROADNET / AMBOS / UNKNOWN. Debe citar
82:   path:offset o path:line, hash y alcance de observación. Clases en config
83:   solamente no prueban instancia WRP ni consumidor efectivo del mapa.
84: - Registrar bounding_center, centro de cada LOD, offset realmente aplicado por
85:   lector/consumidor, resolución Roadway, selecciones, caras y materiales.
86:   No inventar offset si el lector sólo expone vértices. pivot_convention UNKNOWN
87:   hasta referente independiente; tres instancias coherentes, propuestas por el
88:   revisor, tampoco demostrarían por sí solas convención o altura del motor.
89: - Fuente vial candidata: tests/regional_foundation_roads_v6/reference.npz en
90:   checkout principal, ligada por ROAD_SHA de pilot_visible_exposure_ev112.py.
91:   Fuente de superficies candidatas: surface-prototypes.npz/instances.npz y
92:   manifiesto de evidence/deployed-surface-prototypes-20261028; es inventario
93:   geométrico, NO referente independiente de intención/clases/anchuras de agua.
94:   No derivar cruces del listado de puentes. Intersección debe ser línea contra
95:   superficie/área completa, conservar contactos puntuales y casos marginales.
96:   Se rechaza prescribir segmento-segmento/tolerancia0 sin definir representación;
97:   el método y error numérico se fijan contra fuentes antes de implementar cruces.
98: - Campos obligatorios: consumer_observed, pivot_convention, usable_width,
99:   shoulder_material, roadway_present, crossings_exact, sources, coverage,
100:   elapsed_s y peak_bytes. Desconocido explícito; Roadway ausente=false y ancho
101:   UNKNOWN, nunca0. Cualquier UNKNOWN necesario impide DISCOVERY_COMPLETE.
102:   Las alternativas de anchura futuras mostrarán huellas/conflictos medidos.
103: - cross0.03/grade0.065/chord0.03 son restricciones preservadas para piloto B,
104:   no prueban B0. RAM, nueve regresiones y C1 SIN REVISAR siguen abiertos.

FILE E:\DayZ-Baltic-Build\shape-repair-20261025\run_road_b0_execution_20261028.py
1: from pathlib import Path
2: import hashlib,json,sys
3: W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');sys.path.insert(0,str(W/'tools/quality'))
4: import build_prism_b3e2_ev112 as runtime
5: sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
6: A=R/'road-b0-execution-approval-20261028.json';O=R/'road-b0-discovery-20261028';log=R/'road-b0-execution-driver-20261028.log'
7: assert not O.exists() and not log.exists(),'already_started'
8: a=json.loads(A.read_bytes());assert a['schema']=='ROAD_B0_EXECUTION_V1' and a['status']=='REVIEW_ADJUDICATED_TESTS_PASS' and Path(a['output']).resolve()==O.resolve()
9: required=[W/'tools/quality/road_consumer_discovery_ev112.py',W/'tools/quality/test_road_consumer_discovery_ev112.py',W/'plans/ev112-road-consumer-discovery-b0-20261028.md',Path(__file__).resolve(),Path(a['tests']),Path(a['review_adjudication'])]
10: assert all(str(p) in a['pins'] for p in required)
11: for p,h in a['pins'].items():assert sha(p)==h,p
12: suite=json.loads(Path(a['tests']).read_bytes());assert suite['status']=='TESTS_PASS' and suite['seconds']<=120 and suite['tests']>0
13: for p in required[:2]:assert suite['postimages'][str(p)]==a['pins'][str(p)]
14: receipt=runtime.base.run_tree([sys.executable,'-I',str(required[0]),str(O)],W,log,120)
15: assert receipt['stop_reason'] is None and receipt['seconds']<=120 and receipt['peak_sampled_tree_rss_bytes']<=2*1024**3
16: assert receipt['returncode'] in (0,2)
17: for p,h in a['pins'].items():assert sha(p)==h,p
18: report=json.loads((O/'report.json').read_bytes());assert 'error' not in report,report
19: assert report['status'] in ('INCONCLUSIVE_DISCOVERY','DISCOVERY_COMPLETE_NOT_PLACEMENT') and len(report['models'])==3
20: runtime.dump(O/'completion.json',dict(status=report['status'],report_sha256=sha(O/'report.json'),approval_sha256=sha(A),receipt=receipt,no_dayz_or_placement=True))
21: print(json.dumps(dict(status=report['status'],report_sha256=sha(O/'report.json'),seconds=report['elapsed_s'])))