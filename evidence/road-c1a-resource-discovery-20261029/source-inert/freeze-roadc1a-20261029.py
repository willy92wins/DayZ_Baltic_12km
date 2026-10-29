from pathlib import Path
import json,hashlib,shutil,collections,time,sys
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');P=R/'public-repo';E=W/'evidence/road-c1a-resource-discovery-20261029';E.mkdir(exist_ok=False)
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
def cp(s,d):d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,d);assert sha(s)==sha(d)
A=R/'road-c1a-research-20261029';B=R/'road-c1a1-recovery-20261029';a=load(A/'capture/report.json');b=load(B/'capture/report.json');c=load(B/'contract.json');check=load(B/'capture/oracle-check.json')
assert b['contract_sha256']==sha(B/'contract.json') and b['input_report_sha256']==sha(A/'capture/report.json')
assert check=={'positive':True,'negative_cases':2,'suffix_mutant_rejected':True,'geometric_tests':0}
assert len(a['materials'])==len(b['files'])==4775 and len(set(b['strings']))==len(b['strings'])==2061
for i,f in enumerate(b['files']):
 assert f['material_index']==i and f['bytes']==a['materials'][i]['bytes'] and f['sha256']==a['materials'][i]['sha256']
 assert all(type(line) is int and line>0 and type(idx) is int and 0<=idx<len(b['strings']) for line,idx in f['uses'])
oracle=load(B/'oracle.json');first=[[line,b['strings'][idx]] for line,idx in b['files'][0]['uses']];assert all(x in first for x in oracle['literal_counterexample'])
assert sum(p.stat().st_size for p in (A/'capture').iterdir())<=4*1024**2
assert sum(p.stat().st_size for p in (B/'capture').iterdir())<=4*1024**2
assert len(b['locations'])==2061 and [x['string_index'] for x in b['locations']]==list(range(2061))
assert sum(f['bytes'] for f in b['files'])==b['read_bytes']==10052971
reconcile={'status':'SAVED_DOCUMENTARY_BINDINGS_RECONCILED','capture_sha256':sha(B/'capture/report.json'),'input_sha256':sha(A/'capture/report.json'),'files':4775,'literal_counterexample_verified':True,'global_quote_count':'SELF_CONSISTENCY_ONLY','geometric_tests':0,'seconds':None,'no_sources_reopened':True,'build_ready':False}
dump(B/'reconciliation.json',reconcile)
summary={'status':b['status'],'material_table_rows':4776,'empty_material_rows':1,'materials':4775,'material_bytes':10052971,'quoted_uses':sum(len(f['uses']) for f in b['files']),'unique_strings':2061,'png_paths':2048,'paa_paths':8,'locations':dict(collections.Counter(x['state'] for x in b['locations'])),'located_png_bytes_metadata_only':sum(x['identity'][2] for x in b['locations'] if x['state']=='LOCATED_NOT_READ' and b['strings'][x['string_index']].endswith('.png')),'located_paa_bytes_metadata_only':sum(x['identity'][2] for x in b['locations'] if x['state']=='LOCATED_NOT_READ' and b['strings'][x['string_index']].endswith('.paa')),'capture_c1a':load(A/'run/completion.json'),'capture_c1a1':load(B/'run/completion.json'),'private_report_paths':[str(A/'capture/report.json'),str(B/'capture/report.json')],'private_report_sha256':[sha(A/'capture/report.json'),sha(B/'capture/report.json')],'limits_preserved':True,'C1A_reference_inventory':'INCOMPLETE_SUFFIX_FILTER','core_config_observations':a['core_configs'],'build_ready':False,'dependency_closure':'NOT_EVALUATED','compiled_terrain_decoder':'NOT_VERIFIED','map_changed':False,'C1':'NOT_REVIEWED','human_resolved':0,'geometric_tests':0}
dump(E/'summary.json',summary);cp(A/'reconciliation.json',E/'c1a-reconciliation.json');cp(B/'reconciliation.json',E/'c1a1-reconciliation.json')
dump(E/'errata.json',{'source':'c1a-reconciliation.json','field':'counterexample.script_filter_line','recorded':56,'actual':74,'evidence':'source-inert/investigate.py:74','original_pinned_receipt_unchanged':True})
for n in ('contract.json','oracle.json','seal-before-code.json','author-completion.json'):cp(B/n,E/'recovery'/n)
cp(A/'start.json',E/'initial/start.json');cp(A/'author-completion.json',E/'initial/author-completion.json');cp(R/'road-c1-planning-discovery-20261029/scope-before.json',E/'initial-r0/scope-before.json');cp(R/'road-c1-planning-discovery-20261029/disposition.json',E/'initial-r0/disposition.json')
for label,d in [('initial',A),('recovery',B)]:
 for n in ('completion.json','stdout','stderr'):cp(d/'run'/n,E/label/n)
 for p in (d/'capture').glob('phase-*.json'):cp(p,E/label/p.name)
