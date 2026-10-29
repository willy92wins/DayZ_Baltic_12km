from pathlib import Path
import json,hashlib,time
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1a-research-20261029';C=D/'capture';t=time.monotonic()
def sha(b):return hashlib.sha256(b).hexdigest()
b=(C/'material-table.bin').read_bytes();r=json.loads((C/'report.json').read_bytes());assert len(b)==399313 and sha(b)==r['table_sha256'];at=0;rows=[];names=[]
for i in range(4776):
 row=[]
 while True:
  assert at+4<=len(b);n=int.from_bytes(b[at:at+4],'little');at+=4
  if not n:break
  assert n<=4096 and at+n<=len(b);raw=b[at:at+n].decode('ascii');at+=n;row.append(raw);names.append(raw)
 rows.append(row)
assert at==len(b)
declared=[[r['materials'][i]['raw'] for i in row] for row in r['groups']];assert rows==declared
assert len(set(names))==len(r['materials'])==4775
sample=Path(r['materials'][0]['path']);raw=sample.read_bytes();assert sha(raw)==r['materials'][0]['sha256']
# Closed counterexample, not a new census: literal lines in the first material.
lines=raw.decode().splitlines();png=[{'line':i+1,'text':s.strip()} for i,s in enumerate(lines) if '.png"' in s];assert len(png)==2
assert all('.png' not in x['raw'] for x in r['references'])
result={'status':'RECONCILED_MATERIAL_ROWS_INCOMPLETE_REFERENCE_FILTER','report_sha256':sha((C/'report.json').read_bytes()),'table_sha256':sha(b),'rows':4776,'nonempty_rows':4775,'unique_material_names':4775,'table_reconciled':True,'reference_completeness':False,'counterexample':{'path':str(sample),'sha256':sha(raw),'bytes':len(raw),'omitted_literal_png_lines':png,'script_filter_line':56,'cause':'suffix tuple omitted .png, although source materials use .png in Stage0/1'},'total_research_read_bytes':r['bytes_read'],'source_sample_reread_bytes':len(raw),'seconds':time.monotonic()-t,'build_ready':False,'tests_geometric':0,'map_changed':False}
(D/'reconciliation.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))
