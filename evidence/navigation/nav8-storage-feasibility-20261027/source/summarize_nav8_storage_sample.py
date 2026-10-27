from pathlib import Path
import json,hashlib
R=Path(__file__).parent;O=R/'nav8-storage-sample-20261027';p=O/'result.json';r=json.loads(p.read_text())
summary=[]
for a in r['artifacts']:
 rows=a['rows'];n=len(rows)
 summary.append(dict(label=a['label'],sample_count=n,original_upstream16_exact=sum(x['residuals']['16']==0 for x in rows),with_unknown100_exact=sum(x['residuals']['16']==x['u32_at100'] for x in rows),posthoc_with_unknown100_and_8_times_field13_exact=sum(x['residuals']['16']==x['u32_at100']+8*x['fields8_14'][5] for x in rows),detail_triplet_all_zero=all(x['fields8_14'][1:4]==[0,0,0] for x in rows),nonzero_field13_rows=sum(x['fields8_14'][5]!=0 for x in rows)))
out=dict(status='INCONCLUSIVE_FORMAT_CONTRACT',sample_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),total_samples=sum(x['sample_count'] for x in summary),summary=summary,hypotheses=dict(H1='Serialized overhead observed; not causal heap profile or removable capacity.',H2='No verified DayZ contract for portals/references/extra section: writer/retiling rejected.'),posthoc_warning='The extra-size equation was discovered AFTER inspecting this sample. It is a fitted observation, not independent validation or semantic proof.',next='No new NM candidate authorized. Need supported generation control or a bounded source-geometry correction study; no blind tileWidth retry.',limits=['No heap causal isolation.','i9..i11=0 does not exclude other extra/detail data.','No genotype/consumer contract for opaque u32 at header offset100.','No map/height/RAM/client/actor acceptance.'])
(O/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
