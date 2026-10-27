"""Archive actual verdicts; never promote a rejected candidate as a map fix."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
E=W/'evidence/navigation/dry-bank-domain-pilot-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    result=read(R/'dry-bank-domain-run-20261027/result.json')
    tests=read(R/'dry-bank-domain-controls-20261027/summary.json')
    review=read(R/'dry-bank-domain-code-review-20261027/response.json')
    author=read(R/'dry-bank-domain-pilot-20261027/author-report.json')
    visual=read(R/'dry-bank-domain-analysis-20261027/visual-water-freeboard.json')
    context=read(R/'dry-bank-domain-setup-fixed-20261027/context.json')
    assert all(sha(Path(p))==h for p,h in context['hashes'].items())
    assert result['status'] in ('OFFLINE_CANDIDATE_ONLY','REJECTED_OFFLINE')
    assert result['candidate_sha256']==author['candidate_sha256']==sha(R/'dry-bank-domain-pilot-20261027/candidate-surfaces.npz')
    assert visual['candidate_sha256']==result['candidate_sha256']
    assert tests['status']=='PASS' and sum(t['result']=='PASS' for t in tests['tests'])==10
    assert sum(t['result']=='NOT_APPLICABLE' for t in tests['tests'])==1
    assert not review['is_error'] and not review.get('permission_denials') and 'FIN_REVISION' in review['result']
    assert 'claude-fable-5-1' in review['modelUsage']
    assert read(R/'dry-bank-domain-code-review-20261027/completion.json')['inputs_unchanged']
    assert read(R/'dry-bank-domain-run-20261027/completion.json')['returncode']==0
    assert not read(R/'dry-bank-domain-run-20261027/completion.json')['timeout']
    E.mkdir(exist_ok=False)
    def cp(source,relative):
        dest=E/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);assert sha(source)==sha(dest)
    for name in ('pilot_dry_bank_domain','verify_dry_bank_domain','test_dry_bank_domain','run_dry_bank_domain',
                 'prepare_dry_bank_domain','review_dry_bank_domain_code','fix_dry_bank_test_fixture',
                 'inspect_dry_bank_domain','checkpoint_dry_bank_domain','pilot_dry_apron','diagnose_dry_bank_water_rounding'):
        cp(R/(name+'.py'),'source/'+name+'.py')
    for folder,label in [('dry-bank-domain-setup-20261027','setup-reviewed'),('dry-bank-domain-setup-fixed-20261027','setup-final'),
                         ('dry-bank-domain-code-review-20261027','review'),('dry-bank-domain-tests-20261027','failed-test'),
                         ('dry-bank-domain-controls-20261027','controls'),('dry-bank-domain-run-20261027','execution'),
                         ('dry-bank-domain-pilot-20261027','pilot'),('dry-bank-domain-analysis-20261027','analysis'),
                         ('dry-bank-water-reference-diagnosis-20261027','water-reference-diagnosis')]:
        for source in sorted((R/folder).rglob('*')):
            if source.is_file() and source.suffix in ('.json','.log','.md','.py','.png'):
                cp(source,label+'/'+source.relative_to(R/folder).as_posix())
    plan=W/'plans/ev112-dry-bank-domain-pilot-20261027.md';cp(plan,'plan-reviewed.md')
    failures=[k for k,v in result['gates'].items() if not v]
    if not visual['previously_dry_floor_preserved']:failures.append('actual_visual_water_dry_floor')
    summary=dict(status='REJECTED_OFFLINE' if failures else result['status'],consumer_status=result['status'],
        actual_visual_water_dry_floor=visual['previously_dry_floor_preserved'],failed_gates=failures,tests_passed=10,tests_not_applicable=1,
        protected_vertex_count=result['counts']['protected'],initial_test_failure_retained=True,
        candidate_count=1,solver_iterations=author['solver']['iterations'],candidate_sha256=result['candidate_sha256'],
        preserved=result['preservation'],energy=[result['baseline']['discrete_energy'],result['candidate']['discrete_energy']],
        slopes=dict(baseline=result['baseline']['slopes'],candidate=result['candidate']['slopes']),
        review_verdict='SOUND by reading; one separate concrete test-fixture correction after runtime counterexample.',
        native_navigation_status='NOT_TESTED',P14_status='NOT_CERTIFIED',RAM_status='OPEN',
        asset_builds=0,dayz_runs=0,production_deployed=False)
    (E/'adjudication.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    energy=summary['energy'];status=summary['status'];slopes=summary['slopes']
    text=f'''# Kit-7: piloto de toda la orilla seca

**{status}**. Un candidato desde la fuente original, sin rebajar tolerancias.
Energía discreta {energy[0]:.9f} → {energy[1]:.9f};
{author['solver']['iterations']} iteraciones; {result['changed_points']} vértices de altura cambiados.
Puertas fallidas: {', '.join(failures) if failures else 'ninguna en este ensayo offline'}.

El consumidor lee baseline y candidato guardados; deriva el lecho, CAP inclusivo
de seis metros, bordes, agua y XZ sin recibir la máscara del autor. Reconstruye
las protecciones desde fuentes congeladas. Agua/lecho/extremos no se aceptan
por una afirmación del generador. Los detalles por puerta están en execution/result.json.

Diez controles ejecutados: identidad sin mejora, mutaciones CAP interior, lecho,
agua, XZ, borde, techo, no finito, timeout y cero con signo. El test de mutación
de protección es **NOT_APPLICABLE**: este tramo tiene cero vértices que toquen
esas zonas. El primer test abortó por asumir que existía uno; se conserva ese
fallo y su única corrección. No se cuenta como cobertura protegida real.

Fable5.1 revisó el experimento por lectura y dio SOUND. La prueba real encontró
el supuesto anterior pese a esa revisión; ambos resultados quedan registrados.
El timeout devuelve124; exit0 del autor no sustituye el veredicto del consumidor.

![Perfiles antes y después](analysis/profiles.png)

Distribuciones respecto al nivel previo al redondeo: execution/result.json;
respecto al agua visual realmente guardada: analysis/visual-water-freeboard.json.
Se comprueba aparte que se conserva el margen seco previo contra esa agua visual.
El piso experimental
de0.025m no acredita P14, oleaje ni agua nativa. Las14coordenadas históricas se
conservan; sus comparaciones contra la navmesh vieja son únicamente descriptivas.
No se creó MLOD/PBO/NM, no se desplegó y no se utilizó DayZ MCP.
Nav8 sigue607PASS/RAMFAIL; RAM, navegación del candidato, vista y calidad global
siguen abiertas. El council ampliado continúa en cola tras el trabajo vigente.

El NPZ local se liga por SHA256 en los informes; no se publica como mapa validado.
Las fuentes de los scripts y los recibos están incluidos para auditar el ensayo.
'''
    (E/'README.md').write_text(text,encoding='utf-8')
    content=plan.read_text(encoding='utf-8-sig').replace('Estado: REVISADO_SOUND_WITH_FIXES_PENDIENTE_IMPLEMENTACION.',
        'Estado: EJECUTADO_'+status+'.')
    content+='\n## Resultado ejecutado\n\n'+f'{status}; evidencia evidence/navigation/dry-bank-domain-pilot-20261027. Un candidato consumido; no relanzar. Diez controles PASS y uno NOT_APPLICABLE (cero puntos protegidos). Primera ejecución del test falló por ese supuesto, única corrección conservada. Agua/extremos y demás puertas constan por separado. Energía{energy[0]:.9f}→{energy[1]:.9f}. Ningún build ni prueba nativa.\n'
    plan.write_text(content,encoding='utf-8')
    handoff=W/'HANDOFF.md';lines=handoff.read_text(encoding='utf-8-sig').splitlines();inside=False
    updates={'updated:':'updated: 2026-10-27 (piloto de toda la orilla seca ejecutado: '+status+')',
        'plan:':'plan: plans/ev112-dry-bank-domain-pilot-20261027.md EJECUTADO_'+status+'. Un candidato consumido; no relanzar.',
        'next:':'next: Leer ACTIVE-WORK.md y evidence/navigation/dry-bank-domain-pilot-20261027/README.md. '+('Preparar y revisar build de todos los LOD y pruebas agua/colisión/forma/bosque; después navegación12.5/607 y RAM seisABBAAB si pasa.' if not failures else 'Localizar las puertas fallidas antes de proponer otra hipótesis. No integrar este candidato ni repetirlo con otros pesos.'),
        'handoff:':'handoff: evidence/navigation/dry-bank-domain-pilot-20261027/README.md.10controlesPASS,1NOT_APPLICABLE;'+status+'. Sin build/despliegue/nuevasondas; RAM/global/council abiertos.'}
    for i,line in enumerate(lines):
        if line=='<!-- LIVE-STATE:START -->':inside=True
        if line=='<!-- LIVE-STATE:END -->':inside=False
        if inside:
            for prefix,value in updates.items():
                if line.startswith(prefix):lines[i]=value
    handoff.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    manifest={p.relative_to(E).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(E.rglob('*')) if p.is_file()}
    (E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
