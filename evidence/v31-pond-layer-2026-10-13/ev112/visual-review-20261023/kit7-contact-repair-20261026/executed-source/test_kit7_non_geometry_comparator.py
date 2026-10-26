from pathlib import Path
import copy,hashlib,json,struct,sys
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),'C:/temp/moto_lanes/review_g3/tools']
from compare_non_geometry_lods_v31 import canonical_lod,normalized
from odol_reader import ODOL
name='cs_kit_7_0024.p3d';a=ODOL.from_file(str(R/'pilot-kit7-fc-20261026/temp/baltic_stream_pilot'/name),strict=True);b=ODOL.from_file(str(R/'river-kit7-contact-only-20261026/temp/baltic_stream_pilot'/name),strict=True)
for old,new in zip(a.lods,b.lods):
 if abs(old.resolution-1e13)/1e13<1e-4:continue
 assert canonical_lod(old)==canonical_lod(new)
road=min(b.lods,key=lambda l:abs(l.resolution-3e15));positive=canonical_lod(road);cases=[]
def rejected(label,mutator):
 changed=copy.deepcopy(road);mutator(changed)
 try:bad=canonical_lod(changed)!=positive
 except ValueError:bad=True
 assert bad,label;cases.append(dict(name=label,rejected=True))
rejected('reverse_winding',lambda l:l.faces[0].vertex_indices.reverse())
rejected('surface_label_swap',lambda l:setattr(l.sections[0],'texture_index',1-l.sections[0].texture_index))
rejected('vertex_1cm',lambda l:setattr(l.vertices[0],'x',l.vertices[0].x+.01))
rejected('remove_face',lambda l:l.faces.pop())
rejected('section_coverage_gap',lambda l:setattr(l.sections[0],'face_lower',l.sections[0].face_lower+8))
rejected('opaque_stream_change',lambda l:setattr(l,'st_raw',l.st_raw+b'x'))
nan1=struct.unpack('<d',bytes.fromhex('010000000000f87f'))[0];nan2=struct.unpack('<d',bytes.fromhex('020000000000f87f'))[0]
assert normalized(nan1)==normalized(nan1) and normalized(nan1)!=normalized(nan2)
report=dict(status='NON_GEOMETRY_COMPARATOR_CONTROLS_PASS',actual_reordered_binary_pair=True,negative_cases=cases,nan_payload_bits_preserved=True,source_sha256=hashlib.sha256((W/'tools/water/compare_non_geometry_lods_v31.py').read_bytes()).hexdigest())
(R/'kit7-contact-only-build-20261026/nongeometry-controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

