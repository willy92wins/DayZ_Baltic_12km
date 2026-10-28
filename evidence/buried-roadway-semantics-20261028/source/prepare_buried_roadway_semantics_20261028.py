"""Prepare a NEW diagnostic mod/mission; never starts or manages DayZ."""
from pathlib import Path
import collections,json,shutil,sys,time
R=Path(__file__).resolve().parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path[:0]=[str(W/'tools/quality'),str(W/'tools/water')]
import numpy as np
from shapely import Point,Polygon,STRtree
import dry_bed_road_candidate_ev112 as d
import water_constraint_diagnostic_ev112 as meter
O=R/'buried-roadway-semantics-20261028';MOD=Path('P:/Mods/@DayZ_Baltic_EV112_DryRoadSemantics');MISSION=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticDryRoadSemantics.BalticTrial')
meter.STARTED=time.monotonic();meter.MAX_SECONDS=120
def main():
    meter.require(not O.exists() and not MOD.exists() and not MISSION.exists(),'fresh_targets_required');O.mkdir();stop=meter.bounded(O)
    try:
        pins={}
        def pin(p,h=None):
            digest=meter.sha(p)
            if h:meter.require(digest==h,'input_changed:'+str(p))
            pins[str(p)]=digest;return p
        def read(p):return json.loads(pin(p).read_bytes())
        report=read(R/'dry-road-final-package-20261028/report.json');meter.require(report['status']=='EXPERIMENTAL_PACKAGE_IDENTITY_PASS_METADATA_CONDITIONAL','package_gate_missing')
        for p,h in report['inputs'].items():pin(Path(p),h)
        domain=read(R/'dry-road-native-domain-r2-20261028/report.json')
        for p,h in domain['inputs'].items():pin(Path(p),h)
        points=read(R/'dry-road-native-domain-r2-20261028/points.json')
        candidate=np.load(pin(R/'dry-bed-road-candidate-20261028/kit-118-candidate.npz'))['grid'][:21]
        source=d.nz(pin(R/'pilot-visible-surface-extraction-20261028/models/cs_kit_118_0000.npz'));changed=np.any(source['source_grid']!=candidate,axis=2).ravel();cf=np.any(changed[source['source_triangles']],axis=1)
        a=R/'deployed-surface-prototypes-20261028';av=d.nz(a/'surface-prototypes.npz');inst=d.nz(a/'instances.npz');catalog=read(a/'model-catalog.json')
        meter.require(inst['ids'][inst['model_index']==3579].tolist()==[19394363],'changed_model_instances')
        meta=av['meta'].copy();meta['kind']=np.where(meta['kind']==0,1,np.where(meta['kind']==2,2,255))
        p=candidate.reshape(-1,3)[:,[0,2]];polys,verts,refs,_=d.local_water((av['vertices'],meta,inst,catalog),p.min(0),p.max(0));tree=STRtree(polys)
        pools=collections.defaultdict(list);excluded=collections.Counter()
        for row in points:
            faces=[j for k,j in row['sources'] if k=='face_centroid']
            if not faces or row['category']!='dry_interior' or row['bed'] is None or row['boundary_distance']<=1. or row['water_face_ids']:continue
            hits=tree.query(Point(row['xz']),predicate='intersects')
            if not len(hits) or any(int(refs[j,0])!=19394363 or int(refs[j,3])!=0 for j in hits):excluded['foreign_or_ambiguous_roadway']+=1;continue
            modified=any(cf[j] for j in faces);delta=row['bed']-row['ground']
            group=('buried_changed' if modified else 'buried_unchanged') if delta<-.08 else 'exposed_unchanged' if delta>.08 and not modified else None
            if group:pools[group].append(row)
        selected=[]
        for group,n in [('buried_changed',4),('buried_unchanged',4),('exposed_unchanged',8)]:
            pool=sorted(pools[group],key=lambda x:(x['bed']-x['ground'],x['id']));meter.require(len(pool)>=n,'insufficient_'+group)
            for i in np.linspace(0,len(pool)-1,n,dtype=int):
                row=pool[i];selected.append(dict(id=len(selected),domain_id=row['id'],group=group,x=row['xz'][0],z=row['xz'][1],ground=row['ground'],bed=row['bed'],sources=row['sources']))
        meter.require(len({p['domain_id'] for p in selected})==16,'duplicate_selected_position')
        from streambed_kit_v31 import tri_h
        terrain=np.load(pin(R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz',domain['inputs'][str(R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz')]))['heights']
        triangles=candidate.reshape(-1,3)[source['source_triangles']];bedtree=STRtree([Polygon(t[:,[0,2]]) for t in triangles])
        for row in selected:
            q=np.array([row['x'],row['z']]);ids=bedtree.query(Point(q),predicate='intersects');meter.require(len(ids)>0,'selected_outside_bed')
            height=max(float(d.solver.barycentric(triangles[i],q[None,:])[0]@triangles[i,:,1]) for i in ids)
            meter.require(height==row['bed'] and float(tri_h(terrain,*q))==row['ground'],'selected_expectation_mismatch')
            faces=[j for kind,j in row['sources'] if kind=='face_centroid']
            positions=[np.asarray([float(f'{x:.6f}') for x in triangles[j].mean(0)[[0,2]]],np.float32).astype(float) for j in faces]
            meter.require(any(np.array_equal(q,p) for p in positions),'selected_source_position')
        producer=pin(W/'missions/BalticVisualProbeV1.BalticTrial/init.c');files={'narva_trial.pbo':(R/'package-kit7-fc-world-20261026/Addons/narva_trial.pbo','10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc'),'baltic_water_v30.pbo':(Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons/baltic_water_v30.pbo'),'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'),'baltic_stream_pilot.pbo':(R/'dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo',report['pbo_sha256'])}
        for path,h in files.values():pin(path,h)
        old_pre=read(R/'kit7-overlap-native-20261026/prelaunch.json');exe=pin(Path(old_pre['executable']),old_pre['executable_sha256']);bridge=pin(Path(old_pre['bridge_pbo']),old_pre['bridge_sha256'])
        for path in (Path(__file__),W/'tools/quality/buried_roadway_semantics_ev112.py',W/'tools/quality/test_buried_roadway_semantics_ev112.py',W/'plans/ev112-buried-roadway-semantics-20261028.md',R/'consume_buried_roadway_semantics_20261028.py',R/'capture_buried_roadway_semantics_20261028.ps1',R/'finish_buried_roadway_semantics_20261028.js',R/'capture_owned_server_identity.ps1'):pin(path)
        for path,h in pins.items():meter.require(meter.sha(path)==h,'changed_before_preparation')
        (MOD/'Addons').mkdir(parents=True);MISSION.mkdir()
        deployed={}
        for name,(path,h) in files.items():shutil.copyfile(path,MOD/'Addons'/name);meter.require(meter.sha(MOD/'Addons'/name)==h,'copy_mismatch');deployed[str(MOD/'Addons'/name)]=h
        shutil.copyfile(producer,MISSION/'init.c');csv=''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in selected);(MISSION/'points.csv').write_text(csv,encoding='ascii',newline='\n')
        for path in (MISSION/'init.c',MISSION/'points.csv'):pin(path)
        meter.dump(O/'points.json',dict(points=selected,pool_counts={k:len(v) for k,v in pools.items()},excluded=dict(excluded),count=16));pin(O/'points.json')
        meter.dump(O/'prelaunch.json',dict(executable=str(exe),executable_sha256=meter.sha(exe),bridge_pbo=str(bridge),bridge_sha256=meter.sha(bridge)))
        doc=dict(status='PREPARED_DIAGNOSTIC_NOT_RUN',mod=MOD.name,mission=str(MISSION),producer_sha256=meter.sha(producer),deployed=deployed,inputs=pins,count=16,measurement=meter.memory());meter.dump(O/'deployment.json',doc);(O/'run').mkdir();print(json.dumps({k:v for k,v in doc.items() if k not in ('inputs','deployed')}))
    finally:stop.set()
try:main()
except Exception as exc:
    if O.exists():meter.dump(O/'failure.json',dict(type=type(exc).__name__,error=str(exc)))
    raise
