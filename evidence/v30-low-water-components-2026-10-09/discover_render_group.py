"""Prove which already compiled water instances a local whole-object translation would affect."""
from pathlib import Path
import json,sys,time
import numpy as np
import shapely
from shapely.geometry import box
B=Path(__file__).parent
sys.path[:0]=['E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009']
from author_global_visual import ODOL,read,read_pbo,sha
WRP=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')
WATER=Path('P:/Mods/@DayZ_Baltic_HingeSmoothV1/Addons/baltic_water_v30.pbo')
ROOT=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30')

def bounds(lod):
    v=np.array([(p.x,p.y,p.z) for p in lod.vertices]);return [float(x) for x in [v[:,0].min(),v[:,2].min(),v[:,0].max(),v[:,2].max()]],float(v[:,1].min()),float(v[:,1].max())

def main():
    started=time.monotonic();assert sha(WATER)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
    assert sha(WRP)=='a845bee973c2db1c94acf39758358dfcfb5967770e3879263ecf1a1bc4f66fd2'
    objects=[o for o in read(WRP)['objects'] if o['name'].startswith('baltic_water_v30')];_,_,packed=read_pbo(WATER)
    cache={};rows=[]
    for j,o in enumerate(objects):
        name=o['name'].replace('\\','/').split('/')[-1]
        if name not in cache:
            p=ROOT/name;assert p.read_bytes()==packed[name]
            od=ODOL.from_file(str(p));rd=min(od.lods,key=lambda l:abs(l.resolution-3e15));vis=min(od.lods,key=lambda l:abs(l.resolution-1));mem=min(od.lods,key=lambda l:abs(l.resolution-1e15))
            rb,y0,y1=bounds(rd);vb,_,_=bounds(vis);mb,_,_=bounds(mem);assert y1-y0<1e-5
            bb=[min(rb[0],vb[0],mb[0]),min(rb[1],vb[1],mb[1]),max(rb[2],vb[2],mb[2]),max(rb[3],vb[3],mb[3])]
            cache[name]=dict(bounds=bb,physical_y=y0,sha256=sha(p))
        m=o['matrix'];assert np.array_equal(np.array(m[:9]).reshape(3,3),np.eye(3))
        d=cache[name];bb=d['bounds'];world=[bb[0]+m[9],bb[1]+m[11],bb[2]+m[9],bb[3]+m[11]]
        rows.append(dict(id=o['id'],model=name,bounds=world,level=d['physical_y']+m[10],position=m[9:]))
        if (j+1)%4000==0:print(json.dumps(dict(loaded=j+1,total=len(objects),seconds=time.monotonic()-started)),flush=True)
    (B/'compiled-instance-bounds.json').write_text(json.dumps(dict(world_sha256=sha(WRP),water_sha256=sha(WATER),models=cache,objects=rows),separators=(',',':'))+'\n')
    labels=np.load(B/'physical-component-labels.npz')['triangles'];support=np.zeros(labels.shape[:2],bool);selected={274};selected_objects=set();history=[]
    boxes=np.array([box(*o['bounds']) for o in rows],dtype=object);tree=shapely.STRtree(boxes)
    for iteration in range(20):
        cells=np.any(np.isin(labels,list(selected)),axis=2);rr,cc=np.nonzero(cells)
        cellshapes=shapely.box(cc*6,12276-rr*6,cc*6+6,12282-rr*6)
        found=tree.query(cellshapes,predicate='intersects')[1];selected_objects.update(map(int,found))
        for i in selected_objects:
            xmin,zmin,xmax,zmax=rows[i]['bounds'];r0=max(0,int(np.floor((12282-zmax)/6)));r1=min(2047,int(np.ceil((12282-zmin)/6)));c0=max(0,int(np.floor(xmin/6)));c1=min(2047,int(np.ceil(xmax/6)))
            support[r0:r1,c0:c1]=True
        new=set(map(int,np.unique(labels[support])))-{-1};history.append(dict(iteration=iteration+1,components=len(new),objects=len(selected_objects),support_cells=int(support.sum())))
        if new==selected:break
        selected=new
    else:raise AssertionError('Cohort discovery did not close within 20 monotone expansions')
    source=np.load('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz');h=source['heights'];vertices=np.zeros(h.shape,bool)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):vertices[dr:dr+2047,dc:dc+2047]|=support
    r,c=np.nonzero(vertices);rr,cc=np.nonzero(cells);wetclasses=np.unique(source['cls'][vertices]);minbed=float(h[vertices].min());delta=float(np.ceil((1.001-minbed)/.025)*.025)
    report=dict(status='CONSERVATIVE_COMPILED_REPRESENTATION_COHORT_DISCOVERY_NOT_AUTHORED',world_sha256=sha(WRP),water_sha256=sha(WATER),whole_map_instances=len(objects),whole_map_models=len(cache),target_component=274,cohort_components=sorted(selected),objects=[rows[i] for i in sorted(selected_objects)],support_cells=int(support.sum()),support_vertices=int(vertices.sum()),bounds_xz=[int(c.min()*6),int(12282-r.max()*6),int(c.max()*6),int(12282-r.min()*6)],classes=wetclasses.tolist(),minimum_ground_in_support=minbed,quantized_shift_to_1_001m=delta,engineering_vertices=int((vertices&(source['reserve']|source['platform'])).sum()),narva_vertices=int((vertices&source['narva']).sum()),history=history,seconds=time.monotonic()-started,limits=['Bounding rectangles of roadway, visible and memory LODs are conservative. They can include dry gaps and inflate the cohort.','This proves the scope needed by this conservative whole-instance method, not that every cohort component is hydraulically connected.','No levels, terrain, instances or vanilla files have been changed.'])
    np.savez_compressed(B/'cohort-support.npz',cells=support,vertices=vertices)
    (B/'cohort.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='objects'},indent=2))

if __name__=='__main__':main()
