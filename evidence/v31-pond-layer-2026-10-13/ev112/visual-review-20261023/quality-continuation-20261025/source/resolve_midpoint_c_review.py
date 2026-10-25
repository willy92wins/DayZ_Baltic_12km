from pathlib import Path
import hashlib,json
R=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=R/'runtime-midpoint-b/full/points.json';c=R/'runtime-midpoint-c/full/points.json'
before=read(b);after=read(c)
assert before['points']==after['points'] and len(after['points'])==4749
changes={k:dict(before=before.get(k),after=after.get(k)) for k in set(before)|set(after) if before.get(k)!=after.get(k)}
binding_b=R/'river-131-midpoint-b/f-pose-binding.json';binding_c=R/'river-131-midpoint-c/f-pose-binding.json'
assert binding_b.read_bytes()==binding_c.read_bytes()
out=dict(status='REVIEW_RESOLVED_NATIVE_GATES_REQUIRED',points_count=4749,points_array_exact=True,metadata_changes=changes,points_hashes=dict(B=sha(b),C=sha(c)),pose_binding=dict(sha256=sha(binding_c),copied_from=str(binding_b),to=str(binding_c),derivation='25 unchanged B models plus 37 exact U2 entries retain original F poses; package verifier checks the exact changed set'),notes=['The immutable composition receipt has a textual 26/25 typo; pose-statement-errata.json corrects it. Do not rerun the executed composer unchanged.','The maximum hull reduction 102/200 to 72/140 is versus effective U2; compact-a already had 72/140.','The offline overlay passed native-rejected B. Only native full4749 and grid300 may accept C within sampled scope.'])
(R/'midpoint-c-review/resolution.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
