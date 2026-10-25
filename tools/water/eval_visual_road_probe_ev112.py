"""Keep the Q strict server consumer and also judge measured road cross-sections."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import eval_visual_probe_v31 as base


def sections(doc, rows):
    controls=doc['road_sections'];assert len(controls)==11
    seen=set();results=[]
    for section in controls:
        ids=section['ids'];assert len(ids)==len(set(ids))==17 and not seen.intersection(ids)
        seen.update(ids);heights=[rows[i]['ground'] for i in ids]
        delta=max(heights)-min(heights)
        results.append(dict(station_m=section['station_m'],cross_m=delta,ok=delta<=.03))
    return dict(status='PASS' if all(r['ok'] for r in results) else 'FAIL',
                cross_limit_m=.03,sections=results,limits='Measured 11 former failures only; not full road census, vehicle handling or driving.')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('points',type=Path);ap.add_argument('log',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--collision-reference',required=True,type=Path);a=ap.parse_args()
    assert not a.output.exists()
    try:
        doc=json.loads(a.points.read_text());assert doc['schema']=='ev112-visual-probe-v1'
        cal=base.calibrate(a.collision_reference.read_text(encoding='utf-8-sig'))
        rows=base.parse(a.log.read_text(encoding='utf-8-sig'),len(doc['points']))
        original=base.judge(doc['points'],rows,cal['margin_m']);road=sections(doc,rows)
        result=dict(status='SERVER_PROBE_PASS' if original['status']=='SERVER_PROBE_PASS' and road['status']=='PASS' else 'FAIL',
                    base=original,road=road,collision_reference=cal)
    except (AssertionError,ValueError,IndexError,KeyError) as e:result=dict(status='FAIL_INVALID_EVIDENCE',error=str(e))
    result['inputs']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.points,a.log,a.collision_reference,Path(__file__),Path(base.__file__))}
    a.output.write_text(json.dumps(result,indent=2));print(result['status'])
    raise SystemExit(0 if result['status']=='SERVER_PROBE_PASS' else 1)


if __name__=='__main__':main()
