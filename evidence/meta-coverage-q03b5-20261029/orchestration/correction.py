from pathlib import Path
import json,time,hashlib,shutil
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'q03b5-local-author-20261029'
r=next(json.loads(x) for x in (R/'q03b5-code-review-recovery-20261029/stdout').read_text(encoding='utf-8').splitlines() if json.loads(x).get('type')=='result')
(D/'review.md').write_text(r['result']+'\n',encoding='utf-8');(D/'review-identity.json').write_text(json.dumps(r['modelUsage'],indent=2),encoding='utf-8')
for n in ['oracle.json','contract.json']:shutil.copyfile(D/n,D/('precorrection-'+n))
o=json.loads((D/'oracle.json').read_bytes());o['negative_codes'].update(dtype='SCHEMA',archive_link='EPOCH',archive_dtype='NPY_DTYPE',archive_shape='NPY_SHAPE')
(D/'oracle.json').write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((D/'contract.json').read_bytes());c['oracle_sha256']=sha(D/'oracle.json');(D/'contract.json').write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8')
(D/'adjudication.md').write_text('''# Q03B5 adjudicación y corrección cerrada

Fable5.1 nativo113.859s SOUND-with-fixes; Muse120.203s sin dictamen. H1 aceptado: oráculoR0 confundía validación CLI (SCHEMA) con rechazo del header sellado (NPY_DTYPE/NPY_SHAPE); tests no usaban la tabla. R0 preservado, R1 cambia sólo expectativas/códigos y pin del oráculo, nunca datos literales ni fuentes e967. Añadir pruebas CLI de dtype/cantidad, cambio de bytes pinado y vínculo de archive; consumir códigos externos, mantener tests del helper con etiquetas propias. Corrección de expectativa fundada en definición I.load y cabecera, no relajación para PASS.

H2 aceptado: consumidor ancla descriptor META completo literal antes de offsets35. H3 rechazada degradación de identidad por hipótesis de prefijos no observada; preservar guarda de nombres entre índices compartidos. Si falla, conservar rechazo y testigo, no rebajar. H4 riesgo de cardinalidad anotado:60s/4MiB intactos, sin truncar. H5 hipótesis de NumPy antiguo no verificada ni causa; fixture actual con filas duplicadas y campos excluidos distintos ya reconcilia. H6 pins oracle/plan son trazabilidad del driver/review, no nuevos inputs semánticos; verificar su SHA antes de prueba/captura, test fija oracle y no afirmar que I.load lee el plan.

Una corrección120s para H1/H2 y pin de oráculo en test. Postimagen la integra Codex con contexto compartido, no nueva revisión externa. Fuentes históricas aún sin abrir.
''',encoding='utf-8')
now=time.time();receipt={'started':now,'deadline':now+120,'contract_sha256':sha(D/'contract.json'),'oracle_sha256':sha(D/'oracle.json'),'scope':['H1 CLI/oracle','H2 descriptor','H6 oracle test pin']};(D/'correction-start.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt))
