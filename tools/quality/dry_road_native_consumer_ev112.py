"""Independent native channels for the complete dry-road pilot sample universe.

Never compare Bullet BUILDING to the terrain hit returned by RV above a buried
bed. Numeric boundaries remain explicit incomplete coverage, not accepted points.
"""
from pathlib import Path
import math,sys,collections
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'water'))
from eval_visual_probe_v31 import parse,calibrate

def require(ok,why):
    if not ok:raise ValueError(why)

def evaluate(points,rows,calibration):
    require(points and len(points)==len(rows),'coverage_count')
    ids=[p['id'] for p in points]
    require(len(set(ids))==len(ids) and set(ids)==set(rows),'coverage_ids')
    margin=calibration['margin_m'];require(math.isfinite(margin) and .038<margin<.042,'vanilla_margin')
    failures=[];pending=[];details=[];coverage={c:collections.Counter() for c in ('ground','roadway','water','rv','bullet')}
    for p in points:
        r=rows[p['id']];states={};why={};uncertain=set(p['uncertain'])
        require(uncertain <= {'water_boundary_numeric','water_depth_numeric','flagged_surface','outside_changed_model_after_roundtrip','foreign_bed_support'},'unknown_uncertainty')
        require(p['expect'] in ('wet','dry'),'unknown_water_state')
        for k in ('x','z','ground','roadway'):require(math.isfinite(p[k]),'nonfinite_expectation')
        for k in ('effective_bed','water_ext'):
            require(p[k] is None or math.isfinite(p[k]),'nonfinite_surface')
        require(p['expect']!='wet' or p['water_ext'] is not None,'wet_without_waterway')
        require(p['effective_bed'] is None or p.get('bed_shapes'),'bed_without_identity')
        def put(channel,ok,reason):
            states[channel]='PASS' if ok else 'FAIL'
            if not ok:why[channel]=reason
        put('ground',abs(r['ground']-p['ground'])<=.01,'terrain_height')
        roadway_uncertain=bool(uncertain & {'water_boundary_numeric','flagged_surface','outside_changed_model_after_roundtrip'})
        water_uncertain=bool(uncertain & {'water_boundary_numeric','water_depth_numeric','flagged_surface'})
        if roadway_uncertain:
            states['roadway']='INCONCLUSIVE';why['roadway']='roadway_boundary_unresolved'
        else:
            put('roadway',abs(r['road']-p['roadway'])<=.03,'roadway_height')
        if water_uncertain:
            states['water']='INCONCLUSIVE';why['water']='water_or_depth_boundary_unresolved'
        else:
            if p['expect']=='wet':
                put('water',r['pond'] and not r['sea'] and r['depth']>0 and abs(r['surface']-p['water_ext'])<=.05,'pond_water_state_or_height')
            else:put('water',not r['pond'] and not r['sea'] and r['depth']<=0,'water_on_dry_control')
        bed=p['effective_bed']
        if bed is None or uncertain & {'outside_changed_model_after_roundtrip','flagged_surface','foreign_bed_support'}:
            states['rv']=states['bullet']='INCONCLUSIVE';why['rv']=why['bullet']='collision_surface_unresolved'
        else:
            expected=max(p['ground'],bed);shapes={x.lower().replace('/','\\') for x in p['bed_shapes']}
            rvshapes={x for x in r['rv_shapes'].split('|') if x}
            # Near-coincident bed/terrain may expose either identity, with the
            # unchanged 3 cm height bound. Unknown occluders never pass.
            identity=(not rvshapes if p['ground']>bed+.03 else bool(rvshapes) and rvshapes<=shapes if bed>p['ground']+.03 else rvshapes<=shapes)
            rvxz=all(abs(r['rv_pos'][i]-p[k])<=.01 for i,k in ((0,'x'),(2,'z')))
            put('rv',r['rv'] and identity and rvxz and abs(r['rv_pos'][1]-expected)<=.03,'RV_height_identity_or_ray_position')
            normal=r['bullet_normal'];length=math.sqrt(sum(v*v for v in normal))
            offset=None
            if .99<=length<=1.01 and normal[1]>0:
                base=(p['x'],bed,p['z']);offset=sum((b-a)*n/length for a,b,n in zip(base,r['bullet_pos'],normal))
            bxz=all(abs(r['bullet_pos'][i]-p[k])<=.01 for i,k in ((0,'x'),(2,'z')))
            put('bullet',r['bullet'] and r['bullet_shape'] in shapes and bxz and offset is not None and abs(offset-margin)<=.01,'Bullet_identity_ray_or_independent_bed_margin')
        for channel,state in states.items():
            coverage[channel][state]+=1
            if state=='FAIL':failures.append(dict(id=p['id'],channel=channel,reason=why[channel]))
            elif state=='INCONCLUSIVE':pending.append(dict(id=p['id'],channel=channel,reason=why[channel]))
        details.append(dict(id=p['id'],states=states,reasons=why,expected=p,measured=r))
    return dict(status='FAIL' if failures else 'INCONCLUSIVE_COVERAGE' if pending else 'SERVER_PROBE_PASS',points=len(points),failure_count=len(failures),inconclusive_count=len(pending),coverage={k:dict(v) for k,v in coverage.items()},failures=failures,inconclusive=pending,rows=details,limits=['Server queries at measured points only; no visual, driving, client CCT, RAM or global map acceptance.','All source IDs retained; uncertainty never becomes a passing channel.'])
