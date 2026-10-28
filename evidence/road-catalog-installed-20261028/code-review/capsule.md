Delegar JUICIO de código nuevo, Claude Fable5.1 nativo (identidad hoy CLI2.1.310 y respuesta plan75.937s). Codex ejecutor/integrador. Una lane read-only, herramientas deshabilitadas, sin escrituras/hijos. <=180s y850palabras. Devuelve SOUND/SOUND-with-fixes/NEEDS-WORK, bugs concretos con líneas/repro/consecuencia/fix, FIN_REVISION. Plan A revisado/adjudicado está debajo. Sólo catálogo instalado: sin poses, build ni DayZ. Tests en paralelo, no presumir PASS. Receptor verifica repros y corrige antes de una lectura120s/2GiB. Anclas leídas: read_pbo(Path) devuelve data,properties,dict entradas con rutas slash y case original; rechaza MIME!=0/duplicadas/truncadas. pbo_table(f,length) independiente normaliza lower/slash, valida propsduplicadas/sentinel/unsafe/duplicadas/bounds, devuelve props,lista(name,mime,size,offset). sections(lod) asigna cada cara exactamente una sección o ValueError, resuelve materiales/texturas. LectorODOL estrictoPinned con bytesfrom_bytes(strict=True) valida relaciones y EOFLOD; objetosfields reales leídos. Consumerfixtures son objetosanalíticos, no escritorODOLnuevo. Trailer sólo forma/bounds+SHA256externointegral, sin inventar algoritmoSHA1. PBOsha histórico se exige antes/después; si cambió esINCONCLUSIVE. verify_coverage tiene que conservar errores y cadaP3DdelPBO. No exporta arraysmallas, ni anchoútil. ROLElabels resoluciónconvencional, no semánticamotor. meter.bounded: daemon0.1s mata sólointerpreterpropio con os._exit(3) si >120s/2GiB peakresident/commit; resource-stop.json. memory midePID/elapsed/peaks porGetProcessMemoryInfo. Ningúnsubprocessen catálogo. No CLIhelpersconsumidos, sólofunciones. Señala falsos completos, integridad, errorclasification, leakarraysyfaltantes; no reabrir B3E ni producto.

