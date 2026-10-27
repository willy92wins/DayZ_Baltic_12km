from pathlib import Path
import ast,hashlib,json
R=Path(__file__).parent;D=R/'kit7-navv9diag-ram-ab-20261027';V=R/'kit7-navv9diag-ram-review-20261027'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
response=read(V/'response.json');assert response['is_error'] is False and not response['permission_denials']
assert 'claude-fable-5-1' in response['modelUsage'] and 'SOUND-with-fixes' in response['result']
assert read(V/'completion.json')['returncode']==0 and read(V/'completion.json')['inputs_unchanged']
reviewed=read(V/'source-hashes.json')
changed=[p for p,h in reviewed.items() if sha(p)!=h];assert changed==[str(R/'finalize_navv9diag_ram_ab.py')]
final=(R/'finalize_navv9diag_ram_ab.py').read_text();ast.parse(final)
assert "validate_diagnostic(R/'kit7-nav-consumer-20261026/result.json',D/'deployment.json')" in final
assert "gate['status']=='BOUND_DIAGNOSTIC_ONLY_HEIGHT_FAIL'" in final
assert "all(sha(Path(p))==h for p,h in gate['inputs'].items())" in final
inherited=read(R/'kit7-nav12-ram-ab-20261027/accepted.json')['inputs']
paths=set(reviewed)|{p for p in inherited if 'nav12' not in p.lower()}
paths.update(str(V/n) for n in ['response.json','completion.json','source-hashes.json'])
paths.update(str(R/n) for n in ['navv9diag_gate.py','seal_navv9diag_ram.py'])
paths.update(str(Path(row['mission'])/'init.c') for row in read(D/'missions.json')['passes'])
for p,h in inherited.items():
    if p in paths:assert sha(p)==h,('Inherited source changed',p)
(V/'fable-review.md').write_text(response['result']+'\n',encoding='utf-8')
adjudication='''SOUND-with-fixes reconciliado: finalizador reverifica FAIL histórico, deployment y gate de cada pasada con hashes. Heredados sellados sin cambios. Orquestación cargará navv9diagRamConfig directamente de missions.json y comprobará SHA antes de cada pasada. Corrección de finalizador aplicada antes de la primera medición. Gate real cubierto por10 controles; estado diagnóstico y eligibilityfalse permanecen. No aceptación nativa ni RAM todavía. Sin poderes de escritura en la lane Fable,denials0; entradas revisadas inmutables durante revisión.'''
(V/'adjudication.md').write_text(adjudication+'\n',encoding='utf-8')
paths.update(str(V/n) for n in ['fable-review.md','adjudication.md'])
out=dict(status='ACCEPTED_AFTER_REVIEW',model='claude-fable-5-1',verdict='SOUND-with-fixes',scope='DIAGNOSTIC_ONLY; original four height failures preserved',acceptance_eligible=False,inputs={p:sha(p) for p in sorted(paths)},mission_config='Load navv9diagRamConfig directly from frozen missions.json and verify before each pass',fixes=adjudication)
assert not (D/'accepted.json').exists();(D/'accepted.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(status=out['status'],sealed_files=len(paths),scope=out['scope'])))
