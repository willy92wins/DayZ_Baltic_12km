"""Verify compiled coverage, placement, wet/dry exposure and native field for seam pieces."""
from pathlib import Path
import json,sys
import numpy as np
import shapely
from shapely.geometry import Polygon,box

B=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009')
BASE=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(BASE))
from author_global_visual import sha,read_pbo,ODOL
from audit_frozen_visual import visible_error,triangle_areas
from v30_common import tri_sample

def main():
    authored=json.loads((B/'seam-authoring.json').read_text());field=np.load(BASE/'preserved-field.npy')
    assert sha(BASE/'preserved-field.npy')==authored['field_sha256']
    patch=B/'compile-seams/out/baltic_water_v30.pbo';_,props,packed=read_pbo(patch)
    _,oldprops,old=read_pbo(BASE/'compile-r2/out/baltic_water_v30.pbo')
    assert props==oldprops and old['config.bin']==packed['config.bin']
    assert set(packed)=={r['model'] for r in authored['rows']}|{'config.bin'}
    terrain=np.load(B/'candidate/terrain.npz');h=terrain['heights'].astype(float)
    checks=[]
    for row in authored['rows']:
        name=row['model'];path=B/'compile-seams/temp/baltic_water_v30'/name;assert path.read_bytes()==packed[name]
        od=ODOL.from_file(str(path));bc=od.model_info.bounding_center;center=np.array([bc.x,bc.y,bc.z]);origin=np.array(row['origin'])
        assert center[0]==center[2]==0,(name,'Centre is not exact',center.tolist())
        position=np.array(origin+center,dtype=np.float32).astype(float)
        assert np.array_equal(position[[0,2]],origin[[0,2]])
        r,c=row['row'],row['col'];level=origin[1];f=field[r,c];cell=box(c*6,12276-r*6,c*6+6,12282-r*6)
        road=min(od.lods,key=lambda l:abs(l.resolution-3e15));vis=min(od.lods,key=lambda l:abs(l.resolution-1))
        pond=min(od.lods,key=lambda l:abs(l.resolution-1e13));memory=min(od.lods,key=lambda l:abs(l.resolution-1e15))
        assert len(od.lods)==4 and ('class','pond') in pond.named_properties and ('damage','no') in pond.named_properties
        def verts(l):return np.array([(p.x,p.y,p.z) for p in l.vertices])+position
        rv,vv,mv=verts(road),verts(vis),verts(memory)
        assert np.ptp(rv[:,1])==0
        physical_error=float(np.max(np.abs(rv[:,1]-level)))
        rg=shapely.union_all([Polygon(rv[q.vertex_indices][:,[0,2]]) for q in road.faces])
        vg=shapely.union_all([Polygon(vv[q.vertex_indices][:,[0,2]]) for q in vis.faces])
        authored_geom=shapely.from_geojson(row['geometry']);gap=shapely.from_geojson(row['gap_geometry'])
        gap_remaining=float(gap.difference(rg).area);outside=float(rg.difference(cell).area)
        assert box(*rg.bounds).equals(Polygon(mv[[0,2,3,1]][:,[0,2]])),(name,'Memory bounds differ from actual symmetric geometry')
        tri=np.array([vv[q.vertex_indices] for q in vis.faces]);x,z=tri[:,:,0],tri[:,:,2]
        cx,cz=x.mean(1),z.mean(1);fc=(x-c*6)/6;fr=(12282-r*6-z)/6
        target=np.where(((cx-c*6)/6>=(12282-r*6-cz)/6)[:,None],
            f[0]+fc*(f[1]-f[0])+fr*(f[3]-f[1]),f[0]+fr*(f[2]-f[0])+fc*(f[3]-f[2]))
        ground=tri_sample(h,x,z);depth=tri[:,:,1]-ground
        area=np.abs((x[:,1]-x[:,0])*(z[:,2]-z[:,0])-(z[:,1]-z[:,0])*(x[:,2]-x[:,0]))/2
        wet_area=triangle_areas(depth)/18*area
        upper=(cx-c*6)/6>=(12282-r*6-cz)/6
        classes=np.c_[np.full(len(tri),terrain['cls'][r,c]),np.where(upper,terrain['cls'][r,c+1],terrain['cls'][r+1,c]),np.full(len(tri),terrain['cls'][r+1,c+1])]
        dry_area=float(wet_area[np.all(classes==0,axis=1)].sum())
        field_error=float(np.max(np.abs(tri[:,:,1]-target)))
        offset=float(visible_error(depth,tri[:,:,1]-level,wet_area).max(initial=0))
        gates=dict(exact_xz_placement=True,nominal_physical_level=physical_error<1e-6,
                   visible_field=field_error<2e-6,within_frozen_cell=outside<1e-12,gap_covered=gap_remaining<1e-10,
                   shared_visual_physical_footprint=rg.symmetric_difference(vg).area<1e-10,
                   source_footprint=rg.symmetric_difference(authored_geom).area<1e-5,
                   no_new_dry_water=dry_area<1e-8,visible_offset=offset<=.35003)
        checks.append(dict(object_id=row['object_id'],model=name,row=r,col=c,compiled_sha256=sha(path),
             matrix=np.eye(3).ravel().tolist()+position.tolist(),gates=gates,remaining_gap_m2=gap_remaining,
             physical_level_error_m=physical_error,field_error_m=field_error,new_dry_water_m2=dry_area,
             raw_footprint_m2=float(rg.area),visible_offset_m=offset))
    failures=[r for r in checks if not all(r['gates'].values())]
    result=dict(status='PASS_COMPILED_EXACT_SEAMS' if not failures else 'FAIL_COMPILED_EXACT_SEAMS',models=len(checks),
                patch_sha256=sha(patch),authoring_sha256=sha(B/'seam-authoring.json'),checks=checks,failures=failures,
                remaining_gap_m2=sum(r['remaining_gap_m2'] for r in checks),
                new_dry_water_m2=sum(r['new_dry_water_m2'] for r in checks),
                maximum_physical_level_error_m=max(r['physical_level_error_m'] for r in checks),
                maximum_visible_field_error_m=max(r['field_error_m'] for r in checks),
                limits=['Same pond representation and materials; new instance queries/render require native confirmation.'])
    (B/'seam-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))

if __name__=='__main__':main()