FILE road_asset_catalog_ev112.py
1: """Installed road-asset measurements only. No poses or drivable-road acceptance."""
2: import os,time
3: START=time.monotonic()
4: for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
5: from pathlib import Path
6: import argparse,hashlib,importlib,io,json,math,struct,sys,traceback
7: HERE=Path(__file__).resolve().parent
8: sys.path[:0]=[str(HERE),str(HERE.parent/'playtest')]
9: import water_constraint_diagnostic_ev112 as meter
10: from attach_navmesh import read_pbo
11: from deployed_surface_inventory_ev112 import pbo_table,sections
12: 
13: PBO=Path('E:/SteamLibrary/steamapps/common/DayZ Exp/Addons/structures_roads.pbo')
14: PBO_SHA='34c1cabe608823dc09ec25dd62c3738a84075a7187484fc99dbdf4e1c2ed2f5f'
15: READER=Path('C:/temp/moto_lanes/review_g3/tools')
16: READER_PINS={'odol_reader.py':'fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57','bis_reader.py':'c9e5194aaf03e3c1a54578fa52950a1e0236c52ecb6b2597756b6a9ee618b70b','math_types.py':'b6ac444ca190a5cb8a7e5c0f423fafeceb31ddc8a805f2374b466ae5da6fdd10'}
17: HELPER_PINS={'deployed_surface_inventory_ev112.py':'b7a17598c68294622b4bf2ba8bb36afe74d91b24876b8451e10ab0425651bcb6','../playtest/attach_navmesh.py':'717b81469e0a799690d1586cd7a4492f079c3b2db626eec7e2815cd15896e062'}
18: digest=lambda data:hashlib.sha256(data).hexdigest()
19: f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
20: ROLES={f32(v):k for k,v in {'Geometry':1e13,'Memory':1e15,'LandContact':2e15,'Roadway':3e15,'ViewGeometry':6e15,'FireGeometry':7e15}.items()}
21: 
22: def require(condition,reason):
23:     if not condition:raise ValueError(reason)
24: 
25: def xyz(p):
26:     v=[float(p.x),float(p.y),float(p.z)];require(all(map(math.isfinite,v)),'nonfinite_point');return v
27: 
28: def bbox(points):
29:     require(all(len(v)==3 and all(map(math.isfinite,v)) for v in points),'invalid_points')
30:     return dict(min=[min(v[k] for v in points) for k in range(3)],max=[max(v[k] for v in points) for k in range(3)]) if points else None
31: 
32: def category(name):
33:     n=name.lower().replace('\\','/')
34:     if not n.endswith('.p3d'):return 'non_model'
35:     if n.startswith('parts/'):return 'road_part_by_path'
36:     if 'bridge' in n:return 'bridge_candidate_by_name'
37:     return 'other_model'
38: 
39: def check_table(data,props,entries):
40:     """Second independent table parse must cover all original entries and bytes."""
41:     independent,table=pbo_table(io.BytesIO(data),len(data))
42:     require(independent==props,'properties_disagree')
43:     require(props.get('prefix','').replace('\\','/').lower()=='dz/structures/roads','unexpected_prefix')
44:     require([e['name'] for e in table]==[k.lower() for k in entries],'entry_order_or_coverage')
45:     rows=[]
46:     for e,(name,payload) in zip(table,entries.items()):
47:         require(e['mime']==0 and e['size']==len(payload),'entry_method_or_size')
48:         require(data[e['offset']:e['offset']+e['size']]==payload,'payload_disagrees')
49:         rows.append(dict(name=name,normalized_name=e['name'],category=category(name),size=e['size'],mime=e['mime'],sha256=digest(payload)))
50:     end=table[-1]['offset']+table[-1]['size'] if table else len(data)
51:     trailer=data[end:];require(len(trailer)==0 or (len(trailer)==21 and trailer[0]==0),'unexpected_trailer')
52:     return rows,dict(payload_end=end,file_bytes=len(data),trailer_hex=trailer.hex(),trailer_semantics='UNINTERPRETED; whole-image SHA256 externally pinned')
53: 
54: def model_metadata(od,scale=1):
55:     require(scale==1,'nonunit_input_scale')
56:     require(not od.lod_errors and len(od.lods)==od.n_lods==len(od.resolutions) and od.n_lods>0,'incomplete_model')
57:     require(all(l is not None and l.lod_end_ok for l in od.lods),'incomplete_lod')
58:     mi=od.model_info;out=[]
59:     for i,l in enumerate(od.lods):
60:         resolution=float(l.resolution);require(math.isfinite(resolution) and resolution==od.resolutions[i],'resolution')
61:         vertices=[xyz(v) for v in l.vertices]
62:         require(len(l.vertex_raw)==12*len(vertices),'raw_vertex_length')
63:         raw=[list(v) for v in struct.iter_unpack('<fff',l.vertex_raw)]
64:         require(raw==vertices,'raw_decoded_vertex_disagreement')
65:         raw_box=bbox(raw);decoded_box=bbox(vertices);require(raw_box==decoded_box,'bbox_disagreement')
66:         for f in l.faces:require(len(f.vertex_indices) in (3,4) and all(0<=v<len(vertices) for v in f.vertex_indices),'face_indices')
67:         assignment,ss=sections(l)
68:         role=ROLES.get(resolution,'Visual' if 0<=resolution<1000 else 'Unclassified')
69:         selections=[]
70:         for s in l.named_selections:
71:             require(all(0<=v<len(vertices) for v in s.selected_vertices) and all(0<=f<len(l.faces) for f in s.selected_faces),'selection_indices')
72:             selections.append(dict(name=s.name,vertices=len(s.selected_vertices),faces=len(s.selected_faces),sectional=bool(s.is_sectional),sections=list(s.sections)))
73:         out.append(dict(index=i,resolution=resolution,role=role,vertices=len(vertices),faces=len(l.faces),bbox=raw_box,
74:                         declared_bbox=dict(min=xyz(l.b_min),max=xyz(l.b_max)),declared_center=xyz(l.b_center),vertex_raw_sha256=digest(l.vertex_raw),
75:                         selections=selections,properties=list(l.named_properties),sections=ss,textures=list(l.textures),
76:                         materials=[m.material_name for m in l.materials],proxy_count=len(l.proxies),frame_count=len(l.frames)))
77:     return dict(version=od.version,lods=out,model_bbox=dict(min=xyz(mi.bbox_min),max=xyz(mi.bbox_max)),bounding_center=xyz(mi.bounding_center),
78:                 animated=bool(mi.animated),scale=scale,space='model_local',usable_width='UNDETERMINED',roadway_present=any(l['role']=='Roadway' for l in out),
79:                 limits=['No model arrays exported.','Role labels describe stored resolutions, not engine behavior.','No driving or placement acceptance.'])
80: 
81: def verify_coverage(entries,models):
82:     expected=[e for e in entries if e['category']!='non_model']
83:     require([(e['name'],e['sha256']) for e in expected]==[(m['name'],m['sha256']) for m in models],'model_coverage')
84:     require(all(m['status'] in ('READ_STRICT','INCONCLUSIVE_PARSE') for m in models),'model_status')
85:     require(all(m.get('measurement',{}).get('usable_width')=='UNDETERMINED' for m in models if m['status']=='READ_STRICT'),'false_width')
86:     return 'CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE' if all(m['status']=='READ_STRICT' for m in models) and models else 'INCONCLUSIVE_CATALOG'
87: 
88: def collect(entries,payloads,decode,emit):
89:     models=[]
90:     for e in entries:
91:         if e['category']=='non_model':continue
92:         row=dict(name=e['name'],sha256=e['sha256'],category=e['category'])
93:         try:
94:             b=payloads[e['name']];require(digest(b)==e['sha256'] and b.startswith(b'ODOL'),'model_bytes')
95:             row.update(status='READ_STRICT',measurement=model_metadata(decode(b,strict=True)))
96:         except Exception as exc:row.update(status='INCONCLUSIVE_PARSE',error=type(exc).__name__+':'+str(exc))
97:         models.append(row);emit(row)
98:     return models
99: 
100: def check_pins(pins):
101:     for p,h in pins.items():require(meter.sha(p)==h,'input_changed:'+str(p))
102: 
103: def execute(output):
104:     pins={str(PBO):PBO_SHA,**{str(READER/n):h for n,h in READER_PINS.items()},**{str((HERE/n).resolve()):h for n,h in HELPER_PINS.items()}}
105:     check_pins(pins);meter.dump(output/'inputs.json',pins)
106:     # Parse original table even when the payload reader rejects compression.
107:     with PBO.open('rb') as f:props,table=pbo_table(f,PBO.stat().st_size)
108:     meter.dump(output/'source-table.json',dict(properties=props,entries=table))
109:     data,props,entries=read_pbo(PBO);require(digest(data)==PBO_SHA,'image_changed_during_read')
110:     rows,trailer=check_table(data,props,entries);meter.dump(output/'entries.json',rows);del data
111:     sys.path.insert(0,str(READER));backend=importlib.import_module('odol_reader')
112:     require(Path(backend.__file__).resolve()==(READER/'odol_reader.py').resolve(),'reader_module_shadowed')
113:     with (output/'models.jsonl').open('x',encoding='utf-8') as stream:
114:         def emit(row):stream.write(json.dumps(row,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
115:         models=collect(rows,entries,backend.ODOL.from_bytes,emit)
116:     status=verify_coverage(rows,models);del entries
117:     check_pins(pins);measurement=meter.memory()
118:     require(measurement['seconds']<=120 and max(measurement['peak_resident_bytes'],measurement['peak_commit_bytes'])<=2*1024**3,'resource_budget')
119:     return dict(status=status,pbo_sha256=PBO_SHA,entry_count=len(rows),model_count=len(models),strict_models=sum(m['status']=='READ_STRICT' for m in models),
120:                 failed_models=[m['name'] for m in models if m['status']!='READ_STRICT'],classes={c:sum(r['category']==c for r in rows) for c in sorted({r['category'] for r in rows})},
121:                 bridge_scope='Name/path candidates in this PBO only; not global bridge census.',trailer=trailer,measurement=measurement,
122:                 public_arrays=False,usable_width='UNDETERMINED',source_hashes_unchanged=True,no_build_or_dayz=True)
123: 
124: def main():
125:     ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
126:     meter.STARTED=START;meter.MAX_SECONDS=120;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
127:     try:
128:         r=execute(a.output);meter.dump(a.output/'report.json',r);print(json.dumps(r));return 0 if r['status']=='CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE' else 2
129:     except Exception as exc:
130:         meter.dump(a.output/'report.json',dict(status='INCONCLUSIVE_CATALOG',error=type(exc).__name__+':'+str(exc),traceback=traceback.format_exc(),measurement=meter.memory()));return 2
131:     finally:stop.set()
132: 
133: if __name__=='__main__':raise SystemExit(main())

FILE test_road_asset_catalog_ev112.py
1: import io,math,struct,tempfile,unittest,sys
2: from pathlib import Path
3: from types import SimpleNamespace as N
4: sys.path.insert(0,str(Path(__file__).resolve().parent))
5: import road_asset_catalog_ev112 as c
6: 
7: def vec(x,y,z):return N(x=x,y=y,z=z)
8: def model(roadway=False):
9:     vertices=[vec(-6,0,-12.5),vec(6,0,-12.5),vec(6,0,12.5)]
10:     section=N(texture_index=0,material_index=-1,mat_name='',get_face_indices=lambda faces:[0])
11:     lod=N(resolution=c.f32(3e15) if roadway else 0.,lod_end_ok=True,vertices=vertices,
12:           vertex_raw=b''.join(struct.pack('<fff',p.x,p.y,p.z) for p in vertices),faces=[N(vertex_indices=[0,1,2])],
13:           sections=[section],materials=[],textures=['road.paa'],named_selections=[],named_properties=[('class','road')],
14:           b_min=vec(-6,0,-12.5),b_max=vec(6,0,12.5),b_center=vec(0,0,0),proxies=[],frames=[])
15:     return N(lods=[lod],lod_errors={},n_lods=1,resolutions=[lod.resolution],version=54,
16:              model_info=N(bbox_min=vec(-6,0,-12.5),bbox_max=vec(6,0,12.5),bounding_center=vec(0,0,0),animated=False))
17: 
18: def pbo(names=('parts/ASf1.p3d','bridges/a.p3d','config.bin'),prefix='dz\\structures\\roads',mime=0,trailer=b''):
19:     header=b'\0'+struct.pack('<5I',0x56657273,0,0,0,0)+b'prefix\0'+prefix.encode()+b'\0\0'
20:     payloads={n:b'ODOL' if n.lower().endswith('.p3d') else b'cfg' for n in names}
21:     for n in names:header+=n.encode()+b'\0'+struct.pack('<5I',mime,0,0,0,len(payloads[n]))
22:     return header+b'\0'+bytes(20)+b''.join(payloads[n] for n in names)+trailer
23: 
24: def parse(data):
25:     with tempfile.TemporaryDirectory() as d:
26:         p=Path(d)/'test.pbo';p.write_bytes(data);raw,props,entries=c.read_pbo(p)
27:         return c.check_table(raw,props,entries),entries
28: 
29: class CatalogTests(unittest.TestCase):
30:     def test_complete_table_case_and_payload(self):
31:         (rows,tail),entries=parse(pbo());self.assertEqual(len(rows),3);self.assertEqual(rows[0]['name'],'parts/ASf1.p3d')
32:         self.assertEqual(rows[0]['category'],'road_part_by_path');self.assertEqual(tail['payload_end'],tail['file_bytes'])
33:     def test_optional_trailer_shape(self):
34:         self.assertEqual(len(parse(pbo(trailer=b'\0'+b'x'*20))[0][1]['trailer_hex']),42)
35:         with self.assertRaisesRegex(ValueError,'trailer'):parse(pbo(trailer=b'junk'))
36:     def test_duplicate_case(self):
37:         with self.assertRaisesRegex(ValueError,'Duplicate'):parse(pbo(names=('parts/A.p3d','parts/a.p3d')))
38:     def test_prefix_and_truncation(self):
39:         with self.assertRaisesRegex(ValueError,'prefix'):parse(pbo(prefix='wrong'))
40:         with self.assertRaises(ValueError):parse(pbo()[:-1])
41:     def test_compressed_not_green(self):
42:         with self.assertRaisesRegex(ValueError,'Compressed'):parse(pbo(mime=0x43707273))
43:     def test_omitted_payload_not_green(self):
44:         data=pbo();props,table=c.pbo_table(io.BytesIO(data),len(data))
45:         with self.assertRaisesRegex(ValueError,'coverage'):c.check_table(data,props,{'config.bin':b'cfg'})
46:     def test_analytic_bbox_raw_and_no_roadway(self):
47:         out=c.model_metadata(model());self.assertEqual(out['lods'][0]['bbox'],dict(min=[-6,0,-12.5],max=[6,0,12.5]))
48:         self.assertFalse(out['roadway_present']);self.assertEqual(out['usable_width'],'UNDETERMINED')
49:         self.assertNotIn('vertex_raw',out['lods'][0]);self.assertIsInstance(out['lods'][0]['vertices'],int)
50:     def test_roadway_not_usable_width(self):
51:         out=c.model_metadata(model(True));self.assertTrue(out['roadway_present']);self.assertEqual(out['usable_width'],'UNDETERMINED')
52:     def test_incomplete_lod_and_model(self):
53:         m=model();m.lods[0].lod_end_ok=False
54:         with self.assertRaisesRegex(ValueError,'incomplete_lod'):c.model_metadata(m)
55:         m=model();m.n_lods=2
56:         with self.assertRaisesRegex(ValueError,'incomplete_model'):c.model_metadata(m)
57:     def test_nan_and_scale(self):
58:         m=model();m.lods[0].vertices[0].x=math.nan
59:         with self.assertRaisesRegex(ValueError,'nonfinite'):c.model_metadata(m)
60:         with self.assertRaisesRegex(ValueError,'nonunit'):c.model_metadata(model(),2)
61:     def test_raw_disagreement(self):
62:         m=model();m.lods[0].vertices[0].x=-5
63:         with self.assertRaisesRegex(ValueError,'disagreement'):c.model_metadata(m)
64:     def test_bad_face_or_section_not_green(self):
65:         m=model();m.lods[0].faces[0].vertex_indices=[0,1,9]
66:         with self.assertRaisesRegex(ValueError,'face_indices'):c.model_metadata(m)
67:         m=model();m.lods[0].sections=[]
68:         with self.assertRaisesRegex(ValueError,'unassigned'):c.model_metadata(m)
69:     def test_denominator_retains_errors(self):
70:         (rows,_),entries=parse(pbo());calls=[];emitted=[]
71:         def decoder(b,strict):
72:             calls.append(strict)
73:             if len(calls)==1:raise ValueError('unsupported fixture')
74:             return model(True)
75:         records=c.collect(rows,entries,decoder,emitted.append)
76:         self.assertEqual(len(records),2);self.assertEqual(calls,[True,True]);self.assertEqual(len(emitted),2)
77:         self.assertEqual(c.verify_coverage(rows,records),'INCONCLUSIVE_CATALOG')
78:     def test_missing_duplicate_or_mutated_model(self):
79:         (rows,_),entries=parse(pbo());records=c.collect(rows,entries,lambda b,strict:model(),lambda row:None)
80:         self.assertEqual(c.verify_coverage(rows,records),'CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE')
81:         for bad in (records[:-1],records+[records[0]],records[::-1]):
82:             with self.assertRaisesRegex(ValueError,'coverage'):c.verify_coverage(rows,bad)
83:         records[0]['sha256']='0'*64
84:         with self.assertRaisesRegex(ValueError,'coverage'):c.verify_coverage(rows,records)
85:     def test_false_width(self):
86:         (rows,_),entries=parse(pbo());records=c.collect(rows,entries,lambda b,strict:model(),lambda row:None)
87:         records[0]['measurement']['usable_width']=12
88:         with self.assertRaisesRegex(ValueError,'false_width'):c.verify_coverage(rows,records)
89:     def test_unknown_category_is_retained(self):
90:         (rows,_),entries=parse(pbo(names=('ODD.P3D','notes.txt')))
91:         self.assertEqual(rows[0]['category'],'other_model');self.assertEqual(rows[1]['category'],'non_model')
92:     def test_nonfinite_resolution_and_selections(self):
93:         m=model();m.lods[0].resolution=math.nan
94:         with self.assertRaisesRegex(ValueError,'resolution'):c.model_metadata(m)
95:         m=model();m.lods[0].named_selections=[N(name='bad',selected_vertices=[9],selected_faces=[],is_sectional=False,sections=[])]
96:         with self.assertRaisesRegex(ValueError,'selection'):c.model_metadata(m)
97: 
98: if __name__=='__main__':unittest.main()

FILE ev112-road-preparation-20261028.md
1: # Preparar carreteras: pavimento, cruces y empalmes
2: 
3: Estado: REVISADO_PARA_IMPLEMENTAR_A. Petición viva: continuar las pruebas y
4: preparar carreteras en paralelo. Codex ejecutor/integrador. Esta preparación
5: no depende de obtener un nuevo PASS de colisión del río, pero la integración
6: de un piloto que lo cruce sí depende de resolver el conflicto correspondiente.
7: 
8: ## Producto y límites
9: 
10: P5/P6: conexiones existentes, piezas vanilla y anchuras humanas. P9: conservar
11: navegación, gálibos y agua. P10/P11: preparar ahora; emplazamiento físico global
12: y conducción después de la base de terreno/navegación. Esta petición permite
13: avanzar catálogo, corredores y prototipos aislados; no aprueba extender pavimento
14: a todos los ejes ni cambiar clases/ancho de producto para encajar una pieza.
15: No tocar recorte, reserva natural, islas, agua, extremos o protección015-45.
16: 
17: ## Descubrimiento y cuatro pilotos
18: 
19: El censo independiente ya recorre124cadenas/36467aristas/107180.669m. El overlay
20: contra modelos desplegados verificó2413contactos; sólo mide ejes, no anchura de
21: pavimento. Los715.422m de agua de modelo sin tablero coinciden con charca nominal;
22: no sumar ambas categorías. Otros1024.828m son mar nominal. NO son cantidades
23: de puentes omitidos. Recibos: evidence/road-surface-overlay-20261028.
24: 
25: | Piloto | Fuente/localización | Preparación | Puerta específica |
26: | --- | --- | --- | --- |
27: | R-PAVE-49 | Parada5296,6000; cadena49 | Primer corredor seco para comparar encaje de pavimento vanilla con la reserva vial | Elegir límites por geometría/agua, no sólo por la parada; 11secciones tienen evidencia nativa local, no toda la cadena |
28: | R-CROSS-49 | Personaje4789.51465,5516.52197; contacto cadena49/arista301 a11.601m | Resolver cruce completo, entradas y salidas | No colocar un puente en las coordenadas del personaje; verificar continuidad terrestre y navegación bajo cruce |
29: | R-NARVA-71 | Cadena71, contexto2391,6941 | Medir encaje del tablero real y accesos | Diagnóstico previo6.666grados/2.228m no es tolerancia; exigir cobertura del corredor, no sólo proximidad de ejes |
30: | R-END-76 | Kit118; cadena76/aristas124–129; instancia19394363 | Separar corredor y final del río con superficies reales | Solape medido en6aristas; Visual201 midió24m² de lecho sobre terreno en corredor. B3D/B3E no acreditan todavía resolución nativa |
31: 
32: La carretera49 recibió visto bueno visual local, con pavimentado y conducción
33: pendientes. Bosque/c0 no certifican estos pilotos. C1 sigue SIN REVISAR.
34: 
35: ## A. Catálogo instalado, antes de generar poses
36: 
37: [EXACT] PBO instalado de referencia descubierto en la configuración B2A:
38: E:/SteamLibrary/steamapps/common/DayZ Exp/Addons/structures_roads.pbo,
39: 318217469bytes en lectura de metadatos28-10. Hash histórico34c1cabe608823dc09ec25dd62c3738a84075a7187484fc99dbdf4e1c2ed2f5f;
40: debe comprobarse vivo, no atribuirle identidad actual por fecha/tamaño.
41: P:/dz/structures/roads/parts contiene familias asf1/asf2 y curvas; P: no es oráculo
42: del instalado. El piloto FTT03-10 exportó17piezas, no acreditó importación.
43: Su asf1_25 tenía bbox12x25m: NO se equipara bbox con ancho útil de calzada.
44: 
45: [DESIGN] Un inventario nuevo sólo lectura del PBO instalado: lista exhaustiva de
46: entradas parts/*.p3d y modelos de puente separados, sin filtrar sólo los usados
47: por FTT. Validar prefijo, rutas, duplicados y hash de PBO antes/después; conservar
48: orden/lista fuente. Leer cada modelo estrictamente con lector ya fijado por hash,
49: registrar errores por entrada sin borrarla del denominador. Geometría Visual,
50: Roadway, Geometry/Fire/View, puntos/selecciones/properties/materiales, cajas y
51: centro del modelo; ningún LOD ausente se fabrica. Exportar sólo medidas/metadatos
52: y hashes, nunca binarios vanilla al repositorio público.
53: 
54: Anclas a leer antes de implementar: tools/playtest/attach_navmesh.py:read_pbo
55: (Path, no str); tools/quality/compiled_dry_road_gate_ev112.py:read_backend;
56: lector C:/temp/moto_lanes/review_g3/tools/odol_reader.py. from_bytes/from_file,
57: campos y resolución de LOD se revalidan en sus definiciones. No importar ni
58: relanzar CLI de B2A/FTT/B3E consumidos. Si el formato de parts no es el esperado,
59: conservar INCONCLUSIVE_PARSE y proponer adaptación separada, no lector permisivo.
60: 
61: El inventario distingue superficie dibujada, superficie de apoyo y semántica
62: de carretera nativa. Un modelo plano sin Roadway no se descarta ni se acepta
63: como carretera por su bbox: investigar su consumidor nativo/configuración antes
64: de elegir objetos sueltos o RoadNetwork. La vía de generación no queda decidida
65: por el éxito del TXT FTT. Evitar introducir nuevas herramientas mientras no
66: exista un impedimento demostrado en el flujo actual.
67: 
68: Consumidor: cobertura exacta de entradas y hashes del PBO, muestras de geometría
69: analítica con bbox conocido y LOD ausente, y referentes vanilla documentados.
70: Negativos: entrada duplicada/omitida, prefijo erróneo, parse parcial, NaN, escala
71: no unitaria y Roadway ausente no pueden convertirse en aceptación de conducción.
72: El status de cierre será CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE, o
73: INCONCLUSIVE_CATALOG con lista de entradas no leídas; nunca PASS de carretera.
74: 
75: Presupuesto A: revisión de plan180s; code review180s y suite120s antes de una
76: lectura de catálogo120s/2GiB. Un censo, sin compilar/DayZ ni modificar P:/vanilla.
77: Parar ante datos cambiados o formato no soportado; no barrer versiones/lectores.
78: 
79: ## B. Corredores y plantilla del piloto seco
80: 
81: [DESIGN, después de A] Cargar las cadenas de referencia y máscaras/superficies
82: selladas actuales. Seleccionar ventana seca en49, conservando estación, XZ y
83: dirección; asignar el ancho a partir de calzada/material/regla de producto,
84: sin usar el nombre de la pieza ni bbox como única medida. Si falta esa regla,
85: dejarla pendiente explícita y agrupar una decisión nueva de producto.
86: 
87: Preparar footprint continuo de pavimento y márgenes/empalmes, no sólo eje.
88: Comprobar intersección geométrica de toda su anchura con agua, lechos, apoyos,
89: vegetación/objetos y plataformas. Conservar contactos de menos de una muestra,
90: extremos y cruces en nodos: no reutilizar exclusiones del gate de terreno para
91: declararlos resueltos. No eliminar obstáculos para conseguir PASS.
92: 
93: Se conservan los límites existentes de verify_roads_v30.py: cross0.03m,
94: grade0.065, chord0.03m. Ese gate excluye48m del agua,470m de Narva y18m de
95: extremos; son ámbitos NO EVALUADOS, no aceptación de cruces. El nuevo gate de
96: pavimento debe añadir juntas, ancho útil, apoyo continuo y cobertura de accesos,
97: con tolerancias justificadas por el consumidor real y revisadas antes de autoría.
98: No se inventa ahora una tolerancia de desalineación, hueco o velocidad segura.
99: 
100: Sólo tras revisión específica: un candidato aislado, poses/modelos sellados,
101: relectura WRP/PBO, pruebas nativas de superficie y conducción vanilla a velocidades
102: predefinidas. Medir saltos/golpes/atascos y coste de render; navmesh se regenera
103: tras mapeado según P10. No publicar el candidato como colocado antes de demostrarlo.
104: 
105: ## C. Cruces y extensión
106: 
107: R-CROSS-49 y R-NARVA-71 requieren prueba de espacio libre bajo tablero, apoyos
108: y continuidad completa del corredor a ambos lados. R-END-76 requiere que el lecho
109: no invada el corredor y que el agua y extremos sigan intactos. Estos son casos
110: de regresión del generador/validador, no parches locales sin censo global.
111: Después del piloto seco, proponer por clase las correcciones del resto de la red,
112: con detección de huecos basada en agua real y geometría de carretera independiente
113: del inventario de puentes. Nuevos candidatos/builds necesitan su plan/presupuesto.
114: RAM, aceptación visual, mapa completo y council ampliado permanecen abiertos.
115: 
116: ## Revisión adjudicada y contrato del catálogo A
117: 
118: Fable5.1 nativo,75.937s, SOUND-with-fixes; fuentes intactas. Recibos en
119: R/road-preparation-plan-review-20261028. Esta sección concreta A y prevalece
120: sobre formulaciones amplias anteriores; B/C siguen sin autoría autorizada.
121: 
122: - Denominador: TODAS las entradas del PBO, orden original, ruta original y
123:   normalizada, tamaño, método y hash. Todos sus P3D se intentan leer, incluidos
124:   modelos fuera de parts y candidatos de puente identificados por ruta/nombre.
125:   Esa clasificación nominal no demuestra uso del motor. No buscar otros PBOs.
126: - Pin externo del PBO:34c1cabe608823dc09ec25dd62c3738a84075a7187484fc99dbdf4e1c2ed2f5f.
127:   Si cambió, parar antes de extraer. Prefijo requerido dz/structures/roads;
128:   un prefijo distinto deja INCONCLUSIVE, sin reinterpretar rutas.
129: - Lector estricto fijado: odol_reader.py fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57,
130:   bis_reader.py c9e5194aaf03e3c1a54578fa52950a1e0236c52ecb6b2597756b6a9ee618b70b,
131:   math_types.py b6ac444ca190a5cb8a7e5c0f423fafeceb31ddc8a805f2374b466ae5da6fdd10.
132:   No necesidad de duplicarlo ni instrumentarlo: importar definición sin CLI;
133:   strict=True, n_lods exacto, lod_end_ok y errores vacíos. Liberar cada modelo.
134: - Dos lectores de tabla ya existentes contrastan orden, rutas, tamaños y payload:
135:   attach_navmesh.read_pbo:20-66 y deployed_surface_inventory_ev112.pbo_table:49-73.
136:   El primero rechaza MIME comprimido; no es decoder. Método no soportado conserva
137:   inventario de tabla y cierra INCONCLUSIVE_CATALOG, sin lectura parcial verde.
138:   Comprobar suma de cabecera/payload y forma del trailer; registrar sus bytes.
139:   Identidad íntegra por SHA256 externo antes/después. No atribuir semántica SHA1
140:   a un trailer sin referente verificado: el wiki BI advierte que es opcional y
141:   describe ambiguamente sha[20]/md5 (https://community.bistudio.com/wiki/PBO).
142:   Esto no pretende validar todas las variantes posibles del formato.
143: - Metadatos públicos: conteos, bbox por LOD, centros, materiales, propiedades,
144:   nombres/conteos de selecciones y hashes de bloques; sin arrays de vértices/caras.
145:   usable_width=UNDETERMINED siempre. Ningún bbox de Visual o Roadway es ancho útil.
146:   Escala de entrada unitaria, espacio local; ninguna pose mundial todavía.
147: - Fixtures analíticos prueban el consumidor con objetos de datos simples, NO un
148:   escritor ODOL nuevo. Negativos de tabla/PBO son bytes de cabecera documentada.
149:   Cruce independiente: bbox desde vertex_raw float32 con struct, frente a campos
150:   de vértices decodificados. FTT es histórico/P:, sólo comparación si hash igual;
151:   no exigir igualdad instalada por nombres ni rechazar una versión legítima.
152: - Puentes no hallados en este PBO: informar ausencia acotada, no inventario global.
153:   P9 exige agua mínima para calado y máxima para gálibo. El decision.json citado
154:   por product-spec no está en este checkout ni en main: conservar pendiente la
155:   recuperación del recibo antes del plan nativo; P9 y README del contrato sí leídos.
156: - Las11secciones: evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/
157:   quality-continuation-20261025/README.md. La cifra24m² de la tabla es contexto del
158:   handoff, no guarda de este catálogo; requiere su recibo exacto en la fase B.
159: 
160: Presupuestos sin cambio: code review180s, suite120s, un censo120s/2GiB.
161: Un método de parseo incompatible se conserva como inconcluso; no barrer lectores.