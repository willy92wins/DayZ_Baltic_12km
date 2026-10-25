"""Verify a monotonic floor repair using the completed V25 geometric proof."""
from pathlib import Path
import json,hashlib,math
import numpy as np
from rasterio.features import rasterize
from shapely.geometry import shape,LineString
from verify_outline_smoothing import ROOT,EV,TX,basic_checks,river_checks,triangles,clipped_plane_values
from waterway_common import sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    old=ROOT/'tests/regional_outline_smoothing_v25';folder=ROOT/'tests/regional_outline_smoothing_v26';out=folder/'independent-consumer.json';assert not out.exists()
    previous=json.loads((old/'independent-consumer.json').read_text());assert previous['candidate_sha256']=='f7a220fda8ec33e483dad6e93d113a6c4f98cd09020dd1e15769c13dc93c7055'
    assert all(v for k,v in previous['checks'].items() if k!='dry_native_freeboard'),previous['checks']
    before=np.load(old/'reference.npz')['candidate'];ref=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');base=ref['candidate'];h=np.load(folder/'reference.npz')['candidate']
    checks,stats=basic_checks(h,base,ref,folder);changed=h!=before;delta=h.astype(float)-before
    checks['floor_increment_monotonic']=bool((delta>=0).all() and delta.max()<.002 and np.all(h[changed]==np.float32(1.4)) and not np.any(changed&(ref['wet']|ref['ocean']|ref['fairway_support'])))
    # Lower affine bounds are retained under a pointwise non-negative increment
    # (barycentric weights non-negative). This reuses only PASS components, not
    # the overall failed V25 result. All upper lake bounds are inspected below.
    checks['dry_shore_planes']=previous['checks']['dry_shore_planes'] and checks['floor_increment_monotonic']
    checks['protected_island_planes']=previous['checks']['protected_island_planes'] and checks['floor_increment_monotonic']
    touched=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
    lake_records=[]
    for f in json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']:
        if not f['properties']['body'].startswith('lake_'):continue
        core=shape(f['geometry']).buffer(-6*math.sqrt(2))
        if core.is_empty:continue
        cells=rasterize([(core,1)],out_shape=touched.shape,transform=TX,all_touched=True,dtype='uint8').astype(bool)&touched
        rr,cc=np.where(cells);minimum=float('inf');count=0
        if len(rr):
            for vertices,heights in triangles(h,rr,cc):
                v,idx,p=clipped_plane_values(vertices,heights,core)
                if len(v):minimum=min(minimum,float(np.min(f['properties']['level_m']-.15-v)));count+=len(v)
        lake_records.append(dict(body=f['properties']['body'],changed_cells=int(cells.sum()),checked_extrema=count,margin_m=minimum if count else None,passed=minimum>=-1e-5))
    checks['whole_lake_core_depth']=all(r['passed'] for r in lake_records)
    rivers=river_checks(h,ref);checks['dense_navigable_cross_sections']=rivers['passed']
    reserve_source=ROOT/'tests/regional_outline_v3/reference.npz';assert sha(reserve_source)=='b5ca00409f0814285c82a1fe6688fe49719574eadde415de08443ffedcbc574d'
    reserve=np.load(reserve_source)['reserve'];dry=reserve&~(ref['wet']|ref['ocean'])
    reserve_report=dict(dry_area_km2=float(dry.sum()*36/1e6),minimum_dry_height_m=float(h[dry].min()))
    checks['reserve_dry_domain_retained']=bool(abs(reserve_report['dry_area_km2']-5.941332)<1e-8 and np.all(h[dry]>=1.4-1e-5))
    approaches=[]
    for route in json.loads((ROOT/'tests/regional_foundation_combined_v10/solve.json').read_text())['routes']:
        line=LineString(route['coordinates']);s=np.r_[np.arange(0,line.length,.25),line.length];p=np.array([line.interpolate(float(t)).coords[0] for t in s]);lo=np.maximum(0,s-.05);hi=np.minimum(line.length,s+.05)
        tangent=np.array([line.interpolate(float(t)).coords[0] for t in hi])-np.array([line.interpolate(float(t)).coords[0] for t in lo]);tangent/=np.linalg.norm(tangent,axis=1)[:,None];normal=np.c_[-tangent[:,1],tangent[:,0]]
        q=p[None,:,:]+np.linspace(-4,4,33)[:,None,None]*normal[None,:,:];new_y=sample(h,q[:,:,0]+200000,q[:,:,1]);old_y=sample(base,q[:,:,0]+200000,q[:,:,1]);error=float(abs(new_y-old_y).max())
        approaches.append(dict(side=route['side'],samples=int(new_y.size),maximum_change_m=error,passed=error==0))
    checks['whole_bridge_approaches_exact']=all(r['passed'] for r in approaches)
    def roughness(a):
        dry_cells=~(ref['wet']|ref['ocean']);cx=abs(a[:,1:-1]-(a[:,:-2]+a[:,2:])*.5);cz=abs(a[1:-1]-(a[:-2]+a[2:])*.5)
        px=cx[dry_cells[:,1:-1]&dry_cells[:,:-2]&dry_cells[:,2:]];pz=cz[dry_cells[1:-1]&dry_cells[:-2]&dry_cells[2:]];values=np.r_[px,pz]
        return dict(rms_6m_half_chord_m=float(np.sqrt(np.mean(values.astype(float)**2))),p99_half_chord_m=float(np.percentile(values,99)))
    report=dict(status='PASS_OFFLINE_OUTLINE_GEOMETRY' if all(checks.values()) else 'FAIL',checks=checks,candidate_sha256=sha(folder/'baltic_outline_smoothing_v26.asc'),statistics=stats,previous_consumer_sha256=sha(old/'independent-consumer.json'),proof='Monotonic sub2mm dry increment retains all lower native-plane bounds; touched lake upper bounds recomputed; slopes/scope/rivers/approaches checked anew.',coast=previous['coast'],lake_changes=lake_records,rivers=rivers,reserve=reserve_report,approaches=approaches,roughness=dict(v10=roughness(base),v26=roughness(h)),limits=['Offline geometry only; native persistence, visual water/render and new navmesh remain unverified.','Whole-network road smoothness remains open.'])
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('lake_changes','rivers')},indent=2));raise SystemExit(0 if all(checks.values()) else 1)

if __name__=='__main__':main()
