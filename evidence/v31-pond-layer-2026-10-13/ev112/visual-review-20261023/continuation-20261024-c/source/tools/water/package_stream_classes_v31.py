"""Isolate the runtime missing-house-class fix; keep every model byte exact."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'playtest')]
from attach_navmesh import read_pbo
from continuous_stream_pilot_v31 import model_config


def main():
    ap=argparse.ArgumentParser();ap.add_argument('pilot');ap.add_argument('out');a=ap.parse_args()
    pilot=Path(a.pilot);out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    source=pilot/'packed/baltic_stream_pilot.pbo';raw,props,before=read_pbo(source)
    assert hashlib.sha256(raw).hexdigest()=='b2c1799d7edb7adf2deb55f3f3b76e0c0c82f608bcf1673f47074da93c6eeea1'
    instances=json.loads((pilot/'author-report.json').read_text())['instances']
    assert len(instances)==35 and len({i['model'] for i in instances})==35
    config=model_config(instances);cpp=out/'config.cpp';cpp.write_text(config,encoding='ascii')
    cv='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe'
    result=subprocess.run([cv,'-bin','-dst',str(out/'config.bin'),str(cpp)],capture_output=True)
    (out/'cfgconvert.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0
    result=subprocess.run([cv,'-txt','-dst',str(out/'decoded.cpp'),str(out/'config.bin')],capture_output=True)
    assert result.returncode==0
    decoded=(out/'decoded.cpp').read_text(encoding='utf-8-sig')
    for i in instances:
        stem=i['model'].rsplit('\\',1)[-1].removesuffix('.p3d')
        assert 'class Land_'+stem+': HouseNoDestruct' in decoded
        assert '"\\'+i['model']+'"' in decoded
    expected=dict(before);expected['config.bin']=(out/'config.bin').read_bytes()
    folder=out/'compiled/baltic_stream_pilot';folder.mkdir(parents=True);dest=out/'Addons';dest.mkdir()
    for name,data in expected.items():
        target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    argv=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for key,value in props.items():argv+=['-property',key+'='+value]
    argv+=['-dst',str(dest),str(folder)]
    result=subprocess.run(argv,capture_output=True);(out/'filebank.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0
    final,fp,after=read_pbo(dest/'baltic_stream_pilot.pbo')
    assert after==expected and all(fp.get(k)==v for k,v in props.items())
    report=dict(status='CONFIG_ONLY_PACKAGE_PASS',source_sha256=hashlib.sha256(raw).hexdigest(),
                sha256=hashlib.sha256(final).hexdigest(),classes=35,changed_entries=['config.bin'],
                unchanged_entries=len(before)-1,models_byte_exact=True,runtime='PENDING')
    (out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))


if __name__=='__main__':main()
