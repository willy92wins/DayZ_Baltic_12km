"""Read-only diagnosis of V10 dry margins, native facets and subcell shores."""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
from scipy.ndimage import distance_transform_edt,label
from rasterio.features import rasterize
from affine import Affine
from shapely import STRtree,points
from shapely.geometry import shape
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'evidence/foundation-followup-2026-10-01/outline-water-audit-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not OUT.exists(),'Preserve prior evidence'
    OUT.mkdir(parents=True)
    source=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    assert sha(source)=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
    ref=np.load(source);h=ref['candidate'];wet=ref['wet']|ref['ocean']
    bodies=json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']
    geos=[shape(f['geometry']) for f in bodies]
    levels=np.array([f['properties']['level_m'] for f in bodies]+[1.25])
    ocean=shape(json.loads((EV/'ocean-game.json').read_text())['features'][0]['geometry'])
    geos.append(ocean);tree=STRtree(geos)
    # These are design-envelope diagnostics, not a measured motor formula.
    heights=np.maximum(1.25,levels)
    tx=Affine(6,0,-3,0,-6,12285)
    exact_wet=rasterize([(g,1) for g in geos],out_shape=h.shape,transform=tx,dtype='uint8').astype(bool)
    dry=~exact_wet
    coast_dist=distance_transform_edt(~ref['ocean'])*6
    water_dist=distance_transform_edt(~exact_wet)*6
    low=dry&(h<1.4)
    labels,n=label(low)
    counts=np.bincount(labels.ravel());counts[0]=0
    comps=[]
    for k in np.argsort(counts)[-25:][::-1]:
        if not counts[k]:continue
        rr,cc=np.where(labels==k);order=np.argmin(h[rr,cc]);r,c=int(rr[order]),int(cc[order])
        comps.append(dict(cells=int(counts[k]),area_grid_m2=int(counts[k]*36),lowest_xz=[c*6,12282-r*6],minimum_height_m=float(h[r,c]),maximum_coast_distance_grid_m=float(coast_dist[rr,cc].max()),water_distance_grid_m=float(water_dist[r,c])))
    report=dict(status='DIAGNOSTIC_NOT_TERRAIN_ACCEPTANCE',source_sha256=sha(source),vertices=int(h.size),dry_vertices=int(dry.sum()),dry_below_1p25=int((dry&(h<1.25-1e-5)).sum()),dry_below_1p4=int(low.sum()),dry_below_1p6=int((dry&(h<1.6)).sum()),water_raster_classification_disagreements=int((exact_wet!=wet).sum()),largest_low_dry_components=comps)
    print(json.dumps({k:v for k,v in report.items() if k!='largest_low_dry_components'}),flush=True)
    # Subcell grid: 2m in every coastal cell with a dry/wet corner transition.
    w=exact_wet
    cut=(w[:-1,:-1]|w[1:,:-1]|w[:-1,1:]|w[1:,1:])&~(w[:-1,:-1]&w[1:,:-1]&w[:-1,1:]&w[1:,1:])
    rr,cc=np.where(cut)
    all_records=[];group_counts={};lowest=[]
    for dz in (1.,3.,5.):
        for dx in (1.,3.,5.):
            x=cc*6+dx;z=12282-rr*6-dz;p=points(x,z)
            hit=tree.query(p,predicate='intersects');water=np.full(len(p),-np.inf)
            np.maximum.at(water,hit[0],heights[hit[1]])
            ground=sample(h,x+200000,z);is_dry=~np.isfinite(water)
            # Ocean exists below the whole map; <1.25 outside all source water is suspect.
            risk=is_dry&(ground<1.25)
            for key,mask in [('dry',is_dry),('dry_below_1',is_dry&(ground<1)),('dry_below_1p25',risk),('dry_below_1p4',is_dry&(ground<1.4))]:group_counts[key]=group_counts.get(key,0)+int(mask.sum())
            ids=np.flatnonzero(risk)
            all_records.extend(np.c_[x[ids],z[ids],ground[ids]].tolist())
            print(f'Subcell {dx}/{dz}: dry={is_dry.sum()} below1.25={risk.sum()}',flush=True)
    risks=np.array(all_records).reshape(-1,3)
    np.save(OUT/'dry-subcell-below-diagnostic-envelope.npy',risks)
    report['shore_subcells']=dict(spacing_m=2,shore_cells=len(rr),samples=len(rr)*9,**group_counts)
    # Rank spatially distinct low patches for fixed cameras/runtime samples.
    selected=[]
    for i in np.argsort(risks[:,2]):
        row=risks[i]
        if all(np.linalg.norm(row[:2]-np.array(p[:2]))>=150 for p in selected):selected.append(row.tolist())
        if len(selected)==20:break
    report['runtime_target_candidates']=selected
    hx=np.diff(h.astype(float),axis=1)/6;hz=np.diff(h.astype(float),axis=0)/6
    slopes=np.maximum(np.degrees(np.arctan(np.hypot(hx[:-1],hz[:,1:]))),np.degrees(np.arctan(np.hypot(hx[1:],hz[:,:-1]))))
    chordx=abs(h[:,1:-1]-(h[:,:-2]+h[:,2:])/2)
    chordz=abs(h[1:-1]-(h[:-2]+h[2:])/2)
    report['native_shape']=dict(maximum_triangle_slope_deg=float(slopes.max()),slope_percentiles_deg=np.percentile(slopes,[50,90,99,99.9]).tolist(),x_half_chord_percentiles_m=np.percentile(chordx,[50,90,99,99.9]).tolist(),z_half_chord_percentiles_m=np.percentile(chordz,[50,90,99,99.9]).tolist())
    report['limits']=['Conservative sea diagnostic1.25m is not a new measured maximum.','Subcell shoreline samples only; not whole polygon dry-area proof or flooding area.','Native raster and height curvature do not determine rendered LOD or texture quality.']
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    np.savez_compressed(OUT/'diagnostic-masks.npz',water=exact_wet,low_dry=low,shore_cells=cut)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    fig,axs=plt.subplots(1,2,figsize=(15,7))
    shade=LightSource(azdeg=310,altdeg=35).hillshade(h,vert_exag=1,dx=6,dy=6)
    axs[0].imshow(shade,extent=[0,12.282,0,12.282],cmap='gray',origin='upper')
    axs[0].set_title('V10: geometría, sin textura satélite')
    axs[1].imshow(np.ma.masked_where(~dry,h),extent=[0,12.282,0,12.282],cmap='terrain',vmin=0,vmax=110,origin='upper')
    axs[1].imshow(np.ma.masked_where(~low,low),extent=[0,12.282,0,12.282],cmap='autumn',vmin=0,vmax=1,origin='upper')
    for i,p in enumerate(selected):axs[1].plot(p[0]/1000,p[1]/1000,'r.',ms=4);axs[1].annotate(str(i),np.array(p[:2])/1000,fontsize=6)
    axs[1].set_title('Rojo: muestras secas bajas / amarillo: vértices <1,4m')
    for ax in axs:ax.set_xlabel('Este local (km)');ax.set_ylabel('Norte local (km)')
    fig.tight_layout();fig.savefig(OUT/'outline-diagnostic.png',dpi=160);plt.close(fig)
    print(json.dumps(report['shore_subcells']),flush=True)

if __name__=='__main__':main()
