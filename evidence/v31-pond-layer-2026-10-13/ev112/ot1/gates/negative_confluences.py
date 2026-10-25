"""Actual confluence positive and adversarial controls against the independent G7 contract.
Usage: negative_confluences.py run_dir sites.json output.json
"""
import copy,json,pathlib,sys
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,str(pathlib.Path(__file__).parent))
import gatelib as G
from probe_confluence_contract import validate
run=pathlib.Path(sys.argv[1]);site_list=json.loads(pathlib.Path(sys.argv[2]).read_text())
full=json.loads((run/'probe/points.json.full.json').read_text());runtime=json.loads((run/'probe/points.json').read_text())
models=json.load(open(G.GEOM))['models'];records=json.loads((run/'kit-records.json').read_text())
pieces={(r['site'],r['piece']):G.Piece(r,models) for r in records if r['piece']!='stones'}
H=np.load(run/'terrain-ev108.npz')['heights'].astype(float)
positive=next(p for p in full if p['kind']=='kit_confluence' and p['site']=='100.0-0' and p['other_site']=='100.2-0')
assert positive['kind']=='kit_confluence' and positive['other_site']=='100.2-0',positive
assert not validate(full,pieces,site_list,H,runtime)
results=[dict(case='actual_declared_confluence',passed=True,point=positive)]
def rejects(name,p,expected,pcs=pieces,rt=None):
    errors=validate([p],pcs,site_list,H,[p] if rt is None else rt)
    assert any(e[0]==expected for e in errors),(name,expected,errors)
    results.append(dict(case=name,passed=True,expected_rejection=expected,errors=errors))
p=copy.deepcopy(positive);p.pop('expect');rejects('missing_expectation',p,'confluence_expect')
p=copy.deepcopy(positive);p['expect']='test';rejects('test_label',p,'confluence_expect')
p=copy.deepcopy(positive);p['other_site']='__not_built__';rejects('invented_partner',p,'confluence_built_partner')
p=copy.deepcopy(positive);p['other_site']='kit-118';rejects('unlinked_built_branch',p,'confluence_relation')
p=copy.deepcopy(next(p for p in full if p['kind']=='kit_side' and p['site']==positive['site']))
p.update(kind='kit_confluence',expect='wet',other_site=positive['other_site'],other_water=positive['other_water'],other_axis_distance=positive['other_axis_distance'])
rejects('ordinary_lateral_disguised_as_confluence',p,'confluence_axis_distance')
no_water=pieces.copy()
for key,pc in pieces.items():
    if key[0]==positive['other_site']:
        no_water[key]=copy.copy(pc);no_water[key].water=np.empty((0,3,3))
rejects('partner_geometry_has_no_water',positive,'confluence_partner_not_wet',pcs=no_water)
rejects('runtime_omits_confluence',positive,'runtime_confluence_coverage',rt=[])
p=copy.deepcopy(positive);p['other_water']=float('nan');rejects('nonfinite_declared_water',p,'confluence_value')
byid={p['id']:p for p in runtime}
for p in runtime:
    if p['kind']=='kit_confluence':
        assert p['of'] in byid
        sibling=[q for q in runtime if q.get('of')==p['of'] and q['kind'] in ('kit_side','kit_confluence')]
        assert len(sibling)==2 and {q['side'] for q in sibling}=={-1,1}
assert len(runtime)<=3000
result=dict(passed=True,checks=results,runtime_points=len(runtime),confluence_count=sum(p['kind']=='kit_confluence' for p in full))
pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print('CONFLUENCE CONTROLS PASS',len(results))
