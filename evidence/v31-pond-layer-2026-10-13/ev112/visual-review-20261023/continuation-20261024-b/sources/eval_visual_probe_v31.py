"""Fail-closed consumer for the visual probe, with separate native/mesh queries.

RV Geometry checks bed location/identity. Bullet BUILDING is also required for
exposed pilot bed: this proves that server query, not client CCT walking. No
appearance verdict. Water uses the saved water_ext Roadway face, not visual Y.
"""
import argparse,json,math
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
    assert lines[0]=='BALTIC_VISUAL_PROBE_V1;BalticTrial','wrong probe header'
    assert lines.count('BEGIN;'+str(expected))==1 and lines.count('END;'+str(expected))==1,'probe incomplete'
    assert lines[-1]=='END;'+str(expected),'trailing content after probe end'
    rows={}
    for line in lines[2:-1]:
        a=line.split(';');assert len(a)==15 and a[0]=='P',('malformed row',line)
        ident=int(a[1]);assert ident not in rows,('duplicate',ident)
        row=dict(ground=float(a[2]),sea=boolean(a[3]),pond=boolean(a[4]),surface=float(a[5]),depth=float(a[6]),road=float(a[7]),objects=int(a[8]),
                 rv=boolean(a[9]),rv_pos=vector(a[10]),rv_shapes=a[11].lower().replace('/','\\'),bullet=boolean(a[12]),bullet_pos=vector(a[13]),bullet_shape=a[14].lower().replace('/','\\'))
        assert all(math.isfinite(row[k]) for k in ('ground','surface','depth','road'))
        rows[ident]=row
    assert len(rows)==expected
    return rows


def judge(points,rows):
    assert set(rows)=={p['id'] for p in points},'unexpected or missing IDs'
    refs=[rows[p['id']]['surface'] for p in points if p['kind']=='sea_reference' and rows[p['id']]['sea'] and not rows[p['id']]['pond']]
    tide_ok=len(refs)==3 and max(refs)-min(refs)<=.02
    sea=sum(refs)/len(refs) if refs else None
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
            if not tide_ok:why.append('sea reference unavailable')
            elif not r['sea'] or r['pond'] or r['depth']<=0 or abs(r['surface']-sea)>.05:why.append('sea does not reach intended point')
        if p.get('collision_pilot'):
            if not r['rv'] or 'baltic_stream_pilot\\' not in r['rv_shapes'] or abs(r['rv_pos'][1]-p['bed'])>.03:why.append('RV bed collision missing/wrong')
            if not r['bullet'] or 'baltic_stream_pilot\\' not in r['bullet_shape'] or abs(r['bullet_pos'][1]-p['bed'])>.03:why.append('Bullet BUILDING bed collision missing/wrong')
        if why:failures.append(dict(id=p['id'],kind=p['kind'],site=p.get('site'),x=p['x'],z=p['z'],why=why,measured=r))
    return dict(status='SERVER_PROBE_PASS' if tide_ok and not failures else 'FAIL',points=len(points),sea_level=sea,sea_reference_valid=tide_ok,
                failure_count=len(failures),failures=failures,limits=['Measured server queries at fixed points only.','No client walking, visual, AI, full forest or global river rollout acceptance.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('points');ap.add_argument('log');ap.add_argument('output');a=ap.parse_args()
    doc=json.loads(Path(a.points).read_text());assert doc['schema']=='ev112-visual-probe-v1'
    try:result=judge(doc['points'],parse(Path(a.log).read_text(encoding='utf-8-sig'),len(doc['points'])))
    except (AssertionError,ValueError,IndexError) as e:result=dict(status='FAIL_INVALID_EVIDENCE',error=str(e))
    Path(a.output).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='failures'},indent=2))
    raise SystemExit(0 if result['status']=='SERVER_PROBE_PASS' else 1)


if __name__=='__main__':main()
