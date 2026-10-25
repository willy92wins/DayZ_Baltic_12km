from pathlib import Path
import argparse,json,math
from discover_components import sha
B=Path(__file__).parent

def judge(text,ref):
    rows=[s.split(';') for s in text.splitlines() if s];errors=[];points=[r for r in rows if r[0]=='P'];temporal=[r for r in rows if r[0]=='T'];end=[r for r in rows if r[0]=='END'];ge=[r for r in rows if r[0]=='GRID_END']
    if not rows or rows[0]!=['BALTIC_BASIN_TRANSLATE',ref['phase'],ref['terrain_sha256']]:errors.append('identity')
    if any(r[0]=='FAIL' for r in rows):errors.append('mission_failure')
    if len(points)!=len(ref['points']) or [r[1] for r in points]!=list(map(str,range(len(ref['points'])))):errors.append('grid_coverage_order')
    if ge!=[['GRID_END',str(len(ref['points']))]]:errors.append('grid_end')
    maxerr=0;wet=0;dry_positive=[]
    for row,p in zip(points,ref['points']):
        if len(row)!=9:errors.append('grid_schema');continue
        vals=list(map(float,[row[2],row[3],row[4],row[7],row[8]]))
        if not all(math.isfinite(v) for v in vals):errors.append('nonfinite');continue
        x,z,g,plane,depth=vals;maxerr=max(maxerr,abs(g-p['ground']))
        if abs(x-p['x'])>.006 or abs(z-p['z'])>.006:errors.append('coordinates')
        if abs(g-p['ground'])>.001:errors.append('ground')
        if p['assert_wet']:
            wet+=1
            if row[6]!='true' or abs(plane-p['level'])>.001:errors.append('water_plane')
        elif (row[5]=='true' or row[6]=='true') and plane>g+.03:dry_positive.append(int(row[1]))
    if len(temporal)!=64 or [r[1] for r in temporal]!=list(map(str,range(64))) or end!=[['END','64']]:errors.append('temporal_coverage')
    times=[];sea=[];wind=[];depths=[]
    for row in temporal:
        if len(row)!=12:errors.append('temporal_schema');continue
        vals=list(map(float,[row[2],row[3],row[4],row[5],row[6],row[7],row[10],row[11]]))
        if not all(math.isfinite(v) for v in vals):errors.append('temporal_nonfinite');continue
        ms,s,w,x,z,g,plane,d=vals;times.append(ms);sea.append(s);wind.append(w);depths.append(d)
        if abs(g-ref['points'][-1]['ground'])>.001 or row[8:10]!=['false','false'] or d>=0:errors.append('calibrated_dry')
    if times and (times[-1]-times[0]<12500 or any(b<=a or b-a>550 for a,b in zip(times,times[1:]))):errors.append('temporal_timing')
    if sea and (min(sea)>.66 or max(sea)<.84 or min(sea)<.649 or max(sea)>.851):errors.append('wave_envelope')
    if wind and min(wind)<19:errors.append('wind')
    return dict(pass_gate=not errors,errors=sorted(set(errors)),points=len(points),wet_level_points=wet,max_ground_error_m=maxerr,unasserted_positive_water_points=dry_positive,temporal_samples=len(temporal),sea_range=[min(sea),max(sea)] if sea else None,wind_range=[min(wind),max(wind)] if wind else None,dry_depth_range=[min(depths),max(depths)] if depths else None)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('label');parser.add_argument('phase',choices=['A','B']);a=parser.parse_args()
    ref=json.loads((B/f'probe-{a.phase}.json').read_text());path=B/f'runtime-{a.label}.log';text=path.read_text(encoding='utf-8-sig');result=judge(text,ref)
    negatives={}
    for name,prefix in [('missing_point','P;4;'),('missing_grid_end','GRID_END;'),('missing_time','T;2;'),('missing_end','END;')]:negatives[name]=not judge('\n'.join(s for s in text.splitlines() if not s.startswith(prefix)),ref)['pass_gate']
    row=next(s for s in text.splitlines() if s.startswith('P;0;'));f=row.split(';');f[4]=str(float(f[4])+1);negatives['height_error']=not judge(text.replace(row,';'.join(f),1),ref)['pass_gate']
    wet_id=next(i for i,p in enumerate(ref['points']) if p['assert_wet']);row=next(s for s in text.splitlines() if s.startswith(f'P;{wet_id};'));f=row.split(';');f[7]=str(float(f[7])+.1);negatives['wrong_water_level']=not judge(text.replace(row,';'.join(f),1),ref)['pass_gate']
    assert all(negatives.values()),negatives
    result|=dict(status='PASS_LOCAL_NATIVE_GROUND_AND_WATER' if result['pass_gate'] else 'FAIL',terrain_sha256=ref['terrain_sha256'],runtime_sha256=sha(path),negative=negatives,limits=['784 local ground queries and 19 interior water-level probes; not whole-map visual acceptance.','64 temporal samples at the reported physically dry point. Renderer effects do not follow from query flags.'])
    (B/f'verification-{a.label}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['pass_gate']

if __name__=='__main__':main()
