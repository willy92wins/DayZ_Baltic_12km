"""Fail-closed consumer for the visual probe, with separate native/mesh queries.

RV Geometry checks bed location/identity. Bullet BUILDING is also required for
exposed pilot bed: this proves that server query, not client CCT walking. No
appearance verdict. Water uses the saved water_ext Roadway face, not visual Y.
"""
import argparse,json,math,hashlib
from pathlib import Path


def boolean(s):
    assert s in ('true','false'),('invalid boolean',s)
    return s=='true'


def vector(s):
    v=list(map(float,s.strip('<> ').split(',')))
    if len(v)!=3:raise ValueError(('invalid engine vector',s))
    assert all(math.isfinite(x) for x in v)
    return v


def parse(text,expected):
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    assert lines[0]=='BALTIC_VISUAL_PROBE_V3;BalticTrial','wrong probe header'
    assert lines.count('BEGIN;'+str(expected))==1 and lines.count('END;'+str(expected))==1,'probe incomplete'
    assert lines[-1]=='END;'+str(expected),'trailing content after probe end'
    rows={}
    for line in lines[2:-1]:
        a=line.split(';');assert len(a)==22 and a[0]=='P',('malformed row',line)
        ident=int(a[1]);assert ident not in rows,('duplicate',ident)
        row=dict(ground=float(a[2]),sea=boolean(a[3]),pond=boolean(a[4]),surface=float(a[5]),depth=float(a[6]),road=float(a[7]),objects=int(a[8]),
                 rv=boolean(a[9]),rv_pos=vector(a[10]),rv_shapes=a[11].lower().replace('/','\\'),bullet=boolean(a[12]),bullet_pos=vector(a[13]),bullet_shape=a[14].lower().replace('/','\\'))
        assert all(math.isfinite(row[k]) for k in ('ground','surface','depth','road'))
        row.update(sea_refs=list(map(float,a[15:18])),sea_refs_valid=boolean(a[18]),time_ms=int(a[19]))
        row.update(rv_normal=vector(a[20]),bullet_normal=vector(a[21]))
        assert all(math.isfinite(v) for v in row['sea_refs']) and row['time_ms']>=0
        rows[ident]=row
    assert len(rows)==expected
    times=[r['time_ms'] for r in rows.values()]
    assert all(b>a for a,b in zip(times,times[1:])), 'non-increasing measurement clock'
    return rows


def projected_margin(r):
    n=r['bullet_normal'];length=math.sqrt(sum(v*v for v in n))
    assert .99<=length<=1.01 and n[1]>0, 'invalid Bullet contact normal'
    return sum((b-a)*v/length for a,b,v in zip(r['rv_pos'],r['bullet_pos'],n))


def calibrate(text,expected_grid=289):
    lines=text.splitlines()
    assert lines[0]=='BALTIC_COLLISION_DIAGNOSTIC_V3' and lines[-1]=='END;289'
    groups={k:[] for k in ('spawn_native','empty')};margins=[]
    for line in lines:
        a=line.split(';')
        if a[0]!='RAY' or a[1] not in groups:continue
        assert len(a)==12
        groups[a[1]].append((float(a[2]),float(a[3])))
        rv=boolean(a[4]);bullet=boolean(a[7])
        if a[1]=='empty':assert not rv and not bullet, 'negative space control hit'
        elif rv or bullet:
            assert rv and bullet and 'dz\\water\\streambed\\streambed_leaf_long_straight.p3d' in a[6].lower() and a[9].lower()=='dz\\water\\streambed\\streambed_leaf_long_straight.p3d'
            margins.append(projected_margin(dict(rv_pos=vector(a[5]),bullet_pos=vector(a[8]),bullet_normal=vector(a[11]))))
    for group in groups.values():assert len(group)==expected_grid and len(set(group))==expected_grid
    assert len(margins)>=3 and max(margins)-min(margins)<.002 and .038<sum(margins)/len(margins)<.042
    return dict(margin_m=sum(margins)/len(margins),native_hits=len(margins),empty_misses=expected_grid,range_m=[min(margins),max(margins)])


