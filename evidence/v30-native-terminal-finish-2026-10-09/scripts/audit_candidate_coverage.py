"""Whole-domain compiled footprint coverage, including native-triangle wet slivers."""
from pathlib import Path
from collections import defaultdict
import argparse,json,sys,time
import numpy as np
import shapely
from shapely.geometry import Polygon,box
from shapely.affinity import translate

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from author_global_visual import B10,sha,ODOL,read,read_pbo,polygons
from audit_frozen_visual import clip,UNIT

def wet_shape(r,c,h,levels):
    corners=np.c_[[c*6,c*6+6,c*6,c*6+6],[12282-r*6,12282-r*6,12276-r*6,12276-r*6]]
    ground=np.array([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]])
    pieces=[]
    for ids in ([0,1,3],[0,2,3]):
        weights=clip(UNIT,levels[ids]-ground[ids])
        if len(weights)>=3:pieces.append(Polygon(weights@corners[ids]))
    return shapely.union_all(pieces)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seams',action='store_true');parser.add_argument('--terrain',type=Path,required=True);parser.add_argument('--terrain-hash',required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--package-root',type=Path);parser.add_argument('--package-reference',type=Path);args=parser.parse_args();assert sha(args.terrain)==args.terrain_hash
    assert bool(args.package_root)==bool(args.package_reference)
    root=args.package_root or (B/'final' if args.seams else B)
    start=time.monotonic();ref=json.loads((args.package_reference or B/('package-final.json' if args.seams else 'package.json')).read_text())
    output=args.output;assert not output.exists()
    water=root/'water/packed/baltic_water_v30.pbo';wp=root/'world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(water)==ref['water_sha256'] and sha(wp)==ref['world_source_sha256']
    _,_,packed=read_pbo(water)
    cache={};physical=[];visual=[];bands=[];ids=[];max_footprint_difference=0.
    objects=[o for o in read(wp)['objects'] if o['name'].startswith('baltic_water_v30')]
    for n,obj in enumerate(objects):
        name=obj['name'].replace('\\','/').split('/')[-1];path=root/'water/temp/baltic_water_v30'/name
        if name not in cache:
            assert path.read_bytes()==packed[name]
            od=ODOL.from_file(str(path));road=min(od.lods,key=lambda l:abs(l.resolution-3e15));vis=min(od.lods,key=lambda l:abs(l.resolution-1))
            def geometry(lod):
                v=np.array([(p.x,p.y,p.z) for p in lod.vertices])
                return shapely.union_all([Polygon(v[f.vertex_indices][:,[0,2]]) for f in lod.faces]),v
            rg,rv=geometry(road);vg,vv=geometry(vis);assert np.ptp(rv[:,1])<1e-6
            difference=float(rg.symmetric_difference(vg).area)
            assert difference<1e-5,(name,'Visible/physical footprint discrepancy',difference)
            max_footprint_difference=max(max_footprint_difference,difference)
            cache[name]=(rg,vg,float(rv[0,1]))
        rg,vg,y=cache[name];m=np.array(obj['matrix']);assert np.array_equal(m[:9].reshape(3,3),np.eye(3))
        physical.append(translate(rg,xoff=m[9],yoff=m[11]));visual.append(translate(vg,xoff=m[9],yoff=m[11]))
        level=y+m[10];band=round(level/.025);assert abs(level-band*.025)<1e-5
        bands.append(band);ids.append(obj['id'])
        if (n+1)%3000==0:print('Loaded footprints',n+1,'of',len(objects),flush=True)
    physical=np.array(physical,dtype=object);visual=np.array(visual,dtype=object);bands=np.array(bands)
    tree=shapely.STRtree(physical)
    plane=np.load(B10/'frozen-field-reference/plane.npy');field=np.load(B/'preserved-field.npy')
    h=np.load(args.terrain)['heights'].astype(float)
    rr,cc=np.nonzero(np.isfinite(plane));groups=defaultdict(list)
    for r,c in zip(rr,cc):groups[(int(r)//4,int(c)//4)].append((int(r),int(c)))
    missing=[];dry_missing_count=0;area_physical=0.;area_visual=0.;cells_checked=0
    for n,((tr,tc),cells) in enumerate(groups.items()):
        tile=box(tc*24,12282-min(2047,tr*4+4)*6,min(2047,tc*4+4)*6,12282-tr*24)
        hits=tree.query(tile,predicate='intersects');pool=physical[hits]
        footprint=shapely.union_all(visual[hits]);own={}
        for band in {round(plane[r,c]/.025) for r,c in cells}:
            own[band]=shapely.union_all(pool[bands[hits]==band])
        for r,c in cells:
            cell=box(c*6,12276-r*6,c*6+6,12282-r*6);band=round(plane[r,c]/.025)
            flat_missing=cell.difference(own[band]);visual_missing=cell.difference(footprint)
            a=b=0.
            if flat_missing.area>1e-12:a=float(flat_missing.intersection(wet_shape(r,c,h,np.full(4,plane[r,c]))).area)
            if visual_missing.area>1e-12:b=float(visual_missing.intersection(wet_shape(r,c,h,field[r,c])).area)
            area_physical+=a;area_visual+=b;cells_checked+=1
            if a>1e-10 or b>1e-10:
                missing.append(dict(row=r,col=c,physical_missing_m2=a,visible_footprint_missing_m2=b,
                                    physical_geometry=shapely.to_geojson(flat_missing),visual_geometry=shapely.to_geojson(visual_missing)))
            elif flat_missing.area>1e-10 or visual_missing.area>1e-10:dry_missing_count+=1
        if (n+1)%4000==0:print('Covered tiles',n+1,'of',len(groups),'uncovered wet cells',len(missing),flush=True)
    # Positive and negative controls on an actual independently specified cell.
    test_h=np.zeros((2,2));wet=wet_shape(0,0,test_h,np.ones(4));full=box(0,12276,6,12282)
    assert wet.area==36 and wet.difference(full).area==0
    assert abs(wet.difference(box(0,12276,5.99,12282)).area-.06)<1e-10
    gates=dict(all_frozen_water_cells=cells_checked==int(np.isfinite(plane).sum()),
               nominal_wet_coverage=area_physical<1e-7,visible_field_footprint_coverage=area_visual<1e-7)
    report=dict(status='PASS_GLOBAL_COMPILED_COVERAGE' if all(gates.values()) else 'FAIL_GLOBAL_COMPILED_COVERAGE',
                gates=gates,instances=len(objects),models=len(cache),cells=cells_checked,tiles=len(groups),
                uncovered_physical_m2=area_physical,uncovered_visible_footprint_m2=area_visual,
                uncovered_cells=missing,uncovered_only_dry_cells=dry_missing_count,
                max_model_visible_physical_footprint_difference_m2=max_footprint_difference,
                terrain_sha256=sha(args.terrain),water_sha256=sha(water),world_source_sha256=sha(wp),elapsed_s=time.monotonic()-start,
                controls=['whole_native_cell_36_m2_covered','one_centimetre_gap_0.06_m2_rejected'],
                limits=['Coverage gate, not native render acceptance. Visible heights and connectivity have separate gates.',
                        'Every frozen pond cell included; this does not test the native ocean renderer.'])
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='uncovered_cells'},indent=2))

if __name__=='__main__':main()
