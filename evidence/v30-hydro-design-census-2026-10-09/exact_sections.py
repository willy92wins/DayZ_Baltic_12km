"""Adjudicate sampled alarms by intersecting exact native wet polygons with sections."""
from pathlib import Path
import sys,json,collections,time
import numpy as np
import shapely
from shapely.geometry import shape,LineString
B=Path(__file__).parent
sys.path.insert(0,str(B));from census import SOURCE,PFILE,FFILE,DESIGN,intervals,sha
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009');from verify_native_turns import geometry
def main():
 begin=time.monotonic();data=json.loads((B/'attribution.json').read_text());h=np.load(SOURCE)['heights'].astype(float);p=np.load(PFILE);pf=np.repeat(p[:,:,None],4,axis=2);f=np.load(FFILE);profiles=np.load(DESIGN/'profiles.npz')
 water=json.loads((DESIGN/'water_v3.geojson').read_text())['features'];streams=json.loads((DESIGN/'streams_candidates.geojson').read_text())['features'];features={v['properties']['id']:v for v in water+streams if v['properties'].get('id')}
 rows=[]
 for index,gap in enumerate(data['gaps_detail']):
  key=gap['id'];a=profiles[key];s=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(a[:,1:3],axis=0),axis=1))];ss=np.arange(max(s[0],gap['start_s']-2),min(s[-1],gap['end_s']+2)+.01,.25)
  q=np.c_[np.interp(ss,s,a[:,1]),np.interp(ss,s,a[:,2])];direction=np.gradient(q,axis=0);length=np.linalg.norm(direction,axis=1);normal=np.c_[-direction[:,1],direction[:,0]]/np.maximum(length[:,None],1e-8)
  ca=max(0,int((q[:,0].min()-45)//6));cb=min(2047,int(np.ceil((q[:,0].max()+45)/6)));ra=max(0,int((12282-q[:,1].max()-45)//6));rb=min(2047,int(np.ceil((12282-q[:,1].min()+45)/6)))
  cells=[(r,c) for r in range(ra,rb) for c in range(ca,cb) if np.isfinite(p[r,c])]
  wet=geometry(h,pf,cells);visible=geometry(h,f,cells);corridor=shape(features[key]['geometry']).buffer(6)
  lines=shapely.linestrings(np.stack((q-normal*36,q+normal*36),axis=1));allowed=shapely.intersection(lines,corridor)
  widths=shapely.length(shapely.intersection(allowed,wet));vwidths=shapely.length(shapely.intersection(allowed,visible))
  dry=widths<=.01;vdry=vwidths<=.01
  row=dict(id=key,original_gap=gap,physical_dry_sections=int(dry.sum()),visible_dry_sections=int(vdry.sum()),sections=len(q),minimum_physical_width_m=float(widths.min()),minimum_visible_width_m=float(vwidths.min()),physical_dry_intervals=intervals(dry,ss),visible_dry_intervals=intervals(vdry,ss),status='EXACT_DRY_CONFIRMED' if np.any(dry) else 'SAMPLED_FALSE_ALARM_WATER_PRESENT')
  rows.append(row)
  if index%10==0:print(json.dumps(dict(done=index+1,total=len(data['gaps_detail']),seconds=time.monotonic()-begin)),flush=True)
 # Cross-section grid can miss a narrow valid stream: explicit adversarial fixture.
 thin=shapely.box(-1,.2,1,.7);line=LineString([(0,-3),(0,3)]);assert abs(thin.intersection(line).length-.5)<1e-10
 assert not any(thin.intersects(shapely.Point(0,y)) for y in np.arange(-3,3.1,1.5))
 report=dict(status='EXACT_ALARM_ADJUDICATION',source_sha256=sha(SOURCE),counts=dict(collections.Counter(r['status'] for r in rows)),rows=rows,controls=['thin_stream_between_discrete_samples_detected_by_exact_intersection'],limits=['Exact polygon sections remove sample aliasing; they still do not by themselves prove longitudinal connectivity or in-game render.'])
 (B/'exact-sections.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(counts=report['counts'],unprotected=[{k:v for k,v in row.items() if k!='original_gap'} for row in rows if row['original_gap']['attribution']=='UNATTRIBUTED'],seconds=time.monotonic()-begin),indent=2))
if __name__=='__main__':main()
