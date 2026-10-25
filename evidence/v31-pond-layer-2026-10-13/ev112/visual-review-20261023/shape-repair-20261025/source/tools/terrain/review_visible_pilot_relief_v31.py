"""Diagnose actual saved bed + native terrain, including end aprons.

No acceptance threshold is invented: report native sharp edges still exposed,
and overlaps/dihedrals of the full saved MLOD bed. Visibility uses samples on
both sides of each native edge (0.10m inset, 0.5m spacing), not a claim of
exhaustive occlusion. The independent native angle census includes all edges.
"""
import argparse,csv,hashlib,json,sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from shapely.ops import unary_union
sys.path[:0]=[str(Path(__file__).resolve().parent),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import census_creases_v31 as crease
import py3d


def top_height(tris, tree, xz):
    """Interpolate an arbitrary saved triangle mesh, retaining the upper sheet."""
    points=shapely.points(xz);pi,ti=tree.query(points,predicate='intersects')
    result=np.full(len(xz),-np.inf)
    if not len(pi):return result
    t=tris[ti];a=t[:,0][:,[0,2]];b=t[:,1][:,[0,2]]-a;c=t[:,2][:,[0,2]]-a;d=xz[pi]-a
    cross=lambda u,v:u[:,0]*v[:,1]-u[:,1]*v[:,0]
    det=cross(b,c);u=cross(d,c)/det;v=cross(b,d)/det
    y=t[:,0,1]+u*(t[:,1,1]-t[:,0,1])+v*(t[:,2,1]-t[:,0,1])
    np.maximum.at(result,pi,y)
    return result


def native_height(H,xz):
    c=xz[:,0]/6;r=(12282-xz[:,1])/6;ci=c.astype(int);ri=r.astype(int);u=c-ci;v=r-ri
    a=H[ri,ci];b=H[ri,ci+1];d=H[ri+1,ci];e=H[ri+1,ci+1]
    return np.where(u>=v,a+u*(b-a)+v*(e-b),a+v*(d-a)+u*(e-d))


def mesh_edges(tris,H,water):
    n=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
    edges={}
    for i,t in enumerate(tris):
        for a,b in ((0,1),(1,2),(2,0)):
            key=tuple(sorted((tuple(t[a]),tuple(t[b]))));edges.setdefault(key,[]).append(i)
    angles=[];worst=[];visible_angles=[];visible_worst=[];nonmanifold=0
    wt=STRtree([Polygon(t[:,[0,2]]) for t in water])
    for edge,ids in edges.items():
        if len(ids)>2:nonmanifold+=1
        if len(ids)==2:
            angle=float(np.degrees(np.arccos(np.clip(n[ids[0]]@n[ids[1]],-1,1))))
            angles.append(angle)
            if angle>45:worst.append(dict(angle_deg=angle,midpoint=np.mean(edge,axis=0).tolist()))
            if angle>20:
                line=np.asarray(edge)[0]+np.linspace(.03,.97,9)[:,None]*(np.asarray(edge)[1]-np.asarray(edge)[0])
                samples=np.concatenate([line*.97+tris[i].mean(0)*.03 for i in ids])
                terrain=native_height(H,samples[:,[0,2]]);wh=top_height(water,wt,samples[:,[0,2]])
                visible=(samples[:,1]>=np.maximum(terrain,wh)-.002).reshape(2,-1)
                if (visible[0]&visible[1]).any():
                    visible_angles.append(angle);visible_worst.append(dict(angle_deg=angle,midpoint=np.mean(edge,axis=0).tolist()))
    return dict(shared_edges=len(angles),nonmanifold_edges=nonmanifold,max_deg=max(angles),
                above20=int((np.array(angles)>20).sum()),above45=int((np.array(angles)>45).sum()),
                worst=sorted(worst,key=lambda r:-r['angle_deg'])[:10],visible_above20=len(visible_angles),
                visible_above45=int((np.array(visible_angles)>45).sum()),
                worst_visible=sorted(visible_worst,key=lambda r:-r['angle_deg'])[:10])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('pilot');ap.add_argument('build')
    ap.add_argument('--base-terrain',type=Path);ap.add_argument('--expected-base-sha256');a=ap.parse_args()
    if bool(a.base_terrain)!=bool(a.expected_base_sha256):ap.error('base terrain and its frozen hash must be supplied together')
    P=Path(a.pilot);B=Path(a.build);rep=json.loads((P/'author-report.json').read_text())
    base=a.base_terrain or B/'water-fix-b/terrain.npz'
    base_hash=hashlib.sha256(base.read_bytes()).hexdigest()
    assert base_hash==(a.expected_base_sha256 or '07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62')
    assert rep['terrain_input_sha256']==base_hash
    H=np.load(P/'terrain.npz')['heights'].astype(float);H0=np.load(base)['heights'].astype(float)
    alltris=[];allwater=[];meshes=[]
    for site in rep['sites']:
        tris=[];water=[]
        for inst in rep['instances']:
            if inst['site']!=site['site']:continue
            path=P/'source'/Path(inst['model'].replace('\\','/'));model=py3d.P3D(open(path,'rb'));lod=model.lods[0]
            v=np.array([p.coords for p in lod.points])+inst['origin']
            for f in lod.faces:
                tri=v[[q.point_index for q in f.vertices]]
                (water if 'water_streambed' in f.material else tris).append(tri)
        tris=np.array(tris);polys=[Polygon(t[:,[0,2]]) for t in tris];union=unary_union(polys)
        overlap=sum(p.area for p in polys)-union.area
        meshes.append(dict(site=site['site'],triangles=len(tris),overlap_area_m2=float(overlap),
                           connected=union.geom_type=='Polygon',bed_edges=mesh_edges(tris,H,np.array(water))))
        alltris.extend(tris);allwater.extend(water)
    alltris=np.array(alltris+allwater);tree=STRtree([Polygon(t[:,[0,2]]) for t in alltris])
    A=crease.angles(H);A0=crease.angles(H0);aff=crease.pair_union(*crease.tri_any(H!=H0));rows=[]
    for kind,angles in A.items():
        for r,c in np.argwhere(aff[kind]&(angles>20)):
            nw=np.array([6*c,12282-6*r]);start,end={'diagonal':(nw,nw+[6,-6]),'east':(nw+[6,0],nw+[6,-6]),'south':(nw+[0,-6],nw+[6,-6])}[kind]
            d=end-start;normal=np.array([-d[1],d[0]])/np.linalg.norm(d)
            edge=start+np.linspace(.04,.96,17)[:,None]*d
            sample=np.concatenate((edge+normal*.10,edge-normal*.10));ground=native_height(H,sample);top=top_height(alltris,tree,sample)
            visible=(ground>=top-.002).reshape(2,-1);exposed=bool((visible[0]&visible[1]).any())
            rows.append(dict(edge=kind,row=int(r),col=int(c),x=float(edge[8,0]),z=float(edge[8,1]),
                             before=float(A0[kind][r,c]),after=float(angles[r,c]),exposed=exposed,
                             worsened=bool(angles[r,c]>A0[kind][r,c]+.01),both_sides_visible_samples=int((visible[0]&visible[1]).sum())))
    rows.sort(key=lambda r:(not r['exposed'],-r['after']))
    with open(P/'visible-native-creases.csv','w',newline='',encoding='utf-8') as f:
        fields=['edge','row','col','x','z','before','after','exposed','worsened','both_sides_visible_samples']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    exposed=[r for r in rows if r['exposed']]
    result=dict(status='DIAGNOSTIC',base_terrain_sha256=base_hash,meshes=meshes,native_over20=len(rows),exposed_over20=len(exposed),
                exposed_worsened=sum(r['worsened'] for r in exposed),worst_exposed=exposed[:15],
                limitations=['Sampled visibility, not exhaustive occlusion.','20 degrees is diagnostic, not an aesthetic acceptance threshold.','Saved MLOD, not engine rendering.'])
    (P/'visible-relief-review.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
