"""Read back the visual probe's compiled objects and package only WRP/config deltas.

OPRW object-table discovery remains heuristic, bounded by version/record validity,
source ID equality and the following map-info block. Heights are NOT decoded here.
Unlike the old EV111 reader, traversal does not stop at an unexpected source ID.
"""
import argparse, hashlib, json, re, struct, subprocess, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent/'playtest')]
from wrp0wzd import read
from attach_navmesh import read_pbo


def sha(b): return hashlib.sha256(b).hexdigest()
def norm(p): return p.replace('/', '\\').lower().lstrip('\\')


def compiled_objects(b, anchor):
    assert b[:4] == b'OPRW'
    version = struct.unpack_from('<I', b, 4)[0]
    stride = {29: 60, 32: 64}[version]
    mark = b.find(b'baltic_water_v30\\')
    assert mark >= 4
    candidates = []
    for start in range(max(0, mark-4000), mark-3):
        count = struct.unpack_from('<I', b, start)[0]
        if not 0 < count < 200000: continue
        p = start+4; names = []
        try:
            for _ in range(count):
                end = b.index(b'\0', p, p+300)
                name = b[p:end].decode('ascii')
                if not name.lower().endswith('.p3d'): raise ValueError()
                names.append(name); p = end+1
            if start+4 <= mark < p: candidates.append((start, names, p))
        except (ValueError, UnicodeDecodeError): pass
    assert len(candidates) == 1, ('ambiguous model table', len(candidates))
    _, names, mend = candidates[0]
    mi = [norm(n) for n in names].index(norm(anchor['name']))
    # First known source object locates a record, not the table's extent.
    needle = struct.pack('<2I', anchor['id'], mi)
    hits = []; p = mend
    while True:
        p = b.find(needle, p)
        if p < 0: break
        if p+stride <= len(b):
            matrix = np.array(struct.unpack_from('<12f', b, p+8))
            if np.max(np.abs(matrix-anchor['matrix'])) <= 1e-5: hits.append(p)
        p += 1
    assert len(hits) == 1, ('ambiguous object anchor', hits)

    def valid(o):
        if o < mend or o+stride > len(b): return False
        oid, index = struct.unpack_from('<2I', b, o)
        matrix = np.array(struct.unpack_from('<12f', b, o+8))
        shape = struct.unpack_from('<I', b, o+56)[0]
        if oid == 0 or index >= len(names) or shape > 64: return False
        if stride == 64 and struct.unpack_from('<I', b, o+60)[0] != 0: return False
        if not np.isfinite(matrix).all() or np.max(np.abs(matrix[9:])) >= 1e6: return False
        lengths = np.linalg.norm(matrix[:9].reshape(3,3), axis=1)
        return bool(((lengths > 1e-5).all() or (lengths == 0).all()) and (lengths < 100).all())

    first = hits[0]
    while valid(first-stride): first -= stride
    rows = []; p = first
    while valid(p):
        oid, index = struct.unpack_from('<2I', b, p)
        rows.append(dict(id=oid, name=names[index], matrix=list(struct.unpack_from('<12f', b, p+8)), shape=struct.unpack_from('<I', b, p+56)[0]))
        p += stride
    ids = {r['id'] for r in rows}
    assert len(ids) == len(rows)
    after = struct.unpack_from('<2I', b, p)
    assert after[0] <= 64 and after[1] in ids, ('table must end at map-info', after)
    return rows, dict(version=version, stride=stride, model_count=len(names), table=[first,p], after=list(after))


