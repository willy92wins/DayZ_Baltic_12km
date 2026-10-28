"""Resolve concrete review uncertainties from the actual compiled neighbour."""
from pathlib import Path
import collections,hashlib,json,sys,time
R=Path(__file__).resolve().parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(W/'tools/quality'))
import compiled_dry_road_gate_ev112 as g
import dry_bed_road_candidate_ev112 as d
import numpy as np
O=R/'dry-road-full-review-claims-20261028';O.mkdir(exist_ok=False);g.meter.STARTED=time.monotonic();g.meter.MAX_SECONDS=120;stop=g.meter.bounded(O)
pins={}
def pin(p,h=None):
    got=g.sha(p);g.require(h is None or got==h,'input_drift');pins[str(p)]=got;return p
def read(p):return json.loads(pin(p).read_bytes())
try:
    root=R/'dry-road-effective-domain-20261028';report=read(root/'report.json');points=read(root/'points.json');fi=read(root/'face-info.json')
    for p,h in report['inputs'].items():pin(Path(p),h)
    meta=d.nz(R/'deployed-surface-prototypes-20261028/surface-prototypes.npz')['meta']
    counts=collections.Counter(int(meta[f['prototype_face']]['vertices']) if 'prototype_face' in f else 3 for f in fi)
    g.require(set(counts)=={3},'nontriangular_actual_support_requires_diagonal_discriminator')
    wb=[p['water_ext']-p['ground'] for p in points if p['water_ext'] is not None]
    shallow=[dict(id=p['id'],water_minus_ground=p['water_ext']-p['ground']) for p in points if p['water_ext'] is not None and 0<p['water_ext']-p['ground']<=.02]
    pbo=pin(R/'dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo','ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84');_,_,entries=g.read_pbo(pbo)
    name='cs_kit_118_0012.p3d';content=entries[name];reader_root=Path('C:/temp/moto_lanes/review_g3/tools');ODOL=g.read_backend(reader_root)
    for n,h in g.READER_HASHES.items():pin(reader_root/n,h)
    od=ODOL.from_bytes(content,strict=True);g.require(not od.lod_errors and all(l.lod_end_ok for l in od.lods),'incomplete_model')
    ar,lr=g.sections(od.lods[3]);roadpts=g.xyz(od.lods[3].vertices);bed=np.array([roadpts[f.vertex_indices] for i,f in enumerate(od.lods[3].faces) if not lr[int(ar[i])]['texture'].endswith('/water_ext.paa')])
    gp=g.xyz(od.lods[1].vertices);geo=np.array([gp[f.vertex_indices] for f in od.lods[1].faces]);normal=np.cross(geo[:,1]-geo[:,0],geo[:,2]-geo[:,0]);roof=geo[normal[:,1]>1e-10]
    contact=g.overlay(bed,roof);g.require(all(contact['checks'].values()) and contact['minimum_pair_height_error_m']==contact['maximum_height_error_m']==0.,'neighbour_Roadway_Geometry_not_exact')
    pin(Path(__file__).resolve());pin(W/'tools/quality/compiled_dry_road_gate_ev112.py');pin(W/'tools/water/review_compact_collision_v31.py')
    out=dict(status='REVIEW_DIMENSIONS_VERIFIED_OFFLINE',support_face_vertex_counts=dict(counts),shallow_water_up_to_2cm=shallow,water_minus_ground_range=[min(wb),max(wb)],foreign_model=name,model_sha256=hashlib.sha256(content).hexdigest(),roadway_geometry_contact=contact,inputs=pins,measurement=g.meter.memory(),limits=['No fresh calibration or full native launch.','Geometry equivalence of neighbouring model is offline evidence, not a new engine pass.'])
    g.meter.dump(O/'report.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('inputs','roadway_geometry_contact')},indent=2))
except Exception as e:g.meter.dump(O/'failure.json',dict(type=type(e).__name__,error=str(e)));raise
finally:stop.set()
