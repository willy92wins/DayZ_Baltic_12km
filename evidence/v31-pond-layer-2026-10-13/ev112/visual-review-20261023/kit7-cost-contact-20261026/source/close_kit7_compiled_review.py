from pathlib import Path
import json,hashlib,sys
R=Path(__file__).parent;K=R/'river-kit7-midpoint-a-20261026';V=R/'kit7-compiled-review-20261026'
sys.path[:0]=['C:/temp/moto_lanes/review_g3/tools','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
from odol_reader import ODOL
import py3d
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
read=lambda p:json.loads(Path(p).read_text())
pinned={R/'river-kit7-a-on-f-20261026/author-report.json':'5bca325f35bfc1ddabfdc9368eb06ad5898ea8a2d3e4867f174e1e6aab5d152f',K/'author-report.json':'16193c0c96a4b1d127d3706ff698ab928c8139fa534a926a9c61e1bf40320b58',R/'kit7-midpoint-saved-review-20261026/inputs.json':'eccf904ce70080e8bbe8423da52aa91dfdac3463dcff7254292ac96e329f2da4',R/'kit7-midpoint-build-20261026/inputs.json':'159580d6d85e51286b1e55914935654036ab55888920e7d3d85b472f1ec9a335',K/'compiled-contact-review.json':'7d97d74f4b36995ee996d38ab3ae29296e83170b485035312de496ce277ab2ed',R/'verify_kit7_compiled_contact.py':'3cb67110509d02e0a0e99f3494f7e27869b1aab16eb703a99facf276b54130b7'}
assert all(sha(p)==h for p,h in pinned.items())
for p in [R/'kit7-midpoint-saved-review-20261026/inputs.json',R/'kit7-midpoint-build-20261026/inputs.json',R/'kit7-compiled-contact-20261026/inputs.json',V/'source-hashes.json']:
 assert all(sha(n)==h for n,h in read(p).items())
review=read(V/'review-response.json');done=read(V/'completion.json')
assert done['exit_code']==0 and done['inputs_unchanged'] and not review.get('is_error') and '**Dictamen: SOUND-with-fixes.' in review['result']
run=read(R/'kit7-compiled-contact-20261026/receipt.json');report=read(K/'compiled-contact-review.json')
assert run['returncode']==0 and not run['timeout'] and run['inputs_unchanged'] and report['status']=='PACKED_KIT7_COLLISION_AT_DERIVED_POSES_PASS'
rows=[];author=read(K/'author-report.json')
for inst in author['instances']:
 name=inst['model'].split('\\')[-1];od=ODOL.from_file(str(K/'temp/baltic_stream_pilot'/name),strict=True)
 geo=min(od.lods,key=lambda l:abs(l.resolution-1e13));assert py3d.classify_lod_resolution(geo.resolution)=='geometry'
 assert len([l for l in od.lods if py3d.classify_lod_resolution(l.resolution)=='geometry'])==1
 rows.append(dict(model=name,resolution=geo.resolution,kind='geometry'))
a,b=author['instances'][:2];assert a['site']==b['site']=='kit-7' and a['station'][1]==b['station'][0]
assert report['negative_controls']['scope_models']==[x['model'].split('\\')[-1] for x in [a,b]]
result=dict(status='ACCEPTED_KIT7_PACKED_OFFLINE',pinned_inputs={str(p):h for p,h in pinned.items()},compiled_report_sha256=sha(K/'compiled-contact-review.json'),review_sha256=sha(V/'review-response.json'),closure_source_sha256=sha(__file__),geometry_lods=rows,negative_control_adjacency_confirmed=True,resolution=['Pinned both author reports, both mutable input manifests and the produced full-contact report, then reverified every transitive binding. Original execution preserved.','Verified all139 actual ODOL LOD roles with canonical float-aware classifier; exact decimal1e13 is not a valid stored-float equality requirement.','Verified first two negative-control models share the same site and exact station boundary.'],limits=['Only isolated compiled offline candidate. No WRP/forest/native/navigation/client acceptance for kit7.','No reuse of the one-shot original reader without this mandatory closure receipt.'])
out=V/'accepted.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(rows))
