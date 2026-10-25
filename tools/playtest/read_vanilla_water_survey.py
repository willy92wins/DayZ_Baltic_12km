"""Summarize the vanilla Chernarus water survey (missions/BalticVanillaWaterSurveyV1.chernarusplus).

Per family: placement tilt from GetDirectionUp, water flags and depth at the piece centre, and whether
the reported water surface follows the piece slope along its local Z axis. Read-only; engine
observations, not engine source.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import math

import numpy as np

BS = chr(92)


def vec(text):
    return [float(v) for v in text.strip('<> ').split(',')]


def family(shape):
    name = shape.split(BS)[-1].replace('.p3d', '')
    for prefix in ('river_24', 'stream_14', 'streambed', 'stones_'):
        if name.startswith(prefix):
            return prefix.rstrip('_')
    return 'pond' if ('pond' in name or name.startswith('lake')) else name


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.exists(), 'Preserve prior evidence'
    lines = a.log.read_text(encoding='utf-8').splitlines()
    assert lines[0].startswith('BALTIC_VANILLA_WATER_SURVEY_V1;') and lines[-1].startswith('END;'), 'Incomplete survey'
    objs, channel, samples = {}, [], collections.defaultdict(list)
    for line in lines:
        f = line.split(';')
        if f[0] == 'O':
            objs[int(f[1])] = dict(shape=f[2], pos=vec(f[3]), ori=vec(f[4]), up=vec(f[5]))
            # Same membership test as the mission (IsChannelShape): full path, so streambed\misc stones count.
            if any(k in f[2] for k in ('stream_', 'river_', 'streambed')):
                channel.append(int(f[1]))
        elif f[0] == 'W':
            samples[int(f[1])].append(dict(axis=f[2], off=float(f[3]), y=float(f[5]), ground=float(f[7]),
                                           sea=f[8] == 'true', pond=f[9] == 'true', plane=float(f[10]),
                                           depth=float(f[11])))
    placement = {}
    groups = collections.defaultdict(list)
    for o in objs.values():
        groups[family(o['shape'])].append(math.degrees(math.acos(max(-1.0, min(1.0, o['up'][1])))))
    for fam, tilt in groups.items():
        t = np.sort(np.array(tilt))
        placement[fam] = dict(pieces=int(t.size), tilted_over_0_05_deg=int((t > 0.05).sum()),
                              median_deg=float(np.median(t)), p95_deg=float(np.percentile(t, 95)), max_deg=float(t.max()))
    water = {}
    for fam in ('river_24', 'stream_14', 'streambed'):
        rows, ratios = [], []
        for idx, ss in samples.items():
            o = objs[channel[idx]]
            if family(o['shape']) != fam or o['pos'][1] <= 50:
                continue  # above 50 m the sea cannot supply the water reading
            centre = next(s for s in ss if s['off'] == 0)
            rows.append(centre)
            tilt = math.degrees(math.acos(max(-1.0, min(1.0, o['up'][1]))))
            line = sorted((s for s in ss if s['axis'] == 'z' and s['depth'] > 0), key=lambda s: s['off'])
            if tilt > 1 and len(line) >= 3:
                off = np.array([s['off'] for s in line])
                piece = np.polyfit(off, [s['y'] for s in line], 1)[0]
                if abs(piece) > 0.01:
                    ratios.append(np.polyfit(off, [s['plane'] for s in line], 1)[0] / piece)
        water[fam] = dict(pieces_above_50m=len(rows), centre_depth_positive=sum(r['depth'] > 0 for r in rows),
                          centre_pond_flag=sum(r['pond'] for r in rows),
                          centre_depth_median_m=float(np.median([r['depth'] for r in rows])) if rows else None,
                          water_to_piece_slope_ratio=dict(n=len(ratios), median=float(np.median(ratios)) if ratios else None,
                                                          iqr=[float(np.percentile(ratios, q)) for q in (25, 75)] if ratios else None))
    result = dict(status='VANILLA_WATER_SURVEY_SUMMARY', world=lines[0].split(';')[1], objects=len(objs),
                  channel_pieces=len(channel), sampled_channel_pieces=len(samples), placement=placement, water=water,
                  log_sha256=hashlib.sha256(a.log.read_bytes()).hexdigest(),
                  limits=['Server readback of native APIs; no visual, boat or drinking test.',
                          'Streambed water readings mix other surfaces; river/stream rows are the reliable ones.'])
    a.out.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main()
