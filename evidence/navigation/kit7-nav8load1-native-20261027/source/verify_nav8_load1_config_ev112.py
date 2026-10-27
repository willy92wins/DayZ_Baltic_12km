"""Require the exact experimental OnLoad config; no graph or RAM acceptance."""
import argparse
import json
from pathlib import Path
from verify_nav_config_types_ev112 import evaluate, require


def verify(text, probe):
    result = evaluate(text, probe)
    rows = result['observations']
    for index in (0, 2, 3):
        row = rows[index]
        require(row['native_type'] == 0 and row['text_ok'] and row['text'] == '1' and row['integer'] == row['floating'] == 1, 'Expected native numeric flag: '+str(index))
    row = rows[1]
    require(row['native_type'] == 2 and row['text_ok'] and row['text'] == 'true' and row['integer'] == row['floating'] == 0, 'GenParams must remain unchanged string true')
    result['status'] = 'PASS_NATIVE_LOAD1_CONFIG'
    result['limits'] = ['Exact script-facing configuration verified on the bound engine; native loader implementation remains unknown.', 'Graph607 and fresh RAM comparison are separate required gates.', 'No GenParams application, NM regeneration or global acceptance.']
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', type=Path, required=True)
    ap.add_argument('--probe-id', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    require(not a.out.exists(), 'Fresh result required')
    try: result = verify(a.log.read_text(encoding='utf-8-sig'), a.probe_id)
    except (ValueError, IndexError) as error: result = dict(status='FAIL_LOAD1_CONFIG_EVIDENCE', acceptance_eligible=False, error=str(error))
    a.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return 0 if result['status'] == 'PASS_NATIVE_LOAD1_CONFIG' else 1


if __name__ == '__main__': raise SystemExit(main())
