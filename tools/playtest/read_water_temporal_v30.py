"""Read a complete frozen temporal experiment, without rewriting shore acceptance."""
from pathlib import Path
import argparse
import hashlib
import json
import math


def read_series(ref, text):
    points = {p['id']:p for p in ref['points']}
    samples = ref['samples']
    count = len(points)
    interval = ref['interval_s']
    lines = text.splitlines()
    assert len(points)==len(ref['points']), 'Duplicate reference ID'
    assert lines[0]==ref['header'] and lines[1]==f'BEGIN;{count};{samples};{interval}'
    assert lines[-1]==f'END;{samples};{count}', 'Missing terminal'
    assert len(lines)==3+count*samples, 'Wrong row count'
    actual = {i:[] for i in points}
    for k, line in enumerate(lines[2:-1]):
        f = line.split(';')
        assert len(f)==ref.get('fields',15) and f[0]=='T', 'Bad schema'
        sample, ident = int(f[1]), int(f[2])
        assert sample==k//count and ident in points, 'Wrong round or ID'
        assert f[5] in ('true','false') and f[6] in ('true','false'), 'Bad boolean'
        assert len(actual[ident])==sample, 'Duplicate/missing ID in round'
        values = [float(f[i]) for i in (3,4,7,8,9,10,11,12,13,14)]
        assert all(math.isfinite(x) for x in values), 'Nonfinite sample'
        row = dict(zip(('time_ms','ground','no_fake','with_fake','depth_bed','depth_above','depth_plane_minus_1','sea_level','sea_wave','sea_wave_max'),values))
        row.update(sea=f[5]=='true',pond=f[6]=='true')
        if ref.get('fields',15)==17:
            extra=[float(f[15]),float(f[16])]
            assert all(math.isfinite(x) for x in extra), 'Nonfinite weather'
            row.update(wind_mps=extra[0],overcast=extra[1])
        assert abs(row['ground']-points[ident]['expected_ground_m'])<=.02, 'Unexpected terrain'
        if actual[ident]:
            assert row['time_ms']-actual[ident][-1]['time_ms']>=interval*1000-1, 'Temporal samples too close/reversed'
        actual[ident].append(row)
    def span(values):
        return dict(min=min(values),max=max(values))
    output=[]
    for ident, rows in actual.items():
        assert len(rows)==samples
        elapsed=(rows[-1]['time_ms']-rows[0]['time_ms'])/1000
        assert elapsed>=(samples-1)*interval-.001, 'Insufficient duration'
        def residual(field):
            return [r['depth_bed']-(r[field]-r['ground']-.01) for r in rows]
        output.append(dict(id=ident,role=points[ident]['role'],x=points[ident]['x'],z=points[ident]['z'],elapsed_s=elapsed,
            pond_true=sum(r['pond'] for r in rows),sea_true=sum(r['sea'] for r in rows),
            positive_depth_samples=sum(r['depth_bed']>0 for r in rows),
            depth_sign_changes=sum((a['depth_bed']>0)!=(b['depth_bed']>0) for a,b in zip(rows,rows[1:])),
            ranges={key:span([r[key] for r in rows]) for key in rows[0] if key not in ('pond','sea','time_ms','wind_mps','overcast')},
            no_fake_minus_ground=span([r['no_fake']-r['ground'] for r in rows]),
            depth_residual_no_fake=span(residual('no_fake')),
            depth_residual_with_fake=span(residual('with_fake')),
            depth_above_minus_bed=span([r['depth_above']-r['depth_bed'] for r in rows]),
            max_gap_s=max(b['time_ms']-a['time_ms'] for a,b in zip(rows,rows[1:]))/1000))
    gate=phase_gate(ref,actual) if ref.get('phases') else None
    return dict(status='DIAGNOSTIC_SERIES_COMPLETE',samples_per_point=samples,point_count=count,results=output,gate=gate,
        control_gate=reference_control_gate(ref, actual),
        limits=['No terrain, appearance, navigation or boat PASS is awarded.','A valid time series can contain persistent physical failures.','Relations between native APIs are empirical observations, not engine source proof.'])


