"""Measure the island support tradeoff at lake 217; does not mutate inputs."""
from pathlib import Path
import json
import numpy as np
from shapely import points
from shapely.geometry import shape
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'

def main():
    f=next(f for f in json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features'] if f['properties']['body']=='lake_217')
    g=shape(f['geometry']);level=f['properties']['level_m'];x0,z0,x1,z1=g.bounds
    islands=[dict(index=i,area_m2=shape(f['geometry']).area,intersection_m2=shape(f['geometry']).intersection(g).area,geo=shape(f['geometry'])) for i,f in enumerate(json.loads((EV/'protected-islands-game.json').read_text())['features']) if shape(f['geometry']).distance(g)<12]
    xx,zz=np.meshgrid(np.arange(x0,x1,1),np.arange(z0,z1,1));p=np.c_[xx.ravel(),zz.ravel()];p=p[g.contains(points(p))]
    refs={v:np.load(ROOT/f'tests/regional_foundation_combined_{v}/reference.npz')['candidate'] for v in ('v4','v8','v9')}
    records={v:dict(sample_count=len(p),wet_points=int((sample(h,p[:,0]+200000,p[:,1])<level).sum()),depth_quantiles=np.quantile(level-sample(h,p[:,0]+200000,p[:,1]),[0,.1,.5,.9,1]).tolist()) for v,h in refs.items()}
    report=dict(lake_properties=f['properties'],area_m2=g.area,bounds=g.bounds,nearby_islands=[{k:v for k,v in r.items() if k!='geo'} for r in islands],versions=records)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(16,6))
    for ax,(v,h) in zip(axes,refs.items()):
        value=level-sample(h,p[:,0]+200000,p[:,1]);ax.scatter(p[:,0],p[:,1],c=value,cmap='coolwarm_r',vmin=-2,vmax=2,s=12,marker='s')
        for poly in (list(g.geoms) if hasattr(g,'geoms') else [g]):ax.plot(*poly.exterior.xy,color='navy')
        for r in islands:
            for poly in (list(r['geo'].geoms) if hasattr(r['geo'],'geoms') else [r['geo']]):ax.plot(*poly.exterior.xy,color='green');ax.text(poly.centroid.x,poly.centroid.y,str(r['index']),color='black')
        ax.set_aspect('equal');ax.set_xlim(x0-12,x1+12);ax.set_ylim(z0-12,z1+12);ax.set_title(v+' depth blue=wet red=dry')
    fig.savefig(EV/'lake-217-island-tradeoff-v9.png',dpi=130);plt.close(fig)
    (EV/'lake-217-island-tradeoff-v9.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
