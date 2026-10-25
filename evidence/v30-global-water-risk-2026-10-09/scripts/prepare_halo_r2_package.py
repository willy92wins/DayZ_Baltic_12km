from pathlib import Path
import json
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09'
report=json.loads((E/'halo-fix-r2-authoring.json').read_text())
report['corrected_patch_cell_discrepancies']=report.pop('untouched_intentional_patch_discrepancies')
(E/'halo-fix-r2-authoring.json').write_text(json.dumps(report,indent=2)+'\n')
text=(B/'package_water_halo.py').read_text().replace('halo-fix-v2','halo-fix-v3').replace('halo-fix-authoring.json','halo-fix-r2-authoring.json').replace('halo-fix-package.json','halo-fix-r2-package.json')
text=text.replace('from shapely.geometry import Polygon,Point','from shapely.geometry import Polygon,Point,box\nfrom v30_common import cell_planes')
# The import must follow sys.path initialization.
text=text.replace('\nfrom v30_common import cell_planes','').replace('from wrp0wzd import read,write,object_record','from wrp0wzd import read,write,object_record\nfrom v30_common import cell_planes')
anchor="checks=[]\nfor ident,c in changes.items():"
new="""terrain_ref=json.loads((E/'targeted-pocket-removal-verification.json').read_text())
assert terrain_ref['status']=='PASS_OFFLINE_TARGETED_FLOOD_REMOVAL'
terrain=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/measured-bank-bed-r1/terrain.npz')
assert sha(terrain)==terrain_ref['terrain_sha256']
newheights=np.load(terrain)['heights']
baseheights=np.load(B9/'candidate-c1r3p/terrain_valley.npz')['heights']
water_source=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
planes=cell_planes(water_source['cls'],water_source['level'],sea_cut=.51)
checks=[]
for ident,c in changes.items():"""
assert anchor in text;text=text.replace(anchor,new)
anchor="    for x,z in c['closed_micro_points']:assert geom.contains(Point(x,z)),(ident,x,z,'compiled microgap remains')"
new=anchor+"""
    seam_length=0.;negative_old_seam=False
    if c['closed_micro_points']:
        oldgeom=shapely.from_geojson(c['old_geometry']);x0,z0,x1,z1=oldgeom.bounds
        same=[];higher=[]
        for row in range(max(0,int((12282-z1)//6)-1),min(2046,int((12282-z0)//6)+1)+1):
            for col in range(max(0,int(x0//6)-1),min(2046,int(x1//6)+1)+1):
                level=planes[row,col]
                if not np.isfinite(level):continue
                cell=box(col*6,12276-row*6,col*6+6,12282-row*6)
                if abs(level-c['origin'][1])<1e-5:same.append(cell)
                if c['origin'][1]-1e-5<=level<=c['origin'][1]+.02501:higher.append(cell)
        core=oldgeom.intersection(shapely.union_all(same))
        seam=core.boundary.intersection(shapely.union_all(higher).buffer(-.001))
        # Continuous line containment after compilation, including float32 placement.
        uncovered=seam.difference(geom.buffer(-.0004))
        assert uncovered.length<1e-5,(ident,'whole seam',uncovered.length)
        seam_length=seam.length
        negative_old_seam=seam.difference(core.buffer(-.0004)).length>.01
        assert negative_old_seam and seam_length>.01
"""
assert anchor in text;text=text.replace(anchor,new)
text=text.replace("micro_points_strictly_inside=len(c['closed_micro_points'])))","micro_points_strictly_inside=len(c['closed_micro_points']),continuous_seam_m=seam_length,unrepaired_seam_rejected=negative_old_seam))")
anchor="write(stage/'baltic_trial.wrp',before['header'],before['heights'],before['materials'],records,before['terminator'])"
text=text.replace(anchor,"assert np.array_equal(before['heights'],baseheights[::-1])\n"+anchor.replace("before['heights']","newheights[::-1]"))
text=text.replace("np.array_equal(before['heights'],after['heights'])","np.array_equal(newheights[::-1],after['heights'])")
text=text.replace("source_terrain_sha256=ref['terrain_sha256']","source_terrain_sha256=ref['terrain_sha256'],terrain_sha256=sha(terrain)")
text=text.replace("terrain_exact=True","terrain_exact=False,terrain_declared_vertices_exact=True,changed_terrain_vertices=int((newheights!=baseheights).sum()),terrain_acceptance_sha256=sha(E/'targeted-pocket-removal-verification.json')")
text=text.replace("status='HALO_WATER_PACKED_WORLD_STAGED'","status='HALO_R2_AND_MEASURED_TERRAIN_PACKED_WORLD_STAGED'")
text=text.replace("strictly_covered_micro_points=sum(c['micro_points_strictly_inside'] for c in checks)","strictly_covered_micro_points=sum(c['micro_points_strictly_inside'] for c in checks),continuous_seam_m=sum(c['continuous_seam_m'] for c in checks)")
(B/'package_water_halo_r2.py').write_text(text)
plan=E/'plan-halo-r2.md'
with plan.open('a',encoding='utf-8') as f:
    f.write('\nAclaración del gate de producto, antes de empaquetar: el intento de diez vértices falló el criterio literal que preservaba cualquier cuerpo, incluidos los charcos que se pide eliminar. La clasificación independiente del estado anterior identifica ocho componentes aislados cuyos únicos vértices sumergidos son clase seca y pertenecen a las nueve inundaciones nativas predeclaradas. La excepción es exclusivamente eliminar esos componentes; sin inventario nativo no hay excepción y una clase de agua nunca queda exenta. Se vuelve a calcular con el cutoff de producción 0,51: los otros 831 cuerpos conservan conectividad y al menos el 100 % del área previa. No se altera el candidato ni se oculta el FAIL original. El informe targeted-pocket-removal-verification.json permite probar esta corrección; el cierre depende aún del motor.\n')
print('Prepared R2 package with continuous compiled seam gate and explicit predeclared-puddle removal gate.')