def reference_control_gate(ref, actual):
    """Judge declared controls against their role, never against a failed baseline.

    This is separate from the shallow-point gate: a local shore repair may work
    while a missing positive control invalidates the wider experiment.
    """
    positive_pond = {'deep_pond', 'high_deep_pond', 'high_pond_control'}
    dry = {'dry_bank', 'changed_outline_dry_control'}
    checked, failures = [], []
    for point in ref['points']:
        role, ident = point['role'], point['id']
        rows = actual[ident]
        if role in positive_pond:
            bad = [k for k, row in enumerate(rows) if not row['pond'] or row['depth_bed'] <= 0]
        elif role == 'sea':
            bad = [k for k, row in enumerate(rows) if not row['sea'] or row['depth_bed'] <= 0]
        elif role in dry:
            bad = [k for k, row in enumerate(rows) if row['pond'] or row['depth_bed'] > 0]
        else:
            continue
        checked.append(dict(id=ident, role=role, samples=len(rows), failing_samples=len(bad)))
        if bad:
            failures.append(dict(id=ident, role=role, first_failed_sample=bad[0], failing_samples=len(bad)))
    present = {p['role'] for p in ref['points']}
    missing = sorted(set(ref.get('required_control_roles', [])) - present)
    status = ('FAIL_REFERENCE_CONTROLS' if failures else
              'INCONCLUSIVE_REFERENCE_CONTROLS' if missing or not checked else 'PASS_REFERENCE_CONTROLS')
    return dict(status=status, checked=checked, failures=failures, missing_roles=missing,
                limit='Role and presence/depth over the sampled window; not a maximum-wave envelope.')


def phase_gate(ref, actual):
    """V3 only: both phases must reach their weather, and every frozen shallow point must keep its
    pond and a positive bed depth in every sample. A phase that misses its weather is INCONCLUSIVE."""
    out = []
    for ph in ref['phases']:
        rows = {i: r[ph['first']:ph['first'] + ph['count']] for i, r in actual.items()}
        any_rows = next(iter(rows.values()))
        winds = [r['wind_mps'] for r in any_rows]; overcast = [r['overcast'] for r in any_rows]
        if ph['name'] == 'storm':
            reached = min(overcast) >= .95 and min(winds) >= .75 * ph['wind_mps']
        else:
            reached = max(overcast) <= .15 and max(winds) <= 1.0
        shallow = [i for i in rows if ref_role(ref, i) == 'frozen_shallow_failure']
        failing = [dict(id=i, pond_false=sum(not r['pond'] for r in rows[i]),
                        non_positive_depth=sum(r['depth_bed'] <= 0 for r in rows[i]),
                        min_depth_bed=min(r['depth_bed'] for r in rows[i]))
                   for i in shallow if any((not r['pond']) or r['depth_bed'] <= 0 for r in rows[i])]
        out.append(dict(name=ph['name'], weather_reached=reached, wind_mps=dict(min=min(winds), max=max(winds)),
                        overcast=dict(min=min(overcast), max=max(overcast)), shallow_points=len(shallow),
                        failing=failing, min_shallow_depth_bed=min(min(r['depth_bed'] for r in rows[i]) for i in shallow)))
    status = ('INCONCLUSIVE_PHASE_WEATHER' if not all(p['weather_reached'] for p in out) else
              'FAIL_SHALLOW_DEPTH_UNDER_WEATHER' if any(p['failing'] for p in out) else 'PASS_SHALLOW_DEPTH_BOTH_PHASES')
    return dict(status=status, phases=out)


def ref_role(ref, ident):
    return next(p['role'] for p in ref['points'] if p['id'] == ident)


def controls():
    ref=dict(header='BALTIC_V30_WATER_TEMPORAL_V1;BalticTrial',samples=2,interval_s=2,
        points=[dict(id=1,x=1,z=1,expected_ground_m=2,role='frozen_shallow_failure')])
    good=ref['header']+'\nBEGIN;1;2;2\nT;0;1;5000;2;false;true;2.1;2.0;-0.01;-100;1;0.8;0.1;0.25\nT;1;1;7000;2;false;true;2.1;2.2;0.19;-99.8;1.2;0.8;0.1;0.25\nEND;2;1\n'
    result=read_series(ref,good)
    assert result['results'][0]['depth_sign_changes']==1
    bad=dict(missing_end=good.rsplit('END;',1)[0],wrong_world=good.replace(';BalticTrial',';chernarusplus'),
        unknown_id=good.replace('T;1;1;','T;1;9;'),duplicate_round=good.replace('T;1;1;','T;0;1;'),
        nonfinite=good.replace(';7000;2;',';7000;nan;'),clock_stall=good.replace(';7000;',';5000;'),
        wrong_terrain=good.replace(';7000;2;',';7000;3;'),missing_sample=good.replace(good.splitlines()[3]+'\n',''))
    rejected=[]
    for name, text in bad.items():
        try:read_series(ref,text)
        except (AssertionError,ValueError,IndexError):rejected.append(name)
        else:raise AssertionError('False acceptance: '+name)
    v3=controls_v3()
    return dict(status='PASS_READER_CONTROLS',positive=1,negative=rejected,v3=v3,scope='Synthetic reader controls only')