def compare(source, compiled):
    got = {o['id']:o for o in compiled}; want = {o['id']:o for o in source}
    assert len(got) == len(compiled) and set(got) == set(want), 'compiled object IDs differ'
    maximum = 0.; exact_pilot = 0
    for oid, s in want.items():
        c = got[oid]
        assert norm(c['name']) == norm(s['name']), ('model mismatch', oid)
        delta = float(np.max(np.abs(np.array(c['matrix'])-s['matrix'])))
        maximum = max(maximum, delta)
        assert delta <= 1e-5, ('pose mismatch', oid, delta)
        if norm(s['name']).startswith('baltic_stream_pilot\\'):
            assert delta == 0, ('pilot pose must be exact', oid, delta)
            exact_pilot += 1
    return dict(objects=len(got), max_matrix_delta=maximum, pilot_exact=exact_pilot)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('stage');ap.add_argument('output');a=ap.parse_args()
    S=Path(a.stage);out=Path(a.output);assert not out.exists()
    baseline=Path('P:/Mods/@DayZ_Baltic_EV112_RuntimeMarginsV2/Addons/narva_trial.pbo')
    raw, props, before=read_pbo(baseline)
    assert sha(raw)=='751823ac65cd56c9093de9705ee30b08a448a69606690c1363ecf944a15ac838'
    buildraw, _, new=read_pbo(S/'out/narva_trial.pbo')
    source=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    stage=read(source); objects, meta=compiled_objects(new['baltic_trial.wrp'],stage['objects'][0])
    parity=compare(stage['objects'],objects)
    assert parity['pilot_exact']==35
    # Known-bad consumers: a lost endpoint piece, an added ID, and a translated piece must fail.
    negatives={}
    idx=next(i for i,o in enumerate(objects) if norm(o['name']).startswith('baltic_stream_pilot\\'))
    moved=[dict(o,matrix=o['matrix'].copy()) for o in objects];moved[idx]['matrix'][10]+=.1
    for name, case in [('missing',objects[:idx]+objects[idx+1:]),('extra',objects+[dict(objects[idx],id=max(o['id'] for o in objects)+1)]),('moved',moved)]:
        try:compare(stage['objects'],case)
        except AssertionError:negatives[name]=True
        else:negatives[name]=False
    assert all(negatives.values())
    out.mkdir(parents=True)
    converter=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe')
    (out/'config.bin').write_bytes(new['config.bin'])
    result=subprocess.run([str(converter),'-txt','-dst',str(out/'config.cpp'),str(out/'config.bin')],capture_output=True)
    (out/'decode.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0
    original=(S/'baseline-config.cpp').read_text(encoding='utf-8-sig')
    updated=(out/'config.cpp').read_text(encoding='utf-8-sig')
    assert updated.count('"Baltic_Stream_Pilot"')==1
    stripped=re.sub(r',\s*"Baltic_Stream_Pilot"','',updated)
    assert re.sub(r'\s+','',stripped)==re.sub(r'\s+','',original), 'unexpected config change'
    expected=dict(before)
    for entry in ('baltic_trial.wrp','config.bin'): expected[entry]=new[entry]
    folder=out/'compiled/narva_trial';folder.mkdir(parents=True);dest=out/'Addons';dest.mkdir()
    for name,data in expected.items():
        path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    bank='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe'
    argv=[bank]
    for key,value in props.items():argv+=['-property',key+'='+value]
    argv+=['-dst',str(dest),str(folder)]
    packed=subprocess.run(argv,capture_output=True);(out/'filebank.log').write_bytes(packed.stdout+packed.stderr);assert packed.returncode==0
    finalraw,finalprops,final=read_pbo(dest/'narva_trial.pbo')
    assert final==expected and all(finalprops.get(k)==v for k,v in props.items())
    report=dict(status='OFFLINE_PACKAGE_PASS',baseline_sha256=sha(raw),compiled_pbo_sha256=sha(buildraw),pbo_sha256=sha(finalraw),
                wrp_sha256=sha(final['baltic_trial.wrp']),source_wrp_sha256=sha(source.read_bytes()),objects=parity,reader=meta,
                negative_controls=negatives,entries_unchanged=len(before)-2,changed_entries=['baltic_trial.wrp','config.bin'],
                config_delta='requiredAddons += Baltic_Stream_Pilot',forest=False,
                limits=['OPRW table locator is heuristic; heights require independent engine probes.','Technical probe without forest; not acceptance of final map, AI, water, collision or appearance.'])
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
