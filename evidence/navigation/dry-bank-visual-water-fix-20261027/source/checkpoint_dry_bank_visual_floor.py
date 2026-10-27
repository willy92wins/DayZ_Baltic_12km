from pathlib import Path
import hashlib,json,shutil
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
E=W/'evidence/navigation/dry-bank-visual-water-fix-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ctx=read(R/'dry-bank-visual-water-setup-20261027/context.json')
    assert all(sha(Path(p))==h for p,h in ctx['hashes'].items())
    r=read(R/'dry-bank-visual-water-run-20261027/result.json')
    t=read(R/'dry-bank-visual-water-controls-20261027/summary.json')
    v=read(R/'dry-bank-visual-water-analysis-20261027/visual-water-freeboard.json')
    a=read(R/'dry-bank-visual-water-pilot-20261027/author-report.json')
    review=read(R/'dry-bank-visual-water-plan-review-20261027/response.json')
    assert not review['is_error'] and not review.get('permission_denials') and 'FIN_REVISION' in review['result'] and 'claude-fable-5-1' in review['modelUsage']
    assert t['status']=='PASS' and sum(x['result']=='PASS' for x in t['tests'])==12
    assert sum(x['result']=='NOT_APPLICABLE' for x in t['tests'])==1
    for name in ('retired_candidate','actual_dry_floor'):
        assert read(R/'dry-bank-visual-water-controls-20261027'/name/'result.json')['gates']['bounds'] is False
    candidate=R/'dry-bank-visual-water-pilot-20261027/candidate-surfaces.npz'
    assert sha(candidate)==r['candidate_sha256']==v['candidate_sha256']==a['candidate_sha256']
    assert read(R/'dry-bank-visual-water-run-20261027/completion.json')['returncode']==0
    final_status='OFFLINE_CANDIDATE_ONLY' if r['status']=='OFFLINE_CANDIDATE_ONLY' and v['status']=='PASS' else 'REJECTED_OFFLINE'
    assert final_status=='OFFLINE_CANDIDATE_ONLY','This publication template requires the complete offline gates; preserve raw rejection separately.'
    original=np.load(ctx['paths']['source']);current=np.load(candidate);four=[]
    for point in read(Path(ctx['paths']['rounding_diagnosis']))['rows']:
        i,j=point['row'],point['column'];four.append(dict(row=i,column=j,
            original_y=float(original['bed'][i,j,1]),candidate_y=float(current['bed'][i,j,1]),
            visual_margin=float(current['bed'][i,j,1]-original['water'][i,0,1])))
    summary=dict(status=final_status,consumer_status=r['status'],additional_visual_floor=v['status'],
        changed_points=r['changed_points'],energy=[r['baseline']['discrete_energy'],r['candidate']['discrete_energy']],
        slopes=dict(baseline=r['baseline']['slopes'],candidate=r['candidate']['slopes']),
        tests_passed=12,protected_mutant='NOT_APPLICABLE_ZERO_VERTICES',
        retired_candidate_rejected_by_bounds=True,single_point_regression_rejected_by_bounds=True,
        previous_four_points=four,previously_dry_checked=v['was_visual_dry_count'],
        candidate_sha256=sha(candidate),solver_iterations=a['solver']['iterations'],solver_success=a['solver']['success'],
        source_inputs_unchanged=True,builds=0,dayz_runs=0,deployed=False,
        limits=['Offline geometry only. P14, water/actors in engine, navigation, RAM and visual/global acceptance remain open.',
                'One new candidate from original baseline after retiring a demonstrated false PASS; no parameter sweep.'])
    E.mkdir(exist_ok=False)
    def cp(source,dest):
        target=E/dest;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);assert sha(source)==sha(target)
    for name in ('pilot_dry_bank_visual_floor','verify_dry_bank_visual_floor','run_dry_bank_visual_floor','test_dry_bank_visual_floor',
                 'implement_dry_bank_visual_floor','review_dry_bank_visual_water_plan','inspect_dry_bank_visual_floor',
                 'prepare_dry_bank_visual_analysis','checkpoint_dry_bank_visual_floor'):
        cp(R/(name+'.py'),'source/'+name+'.py')
    for folder,label in [('dry-bank-visual-water-setup-20261027','setup'),('dry-bank-visual-water-plan-review-20261027','review'),
                         ('dry-bank-visual-water-controls-20261027','controls'),('dry-bank-visual-water-run-20261027','execution'),
                         ('dry-bank-visual-water-pilot-20261027','pilot'),('dry-bank-visual-water-analysis-20261027','analysis')]:
        for p in sorted((R/folder).rglob('*')):
            if p.is_file() and p.suffix in ('.json','.log','.md','.py','.png','.diff'):cp(p,label+'/'+p.relative_to(R/folder).as_posix())
    plan=W/'plans/ev112-dry-bank-visual-water-fix-20261027.md';cp(plan,'plan-executed.md')
    cp(R/'dry-bank-next-build-discovery.md','next-build-discovery.md')
    (E/'adjudication.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    energy=summary['energy'];reduction=100*(1-energy[1]/energy[0])
    (E/'README.md').write_text(f'''# Orilla seca completa: referencia de agua corregida

**{final_status}**. Se conserva exactamente agua, lecho, extremos completos
CAP≤6m, XZ y bordes. El margen seco se comprueba contra el agua realmente
guardada; los47.178puntos previamente secos conservan al menos0.025m.

Energía discreta: **{energy[0]:.9f} → {energy[1]:.9f}** ({reduction:.3f}% menos).
Ninguna pendiente máxima longitudinal, transversal o de cara aumenta.
Vértices cambiados: {r['changed_points']}; iteraciones: {a['solver']['iterations']}.
El límite de iteraciones no es convergencia ni aceptación por sí solo.

**12controles PASS y1NOT_APPLICABLE** (no hay vértices en zonas protegidas).
Incluyen mutantes de agua, extremos, lecho, XZ, borde, techo y no finito,
identidad sin mejora, timeout y bytes. Dos regresiones nuevas rechazan por
bounds tanto el candidato retirado como un solo punto con el fallo real.
Cuatro puntos originales que perdían el margen constan en adjudication.json.

El ensayo anterior df0c5994 queda REJECTED_OFFLINE: autor y checker compartían
una referencia errónea (level sin redondear). Un postcheck independiente lo
detectó pese al PASS inicial. Sus informes y pruebas se conservan en
../dry-bank-domain-pilot-20261027. Ese falso PASS no se reescribe ni se oculta.
Fable5.1 revisó el mecanismo y la sustitución antes de ejecutar la reparación.
No se cambiaron0.025/.02/.002/500 ni el dominio; se partió de la fuente original.

![Perfiles de la orilla](analysis/profiles.png)

Esto valida geometría offline. **No es aceptación nativa, de navegación,
RAM, oleaje/P14, visual ni del mapa completo.** No hubo MLOD/PBO/NM ni despliegue.
Siguiente: materializar todos los LOD con colisión correcta, comprobar el paquete,
agua/forma/bosque y luego nueva navegación12.5/607consultas. RAM requiere seis
ABBAAB frescas si pasa la fase funcional. Mantener todos los límites actuales.
El council ampliado sigue en cola tras el trabajo vigente.
''',encoding='utf-8')
    plan.write_text(plan.read_text(encoding='utf-8-sig').replace('Estado: REVISADO_SOUND_PENDIENTE_IMPLEMENTACION.',
        'Estado: EJECUTADO_'+final_status+'.')+f'\nResultado: {final_status};12controlesPASS/1N_A; evidencia evidence/navigation/dry-bank-visual-water-fix-20261027. Candidato consumido, no relanzar.\n',encoding='utf-8')
    hp=W/'HANDOFF.md';lines=hp.read_text(encoding='utf-8-sig').splitlines();inside=False
    updates={'updated:':'updated: 2026-10-27 (orilla seca completa y referencia real del agua: '+final_status+')',
        'plan:':'plan: plans/ev112-dry-bank-visual-water-fix-20261027.md EJECUTADO_'+final_status+'. Candidatos anteriores retirados, no relanzar.',
        'next:':'next: Preparar y revisar materialización de LOD desde candidato seco validado; conservar todas las correcciones de colisión. Luego paquete/agua/forma/bosque, navegación12.5/607 y RAM seisABBAAB si cumple. Leer ACTIVE-WORK.md.',
        'handoff:':'handoff: evidence/navigation/dry-bank-visual-water-fix-20261027/README.md.12controlesPASS/1N_A; agua/extremos exactos y margen seco real verificado. Sólo offline; RAM/global/council siguen abiertos.'}
    for i,line in enumerate(lines):
        if line=='<!-- LIVE-STATE:START -->':inside=True
        if line=='<!-- LIVE-STATE:END -->':inside=False
        if inside:
            for prefix,value in updates.items():
                if line.startswith(prefix):lines[i]=value
    hp.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    manifest={p.relative_to(E).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(E.rglob('*')) if p.is_file()}
    (E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
