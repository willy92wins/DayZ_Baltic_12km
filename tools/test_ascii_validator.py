"""Independent tiny known grids exercise corruptions before terrain validation."""
from pathlib import Path
import copy,json,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/validator-fixtures';OUT.mkdir(exist_ok=True)
HEADER='ncols 3\nnrows 3\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n'
BODY='91 92 93\n51 52 53\n11 12 13\n'
SPEC={'ncols':3,'nrows':3,'cellsize':6,'xllcorner':200000,'yllcorner':0,
      'height_min':0,'height_max':100,
      'controls':[{'name':'northwest','row':0,'col':0,'expected_z':91,'tolerance':0.001},
                  {'name':'southeast','row':2,'col':2,'expected_z':13,'tolerance':0.001}]}
CASES=[('valid',HEADER+BODY,True),
       ('north_south_flip',HEADER+'11 12 13\n51 52 53\n91 92 93\n',False),
       ('one_cell_origin_shift',HEADER.replace('200000','200006')+BODY,False),
       ('one_cell_data_shift',HEADER+'93 91 92\n53 51 52\n13 11 12\n',False),
       ('nodata',HEADER+BODY.replace('52','-9999'),False),
       ('nan',HEADER+BODY.replace('52','NaN'),False),
       ('truncated',HEADER+'91 92 93\n51 52 53\n',False),
       ('bad_row',HEADER+BODY.replace('51 52 53','51 52'),False),
       ('extra_data',HEADER+BODY+'14 15 16\n',False),
       ('centre_equivalent',HEADER.replace('xllcorner 200000','xllcenter 200003').replace('yllcorner 0','yllcenter 3')+BODY,True),
       ('centre_half_cell_error',HEADER.replace('xllcorner 200000','xllcenter 200000').replace('yllcorner 0','yllcenter 0')+BODY,False),
       ('duplicate_header',HEADER.replace('cellsize 6','nrows 6')+BODY,False)]
results=[]
for name,text,expected in CASES:
    path=OUT/(name+'.asc');path.write_text(text,encoding='ascii')
    spec_path=OUT/(name+'.spec.json');spec_path.write_text(json.dumps(SPEC),encoding='utf-8')
    report=OUT/(name+'.report.json')
    process=subprocess.run([sys.executable,str(ROOT/'tools/validate_ascii.py'),str(path),'--spec',str(spec_path),'--report',str(report)],capture_output=True,text=True)
    result=json.loads(report.read_text())
    passed=process.returncode==0 and result['status']=='PASS'
    assert passed==expected,(name,process.returncode,result,process.stderr)
    results.append({'case':name,'expected_valid':expected,'exit':process.returncode,'errors':result['errors']})
extra_spec=copy.deepcopy(SPEC);extra_spec['cellsize']=float('nan')
(OUT/'invalid.spec.json').write_text(json.dumps(extra_spec))
process=subprocess.run([sys.executable,str(ROOT/'tools/validate_ascii.py'),str(OUT/'valid.asc'),'--spec',str(OUT/'invalid.spec.json'),'--report',str(OUT/'invalid_spec.report.json')],capture_output=True,text=True)
assert process.returncode!=0
results.append({'case':'nonfinite_spec','expected_valid':False,'exit':process.returncode})
(ROOT/'evidence/validator-tests.json').write_text(json.dumps({'status':'PASS','cases':results},indent=2))
print(f'PASS {len(results)} independent positive/negative fixtures')
