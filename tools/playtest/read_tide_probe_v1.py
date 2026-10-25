"""Read the log of missions/BalticTideProbeV1: tide scan per date and the held series (sea, surface, weather).

Rows: SCAN;day;step;Y-M-D;h;m;level;min;max;waveMax;waveCur
      HOLD;step;level;Y-M-D;h;m
      SEA;sample;ms;Y-M-D;h;m;level;min;max;waveMax;waveCur;nf1;wf1;nf2;wf2;nf3;wf3;wind;overcast;rain
      WIND;storm|calm;Y-M-D;h;m
"""
import argparse
import json
from pathlib import Path


def read(text):
    lines = [l for l in text.splitlines() if l.strip()]
    head = lines[0].split(';')
    assert head[0] == 'BALTIC_TIDE_PROBE_V1' and head[1] == 'BalticTrial', 'Wrong log or world'
    days, steps = int(head[2]), int(head[3])
    scan, hold, sea, wind = {}, None, [], []
    for l in lines[1:]:
        f = l.split(';')
        if f[0] == 'SCAN':
            assert len(f) == 11, l
            d = int(f[1])
            scan.setdefault(d, []).append(dict(step=int(f[2]), date=f[3], hour=int(f[4]), minute=int(f[5]),
                                               level=float(f[6]), min=float(f[7]), max=float(f[8]),
                                               wave_max=float(f[9]), wave_cur=float(f[10])))
        elif f[0] == 'HOLD':
            hold = dict(step=int(f[1]), level=float(f[2]), date=f[3], hour=int(f[4]), minute=int(f[5]))
        elif f[0] == 'SEA':
            assert len(f) == 20, l
            v = [float(x) for x in f[6:]]
            sea.append(dict(sample=int(f[1]), ms=int(f[2]), date=f[3], hour=int(f[4]), minute=int(f[5]),
                            level=v[0], min=v[1], max=v[2], wave_max=v[3], wave_cur=v[4],
                            open_sea=(v[5], v[6]), narva_edge1=(v[7], v[8]), north_coast=(v[9], v[10]),
                            wind=v[11], overcast=v[12], rain=v[13]))
        elif f[0] == 'WIND':
            wind.append(dict(state=f[1], date=f[2], hour=int(f[3]), minute=int(f[4])))
    out = dict(days_declared=days, steps_declared=steps, scan=[], hold=hold, wind_events=wind)
    for d, rows in sorted(scan.items()):
        lv = [r['level'] for r in rows]
        hi, lo = max(rows, key=lambda r: r['level']), min(rows, key=lambda r: r['level'])
        dates = sorted({r['date'] for r in rows})
        out['scan'].append(dict(day_index=d, rows=len(rows), dates=dates, level_min=min(lv), level_max=max(lv),
                                api_min=sorted({r['min'] for r in rows}), api_max=sorted({r['max'] for r in rows}),
                                wave_max=sorted({r['wave_max'] for r in rows}),
                                wave_cur_minus_level_plus_075=max(abs(r['wave_cur'] - (r['level'] - 0.75)) for r in rows),
                                high=dict(date=hi['date'], hour=hi['hour'], minute=hi['minute'], level=hi['level']),
                                low=dict(date=lo['date'], hour=lo['hour'], minute=lo['minute'], level=lo['level'])))
    if sea:
        def span(key, i=None):
            vals = [r[key] if i is None else r[key][i] for r in sea]
            return dict(min=min(vals), max=max(vals))
        out['held'] = dict(samples=len(sea), level=span('level'), wind=span('wind'), overcast=span('overcast'),
                           open_sea_no_fake=span('open_sea', 0), open_sea_with_fake=span('open_sea', 1),
                           narva_edge1_with_fake=span('narva_edge1', 1), north_coast_with_fake=span('north_coast', 1),
                           fake_minus_no_fake_open_sea=dict(min=min(r['open_sea'][1] - r['open_sea'][0] for r in sea),
                                                            max=max(r['open_sea'][1] - r['open_sea'][0] for r in sea)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    res = read(a.log.read_text(encoding='utf-8-sig'))
    text = json.dumps(res, indent=1)
    if a.out:
        assert not a.out.exists(), 'Preserve prior evidence'
        a.out.write_text(text + '\n', encoding='utf-8')
    print(text[:6000])


if __name__ == '__main__':
    main()
