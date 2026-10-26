from pathlib import Path
import hashlib,json,gzip,sys,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water')]
from review_compact_collision_v31 import load
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
out=R/'kit7-collision-baseline-20261026';out.mkdir(exist_ok=False)
ref=R/'river-131-midpoint-c';candidate=R/'river-kit7-a-on-f-20261026'
arch=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/quality-continuation-20261025/collision/c/author-report.json.gz'
assert gzip.decompress(arch.read_bytes())==(ref/'author-report.json').read_bytes()
assert sha(candidate/'author-report.json')=='5bca325f35bfc1ddabfdc9368eb06ad5898ea8a2d3e4867f174e1e6aab5d152f'
reports={}
for label,root in [('native_C_reference',ref),('kit7_unpacked_candidate',candidate)]:
 author=json.loads((root/'author-report.json').read_text());rows=[]
 for inst in author['instances']:
  path=root/'source'/inst['model'].replace('\\','/');assert sha(path)==inst['sha256'];_,lods,_=load(path);geo=lods[1]
  selected=[id(f) for s in geo.selections.values() for f in s.faces]
  assert len(selected)==len(set(selected))==len(geo.faces)
  row=dict(model=path.name,sha256=inst['sha256'],bytes=path.stat().st_size,components=len(geo.selections),faces=len(geo.faces),vertices=len(geo.points),max_vertices_per_component=max(len(s.points) for s in geo.selections.values()),max_faces_per_component=max(len(s.faces) for s in geo.selections.values()))
  rows.append(row)
 totals={key:(max(r[key] for r in rows) if key.startswith('max_') else sum(r[key] for r in rows)) for key in ['components','faces','vertices','max_vertices_per_component','max_faces_per_component','bytes']}
 reports[label]=dict(author_sha256=sha(root/'author-report.json'),models=len(rows),totals=totals,rows=rows)
 print(label,totals,flush=True)
result=dict(status='SAVED_MODEL_BASELINES_MEASURED',sources={str(Path(__file__)):sha(__file__),str(W/'tools/water/review_compact_collision_v31.py'):sha(W/'tools/water/review_compact_collision_v31.py')},references=reports,limits=['Candidate ceilings may use observed native-C component complexity, but this is not a performance equivalence proof.','No model/terrain/PBO changed. Geometry author and independent full overlay/native gates remain mandatory.'])
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
