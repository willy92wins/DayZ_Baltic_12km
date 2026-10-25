"""Server-only readback mission for the vanilla channel pilot (plans/v30-vanilla-channel-water-pilot.md, step 4).

Per placed vanilla piece: the object found at its origin, with direction, up vector and scale. Per sample, every
2 m along each reach axis (centre and inside both wet banks) and on a grid over each calibration pad piece:
SurfaceY, sea level, sea/pond flags, GetWaterSurfaceHeightNoFakeWave at two gameplay heights (hull: visual
surface + 0.05 m; body: visual surface - 1.0 m; ground + 0.5 / - 0.5 where there is no visual surface) and
GetWaterDepth at the body height. The reference freezes, before the run, the visual top surface (with its zone:
flat, +z skirt or -z skirt) and the engine level predicted for both heights by tools/water/engine_water_model.py.
V1 (run 8392533a, git bf46492) queried from ground + 50 m, which displaces the reading on pitched pieces.
Helper functions hold at most 32 calls (the engine compiler rejects longer generated functions). Usage:
  prepare_vanilla_channel_readback.py --fit <fit dir> --mission <dir> --reference <json>
      [--name BalticVanillaChannelPilotV2] [--log baltic_vanilla_channel_pilot_v2.log] [--terrain <npz>]
--terrain replaces the fit's terrain_pilot.npz as the ground source (a later shore edit of the same fit).
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fit = load('fit', 'tools/water/fit_channel_pieces_v30.py')
ewm = load('ewm', 'tools/water/engine_water_model.py')
NAME = 'BalticVanillaChannelPilotV2'
LOG = 'baltic_vanilla_channel_pilot_v2.log'
BATCH = 32
HULL, BODY = 0.05, -1.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--fit', type=Path, required=True)
    ap.add_argument('--mission', type=Path, required=True)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--name', default=NAME)
    ap.add_argument('--log', default=LOG)
    ap.add_argument('--terrain', type=Path)
    a = ap.parse_args()
    name, log = a.name, a.log
    terrain = a.terrain or a.fit / 'terrain_pilot.npz'
    assert not a.mission.exists() and not a.reference.exists(), 'Preserve prior evidence'
    axes = json.loads((a.fit / 'axes.json').read_text(encoding='utf-8'))
    report = json.loads((a.fit / 'report.json').read_text(encoding='utf-8'))
    heights = np.load(terrain)['heights'].astype(float)

    pieces = []
    for reach, ax in axes.items():
        for p in ax['pieces']:
            pieces.append(dict(p, reach=reach))
    for p in report['pad']:
        pieces.append({'reach': 'PAD', 'type': p['type'], 'scale': p['scale'], 'matrix': p['matrix'], 'pitch_deg': p['pitch_deg']})
    model = [ewm.Piece(p['type'], p['matrix']) for p in pieces]

    points = []
    for reach, ax in axes.items():
        s = np.array(ax['s'])
        x, z = np.array(ax['x']), np.array(ax['z'])
        t = np.gradient(np.column_stack([x, z]), axis=0)
        t /= np.linalg.norm(t, axis=1, keepdims=True)
        n = np.column_stack([-t[:, 1], t[:, 0]])
        wl, wr = np.array(ax['wl']), np.array(ax['wr'])
        for i in np.where((s >= ax['s_lo']) & (s <= ax['s_hi']))[0]:
            offs = [0.0] + ([wl[i] - 1.0] if wl[i] >= 2.0 else []) + ([-(wr[i] - 1.0)] if wr[i] >= 2.0 else [])
            for off in offs:
                points.append((reach, float(s[i]), float(off), float(x[i] + off * n[i, 0]), float(z[i] + off * n[i, 1])))
    for k, p in enumerate(report['pad']):
        m = np.array(p['matrix'][:9]).reshape(3, 3)
        pos = np.array(p['matrix'][9:])
        right, fwd = m[0] / np.linalg.norm(m[0]), m[2] / np.linalg.norm(m[2])
        half_l = 12.0 * p['scale'] + 2.0
        half_w = (model[len(pieces) - len(report['pad']) + k].v[:, 0].max()) * p['scale']
        for dz in np.arange(-half_l, half_l + 0.01, 1.0):
            for dx in (0.0, half_w - 0.5, half_w + 0.5, -(half_w - 0.5), -(half_w + 0.5)):
                q = pos + dx * right + dz * np.array([fwd[0], 0, fwd[2]]) / math.hypot(fwd[0], fwd[2])
                points.append((f'PAD{k}', float(dz), float(dx), float(q[0]), float(q[2])))

    samples = []
    for reach, s, off, px, pz in points:
        ground = float(fit.bilinear(heights, px, pz))
        top = ewm.top_visual(model, px, pz)
        qh = top[0] + HULL if top else ground + 0.5
        qb = top[0] + BODY if top else ground - 0.5
        samples.append({'reach': reach, 's': s, 'offset': off, 'x': px, 'z': pz, 'ground': ground,
                        'surface': top[0] if top else None, 'zone': top[2] if top else None,
                        'top_piece': top[1] if top else None, 'qh': qh, 'qb': qb,
                        'model_hull': ewm.predict(model, px, qh, pz), 'model_body': ewm.predict(model, px, qb, pz)})

    lines = ['// Server-only readback of the vanilla channel pilot: pieces and water at gameplay heights along the reaches.',
             '// APIs (scripts/3_game/global/game.c): SurfaceGetSeaLevel :1176, GetWaterDepth :1183,',
             '// GetWaterSurfaceHeightNoFakeWave :1185; GetObjectsAtPosition; object.c GetPosition/GetDirection/GetDirectionUp.',
             'void main()', '{', '    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);',
             '    Weather weather = GetGame().GetWeather();', '    weather.MissionWeather(true);',
             '    weather.GetOvercast().SetLimits(0.1, 0.1);', '    weather.GetOvercast().Set(0.1, 0, 3600);',
             '    weather.GetRain().SetLimits(0, 0);', '    weather.GetRain().Set(0, 0, 3600);',
             '    weather.GetFog().SetLimits(0, 0);', '    weather.GetFog().Set(0, 0, 3600);', '}', '',
             f'class {name}Mission: MissionServer', '{',
             '    protected ref array<Object> m_Objects = new array<Object>;',
             '    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;',
             '    protected int m_Batch;', '    protected bool m_Started;', '    protected bool m_Done;', '    protected int m_StartMs;', '',
             '    void LogRow(string row)', '    {',
             f'        FileHandle file = OpenFile("$profile:{log}", FileMode.APPEND);',
             '        if (!file) { m_Done = true; return; }', '        FPrintln(file, row);', '        CloseFile(file);', '    }', '',
             '    override void OnInit()', '    {', '        super.OnInit();', '        if (!GetGame().IsDedicatedServer()) return;',
             f'        FileHandle file = OpenFile("$profile:{log}", FileMode.WRITE);', '        if (!file) return;',
             f'        FPrintln(file, "BALTIC_VANILLA_CHANNEL_PILOT_V2;" + GetGame().GetWorldName() + ";{len(pieces)};{len(samples)}");',
             '        CloseFile(file);', '        m_Started = true;', '        m_StartMs = GetGame().GetTime() + 10000;', '    }', '',
             '    void P(int index, float x, float y, float z, string model)', '    {',
             '        m_Objects.Clear();', '        m_Proxies.Clear();',
             '        GetGame().GetObjectsAtPosition(Vector(x, y, z), 0.5, m_Objects, m_Proxies);',
             '        foreach (Object o : m_Objects)', '        {', '            if (!o) continue;',
             '            string shape = o.GetShapeName();', '            shape.ToLower();',
             '            if (!shape.Contains(model)) continue;',
             '            string row = "P;" + index + ";" + shape;', '            row = row + ";" + o.GetPosition();',
             '            row = row + ";" + o.GetDirection();', '            row = row + ";" + o.GetDirectionUp();',
             '            row = row + ";" + o.GetScale();', '            LogRow(row);', '            return;', '        }',
             '        LogRow("P;" + index + ";MISSING");', '    }', '',
             '    void S(int index, float x, float z, float qh, float qb)', '    {', '        float ground = GetGame().SurfaceY(x, z);',
             '        float sea = GetGame().SurfaceGetSeaLevel();', '        bool isSea = GetGame().SurfaceIsSea(x, z);',
             '        bool pond = GetGame().SurfaceIsPond(x, z);',
             '        float hull = GetGame().GetWaterSurfaceHeightNoFakeWave(Vector(x, qh, z));',
             '        float body = GetGame().GetWaterSurfaceHeightNoFakeWave(Vector(x, qb, z));',
             '        float depth = GetGame().GetWaterDepth(Vector(x, qb, z));',
             '        string row = "W2;" + index + ";" + x;', '        row = row + ";" + z + ";" + ground;',
             '        row = row + ";" + sea + ";" + isSea + ";" + pond;', '        row = row + ";" + hull + ";" + body + ";" + depth;',
             '        LogRow(row);', '    }', '']
    calls = []
    for k, p in enumerate(pieces):
        pos = p['matrix'][9:]
        calls.append(f'P({k}, {pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f}, "{p["type"]}");')
    for k, smp in enumerate(samples):
        calls.append(f'S({k}, {smp["x"]:.4f}, {smp["z"]:.4f}, {smp["qh"]:.4f}, {smp["qb"]:.4f});')
    batches = [calls[i:i + BATCH] for i in range(0, len(calls), BATCH)]
    for b, chunk in enumerate(batches):
        lines += [f'    void Batch{b:04d}()', '    {'] + ['        ' + c for c in chunk] + ['    }', '']
    lines += ['    void RunBatch(int b)', '    {', '        switch (b)', '        {']
    for b in range(len(batches)):
        lines += [f'            case {b}: Batch{b:04d}(); break;']
    lines += ['        }', '    }', '',
              '    override void OnUpdate(float timeslice)', '    {', '        super.OnUpdate(timeslice);',
              '        if (!GetGame().IsDedicatedServer() || !m_Started || m_Done) return;',
              '        if (GetGame().GetTime() < m_StartMs) return;',
              f'        if (m_Batch < {len(batches)})', '        {', '            RunBatch(m_Batch);', '            m_Batch++;', '            return;', '        }',
              f'        LogRow("END;{len(pieces)};{len(samples)}");', '        m_Done = true;', '    }', '}', '',
              f'Mission CreateCustomMission(string path) {{ return new {name}Mission(); }}', '']
    a.mission.mkdir(parents=True)
    text = '\n'.join(lines)
    (a.mission / 'init.c').write_text(text, encoding='utf-8', newline='\n')
    ref = {'status': 'PREPARED_NOT_EXECUTED', 'version': 2, 'heights': {'hull': HULL, 'body': BODY},
           'pieces': [{'index': k, 'reach': p['reach'], 'type': p['type'], 'scale': p['scale'], 'matrix': p['matrix'],
                       'pitch_deg': p['pitch_deg']} for k, p in enumerate(pieces)],
           'samples': [dict(smp, index=k) for k, smp in enumerate(samples)], 'batches': len(batches),
           'mission_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'log': log, 'name': name,
           'inputs': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (a.fit / 'axes.json', a.fit / 'report.json', terrain)}}
    a.reference.write_text(json.dumps(ref) + '\n', encoding='utf-8')
    print(json.dumps({'pieces': len(pieces), 'samples': len(samples), 'batches': len(batches), 'mission_sha256': ref['mission_sha256']}))


if __name__ == '__main__':
    main()