def judge(points,rows,margin):
    if not points or not math.isfinite(margin) or margin <= 0:
        raise ValueError('empty probe or invalid collision margin')
    ids=[p['id'] for p in points]
    if len(set(ids)) != len(ids):raise ValueError('duplicate expected point IDs')
    for p in points:
        if p['expect'] not in ('wet','dry','sea','ground'):
            raise ValueError(('unknown expected surface',p['id'],p['expect']))
        required=['x','z','ground']
        if p['expect'] in ('wet','dry') or p.get('collision_pilot'):required.append('bed')
        if p['expect']=='wet':required.append('water_ext')
        for key in required:
            if not math.isfinite(p[key]):raise ValueError(('non-finite expected point',p['id'],key))
    assert set(rows)=={p['id'] for p in points},'unexpected or missing IDs'
    tide_ok=all(r['sea_refs_valid'] and max(r['sea_refs'])-min(r['sea_refs'])<=.02 for r in rows.values())
    failures=[]
    for p in points:
        r=rows[p['id']];why=[]
        if abs(r['ground']-p['ground'])>.01:why.append('native ground differs >1cm')
        if p['expect']=='wet':
            if not r['pond'] or r['sea'] or r['depth']<=0:why.append('expected pond water absent')
            if abs(r['surface']-p['water_ext'])>.05:why.append('water surface differs >5cm')
            if abs(r['road']-max(p['bed'],p['water_ext'],p['ground']))>.03:why.append('roadway differs >3cm')
        elif p['expect']=='dry':
            if r['pond'] or r['sea'] or r['depth']>0:why.append('dry bank has water')
            if abs(r['road']-max(p['bed'],p['ground']))>.03:why.append('bank roadway differs >3cm')
        elif p['expect']=='sea':
            sea=sum(r['sea_refs'])/3
            if not r['sea_refs_valid'] or max(r['sea_refs'])-min(r['sea_refs'])>.02:why.append('sea reference unavailable')
            elif not r['sea'] or r['pond'] or r['depth']<=0 or abs(r['surface']-sea)>.05:why.append('sea does not reach intended point')
        if p.get('collision_pilot'):
            if not r['rv'] or 'baltic_stream_pilot\\' not in r['rv_shapes'] or abs(r['rv_pos'][1]-p['bed'])>.03:why.append('RV bed collision missing/wrong')
            if not r['bullet'] or 'baltic_stream_pilot\\' not in r['bullet_shape']:why.append('Bullet BUILDING bed collision missing/wrong')
            else:
                try:offset=projected_margin(r)
                except AssertionError:why.append('invalid Bullet contact normal')
                else:
                    if abs(offset-margin)>.01:why.append('Bullet margin differs from vanilla >1cm')
            if any(abs(r[key][i]-p[axis])>.01 for key in ('rv_pos','bullet_pos') for i,axis in ((0,'x'),(2,'z'))):why.append('collision ray position differs >1cm')
        if why:failures.append(dict(id=p['id'],kind=p['kind'],site=p.get('site'),x=p['x'],z=p['z'],why=why,measured=r))
    sea_levels=[sum(r['sea_refs'])/3 for r in rows.values()]
    return dict(status='SERVER_PROBE_PASS' if tide_ok and not failures else 'FAIL',points=len(points),sea_level_range=[min(sea_levels),max(sea_levels)],sea_reference_valid=tide_ok,
                failure_count=len(failures),failures=failures,limits=['Measured server queries at fixed points only.','No client walking, visual, AI, full forest or global river rollout acceptance.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('points');ap.add_argument('log');ap.add_argument('output');ap.add_argument('--collision-reference',required=True);a=ap.parse_args()
    doc=json.loads(Path(a.points).read_text());assert doc['schema']=='ev112-visual-probe-v1'
    try:
        ref=Path(a.collision_reference).read_bytes();cal=calibrate(ref.decode('utf-8-sig'))
        result=judge(doc['points'],parse(Path(a.log).read_text(encoding='utf-8-sig'),len(doc['points'])),cal['margin_m'])
        result['collision_reference']=dict(cal,sha256=hashlib.sha256(ref).hexdigest(),path=str(Path(a.collision_reference).resolve()))
    except (AssertionError,ValueError,IndexError,KeyError,TypeError) as e:result=dict(status='FAIL_INVALID_EVIDENCE',error=str(e))
    Path(a.output).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='failures'},indent=2))
    raise SystemExit(0 if result['status']=='SERVER_PROBE_PASS' else 1)


if __name__=='__main__':main()
