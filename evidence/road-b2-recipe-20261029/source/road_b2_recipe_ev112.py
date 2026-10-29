"""Offline hypotheses, not road placement or a certified engine pivot.

Inputs are pinned saved faces from installed B0 models. Never extracts PBOs,
writes WRP, selects a best-fit hypothesis or derives usable width from a box.
"""
from pathlib import Path
import argparse,hashlib,json,itertools,time
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

HYPOTHESES=('raw_row','raw_column','origin_row','origin_column')
def require(v,msg):
    if not v:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def transform(points,center,row,hypothesis):
    require(hypothesis in HYPOTHESES,'hypothesis')
    p=np.asarray(points,dtype=np.float32).astype(np.float64);c=np.asarray(center,dtype=np.float32).astype(np.float64)
    matrix=np.asarray(row['matrix'],dtype=np.float32).astype(np.float64);t=np.asarray(row['translation'],dtype=np.float32).astype(np.float64)
    require(p.shape[-1]==3 and c.shape==(3,) and matrix.shape==(3,3) and t.shape==(3,) and all(np.isfinite(v).all() for v in (p,c,matrix,t)),'frame')
    require(np.array_equal(matrix@matrix.T,np.eye(3)) and np.linalg.det(matrix)==1,'proper_rotation')
    if hypothesis.startswith('origin'):p=p+c
    value=(p@matrix if hypothesis.endswith('row') else p@matrix.T)+t
    return value.astype(np.float32)

def fixtures(recipe,fixture):
    require(fixture['provenance']=='MANUAL_CLOSED_FORM_BEFORE_GENERATOR','fixture_provenance')
    require(fixture['order']==list(HYPOTHESES) and len(fixture['expected'])==3,'fixture_scope')
    measured=[]
    for i,row in enumerate(recipe['instances']):
        require(sha(row['faces'])==row['sha256'],'face_pin');model=read(row['faces'])
        points=[]
        for j,h in enumerate(HYPOTHESES):
            v=transform([fixture['local_probe']],model['bounding_center'],row,h)[0]
            expected=np.asarray(fixture['expected'][i][j],dtype=np.float32)
            require(np.array_equal(v.view(np.uint32),expected.view(np.uint32)),'literal_fixture_mismatch')
            points.append(v)
        measured.append(points)
    measured=np.asarray(measured,dtype=np.float32)
    ulp=float(np.max(np.spacing(np.abs(measured))));pairs=[]
    for a,b in itertools.combinations(range(4),2):
        distances=np.linalg.norm(measured[:,a,:].astype(float)-measured[:,b,:],axis=1);separation=float(np.max(distances))
        require(separation>.03 and separation>10*ulp,'hypotheses_not_distinct')
        pairs.append(dict(a=HYPOTHESES[a],b=HYPOTHESES[b],best_discriminator_m=separation,per_instance_m=distances.tolist()))
    return dict(probe_world_float32=measured.tolist(),world_ulp_m=ulp,distinctions=pairs)

def predict(recipe,fixture):
    require(recipe['status']=='HYPOTHESES_NOT_PLACEMENTS' and len(recipe['instances'])==3,'recipe_scope')
    require(len({r['name'] for r in recipe['instances']})==3 and all(r['id'] is None for r in recipe['instances']),'not_placed_ids')
    require(sha(recipe['fixtures'])==recipe['fixtures_sha256'],'fixture_pin')
    require(sha(recipe['derivation'])==recipe['derivation_sha256'],'derivation_pin')
    check=fixtures(recipe,fixture);private=[];summaries=[]
    for row in recipe['instances']:
        model=read(row['faces']);roles={x['role'] for x in model['lods']};require(roles=={'Visual','Roadway'},'required_roles')
        for h in HYPOTHESES:
            for lod in model['lods']:
                require(lod['reader_applied_offset']==[0,0,0] and lod['projection_complete'] is True,'reader_frame_incomplete')
                polygons=[];faces=[];max_ulp=0.;local_ulp=0.
                require(lod['face_count']==len(lod['faces']) and len(lod['faces'])>0,'face_count')
                for face in lod['faces']:
                    xyz=transform(face['xyz'],model['bounding_center'],row,h)
                    max_ulp=max(max_ulp,float(np.max(np.spacing(np.abs(xyz)))))
                    local_ulp=max(local_ulp,float(np.max(np.spacing(np.abs(np.asarray(face['xyz'],dtype=np.float32))))))
                    polygon=Polygon(xyz[:,[0,2]])
                    require(polygon.is_valid or polygon.area==0,'invalid_polygon:'+row['name']+':'+lod['role']+':'+str(face['face']))
                    if polygon.area>0:polygons.append(polygon)
                    faces.append({**face,'xyz':xyz.tolist()})
                require(polygons,'empty_footprint');footprint=unary_union(polygons)
                private.append(dict(instance=row['name'],hypothesis=h,role=lod['role'],faces=faces,footprint_wkt=footprint.wkt))
                summaries.append(dict(instance=row['name'],hypothesis=h,role=lod['role'],face_count=len(faces),area_m2=footprint.area,perimeter_m=footprint.length,
                  world_ulp_m=max_ulp,local_ulp_m=local_ulp,material_names=sorted({f['material'] for f in faces}),
                  bounds_for_extent_only=list(footprint.bounds),usable_width='UNDETERMINED'))
    all_ulp=max(x['world_ulp_m'] for x in summaries)
    require(all(p['best_discriminator_m']>10*all_ulp for p in check['distinctions']),'full_footprint_ulp_separation')
    return dict(status='RECIPE_HYPOTHESES_READY',probe=check,footprints=summaries,full_footprint_world_ulp_m=all_ulp,
         verified=['Pinned B0 local face coverage and float32 predictions for all four hypotheses.','Independent closed-form probe literals.'],
         assumed=['Future WRP objects use one of these four frames; not established by this unit.'],
         not_observed=['Engine pivot','Actual WRP serialization','Native contact','Road terrain support','Accesses and connections','Driving','RoadNetwork/ALB1']),private

def main():
    p=argparse.ArgumentParser();p.add_argument('--recipe',required=True,type=Path);p.add_argument('--sha',required=True);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    require(sha(a.recipe)==a.sha,'recipe_pin');require(not a.output.exists(),'fresh_output');a.output.mkdir();start=time.monotonic()
    try:
        recipe=read(a.recipe)
        for p,h in recipe['reference_inputs'].items():require(sha(p)==h,'reference_pin')
        report,private=predict(recipe,read(recipe['fixtures']));require(time.monotonic()-start<=120,'resource_budget')
        (a.output/'world-faces-private.json').write_text(json.dumps(private),encoding='utf-8')
        report.update(seconds=time.monotonic()-start,inputs={str(a.recipe):a.sha,recipe['fixtures']:recipe['fixtures_sha256'],recipe['derivation']:recipe['derivation_sha256'],**recipe['reference_inputs'],**{r['faces']:r['sha256'] for r in recipe['instances']}})
    except (ValueError,KeyError,TypeError,OSError) as e:
        report=dict(status='RESOURCE_FAIL' if str(e)=='resource_budget' else 'INCONCLUSIVE_DISCOVERY' if isinstance(e,ValueError) else 'READER_INCOMPATIBLE',reason=type(e).__name__+':'+str(e),seconds=time.monotonic()-start)
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');raise SystemExit(2)
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':report['status'],'seconds':report['seconds']}))
if __name__=='__main__':main()
