"""Challenge driving acceptance with corrupted copies of an actual positive run."""
from pathlib import Path
import argparse,copy,hashlib,json
import rasterio
from verify_foundation_drive import verify,verify_mission_identity


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--log',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists():raise ValueError('Preserve prior evidence')
    ref=json.loads(args.reference.read_text());verify_mission_identity(ref)
    with rasterio.open(ref['terrain']) as ds:height=ds.read(1)
    raw=args.log.read_text(encoding='utf-8-sig');base=raw.splitlines()
    positive=verify(ref,raw,height)
    if not positive['status'].startswith('PASS_'):raise ValueError('Actual positive run required first')
    indices=[i for i,line in enumerate(base) if line.startswith('D;0;') and float(line.split(';')[2])>=25]
    if len(indices)<10:raise ValueError('Insufficient real samples')
    index=indices[3]
    def field(number,value,selected=index):
        changed=base.copy();row=changed[selected].split(';');row[number]=str(value);changed[selected]=';'.join(row)
        return changed
    def moved(value,delta):
        xyz=[float(x) for x in value[1:-1].split(',')]
        xyz=[a+b for a,b in zip(xyz,delta)]
        return '<'+', '.join(f'{x:.6f}' for x in xyz)+'>'
    chosen=base[index].split(';')
    mutations={
        'missing_end':base[:-1],
        'damage':field(6,float(chosen[6])-2),
        'engine_damage':field(7,float(chosen[7])-2),
        'wrong_ground':field(19,float(chosen[19])+1),
        'missing_wheel':field(17,3),
        'ruined_wheel':field(22,0),
        'false_contact_height':field(21,moved(chosen[21],[0,.5,0])),
        'teleport':field(3,moved(chosen[3],[20,0,0])),
        'sample_gap':field(2,float(chosen[2])+2),
        'tilt':field(18,.2),
        'nonfinite_rpm':field(9,'nan'),
    }
    airborne=base.copy()
    for selected in indices[2:7]:
        row=airborne[selected].split(';')
        for wheel in range(4):row[20+3*wheel]='false'
        airborne[selected]=';'.join(row)
    mutations['all_wheels_airborne']=airborne
    for name,number,value in [('no_motion',5,'<0.000000, 0.000000, 0.000000>'),
                              ('no_callbacks',11,'0'),('neutral_only',10,'1')]:
        rows=base.copy()
        for selected,line in enumerate(rows):
            if line.startswith('D;0;'):
                row=line.split(';');row[number]=value;rows[selected]=';'.join(row)
        mutations[name]=rows
    spawn_index=next(i for i,line in enumerate(base) if line.startswith('SPAWN;0;'))
    mutations['wrong_initial_placement']=field(2,moved(base[spawn_index].split(';')[2],[.1,0,0]),spawn_index)
    mutations['duplicate_case']=base[:2]+['CASE;0;41']+base[2:]
    mutations['false_destination']=[line for line in base if not(line.startswith('D;0;') and float(line.split(';')[2])>=30)]
    outcomes=[]
    for name,lines in mutations.items():
        text='\n'.join(lines)+'\n'
        if text.strip()==raw.strip():raise ValueError('Control did not alter evidence: '+name)
        report=verify(ref,text,height)
        if report['status'].startswith('PASS_'):raise ValueError('False acceptance: '+name)
        outcomes.append(dict(case=name,status='EXPECTED_REJECTION',mutated_log_sha256=hashlib.sha256(text.encode()).hexdigest(),
                             global_failures=[k for k,v in report['global_checks'].items() if not v],
                             case0_failures=[k for k,v in report['cases'][0].get('checks',{}).items() if not v]))
    result=dict(status='PASS_REAL_POSITIVE_AND_NEGATIVE_CONTROLS',source_positive=positive['status'],
                real_log_sha256=hashlib.sha256(args.log.read_bytes()).hexdigest(),
                reference_sha256=hashlib.sha256(args.reference.read_bytes()).hexdigest(),negative_controls=outcomes)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],negative_controls=len(outcomes))))


if __name__=='__main__':main()