def controls_v3():
    ref=dict(header='BALTIC_V30_WATER_TEMPORAL_V3;BalticTrial',samples=4,interval_s=2,fields=17,
        phases=[dict(name='calm',first=0,count=2,overcast=.1,wind_mps=.1),dict(name='storm',first=2,count=2,overcast=1,wind_mps=20)],
        points=[dict(id=1,x=1,z=1,expected_ground_m=2,role='frozen_shallow_failure')])
    def row(i,t,bed,wind,ovc,pond='true'):
        return f'T;{i};1;{t};2;false;{pond};2.2;2.15;{bed};-99.8;1.2;0.8;0.1;0.25;{wind};{ovc}'
    def series(rows):
        return ref['header']+'\nBEGIN;1;4;2\n'+'\n'.join(rows)+'\nEND;4;1\n'
    good=series([row(0,5000,.15,.1,.1),row(1,7000,.14,.1,.1),row(2,40000,.08,20,1),row(3,42000,.07,19.5,1)])
    assert read_series(ref,good)['gate']['status']=='PASS_SHALLOW_DEPTH_BOTH_PHASES'
    exposed=series([row(0,5000,.15,.1,.1),row(1,7000,.14,.1,.1),row(2,40000,-.01,20,1),row(3,42000,.07,19.5,1)])
    assert read_series(ref,exposed)['gate']['status']=='FAIL_SHALLOW_DEPTH_UNDER_WEATHER'
    no_pond=series([row(0,5000,.15,.1,.1),row(1,7000,.14,.1,.1,'false'),row(2,40000,.08,20,1),row(3,42000,.07,19.5,1)])
    assert read_series(ref,no_pond)['gate']['status']=='FAIL_SHALLOW_DEPTH_UNDER_WEATHER'
    calm_storm=series([row(0,5000,.15,.1,.1),row(1,7000,.14,.1,.1),row(2,40000,.08,3,.2),row(3,42000,.07,3,.2)])
    assert read_series(ref,calm_storm)['gate']['status']=='INCONCLUSIVE_PHASE_WEATHER'
    rejected=[]
    for name,text in dict(short_row=good.replace(';19.5;1\n',';19.5\n'),nan_wind=good.replace(';20;1\n',';nan;1\n'),
                          v2_schema=good.replace(';0.1;0.1\n','\n',1)).items():
        try:read_series(ref,text)
        except (AssertionError,ValueError,IndexError):rejected.append(name)
        else:raise AssertionError('False acceptance: '+name)
    return dict(positive=1,gate_controls=['exposed_bed','pond_lost','storm_not_reached'],negative=rejected)


def read_order(ref, primary, text):
    lines = text.splitlines()
    source = [r.split(';') for r in primary.splitlines()[2:-1]]
    assert lines[0]==ref['header'].replace('_TEMPORAL_','_ORDER_'), 'Order header must match the primary revision'
    assert lines[-1]==f'END;{ref["samples"]};{len(ref["points"])}'
    assert len(lines)==len(source)+2, 'Incomplete order probe'
    by_id={p['id']:[] for p in ref['points']}
    for fields, line in zip(source,lines[1:-1]):
        f=line.split(';')
        assert len(f)==7 and f[0]=='O' and f[1:4]==fields[1:4], 'Order probe mismatches primary'
        values=[float(x) for x in f[4:]]
        assert all(math.isfinite(x) for x in values)
        assert values[1]==float(fields[7]), 'Primary query mismatches side record'
        by_id[int(f[2])].append(values)
    output=[]
    for ident,rows in by_id.items():
        presence=[r[1]-r[0] for r in rows]
        depth=[r[2]-r[1] for r in rows]
        output.append(dict(id=ident,after_presence_minus_before=dict(min=min(presence),max=max(presence)),
                           after_depth_minus_after_presence=dict(min=min(depth),max=max(depth))))
    return dict(status='ORDER_COMPARISON_COMPLETE',results=output,
                limit='Before/after API observations; no engine implementation or visual proof.')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path)
    ap.add_argument('--log',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--controls',action='store_true')
    ap.add_argument('--order-log',type=Path)
    a=ap.parse_args()
    assert not a.out.exists(), 'Preserve prior evidence'
    if a.controls: result=controls()
    else:
        assert a.reference and a.log
        result=read_series(json.loads(a.reference.read_text()),a.log.read_text(encoding='utf-8-sig'))
        result['files']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.reference,a.log)}
        if a.order_log:
            result['order']=read_order(json.loads(a.reference.read_text()),a.log.read_text(encoding='utf-8-sig'),a.order_log.read_text(encoding='utf-8-sig'))
            result['files'][str(a.order_log)]=hashlib.sha256(a.order_log.read_bytes()).hexdigest()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],out=str(a.out)),indent=2))


if __name__=='__main__':main()
