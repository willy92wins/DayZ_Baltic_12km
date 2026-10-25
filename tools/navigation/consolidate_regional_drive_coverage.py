"""Consolidate accepted cases without overwriting either run's aggregate verdict."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/foundation-followup-2026-10-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    out=EV/'regional-drive-accepted-coverage.json';assert not out.exists()
    sources={}
    for version in ['v1','v2']:
        folder=EV/f'regional-drive-{version}'
        ref=json.loads((folder/'reference.json').read_text(encoding='utf-8'))
        result=json.loads((folder/'verification.json').read_text(encoding='utf-8'))
        assert sha(folder/'reference.json')==result['reference_sha256']
        assert sha(folder/'closed-logs'/ref['log_name'])==result['log_sha256']
        assert all(result['global_checks'].values()) and not result['parse_errors']
        assert sha(Path(ref['terrain']))==ref['terrain_sha256']
        sources[version]=(ref,result)
    original=sources['v1'][0];repeated=sources['v2'][0]
    assert original['criteria']==repeated['criteria']
    for key in ['terrain_sha256','input_pbo_sha256','bridge']:
        assert original[key]==repeated[key]
    selected=[]
    for case in original['cases']:
        number=case['case'];version='v2' if number in (2,3) else 'v1'
        ref,result=sources[version]
        current=next(c for c in ref['cases'] if c.get('original_case',c['case'])==number)
        assert {k:v for k,v in current.items() if k not in ('case','original_case')}=={k:v for k,v in case.items() if k!='case'}
        report=next(c for c in result['cases'] if c['case']==current['case'])
        assert report['status']=='PASS' and all(report['checks'].values())
        selected.append(dict(original_case=number,name=case['name'],reverse=case['reverse'],length_m=case['length_m'],source=version,source_case=current['case'],source_reference_sha256=result['reference_sha256'],source_log_sha256=result['log_sha256'],samples=report['samples'],health_min=report['health_min'],maximum_speed_kmh=report['speed_m_s']['max']*3.6))
    assert len(selected)==6
    controls=EV/'regional-drive-v2/negative-controls.json';negative=json.loads(controls.read_text(encoding='utf-8'))
    assert negative['status']=='PASS_REAL_POSITIVE_AND_NEGATIVE_CONTROLS' and len(negative['negative_controls'])==18
    result=dict(status='SIX_REGIONAL_JOURNEYS_ACCEPTED_ACROSS_TWO_RUNS',terrain_sha256=original['terrain_sha256'],selected=selected,total_travelled_planned_km=sum(c['length_m'] for c in selected)/1000,distinct_corridor_km=sum(c['length_m'] for c in selected if not c['reverse'])/1000,negative_controls_sha256=sha(controls),limits=['Three frozen corridors both directions, empty vanilla sedan. Not entire road network, driver control, physical road pieces or multiplayer.','V1 aggregate FAIL remains unchanged; hill cases use separate V2 evidence.','Physical path acceptance does not erase the separate full-width geometry failure.'])
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='selected'}))


if __name__=='__main__':main()
