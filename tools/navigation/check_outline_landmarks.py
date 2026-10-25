"""Independent reserve/bridge comparisons and fault-injection controls."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import rasterio
from shapely.geometry import shape,LineString,box
from shapely.ops import unary_union
from verify_outline_smoothing import ROOT,EV,basic_checks,triangles,clipped_plane_values
from waterway_common import sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
    with rasterio.open(a.candidate) as ds:h=ds.read(1)
    source=ROOT/'tests/regional_foundation_combined_v10/reference.npz';assert sha(source)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d';ref=np.load(source);base=ref['candidate'];wet=ref['wet']|ref['ocean']
    reserve_path=ROOT/'tests/regional_outline_v3/reference.npz';assert sha(reserve_path)=='b5ca00409f0814285c82a1fe6688fe49719574eadde415de08443ffedcbc574d';reserve=np.load(reserve_path)['reserve'];dry=reserve&~wet
    reserve_report=dict(dry_area_km2=float(dry.sum()*36/1e6),minimum_dry_height_m=float(h[dry].min()),passed=bool(dry.sum()*36==5941332 and h[dry].min()>=1.4-1e-5))
    approaches=[]
    for route in json.loads((ROOT/'tests/regional_foundation_combined_v10/solve.json').read_text())['routes']:
        line=LineString(route['coordinates']);s=np.r_[np.arange(0,line.length,.25),line.length];p=np.array([line.interpolate(float(t)).coords[0] for t in s]);lo=np.maximum(0,s-.05);hi=np.minimum(line.length,s+.05)
        tangent=np.array([line.interpolate(float(t)).coords[0] for t in hi])-np.array([line.interpolate(float(t)).coords[0] for t in lo]);tangent/=np.linalg.norm(tangent,axis=1)[:,None];normal=np.c_[-tangent[:,1],tangent[:,0]]
        q=p[None,:,:]+np.linspace(-4,4,33)[:,None,None]*normal[None,:,:];new_y=sample(h,q[:,:,0]+200000,q[:,:,1]);old_y=sample(base,q[:,:,0]+200000,q[:,:,1]);error=float(abs(new_y-old_y).max())
        def metrics(y):
            ds=np.diff(s);lane_ds=np.linalg.norm(np.diff(q,axis=1),axis=2);grade=float(np.max(abs(np.diff(y,axis=1)/ds)));lane_grade=float(np.max(abs(np.diff(y,axis=1)/lane_ds)));cross=float(np.ptp(y,axis=0).max());chords=[]
            for k in range(1,24):
                w=(s[k:-24+k]-s[:-24])/(s[24:]-s[:-24]);chords.append(abs(y[:,k:-24+k]-(y[:,:-24]*(1-w)+y[:,24:]*w)))
            chord=float(np.max(chords));joint=float(abs(y[:,0]-11).max())
            return dict(maximum_grade=grade,maximum_lane_grade=lane_grade,maximum_cross_height_m=cross,maximum_6m_chord_m=chord,joint_error_m=joint,passed=grade<=.065 and lane_grade<=.065 and cross<=.03 and chord<=.03 and joint<=.01)
        original=metrics(old_y);current=metrics(new_y);assert original['passed']
        approaches.append(dict(side=route['side'],samples=int(new_y.size),maximum_change_m=error,all_heights_exact=error==0,baseline=original,candidate=current,passed=current['passed']))
    def roughness(h):
        d=~wet;cx=abs(h[:,1:-1]-(h[:,:-2]+h[:,2:])*.5);cz=abs(h[1:-1]-(h[:-2]+h[2:])*.5);v=np.r_[cx[d[:,1:-1]&d[:,:-2]&d[:,2:]],cz[d[1:-1]&d[:-2]&d[2:]]]
        return dict(rms_half_chord_m=float(np.sqrt(np.mean(v.astype(float)**2))),p99_half_chord_m=float(np.percentile(v,99)))
    # Real historical bad shoreline, retaining its source polygon classification.
    x,z=8203,10433;r,c=int((12282-z)//6),int(x//6);geometry=unary_union([shape(f['geometry']) for f in json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']]+[shape(json.loads((EV/'ocean-game.json').read_text())['features'][0]['geometry'])]);land=box(c*6,12282-r*6-6,c*6+6,12282-r*6).difference(geometry)
    def local_margin(terrain):
        values=[]
        for v,y in triangles(terrain,np.array([r]),np.array([c])):
            q,_,_=clipped_plane_values(v,y,land);values.extend(q)
        return float(min(values)-1.4)
    actual_margin=local_margin(h);old_margin=local_margin(base);broken=h.copy();broken[r:r+2,c:c+2]=base[r:r+2,c:c+2];damaged_margin=local_margin(broken)
    faults=dict(new_coast_positive=actual_margin>=-1e-5,baseline_coast_rejected=old_margin< -1e-5,restored_old_subcell_rejected=damaged_margin< -1e-5)
    basic,_=basic_checks(h,base,ref,a.candidate.parent);faults['positive_basic_contract']=all(basic.values())
    rr,cc=np.argwhere(ref['fairway_support'])[len(np.argwhere(ref['fairway_support']))//2];broken=h.copy();broken[rr,cc]+=.25;check,_=basic_checks(broken,base,ref,a.candidate.parent);faults['changed_fairway_rejected']=not check['fairway_vertices_exact']
    broken=h.copy();broken[0,0]+=.25;check,_=basic_checks(broken,base,ref,a.candidate.parent);faults['changed_map_edge_rejected']=not check['map_edge_exact']
    broken=h.copy();broken[1024,1024]=base[1024,1024]+20;check,_=basic_checks(broken,base,ref,a.candidate.parent);faults['excess_delta_rejected']=not check['delta_bounds']
    checks=dict(reserve=reserve_report['passed'],approaches=all(r['passed'] for r in approaches),negative_controls=all(faults.values()))
    report=dict(status='PASS_OUTLINE_LANDMARKS_AND_CONTROLS' if all(checks.values()) else 'FAIL',candidate_sha256=sha(a.candidate),checks=checks,reserve=reserve_report,approaches=approaches,coast_margin_m=dict(candidate=actual_margin,baseline=old_margin,corrupted=damaged_margin),fault_controls=faults,roughness=dict(v10=roughness(base),candidate=roughness(h)),limits=['Geometry and deliberate corruptions only; no runtime/navmesh/render acceptance.','Dry curvature statistic includes protected roads and shore neighborhoods; it is not a claim of smooth driving everywhere.'])
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if all(checks.values()) else 1)
if __name__=='__main__':main()
