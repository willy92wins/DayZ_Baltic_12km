Delegar JUICIO correccion de instrumento RoadB0 R1. Una lane Fable5.1 CLI nativo medido hoy, Codex executor/integrator adjudica. Read-only sin herramientas/hijos/escrituras/Git.180s <=550palabras SOUND/SOUND-with-fixes/NEEDS-WORK con lineas y FIN_REVISION. No otra opinion sobre codigo intacto: revisar correccion NUEVA demostrada por fallo real. R0 ValueError:prefix en1.734s,716783616bytes ANTES de CfgConvert/caras. Source-table A PBO34c1 exacto props prefix DZ\structures\roads (D yZ mayusculas), guard anterior exigia dz. R1 exige literal instalado, PBOhash inmutable. Ademas brief anterior erroneo: base.run_tree REAL build_prism_b3e_ev112.py65 hace if child.returncode or reason:raise RuntimeError despuesdeguardar log.with_suffix(.receipt.json). No permite rc2 directamente. WrapperR1 captura SOLO RuntimeError, registra excepcion, relee receipt exclusivo, exige stop_reasonNone/seconds<=120/RSS<=2GiB/rc0o2, todos pins, report3modelos/sinerror yfuncionaccept_run_receipt comprueba par0+COMPLETE o2+INCONCLUSIVE. Fallo verdadero sigue rechazado. No cambiahelpers. R0 fuentes/recibos archivados, outputR1nuevo.22testsPASS0.954s incluyeprefijoreal yreceiptpositivo2,contradictorio0,error ytimeout. Unknownconsumer/pivot/width/crossings preservados;3modelos yconfigsololectura, sinWRP/build/deploy/DayZ. PlanR1 fijaunaextraccionnueva120s2GiB sinreintentos, no relajacion. Revisar contratos/recibo falso/reuso/alcance errores nuevos; no pedirrepetirA/R0. Fuente run_tree base ya sellada: observa PIDcreate_time/runnableowns, muestreaRSSdescendants, guarda .running, .receipt y arroja RuntimeError porrc!=0; mismo hash914bef55. Firmas CfgConvert -txt -dst verificadas, numpy/shapely importados en misma suiteGIS-I; no suponersiteuser. Fuentes completas actuales adjuntas, distinguir limitaciones fuera de R1. ReceptorCodex verificaadjudica.

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\quality\road_consumer_discovery_ev112.py
1: """Bounded RoadB0 subset: local full faces/materials, not placement or driving."""
2: import time
3: START=time.monotonic()
4: from pathlib import Path
5: import argparse,importlib,json,math,re,struct,sys,traceback
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
19: def check_prefix(value):
20:     # Exact installed header measured in catalog A; the archive is also SHA-bound.
21:     require(value=='DZ\\structures\\roads','prefix')
22: 
23: def accept_run_receipt(receipt,report):
24:     require(receipt['stop_reason'] is None and receipt['seconds']<=120 and receipt['peak_sampled_tree_rss_bytes']<=2*1024**3,'resource_receipt')
25:     require('error' not in report and len(report.get('models',[]))==len(SELECTED),'invalid_discovery_report')
26:     require((receipt['returncode'],report.get('status')) in ((0,'DISCOVERY_COMPLETE_NOT_PLACEMENT'),(2,'INCONCLUSIVE_DISCOVERY')),'exit_status_mismatch')
27: 
28: def faces(lod):
29:     points=[cat.xyz(p) for p in lod.vertices]
30:     require(list(struct.iter_unpack('<fff',lod.vertex_raw))==[tuple(p) for p in points],'raw_decoded_vertices')
31:     assignment,materials=sections(lod);rows=[];polygons=[];by_material={}
32:     for fi,face in enumerate(lod.faces):
33:         ids=list(face.vertex_indices);require(len(ids) in (3,4) and all(0<=i<len(points) for i in ids),'face_indices')
34:         xyz=[points[i] for i in ids];poly=Polygon([(p[0],p[2]) for p in xyz]);si=int(assignment[fi]);section=materials[si]
35:         # Retain every source face, including vertical/degenerate projections.
36:         state='AREA' if poly.is_valid and poly.area>0 else ('ZERO_AREA' if poly.area==0 and len(set((p[0],p[2]) for p in xyz))<3 else 'INVALID_PROJECTION')
37:         rows.append(dict(face=fi,vertex_indices=ids,xyz=xyz,section=si,material=section['material'],texture=section['texture'],projection=state))
38:         if state=='AREA':polygons.append(poly);by_material.setdefault((section['material'],section['texture']),[]).append(poly)
39:     footprint=union_all(polygons)
40:     return dict(faces=rows,face_count=len(rows),bbox=cat.bbox(points),sections=materials,
41:                 projection_area_m2=float(footprint.area),projection_wkt=footprint.wkt,
42:                 material_masks=[dict(material=k[0],texture=k[1],area_m2=float((g:=union_all(v)).area),wkt=g.wkt) for k,v in by_material.items()],
43:                 degenerate_projection_faces=sum(r['projection']=='ZERO_AREA' for r in rows),
44:                 invalid_projection_faces=sum(r['projection']=='INVALID_PROJECTION' for r in rows),
45:                 projection_complete=all(r['projection']!='INVALID_PROJECTION' for r in rows))
46: 
47: def visual_coverage(local):
48:     require(any(r['role']=='Visual' for r in local),'no_visual_lod')
49:     return all(r['projection_complete'] for r in local)
50: 
51: def discovery_fields(roadway):
52:     require(isinstance(roadway,bool),'roadway_not_boolean')
53:     return dict(consumer_observed='UNKNOWN',pivot_convention='UNKNOWN',usable_width='UNKNOWN',shoulder_material='UNKNOWN',roadway_present=roadway,crossings_exact='UNKNOWN')
54: 
55: def status(rows):
56:     required=('consumer_observed','pivot_convention','usable_width','shoulder_material','roadway_present','crossings_exact')
57:     require(bool(rows),'empty_discovery')
58:     for row in rows:
59:         require(all(k in row for k in required),'missing_discovery_field')
60:         require(isinstance(row['roadway_present'],bool),'roadway_not_boolean')
61:         require(row['consumer_observed'] in ('WRP_OBJECT','WRP_ROADNET','AMBOS','UNKNOWN'),'invalid_consumer')
62:         require(row['crossings_exact']=='UNKNOWN' or type(row['crossings_exact']) is bool,'invalid_crossings')
63:         require(row['usable_width']=='UNKNOWN' or (type(row['usable_width']) in (int,float) and math.isfinite(row['usable_width']) and row['usable_width']>0),'invalid_width')
64:         require(row['roadway_present'] or row['usable_width']=='UNKNOWN','width_without_roadway')
65:         if any(row[k]!='UNKNOWN' for k in required if k!='roadway_present'):
66:             evidence=row.get('source_evidence',[])
67:             require(bool(evidence) and all(isinstance(e.get('path'),str) and bool(e['path']) and isinstance(e.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',e['sha256']) and (type(e.get('line')) is int and e['line']>0 or type(e.get('offset')) is int and e['offset']>=0) for e in evidence),'missing_source_evidence')
68:     return 'INCONCLUSIVE_DISCOVERY' if any(row[k]=='UNKNOWN' for row in rows for k in required) else 'DISCOVERY_COMPLETE_NOT_PLACEMENT'
69: 
70: def run(output):
71:     pins={str(cat.PBO):cat.PBO_SHA,str(CFG):CFG_SHA,str(HERE/'road_asset_catalog_ev112.py'):CAT_SHA,
72:           **{str(cat.READER/n):h for n,h in cat.READER_PINS.items()},**{str((HERE/n).resolve()):h for n,h in cat.HELPER_PINS.items()},
73:           **{str(p):h for p,h in runtime.HELPERS.items()},str(HERE/'build_prism_b3e2_ev112.py'):'b131794d75a2748f40dfdd87e5e01389cf6434ca2f9b160253f70f241f538cbb'}
74:     cat.check_pins(pins);dump(output/'inputs.json',pins)
75:     raw,props,entries=cat.read_pbo(cat.PBO);require(cat.digest(raw)==cat.PBO_SHA,'pbo_changed');del raw
76:     check_prefix(props.get('prefix'))
77:     require(cat.digest(entries['config.bin'])==CONFIG_SHA,'config_changed')
78:     for name,h in SELECTED.items():require(cat.digest(entries[name])==h,'selected_changed:'+name)
79:     (output/'installed-config.bin').write_bytes(entries['config.bin'])
80:     runtime.run_process([str(CFG),'-txt','-dst',str(output/'installed-config.cpp'),str(output/'installed-config.bin')],output/'decode.log',min(60,max(1,120-(time.monotonic()-START))))
81:     cpp=(output/'installed-config.cpp').read_text(encoding='utf-8-sig');require(bool(cpp.strip()),'empty_decoded_config')
82:     # This is source evidence only: declarations do not imply WRP instances.
83:     source_lines=[dict(line=i+1,text=s.strip()) for i,s in enumerate(cpp.splitlines()) if 'StaticObj_Roads_Partasf' in s or any(n[6:-4] in s for n in SELECTED)]
84:     dump(output/'config-source-observations.json',dict(config_bin_sha256=CONFIG_SHA,decoded_sha256=sha(output/'installed-config.cpp'),lines=source_lines,consumer_observed='UNKNOWN',limit='Declarations only; no WRP/RoadNetwork/runtime consumer attested.'))
85:     sys.path.insert(0,str(cat.READER));backend=importlib.import_module('odol_reader');cat.loaded_reader_binding();summaries=[]
86:     for number,(name,h) in enumerate(SELECTED.items()):
87:         od=backend.ODOL.from_bytes(entries[name],strict=True);meta=cat.model_metadata(od);local=[]
88:         for li,lod in enumerate(od.lods):
89:             role=meta['lods'][li]['role']
90:             if role not in ('Visual','Roadway'):continue
91:             local.append(dict(lod=li,role=role,resolution=float(lod.resolution),stored_center=cat.xyz(lod.b_center),reader_applied_offset=[0,0,0],**faces(lod)))
92:         complete=visual_coverage(local)
93:         path=output/('local-faces-'+str(number)+'.json');dump(path,dict(model=name,sha256=h,bounding_center=meta['bounding_center'],lods=local,space='stored_local_raw',pivot_convention='UNKNOWN'))
94:         summaries.append(dict(model=name,sha256=h,local_geometry_sha256=sha(path),bounding_center=meta['bounding_center'],projection_complete=complete,lods=[{k:v for k,v in row.items() if k not in ('faces','projection_wkt','material_masks')} for row in local],**discovery_fields(meta['roadway_present'])))
95:     del entries;cat.check_pins(pins);measurement=meter.memory()
96:     require(measurement['seconds']<=120 and max(measurement['peak_resident_bytes'],measurement['peak_commit_bytes'])<=2*1024**3,'resource_budget')
97:     return dict(status=status(summaries),models=summaries,sources=pins,config_bin_sha256=CONFIG_SHA,decoded_config_sha256=sha(output/'installed-config.cpp'),coverage=dict(selected=len(SELECTED),catalog_reference='evidence/road-catalog-installed-20261028/report.json; historical denominator265, not recounted here',wrp_instances='NOT_READ',crossings='NOT_EVALUATED',all_visual_lods_and_roadway=True,projection_complete=all(r['projection_complete'] for r in summaries)),elapsed_s=measurement['seconds'],peak_bytes=max(measurement['peak_resident_bytes'],measurement['peak_commit_bytes']),measurement=measurement,no_placement_build_or_dayz=True,limits=['Local geometry and config declarations only.','No native pivot/width/material friction proof.','World/crossing/access footprint remains unmeasured.','No vanilla coordinates or binaries for public release.'])
98: 
99: def main():
100:     ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
101:     meter.STARTED=START;meter.MAX_SECONDS=120;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
102:     try:r=run(a.output);dump(a.output/'report.json',r);return 0 if r['status']=='DISCOVERY_COMPLETE_NOT_PLACEMENT' else 2
103:     except Exception as e:dump(a.output/'report.json',dict(status='INCONCLUSIVE_DISCOVERY',error=type(e).__name__+':'+str(e),traceback=traceback.format_exc(),measurement=meter.memory()));return 2
104:     finally:stop.set()
105: 
106: if __name__=='__main__':raise SystemExit(main())

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
55:     def test_boolean_width_and_bad_consumer(self):
56:         r=d.discovery_fields(True);r['usable_width']=True
57:         with self.assertRaisesRegex(ValueError,'invalid_width'):d.status([r])
58:         r=d.discovery_fields(True);r['consumer_observed']='WRP'
59:         with self.assertRaisesRegex(ValueError,'invalid_consumer'):d.status([r])
60:     def test_width_without_roadway(self):
61:         r=d.discovery_fields(False);r['usable_width']=4
62:         with self.assertRaisesRegex(ValueError,'width_without_roadway'):d.status([r])
63:     def test_known_requires_source(self):
64:         r=d.discovery_fields(True);r['consumer_observed']='WRP_OBJECT'
65:         with self.assertRaisesRegex(ValueError,'missing_source'):d.status([r])
66:         r['source_evidence']=[dict(path='synthetic.wrp',offset=100,sha256='a'*64)]
67:         self.assertEqual(d.status([r]),'INCONCLUSIVE_DISCOVERY')
68:     def test_bad_crossing_type(self):
69:         r=d.discovery_fields(True);r['crossings_exact']=1
70:         with self.assertRaisesRegex(ValueError,'invalid_crossings'):d.status([r])
71:     def test_bowtie_is_explicit_unknown_area(self):
72:         l=lod([(0,0,0),(2,0,2),(0,0,2),(2,0,0)],[[0,1,2,3]])
73:         r=d.faces(l);self.assertEqual(r['faces'][0]['projection'],'INVALID_PROJECTION');self.assertFalse(r['projection_complete']);self.assertEqual(r['invalid_projection_faces'],1)
74:     def test_no_visual_not_complete(self):
75:         with self.assertRaisesRegex(ValueError,'no_visual'):d.visual_coverage([dict(role='Roadway',projection_complete=True)])
76:         self.assertFalse(d.visual_coverage([dict(role='Visual',projection_complete=False)]))
77:     def test_exact_installed_prefix(self):
78:         d.check_prefix('DZ\\structures\\roads')
79:         for bad in ('dz\\structures\\roads','DZ\\structures\\road',None):
80:             with self.assertRaisesRegex(ValueError,'prefix'):d.check_prefix(bad)
81:     def test_rc2_valid_and_error_not_accepted(self):
82:         receipt=dict(returncode=2,stop_reason=None,seconds=1,peak_sampled_tree_rss_bytes=100)
83:         report=dict(status='INCONCLUSIVE_DISCOVERY',models=[1,2,3]);d.accept_run_receipt(receipt,report)
84:         with self.assertRaisesRegex(ValueError,'invalid_discovery'):d.accept_run_receipt(receipt,dict(report,error='prefix'))
85:         with self.assertRaisesRegex(ValueError,'exit_status'):d.accept_run_receipt(dict(receipt,returncode=0),report)
86:         with self.assertRaisesRegex(ValueError,'resource'):d.accept_run_receipt(dict(receipt,stop_reason='timeout'),report)
87:         with self.assertRaisesRegex(ValueError,'resource'):d.accept_run_receipt(dict(receipt,seconds=121),report)
88: 
89: if __name__=='__main__':unittest.main()

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

FILE E:\DayZ-Baltic-Build\shape-repair-20261025\run_road_b0_execution_r1_20261028.py
1: from pathlib import Path
2: import hashlib,json,sys
3: W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025');sys.path.insert(0,str(W/'tools/quality'))
4: import build_prism_b3e2_ev112 as runtime
5: import road_consumer_discovery_ev112 as discovery
6: sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
7: A=R/'road-b0-r1-execution-approval-20261028.json';O=R/'road-b0-discovery-r1-20261028';log=R/'road-b0-execution-r1-driver-20261028.log'
8: assert not O.exists() and not log.exists(),'already_started'
9: a=json.loads(A.read_bytes());assert a['schema']=='ROAD_B0_EXECUTION_V1' and a['status']=='REVIEW_ADJUDICATED_TESTS_PASS' and Path(a['output']).resolve()==O.resolve()
10: required=[W/'tools/quality/road_consumer_discovery_ev112.py',W/'tools/quality/test_road_consumer_discovery_ev112.py',W/'plans/ev112-road-consumer-discovery-b0-20261028.md',Path(__file__).resolve(),Path(a['tests']),Path(a['review_adjudication'])]
11: assert all(str(p) in a['pins'] for p in required)
12: for p,h in a['pins'].items():assert sha(p)==h,p
13: suite=json.loads(Path(a['tests']).read_bytes());assert suite['status']=='TESTS_PASS' and suite['seconds']<=120 and suite['tests']>0
14: for p in required[:2]:assert suite['postimages'][str(p)]==a['pins'][str(p)]
15: try:
16:  receipt=runtime.base.run_tree([sys.executable,'-I',str(required[0]),str(O)],W,log,120)
17: except RuntimeError as error:
18:  runtime.dump(R/'road-b0-r1-driver-exception-20261028.json',dict(error=str(error)))
19:  receipt=json.loads(log.with_suffix('.receipt.json').read_bytes())
20: assert receipt['stop_reason'] is None and receipt['seconds']<=120 and receipt['peak_sampled_tree_rss_bytes']<=2*1024**3
21: assert receipt['returncode'] in (0,2)
22: for p,h in a['pins'].items():assert sha(p)==h,p
23: report=json.loads((O/'report.json').read_bytes());assert 'error' not in report,report
24: discovery.accept_run_receipt(receipt,report)
25: runtime.dump(O/'completion.json',dict(status=report['status'],report_sha256=sha(O/'report.json'),approval_sha256=sha(A),receipt=receipt,no_dayz_or_placement=True))
26: print(json.dumps(dict(status=report['status'],report_sha256=sha(O/'report.json'),seconds=report['elapsed_s'])))

FILE C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\plans\ev112-road-b0-instrument-correction-20261028.md
1: # RoadB0 R1 — corrección del instrumento antes de extraer
2: 
3: Estado: PENDIENTE_REVISION. No hay nueva geometría ni cambio de producto.
4: Primer intento preservado en R/road-b0-discovery-20261028: errorValueError:prefix,
5: 1.734s/716783616bytes antes de CfgConvert o extracción de caras. No repetirlo.
6: 
7: Mecanismo demostrado: catálogo A source-table.json contiene prefix exacto
8: DZ\\structures\\roads; el nuevo guard esperaba dz minúsculo. R1 exige el
9: literal instalado observado, manteniendo hash34c1 del PBO. No cambia identidad.
10: Además build_prism_b3e_ev112.py:65 lanza RuntimeError para TODO rc distinto de0;
11: el brief de revisión decía erróneamente que base.run_tree permitía rc2. Recibo
12: se escribe antes del raise. Driver R1 conserva esa excepción y acepta únicamente
13: rc2 sin stop_reason, dentro de120s/2GiB, reporte INCONCLUSIVE sinerror/3modelos.
14: Resource/error/missing receipt o reporte siguen rechazados. No cambia el helper.
15: 
16: Código y driver nuevos requieren revisión180s, suite120s. Una extracción R1 en
17: salida nueva120s/2GiB, sin reintentos; alcance3piezas/config del B0 revisado.
18: Casos reales de prefijo y receipt2 esperado/error/timeout/retorno contradictorio
19: incluidos en regresión. R0 intacto, no elevar fallo de instrumento a fallo mapa.
20: Todo UNKNOWN sigue abierto; no colocar, compilar, desplegar ni arrancar DayZ.