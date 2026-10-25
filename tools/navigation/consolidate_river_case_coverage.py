"""Provenance ledger for twelve accepted segments across separate native runs."""
from pathlib import Path
import hashlib, json
ROOT=Path(__file__).resolve().parents[2]
FOLLOW=ROOT/'evidence/foundation-followup-2026-10-01'
OLD=ROOT/'evidence/overnight-2026-10-01/full-river-v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    out=FOLLOW/'river-accepted-segment-coverage.json';assert not out.exists()
    original=read(OLD/'reference.json');old_result=read(OLD/'runtime-complete/verification.json')
    assert sha(OLD/'reference.json')==old_result['reference_sha256']
    source_cases={c['case']:c for c in original['cases']}
    results=[]
    replacements={6:('river-single-6-v5','verification.json','closed-logs'),8:('delta-isolated-v4','closed-logs/verification.json','closed-logs'),10:('river-single-10-v5','verification.json','closed-logs')}
    for ident,case in source_cases.items():
        if ident in replacements:
            name,report_name,logs=replacements[ident];folder=FOLLOW/name
            reference=read(folder/'reference.json');report_path=folder/report_name;report=read(report_path)
            assert reference['terrain_sha256']==original['terrain_sha256']
            assert reference['criteria']==original['criteria']
            selected=next(c for c in reference['cases'] if c['case']==ident)
            assert selected==case,('Route differs',ident)
            record=next(c for c in report['cases'] if c['case']==ident)
            log_path=folder/logs/f"{reference['log_prefix'].rstrip('_')}_{ident}.log"
            wanted=record['log_sha256']
        else:
            reference=original;folder=OLD;report_path=OLD/'runtime-complete/verification.json';report=old_result
            record=next(c for c in report['cases'] if c['case']==ident)
            log_path=OLD/'runtime-complete'/f"{reference['log_prefix'].rstrip('_')}_{ident}.log"
            wanted=report['files'][log_path.name] if 'files' in report else report['logs_sha256'][log_path.name]
        assert record['status']=='PASS',ident
        assert sha(log_path)==wanted,(ident,'Log differs')
        physical=record['physical']['cases'][0]
        assert all(physical['checks'].values()) and physical['health_first_min_last']==[600.,600.,600.]
        results.append(dict(case=ident,river=case['river'],part=case.get('part'),length_m=case['length_m'],
                            status='PASS_SEPARATE_NATIVE_CASE',reference=str(folder/'reference.json'),reference_sha256=sha(folder/'reference.json'),
                            report=str(report_path),report_sha256=sha(report_path),log=str(log_path),log_sha256=wanted))
    assert len(results)==12 and {c['case'] for c in results}==set(range(12))
    result=dict(status='TWELVE_SEGMENTS_ACCEPTED_ACROSS_SEPARATE_RUNS',terrain_sha256=original['terrain_sha256'],
                distinct_planned_channel_m=old_result['distinct_planned_channel_m'],cases=results,
                limits=['Selected main channels and four delta segments; not every side branch.',
                        'Separate empty boats and overlapping segments, not one continuous end-to-end journey.',
                        'Predominantly one direction; selected regional return journeys have separate evidence.',
                        'No crew, fleet or medium-vessel acceptance. Earlier aggregate FAIL results remain unchanged.'])
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))

if __name__=='__main__':main()
