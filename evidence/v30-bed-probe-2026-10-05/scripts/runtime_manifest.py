"""Runtime manifest of the BALTIC-018 bed probe: runs, poses and captures (file, bytes, sha256)."""
import hashlib
import json
import sys
from pathlib import Path

P = Path('E:/DayZ-Baltic-Build/v30-v7probe')
RUNS = {'views': {'run': 'c20d6f6b-56f2-4414-9653-ae0b541da69f', 'mod': '@DayZ_Baltic_V7BedProbe',
                  'world': '7cecad69', 'surface': 'v6 (E:/DayZ-Baltic-Build/v30-v6/surface)'},
        'views-v5control': {'run': '5d3900d6-9131-4361-8d0f-dc5d2e4c2f3c', 'mod': '@DayZ_Baltic_V5Candidate',
                            'world': '8c523be2', 'surface': 'v5'},
        'views-B': {'run': '7294adce-8a52-48b5-aa6c-79a969151b92', 'mod': '@DayZ_Baltic_V7BedProbeB',
                    'world': 'eb383bd8', 'surface': 'v5 (E:/DayZ-Baltic-Build/v30-v5/surface)'}}
POSES = {'L269_330': ([120, 330, 900], [380, 2.64, 1230], [380, 0, 1230]),
         'L269_40': ([300, 40, 700], [360, 2.64, 900], [380, 0, 1230]),
         'L269_330_SHIFT': ([420, 330, 600], [380, 2.64, 1230], [380, 0, 1230]),
         'L269_330_later': ([120, 330, 900], [380, 2.64, 1230], [380, 0, 1230]),
         'L202_330': ([11540, 330, 820], [11800, 2.13, 1150], [11700, 0, 1460]),
         'L202_40': ([11740, 40, 950], [11800, 2.13, 1150], [11700, 0, 1460]),
         'LHIGH_80': ([3400, 80, 4250], [3457, 4.38, 4366], [3380, 0, 4240])}
out = {'mission': 'BalticTideProbeV2', 'client': '1920x1080, weather overcast 0.3 fog 0 rain 0, time 12:00',
       'workaround': 'player_teleport next to each pose before camera_set (BALTIC-001)',
       'notes': {'L269_330_later': 'the camera_set of a later LHIGH_80 attempt failed on a lapsed lease, so this '
                                   'frame is the L269_330 pose about 2.5 min after the first capture'},
       'poses': {k: {'cam_pos': v[0], 'look_at': v[1], 'player': v[2]} for k, v in POSES.items()}, 'runs': {}}
for folder, meta in RUNS.items():
    shots = []
    for f in sorted((P / folder).glob('*/capture_*.jpg')):
        shots.append({'pose': f.parent.name, 'name': f.name, 'bytes': f.stat().st_size,
                      'sha256': hashlib.sha256(f.read_bytes()).hexdigest()})
    out['runs'][folder] = dict(meta, folder=str(P / folder), shots=shots)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(sum(len(r['shots']) for r in out['runs'].values()), 'shots')
