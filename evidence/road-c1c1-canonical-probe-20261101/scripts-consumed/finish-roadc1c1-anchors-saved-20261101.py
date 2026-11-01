from pathlib import Path
import json,hashlib,os,time,sys,stat
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c1-local-author-20261101';started=json.loads((D/'author-start.json').read_bytes())['started'];sig=json.loads((D/'signature-r1.stdout').read_text(encoding='utf-8-sig'));assert sig['status']=='Valid' and sig['signer'].startswith('CN=Microsoft Windows,') and len(sig['chain'])==3
def dump(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
dump(D/'signature-receipt.json',{'rc':0,'source':'signature-r1.stdout','stdout_sha':hashlib.sha256((D/'signature-r1.stdout').read_bytes()).hexdigest(),'authenticode_status':sig['status'],'raw_current_time_chain_built':sig['chainBuilt'],'no_rerun':True,'adjudication':'Preparador añadía chainBuilt==true, no exigido por plan: este valor se conserva false y no se afirma validez de esa cadena. El contrato fija la firma Authenticode observada Valid y la cadena literal, no transforma false a true. Revisor recibe ambos fallos preparatorios.'})
class Saved:
 stdout=(D/'signature-r1.stdout').read_bytes()
r=Saved()
source=(R/'prepare-roadc1c1-anchors-20261101.py').read_text();exec(compile(source[source.index('def pin(p):'):],'anchored-saved-tail','exec'))