cp(B/'capture/oracle-check.json',E/'recovery/oracle-check.json')
for name in ('road-c1-plan-review-20261029','road-c1a1-plan-review-20261029'):
 d=R/name
 for n in ('plan-reviewed.md','brief.txt','review.md','adjudication.md','approval.json','identity.json','pins.json'):cp(d/n,E/name/n)
 for n in ('completion.json','stderr'):cp(d/'run'/n,E/name/n)
for p in [R/'discover-roadc1-planning-20261029.py',A/'investigate.py',R/'reconcile-roadc1a-20261029.py',B/'recover.py',Path(__file__)]:cp(p,E/'source-inert'/p.name)
sys.path.insert(0,str(R/'dry-road-build-dependencies-20261028'));import psutil
receipts=[R/'road-c1-plan-review-20261029/run/completion.json',R/'road-c1a1-plan-review-20261029/run/completion.json',A/'run/completion.json',B/'run/completion.json'];identities={(int(k),v) for p in receipts for k,v in load(p)['identities'].items()};alive=[]
for pid,birth in identities:
 try:
  proc=psutil.Process(pid)
  if abs(proc.create_time()-birth)<.01 and proc.is_running():alive.append([pid,birth])
 except psutil.NoSuchProcess:pass
assert not alive;dump(E/'owned-processes-closed.json',{'identities_observed_retired':len(identities),'matching_alive':alive,'run':None,'lease':None,'foreign_processes_touched':False})
head=f'''RoadC1A/C1A1 completados como investigación de recursos, NO build.4776filas de material (una vacía),4775RVMAT propios/10052971B. Recuperación completa de85950usos de strings,2061strings distintas:2048PNG+8PAA localizados sin leer payloads y5literales sin resolver. Los PNG suman140323829B por metadata y losPAA40711646B; no identidad ni formatos certificados. C1A17.688s/42471424B, C1A1 única6.812s/54579200B. Dos controles léxicos negativos ymutante de sufijos rechazado,0testsgeométricos; reconciliación documental sobre snapshots, no lectorRVMATsemántico independiente.

R0exploratorio cap4096 rechazó4776 antes de materiales. C1A leyó4775textos pero omitióPNG por filtro de sufijos; reportef3eb0ab1 intacto, no reinterpretarlo como completo. ContraejemploP_000-000_L00.rvmat líneas9/14. C1A1 releyó sólo esos4775textos porSHA para conservar todas las cadenas, sin WRPs/PBOs/P3Ds/alturas/configsbin/core ni texturas. Contrato22dae243 y oráculo77ac398f completos en evidence/road-c1a-resource-discovery-20261029. No nueva geometría ni censo de población. Scripts inertes/consumidos, no promover ni repetir.

PlanRoadC1 Muse30.860s SOUND-with-fixes, seis precisiones adjudicadas. RecuperaciónplanMuse28.359s NEEDS-WORK adjudicado: refutadoF1,27.7MB incluía control17.3MB yconfigs; textos sólo10.05MB,cap16MiB intacto. F2–F7 concretados antes de autoría, postimagen sólo integradorCodex mismo contexto. No consenso ni aprobaciónexterna nueva inventada. Autores47.075s/49.586s dentro240. {len(identities)}identidades propias retiradas; sinoperación/run/lease.

Siguiente: diseñar/revisar RoadC1B stage real acotado y configuración aislada usando los4775RVMAT,2048PNG literales,8PAA y12recursos viales B4A3, más referenciasconfig/bin/core que siguen sin cierre. PNG no puede sustituirse por PAA por basename. Binconfig instalado dcf19f27 difiere de P:/bin/config.cpp42b4cf95; P:/core/config.cpp ausente, no prueba core innecesario. Config histórica mantiene requiredAddonsagua/piloto/navmesh ynoesconfiglab. No copiar variantes a ciegas.

Ningún lector localizado certifica OPRW0/3 yterreno/materiales. No afirmar imposibilidad global: Mikero bin enumerado tienepboProject peronoDeWrp/ConvertWrp; referenciawebv29 no prueba formato32local. Si se necesita observar compilado antes de diseñar lector, proponer plan propio COMPILE_PROBE_ONLY conpresupuesto/inputs ysin paquete aceptado/DayZ; jamás convertir escaneo de modelos/hashmagic enlectura de alturas. RoadC0fuentes0/3 intactas, no garantía decontrolvacío compilable. Q03C/Q05 históricos puedencontinuar sin dependencia circular aidentidadactual. Carreteras/ángulos/referentes y nueve humanos0resueltos/C1NOT_REVIEWED siguenabiertos.

'''
(R/'roadc1a-checkpoint-head-20261029.txt').write_bytes(head.encode())
(E/'README.md').write_bytes(('# RoadC1A — recursos de terreno del laboratorio\n\n'+head+'Fuentes privadas: dos reportes completos y tabla399313B permanecen en E:. Se publican resúmenes ligados, recibos, revisiones y scripts inertes. No captura de vanilla completa ni historial privado. P:/ sólo lecturas acotadas; mapa intacto. Revisión de plan no fue revisión de código productor de build: no existe todavía. No elevar estas comprobaciones documentales a suite de geometría.\n').encode())
dump(E/'web-references.json',{'date':'2026-10-29','sources':[{'url':'https://community.bistudio.com/wiki/Binarize','scope':'Arma3 official documentation; not installed DayZ ABI proof'},{'url':'https://github.com/Braini01/bis-file-formats/issues/24','scope':'author-reported v29 mismatch, not locally reproduced; not evidence for v32'},{'url':'https://mikero.bytex.digital/','scope':'vendor catalog, not local tool availability'}]})
for p in (W/'HANDOFF.md',R/'ACTIVE-WORK.md'):p.write_bytes(('# RoadC1A recursos reconciliados; publicación en curso\n\n'+head+'Seguir publish-roadc1a-20261029; no repetir investigación.\n\n').encode()+p.read_bytes())
master=W/'plans/quality-council-procedural-map-20261029.md';s=master.read_text(encoding='utf-8');a0=s.index('Checkpoint RoadC0');end=s.index('Petición humana',a0);s=s[:a0]+'''Checkpoint RoadC1A/C1A1 29-10:4775materiales propios y2048referenciasPNG/8PAA del laboratorio localizadas. Se corrigió en una recuperación nueva el filtro léxico que omitíaPNG, conservando el informe anterior parcial. No build ni cierre de recursos ni decoderOPRW0/3/terreno. Próximo planRoadC1B stage/config aislado; sólo sonda compilada si se revisa explícitamente. Fuentes0/3C0 intactas. Nueve humanos0resueltos,C1NOT_REVIEWED. Q03C/Q05/ángulos/referentes/reparación abiertos; council ya ejecutado.

'''+s[end:];master.write_bytes(s.encode())
dump(E/'files.json',{p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file() and p.name!='files.json'})
PUB=R/'publish-roadc1a-20261029';PUB.mkdir(exist_ok=False);paths=[]
for p in [*sorted(p for p in E.rglob('*') if p.is_file()),master,W/'HANDOFF.md',W/'plans/ev112-road-c1-compiled-laboratory-20261029.md',W/'plans/ev112-road-c1a1-complete-quoted-dependencies-20261029.md']:
 rel=p.relative_to(W);cp(p,P/rel);paths.append(rel.as_posix())
dump(PUB/'whitelist.json',sorted(paths));dump(PUB/'pins.json',{rel:sha(P/rel) for rel in paths});dump(PUB/'validation.json',{'documentary_reconciliation':True,'geometric_tests':0,'build':False,'native':False,'research_status':b['status'],'identities_retired':len(identities)})
print(json.dumps({'files':len(paths),'identities_retired':len(identities),'status':b['status']}))
