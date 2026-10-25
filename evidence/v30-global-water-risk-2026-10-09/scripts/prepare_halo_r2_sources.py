from pathlib import Path
import shutil
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
code=(B/'author_water_halo_fix.py').read_text()
code=code.replace("selected={r['object_id'] for r in discrepancies if r['model'].startswith(('edge_','full_'))}","selected={r['object_id'] for r in discrepancies}\nselected.add(16807258)  # measured stale 1 cm corner, below the area inventory threshold")
code=code.replace("out=B/'halo-fix-v2'","out=B/'halo-fix-v3'")
code=code.replace("assert name.startswith(('edge_','full_')),name","assert name.startswith(('edge_','full_','patch_')),name")
code=code.replace('cells=[];wet=[]','cells=[];wet=[];higher=[]')
code=code.replace("cell=box(col*6,12276-row*6,col*6+6,12282-row*6);wet.append(cell)","cell=box(col*6,12276-row*6,col*6+6,12282-row*6);wet.append(cell)\n            if pose['origin'][1]-1e-5<=plane<=pose['origin'][1]+.02501:higher.append(cell)")
old='''    for x,z in micros.get(ident,[]):
        patch=corrected.buffer(.001,join_style='mitre').intersection(Point(x,z).buffer(.02)).intersection(unary_union(wet))
        coords=shapely.get_coordinates(patch)
        assert len(coords) and np.min(pose['origin'][1]-tri_sample(h,coords[:,0],coords[:,1]))>.05
        corrected=corrected.union(patch)
        assert corrected.contains(Point(x,z)),(ident,x,z)'''
new='''    if ident in micros:
        # Cover the complete shared edge, not only the previously sampled point.
        patch=corrected.buffer(.001,join_style='mitre').intersection(unary_union(higher))
        corrected=corrected.union(patch)
        for x,z in micros[ident]:
            assert pose['origin'][1]-float(tri_sample(h,x,z))>.05
            assert corrected.contains(Point(x,z)),(ident,x,z)'''
assert old in code;code=code.replace(old,new).replace('assert added.area<.001','assert added.area<.5')
code=code.replace("E/'halo-fix-authoring.json'","E/'halo-fix-r2-authoring.json'")
code=code.replace('Only generic tile halo geometry changed; four custom patch slivers retained for separate classification.','Stale full/edge/patch halos and the measured tiny corner are clipped; five complete lower-band seams receive 1 mm overlap only toward equal/higher adjacent bands.')
code=code.replace('No heightfield, material, water level, stitched model or bridge edited. Full compiled/raster and historic consumer validation required.','This geometry author does not change heights/levels/bridges/stitched models. The separately gated bank/bed terrain may be integrated only after its independent PASS.')
(B/'author_water_halo_r2.py').write_text(code)
for src,dst in [('compile_water_halo.ps1','compile_water_halo_r2.ps1'),('build_halo_world.ps1','build_halo_world_r2.ps1')]:
    (B/dst).write_text((B/src).read_text().replace('halo-fix-v2','halo-fix-v3'))
print('Prepared source-defined correction; original candidate helpers retained.')
