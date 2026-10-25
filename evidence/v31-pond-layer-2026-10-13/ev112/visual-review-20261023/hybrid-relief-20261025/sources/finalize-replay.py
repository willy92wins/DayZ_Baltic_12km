from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=R/'guarded-relief-batch-e';after=R/'guarded-relief-batch-e-replay'
for name in ('terrain.npz','domains.npz'):assert (before/name).read_bytes()==(after/name).read_bytes()
a=json.loads((before/'report.json').read_text());b=json.loads((after/'report.json').read_text())
assert a['checks']==b['checks'] and b['groups_applied']==71 and all(b['checks'].values())
for name,key in [('repair_guarded_shapes_ev112.py','author_sha256'),('repair_free_shapes_ev112.py','solver_sha256')]:
    p=W/'tools/terrain'/name;assert sha(p)==b[key];shutil.copy2(p,after/('author-used.py' if key.startswith('author') else 'solver-used.py'))
proof=dict(status='BYTE_EXACT_TERRAIN_AND_DOMAINS_REPLAY',original_report_sha256=sha(before/'report.json'),replay_report_sha256=sha(after/'report.json'),terrain_sha256=sha(after/'terrain.npz'),domains_sha256=sha(after/'domains.npz'),source_hashes=[b['author_sha256'],b['solver_sha256']],fixes=['Dirty-context guard includes accepted sibling clusters.','Source hashes captured at entry and rechecked at exit.','Retry mode and inherited error recorded separately.'],limits=['Build consumers remain bound to original byte-identical E terrain; source snapshots preserve both runs.'])
(after/'replay-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
(R/'hybrid-code-review/resolution.md').write_text('Los tres ajustes de Fable están aplicados. Reejecución formal con salida nueva: terreno y dominios idénticos byte a byte al candidato E inicial;71grupos y todos los controles iguales. Los clústeres10,11,38 pasan;39 se omite por contexto cambiado. Se conservan los dos autores por hash. Los controles globales, huella, carreteras y comparación independiente de fuente se ejecutaron sobre esos mismos bytes. La ausencia de unit tests para toda la composición y la dependencia numérica de SciPy permanecen como límites; no se sustituyen por una afirmación de certeza.\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
