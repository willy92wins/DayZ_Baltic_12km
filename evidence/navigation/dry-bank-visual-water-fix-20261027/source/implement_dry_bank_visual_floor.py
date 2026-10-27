"""Apply only the independently reviewed water-reference substitutions to NEW files."""
from pathlib import Path
import ast,difflib,hashlib,json
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'dry-bank-visual-water-setup-20261027';O.mkdir(exist_ok=False)
review=R/'dry-bank-visual-water-plan-review-20261027'
response=json.loads((review/'response.json').read_text(encoding='utf-8-sig'))
assert not response['is_error'] and not response.get('permission_denials') and 'FIN_REVISION' in response['result'] and 'claude-fable-5-1' in response['modelUsage']
frozen=json.loads((review/'source-hashes.json').read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(Path(p))==h for p,h in frozen.items())
plan=W/'plans/ev112-dry-bank-visual-water-fix-20261027.md'
(review/'plan-reviewed.md').write_bytes(plan.read_bytes())
plan.write_text(plan.read_text(encoding='utf-8-sig').replace('Estado: PROPUESTO_PARA_REVISION.',
    'Estado: REVISADO_SOUND_PENDIENTE_IMPLEMENTACION.')+'\nFable5.1 SOUND, revisión nativa independiente conservada en dry-bank-visual-water-plan-review-20261027. Autorizar sólo las sustituciones de referencia descritas; regresiones deben comprobar bounds=false.\n',encoding='utf-8')
patches=[]
for name in ('pilot','verify','run'):
    old=R/(name+'_dry_bank_domain.py');new=R/(name+'_dry_bank_visual_floor.py');assert not new.exists()
    before=old.read_text(encoding='utf-8-sig');after=before
    if name=='pilot':
        anchor="floor=ground+.02;water=np.broadcast_to(arrays['level'][:,None],original.shape)"
        replacement="floor=ground+.02\n    assert np.array_equal(arrays['water'][:,0,1],arrays['water'][:,1,1])\n    water=np.broadcast_to(arrays['water'][:,0,1,None],original.shape)"
        assert after.count(anchor)==1;after=after.replace(anchor,replacement)
    if name=='verify':
        anchor="water = np.broadcast_to(arrays['level'][:,None], original.shape)"
        replacement="if not np.array_equal(arrays['water'][:,0,1], arrays['water'][:,1,1]):\n        raise ValueError('water bank Y mismatch')\n    water = np.broadcast_to(arrays['water'][:,0,1,None], original.shape)"
        assert after.count(anchor)==1;after=after.replace(anchor,replacement)
        assert after.count("-a['level']")==2
        after=after.replace("-a['level']","-a['water'][:,0,1]")
    if name=='run':
        after=after.replace('pilot_dry_bank_domain.py','pilot_dry_bank_visual_floor.py').replace('verify_dry_bank_domain.py','verify_dry_bank_visual_floor.py')
    ast.parse(after);new.write_text(after,encoding='utf-8')
    patches.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=old.name,tofile=new.name))
(O/'reviewed-substitution.diff').write_text(''.join(patches),encoding='utf-8')
context=json.loads((R/'dry-bank-domain-setup-fixed-20261027/context.json').read_text(encoding='utf-8-sig'))
context['hashes'].pop(context['paths']['plan'])
context['paths']['plan']=str(plan)
context['paths']['rejected_candidate']=str(R/'dry-bank-domain-pilot-20261027/candidate-surfaces.npz')
context['paths']['rounding_diagnosis']=str(R/'dry-bank-water-reference-diagnosis-20261027/result.json')
assert all(sha(Path(p))==h for p,h in context['hashes'].items())
extra=[plan,Path(context['paths']['rejected_candidate']),Path(context['paths']['rounding_diagnosis']),Path(__file__)]
extra += [R/(name+'_dry_bank_visual_floor.py') for name in ('pilot','verify','run','test')]
for path in extra:context['hashes'][str(path)]=sha(path)
(O/'context.json').write_text(json.dumps(context,indent=2)+'\n',encoding='utf-8')
(O/'budget.json').write_text(json.dumps(dict(candidate_count=1,max_seconds=900,max_iterations=500,weight=.002,
    max_concrete_corrections=1,parallel_readonly_test_children=3,dayz_runs=0,
    retired_candidate='df0c5994964e159431a618022a6dceae22a12964c1157ac0b54b3dc51a9bdeb8',
    regression_required='retired candidate and one dry-floor mutation must fail bounds specifically'),indent=2)+'\n',encoding='utf-8')
print('REVIEWED SUBSTITUTIONS FROZEN',O)
