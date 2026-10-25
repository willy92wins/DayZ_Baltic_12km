"""Read actual deployed/installed ODOL water models; not a frame-cost verdict."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools/performance'), str(ROOT/'tools/playtest'),
               str(ROOT/'tools/vegetation'), 'C:/temp/moto_lanes/review_g3/tools']
import compare_static_worlds_ev112 as inventory
from attach_navmesh import read_pbo
from odol_reader import ODOL
import odol_reader
from prune_visual_forest_v31 import prefix, objects


def digest(data):
    return hashlib.sha256(data).hexdigest()


def census(path, custom):
    raw, _, entries = read_pbo(path)
    b = next(v for k,v in entries.items() if k.lower().endswith('.wrp'))
    if custom:
        src = inventory.B/'stage-visual-forest-20261024-b/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
        with src.open('rb') as f:
            prefix(f); _, name, rec = next(objects(f))
        anchor = dict(name=name,xyz=struct.unpack_from('<3f',rec,36))
        marker = rb'baltic_water_v30\\[^\x00]+\.p3d\x00'
    else:
        with inventory.SURVEY.open(encoding='utf-8-sig',newline='') as f:
            rec = next(csv.DictReader(f))
        anchor = dict(name=rec['shape'],xyz=[float(rec[k]) for k in ('x','y','z')])
        marker = rb'dz\\[^\x00]{1,200}\.p3d\x00'
    rows,names,reader = inventory.locate(b,marker,anchor)
    counts = np.bincount(rows['mi'],minlength=len(names))
    selected = {n:int(c) for n,c in zip(names,counts) if c and inventory.category(n) in ('custom_stream','custom_water','native_water')}
    return selected, dict(path=str(path),pbo_sha256=digest(raw),wrp_sha256=digest(b),reader=reader)


def model_summary(blob):
    od = ODOL.from_bytes(blob,strict=True)
    assert not od.lod_errors and all(l.lod_end_ok for l in od.lods)
    lods = []
    for l in od.lods:
        assert all(len(f.vertex_indices)>=3 and all(0<=v<len(l.vertices) for v in f.vertex_indices) for f in l.faces)
        lods.append(dict(resolution=l.resolution,vertices=len(l.vertices),polygons=len(l.faces),
                         triangle_equivalents=sum(len(f.vertex_indices)-2 for f in l.faces),
                         sections=len(l.sections),textures=l.textures,
                         materials=[m.material_name for m in l.materials],properties=dict(l.named_properties)))
    visual = sorted([l for l in lods if 0<=l['resolution']<1000],key=lambda l:l['resolution'])
    assert visual, 'no distance visual LOD found'
    return dict(bytes=len(blob),sha256=digest(blob),odol_version=od.version,lods=lods,
                visual_lods=len(visual),near=visual[0],far=visual[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__);ap.add_argument('out',type=Path);a=ap.parse_args()
    assert not a.out.exists()
    installed = Path('E:/SteamLibrary/steamapps/common/DayZ Exp/Addons')
    refs, inputs = {}, {}
    for label,path in [('Baltic_Q',inventory.Q/'narva_trial.pbo'),('Chernarus_Exp',installed/'worlds_chernarusplus.pbo')]:
        refs[label],inputs[label] = census(path,label=='Baltic_Q')
    assert inputs['Baltic_Q']['pbo_sha256']==inventory.EXPECTED['narva_trial.pbo']
    assert inputs['Chernarus_Exp']['pbo_sha256']=='ea868be8ca86200d3c2906ba5b932fafe04aed731276db75eca40cdbff6db75f'
    models,errors = {},{}
    wanted = set().union(*[set(r) for r in refs.values()])
    for p in [inventory.Q/'baltic_stream_pilot.pbo',inventory.Q/'baltic_water_v30.pbo',installed/'water.pbo']:
        raw,props,entries = read_pbo(p)
        if p.name in inventory.EXPECTED:assert digest(raw)==inventory.EXPECTED[p.name]
        inputs[p.name] = dict(path=str(p),sha256=digest(raw))
        for k,b in entries.items():
            full = (props['prefix']+'\\'+k.replace('/','\\')).lower()
            if full not in wanted:continue
            try:models[full] = model_summary(b)
            except Exception as e:errors[full] = type(e).__name__+': '+str(e)
        print(p.name,len(models),'parsed',len(errors),'errors',flush=True)
    worlds = {}
    for label,counts in refs.items():
        groups = {}
        for category in sorted(set(inventory.category(n) for n in counts)):
            group = {n:c for n,c in counts.items() if inventory.category(n)==category}
            good = {n:c for n,c in group.items() if n in models}
            lod_hist = Counter()
            for n in good:lod_hist[str(models[n]['visual_lods'])]+=1
            groups[category] = dict(resources=len(group),instances=sum(group.values()),parsed=len(good),
                missing=[n for n in group if n not in models],visual_lod_count_histogram=dict(lod_hist),
                unique_model_bytes=sum(models[n]['bytes'] for n in good),
                whole_world_near_triangle_equivalents=sum(models[n]['near']['triangle_equivalents']*c for n,c in good.items()),
                whole_world_near_sections=sum(models[n]['near']['sections']*c for n,c in good.items()),
                max_near_triangles=max((models[n]['near']['triangle_equivalents'] for n in good),default=0),
                largest_resources=sorted([dict(model=n,instances=c,near_triangles=models[n]['near']['triangle_equivalents'],
                    visual_lods=models[n]['visual_lods'],bytes=models[n]['bytes']) for n,c in good.items()],
                    key=lambda r:-r['near_triangles'])[:8])
        worlds[label] = groups
    result = dict(status='STATIC_LOD_AUDIT_COMPLETE' if len(models)==len(wanted) else 'STATIC_LOD_AUDIT_PARTIAL',
                  inputs=inputs,worlds=worlds,errors=errors,models=models,instances=refs,
                  sources={str(p):digest(p.read_bytes()) for p in (Path(__file__),Path(odol_reader.__file__),Path(inventory.__file__))},
                  limits=['ODOL count audit; not engine LOD selection, GPU time, draw calls, memory residency or FPS.',
                          'All-world weighted triangles/sections are inventory upper sums, not simultaneous visible workloads.',
                          'dz/water contains ponds, streams, streambeds and stones. Groups are not biome-matched scenes.',
                          'Binary reader boundary/indices verified; no runtime rendering or collision acceptance from this audit.'])
    a.out.mkdir(parents=True)
    (a.out/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (a.out/'producer.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status=result['status'],worlds=worlds,errors=errors),indent=2))


if __name__=='__main__':main()
