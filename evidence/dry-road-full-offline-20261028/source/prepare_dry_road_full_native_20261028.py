"""Prepare fresh calibration and full-sample missions after consumer review."""
from pathlib import Path
import collections,json,shutil,sys,time
R=Path(__file__).resolve().parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/quality'),str(W/'tools/water')]
import water_constraint_diagnostic_ev112 as meter
from buried_roadway_semantics_ev112 import verify_frozen
O=R/'dry-road-full-native-20261028';MOD=Path('P:/Mods/@DayZ_Baltic_EV112_DryRoadFull');M=Path('C:/temp/DayZ_MCP_130_dev/mpmissions')
MISSIONS=dict(calibration=M/'BalticDryRoadCal.BalticTrial',probe=M/'BalticDryRoadFull.BalticTrial')
meter.STARTED=time.monotonic();meter.MAX_SECONDS=300
def main():
    meter.require(not O.exists() and not MOD.exists() and all(not p.exists() for p in MISSIONS.values()),'fresh_targets_required');O.mkdir();stop=meter.bounded(O)
    try:
        pins={}
        def pin(p,h=None):
            got=meter.sha(p);meter.require(h is None or got==h,'input_drift:'+str(p));pins[str(p)]=got;return p
        def read(p):return json.loads(pin(p).read_bytes())
        review=read(R/'dry-road-full-consumer-review-20261028/completion.json')
        meter.require(review['returncode']==0 and not review['timeout'] and review['inputs_unchanged'] and review['finish_marker'] and not review['permission_denials'] and review['modelUsage']==['claude-fable-5-1'],'review_missing')
        # A separate adjudication seal is required, not mere completion of a review.
        approved=read(R/'dry-road-full-native-adjudication-20261028.json')
        meter.require(approved['status']=='REVIEWED_PREPARATION_READY','not_adjudicated');verify_frozen(approved['inputs'])
        for path,h in approved['inputs'].items():pin(Path(path),h)
        domain=R/'dry-road-effective-domain-20261028';report=read(domain/'report.json');meter.require(report['count']==2658,'domain_count')
        for path,h in report['inputs'].items():pin(Path(path),h)
        points=read(domain/'points.json');info=read(domain/'face-info.json');pin(domain/'roadway-triangles.npz')
        claims=read(R/'dry-road-full-review-claims-20261028/report.json')
        meter.require(claims['status']=='REVIEW_DIMENSIONS_VERIFIED_OFFLINE' and claims['support_face_vertex_counts']=={'3':1866},'actual_support_requires_review')
        for path,h in claims['inputs'].items():pin(Path(path),h)
        contact=claims['roadway_geometry_contact'];meter.require(all(contact['checks'].values()) and contact['minimum_pair_height_error_m']==contact['maximum_height_error_m']==0.,'neighbour_geometry_unproved')
        meter.require({p['id'] for p in points}==set(range(2658)),'domain_ids')
        for p in points:
            p['bed_shapes']=sorted({info[i]['model'] for i in p['roadway_faces'] if not info[i]['water']})
            meter.require(p['effective_bed'] is None or bool(p['bed_shapes']),'bed_unattributed')
            meter.require(set(p['foreign_dry_support']) <= {'baltic_stream_pilot/'+claims['foreign_model']},'unproved_foreign_bed')
            # Existing 1 cm ground acceptance interval straddles the pond/depth
            # predicates for this interval (producer samples at ground+1 cm).
            # This is unresolved coverage, never a tolerance relaxation or PASS.
            if p['water_ext'] is not None and -.01<=p['water_ext']-p['ground']<=.02:p['uncertain'].append('water_depth_numeric')
        package=read(R/'dry-road-final-package-20261028/report.json');meter.require(package['status']=='EXPERIMENTAL_PACKAGE_IDENTITY_PASS_METADATA_CONDITIONAL','package_gate')
        for path,h in package['inputs'].items():pin(Path(path),h)
        files={'narva_trial.pbo':(R/'package-kit7-fc-world-20261026/Addons/narva_trial.pbo','10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc'),'baltic_water_v30.pbo':(Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons/baltic_water_v30.pbo'),'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'),'baltic_stream_pilot.pbo':(R/'dry-road-final-package-20261028/Addons/baltic_stream_pilot.pbo',package['pbo_sha256'])}
        for path,h in files.values():pin(path,h)
        pre=read(R/'buried-roadway-semantics-20261028/prelaunch.json')
        pin(Path(pre['executable']),pre['executable_sha256']);pin(Path(pre['bridge_pbo']),pre['bridge_sha256'])
        sources=dict(probe=W/'missions/BalticVisualProbeV1.BalticTrial/init.c',calibration=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-contact-repair-20261026/producer/calibration/init.c')
        for path in sources.values():pin(path)
        meter.require('BALTIC_COLLISION_DIAGNOSTIC_V3' in sources['calibration'].read_text(),'wrong_calibration_version')
        for path in [Path(__file__).resolve(),W/'tools/quality/dry_road_native_consumer_ev112.py',W/'tools/quality/test_dry_road_native_consumer_ev112.py',W/'tools/water/eval_visual_probe_v31.py',R/'consume_dry_road_full_native_20261028.py',R/'capture_dry_road_full_native_20261028.ps1',R/'finish_dry_road_full_native_20261028.js',R/'check_dry_road_full_gate_20261028.py',R/'capture_owned_server_identity.ps1']:pin(path)
        verify_frozen(pins)
        (MOD/'Addons').mkdir(parents=True);deployed={}
        for name,(path,h) in files.items():
            dest=MOD/'Addons'/name;shutil.copyfile(path,dest);meter.require(meter.sha(dest)==h,'copied_package_drift');deployed[str(dest)]=h
        units={}
        for mode,mission in MISSIONS.items():
            mission.mkdir();shutil.copyfile(sources[mode],mission/'init.c');pin(mission/'init.c');(O/mode).mkdir()
            units[mode]=dict(mission=str(mission),producer_sha256=meter.sha(sources[mode]),count=2658 if mode=='probe' else 289)
        csv=''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in points);(MISSIONS['probe']/'points.csv').write_text(csv,encoding='ascii',newline='\n');pin(MISSIONS['probe']/'points.csv')
        meter.dump(O/'points.json',dict(points=points,count=2658,scope='All frozen first-model sample IDs; uncertainty explicitly retained'));pin(O/'points.json')
        meter.dump(O/'prelaunch.json',pre);pin(O/'prelaunch.json')
        doc=dict(status='PREPARED_FULL_PROBE_NOT_RUN',mod=MOD.name,units=units,deployed=deployed,inputs=pins,uncertain_labels=dict(collections.Counter(label for p in points for label in p['uncertain'])),uncertain_point_count=sum(bool(p['uncertain']) for p in points),measurement=meter.memory());meter.dump(O/'deployment.json',doc)
        print(json.dumps({k:v for k,v in doc.items() if k not in ('inputs','deployed')},indent=2))
    finally:stop.set()
try:main()
except Exception as exc:
    if O.exists():meter.dump(O/'failure.json',dict(type=type(exc).__name__,error=str(exc)))
    raise
