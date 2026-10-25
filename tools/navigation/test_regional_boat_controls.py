"""Analytic verifier controls. These fixtures are NOT engine evidence."""
from copy import deepcopy
from pathlib import Path
import argparse,json
import numpy as np
from verify_regional_boat_consumer import verify

def fixture():
    h=np.full((2048,2048),-5,dtype='float32')
    ref={'criteria':{'max_sample_dt_s':.8,'max_step_m':3,'max_health_loss':1,'max_axis_distance_m':7,'max_endpoint_distance_m':6,'max_waypoint_distance_m':7,'max_ground_error_m':.002,'min_powered_motion_s':5},'cases':[],'limits':['Analytic test fixture, no runtime claim']}
    lines=['BALTIC_REGIONAL_BOAT_V1']
    for case in range(8):
        z=100+case*30
        ref['cases'].append(dict(case=case,river='analytic',reverse=bool(case%2),waypoints_xz=[[100+i,z] for i in range(0,81,4)]))
        lines.append(f'CASE;{case};21')
        for i in range(1,181):
            x=100+min(i*.5,80)
            fields=['B',case,i*.5,x,0,z,90,1 if i<160 else 0,600,'true',2,1,1200,31,i*20,0,0,min(20,1+i//8),0,-5,.7,.99]
            lines.append(';'.join(map(str,fields)))
        lines.extend([f'ARRIVED;{case};80;180 0 {z}',f'CASE_END;{case};ARRIVED_AND_STOPPED'])
    lines.append('END;ALL_CASES_COMPLETE')
    return ref,lines,h

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--version',type=int,choices=[1,2],default=1)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    ref,base,h=fixture()
    if args.version==2:
        ref['log_version']=2
        base[0]='BALTIC_REGIONAL_BOAT_V2'
        for i,line in enumerate(base):
            if line.startswith('B;'):
                row=line.split(';')
                base[i]=line+';<' + ', '.join(f'{float(row[j]):.6f}' for j in (3,4,5)) + '>'
    positive=verify(ref,base,h)
    assert positive['status'].startswith('PASS_'),positive
    def alter(field,value,line_offset=30):
        result=list(base);i=next(i for i,v in enumerate(result) if v.startswith('B;0;'))+line_offset
        row=result[i].split(';');row[field]=str(value);result[i]=';'.join(row);return result
    cases={
        'missing_end':base[:-1],
        'teleport':alter(3,160),
        'sample_gap':alter(2,99),
        'wrong_ground':alter(19,-4),
        'damage':alter(8,598),
        'outside_corridor':alter(5,108),
        'input_counter_rewinds':alter(14,0),
        'target_backtracks':alter(17,0),
        'nan':alter(7,'nan'),
        'unknown_engine_bool':alter(9,'maybe'),
    }
    if args.version==2:
        cases.update({'missing_precise_vector':[v.rsplit(';',1)[0] if v.startswith('B;0;') else v for v in base],
                      'bad_precise_vector':alter(22,'<nan, 0, 0>'),
                      'incompatible_precise_vector':alter(22,'<500.000000, 0.000000, 100.000000>'),
                      'wrong_log_version':['BALTIC_REGIONAL_BOAT_V1']+base[1:]})
    for field,name,value in [(12,'no_rpm',700),(13,'no_propeller',0),(9,'engine_off','false'),(10,'neutral_only',1)]:
        lines=[]
        for line in base:
            if line.startswith('B;0;'):
                row=line.split(';');row[field]=str(value);line=';'.join(row)
            lines.append(line)
        cases[name]=lines
    outcomes=[]
    for name,lines in cases.items():
        report=verify(ref,lines,h);assert not report['status'].startswith('PASS_'),name
        outcomes.append({'case':name,'status':'EXPECTED_REJECTION'})
    output=args.out or Path(__file__).resolve().parents[2]/'evidence/overnight-2026-10-01/regional-boat-v1/verifier-controls.json'
    if output.exists():raise ValueError('Preserve previous evidence')
    result={'status':'PASS_CONTROLS','log_version':args.version,'positive':'ANALYTIC_KNOWN_PATH_NOT_RUNTIME','negative_cases':outcomes}
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
