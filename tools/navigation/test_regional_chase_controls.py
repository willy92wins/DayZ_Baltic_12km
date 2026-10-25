"""Challenge physical AI acceptance using corrupted copies of a real passing run."""
from pathlib import Path
import argparse
import hashlib
import json
import rasterio
from verify_regional_chase import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--positive-case', type=int, choices=[0],
                        help='Test the real passing control case0 from a completed mixed-result run; never promotes its other cases')
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Preserve prior evidence')
    ref = json.loads(args.reference.read_text())
    asc = Path(ref['terrain'])
    if hashlib.sha256(asc.read_bytes()).hexdigest() != ref['terrain_sha256']:
        raise ValueError('Terrain identity changed')
    with rasterio.open(asc) as dataset:
        height = dataset.read(1)
    raw = args.log.read_text(encoding='utf-8-sig')
    full_run=verify(ref,raw,height)
    if args.positive_case is not None:
        if not full_run['global_checks']['end'] or full_run['cases'][0]['status']!='PASS':
            raise ValueError('Completed run and actual passing case0 required')
        ref=dict(ref,cases=[ref['cases'][0]])
        lines=raw.splitlines()
        raw='\n'.join(lines[:2]+[line for line in lines[2:-1] if line.startswith(('A;0;','ANCHOR;0;'))]+[lines[-1]])+'\n'
    positive = verify(ref, raw, height)
    if not positive['status'].startswith('PASS_'):
        raise ValueError('Actual positive run required')
    base = raw.splitlines()
    index = next(i for i, line in enumerate(base) if line.startswith('A;0;') and line.split(';')[3] == 'SAMPLE')

    def moved(value, delta):
        numbers = [float(v) for v in value[1:-1].split(',')]
        return '<' + ', '.join(f'{v+d:.6f}' for v, d in zip(numbers, delta)) + '>'

    def field(number, value, selected=index):
        lines = base.copy()
        row = lines[selected].split(';')
        row[number] = str(value)
        lines[selected] = ';'.join(row)
        return lines

    row = base[index].split(';')
    mutations = {
        'missing_end': base[:-1],
        'wrong_world': [base[0], 'world=ChernarusPlus'] + base[2:],
        'dead_actor': field(7, 0),
        'wrong_ground': field(9, float(row[9])+1),
        'nonfinite_ground': field(9, 'nan'),
        'target_moved': field(5, moved(row[5], [5, 0, 0])),
        'goal_changed': field(6, moved(row[6], [1, 0, 0])),
        'floating_actor': field(4, moved(row[4], [0, 2, 0])),
        'clock_gap': field(2, float(row[2])+5),
        'malformed_vector': field(4, '<1, 2, 3>'),
        'unknown_event': field(3, 'ACCEPTED_BY_NAME'),
    }
    spawn = next(i for i, line in enumerate(base) if line.startswith('A;0;') and line.split(';')[3] == 'SPAWN')
    mutations['wrong_spawn'] = field(4, moved(base[spawn].split(';')[4], [1, 0, 0]), spawn)
    mutations['duplicate_spawn'] = base[:spawn] + [base[spawn]] + base[spawn:]
    mutations['missing_case'] = [line for line in base if not line.startswith(('A;0;', 'ANCHOR;0;'))]
    reached = next(i for i, line in enumerate(base) if line.startswith('A;0;') and line.split(';')[3] == 'REACHED')
    mutations['false_arrival'] = field(4, base[spawn].split(';')[4], reached)
    mutations['timeout'] = field(3, 'TIMEOUT', reached)
    no_reaction = base.copy()
    for i, line in enumerate(no_reaction):
        if line.startswith('A;0;') and line.split(';')[3] == 'SAMPLE':
            parts = line.split(';')
            parts[8] = '0'
            no_reaction[i] = ';'.join(parts)
    mutations['no_reaction'] = no_reaction
    results = []
    for name, lines in mutations.items():
        text = '\n'.join(lines) + '\n'
        if text.strip() == raw.strip():
            raise ValueError('Unchanged negative control: ' + name)
        report = verify(ref, text, height)
        if report['status'].startswith('PASS_'):
            raise ValueError('False acceptance: ' + name)
        results.append(dict(name=name, status='EXPECTED_REJECTION',
                            global_failures=[k for k, v in report['global_checks'].items() if not v],
                            case0_failures=[k for k, v in report['cases'][0].get('checks', {}).items() if not v],
                            log_sha256=hashlib.sha256(text.encode()).hexdigest()))
    result = dict(status='PASS_ACTUAL_POSITIVE_AND_NEGATIVE_CONTROLS',
                  full_run_status=full_run['status'],positive_case=args.positive_case,
                  scope='Verifier test on actual case0 only; original whole-run failures retained' if args.positive_case is not None else 'Whole real run passed before mutation',
                  reference_sha256=hashlib.sha256(args.reference.read_bytes()).hexdigest(),
                  log_sha256=hashlib.sha256(args.log.read_bytes()).hexdigest(), controls=results)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status=result['status'], negatives=len(results))))


if __name__ == '__main__':
    main()
