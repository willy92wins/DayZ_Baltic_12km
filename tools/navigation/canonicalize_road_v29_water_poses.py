"""Explicit V29 build derivatives; only <=1 micrometre water Y restitution."""
from pathlib import Path
import argparse, json
from canonicalize_outline_water_poses import ROOT, BASELINE, BASELINE_SHA, sha, read, restore, native_pair
from verify_native_road_terrain import inspect

ASC = ROOT/'tests/regional_road_network_v29/baltic_road_network_v29.asc'
ASC_SHA = 'ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6'


def native_input(path):
    assert path.resolve().is_relative_to((ROOT/'tb/regional_road_network_v29').resolve())
    result = inspect(path, ASC, ASC_SHA)
    assert all(value for name, value in result['checks'].items()
               if name != 'all_10161_water_bridge_objects_exact'), result
    return result


def verify_receipt(path):
    receipt = json.loads(path.read_text())
    assert receipt['status'] == 'PASS_EXPLICIT_DERIVED_ROAD_V29_WATER_POSES'
    assert receipt['asc_sha256'] == ASC_SHA and sha(ASC) == ASC_SHA
    assert receipt['baseline_sha256'] == BASELINE_SHA and sha(BASELINE) == BASELINE_SHA
    files = receipt['files']; assert len(files) == 2
    assert Path(files[0]['raw']).resolve() != Path(files[1]['raw']).resolve()
    raw_parsed, derived_parsed = [], []
    for item in files:
        raw, derived = Path(item['raw']), Path(item['derived'])
        assert sha(raw) == item['raw_sha256'] and sha(derived) == item['derived_sha256']
        native_input(raw)
        parsed = read(raw); expected, changes = restore(read(BASELINE), parsed)
        assert changes == item['changes'] and expected == derived.read_bytes()
        gate = inspect(derived, ASC, ASC_SHA); assert all(gate['checks'].values()), gate
        raw_parsed.append(parsed); derived_parsed.append(read(derived))
    native_pair(*raw_parsed); native_pair(*derived_parsed)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--first', type=Path); p.add_argument('--reopened', type=Path)
    p.add_argument('--first-sha256'); p.add_argument('--reopened-sha256')
    p.add_argument('--out', type=Path); p.add_argument('--verify-receipt', type=Path)
    a = p.parse_args()
    if a.verify_receipt:
        receipt = verify_receipt(a.verify_receipt)
        print(json.dumps(dict(status=receipt['status'], literal_persistence=True)))
        return
    assert a.first and a.reopened and a.out and not a.out.exists()
    assert sha(a.first) == a.first_sha256 and sha(a.reopened) == a.reopened_sha256
    assert a.first.resolve() != a.reopened.resolve()
    assert sha(BASELINE) == BASELINE_SHA and sha(ASC) == ASC_SHA
    raw_gates = [native_input(v) for v in (a.first, a.reopened)]
    parsed = [read(v) for v in (a.first, a.reopened)]; native_pair(*parsed)
    results = [restore(read(BASELINE), v) for v in parsed]
    a.out.mkdir(parents=True); files = []
    for tag, raw, (content, changes) in zip(('first', 'reopened'), (a.first, a.reopened), results):
        destination = a.out/(tag+'-derived.wrp'); destination.write_bytes(content)
        files.append(dict(raw=str(raw.resolve()), raw_sha256=sha(raw),
                          derived=str(destination.resolve()), derived_sha256=sha(destination), changes=changes))
    receipt = dict(status='PASS_EXPLICIT_DERIVED_ROAD_V29_WATER_POSES',
                   baseline_sha256=BASELINE_SHA, asc_sha256=ASC_SHA,
                   raw_native_persistence_exact=True, literal_checks=raw_gates, files=files,
                   limits=['Derived build inputs, not literal equality against V10.',
                           'All nonvertical fields and every bridge pose remain exact; water Y above1micrometre is rejected.'])
    path = a.out/'restoration.json'; path.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    verify_receipt(path)
    print(json.dumps(dict(status=receipt['status'], changes_per_file=[len(v['changes']) for v in files])))


if __name__ == '__main__':
    main()
