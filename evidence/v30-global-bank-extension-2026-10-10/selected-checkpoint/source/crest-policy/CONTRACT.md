# EV93: política para crestas de un eje

## Estado y alcance

Este directorio contiene únicamente un helper reutilizable de política escalar, fixtures y contrato. No ejecuta solver, no carga ni escribe soluciones de terreno, no crea candidato y no modifica autor/consumidor EV93. La adopción queda bloqueada hasta que termine la tanda actual de 703 ventanas y pase el consumidor global independiente.

Identidad de política: ev93-crest-one-active-axis-v1.

## Fuentes ancladas

- Propuesta next-method-crests.md, SHA-256 ba9245134a368870bb4e0090ff36f3c1b91b26b5bc8756d8f0fbf48ddb04ccce.
- EV92 verify_ev92.py, SHA-256 87b5ee5ee95318f1a8026c4a7459aa06d27c9b69db80f34ad25149293d5fc1df. Momentos y raíz de energía sin cambios: líneas 83–99; regla antigua de foco: 100–117.
- shape_contract.py, SHA-256 8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533. Prominencias cardinales y puertas de forma: líneas 23–30 y 48–85.
- B EV82-B, SHA-256 f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0.

## Regla

Para centro f y vecinos cardinales n1,n2 en un eje, p(X)=max(0, Xf-max(Xn1,Xn2))=max(0,min(Xf-Xn1,Xf-Xn2)). Eje activo si y solo si p(B)>0. El activo exige p(Hα)≤3p(B)/4. El inactivo exige p(Hα)=0 para impedir crear un pico en el foco. Si ambos ejes son inactivos, se rechaza.

Para cada vecino i, d_i(α)=(Bf-Bni)+α[(Hf-Bf)-(Hni-Bni)]. Como T≥0, p(Hα)≤T equivale exactamente a min_i d_i(α)≤T: unión de dos intervalos subnivel afines en [0,1]. Si ambos ejes están activos, se devuelve la regla EV92 original sin exigir una cola hasta α=1. Si exactamente un eje está activo, se toma en cada eje la componente conexa de la unión que contiene α=1; se rechaza si no existe o si su ancho es cero. Se combinan sus inicios EW y NS con alpha_energy, raíz inferior calculada por EV92 intacto: start=max(alpha_energy,start_EW,start_NS). El único alpha es (start+1)/2 y debe quedar estrictamente en (0,1). El cast y la operación float64→float32 siguen los de EV92. Todos los gates de forma restantes, D8, agua, corredor y globales se vuelven a evaluar; el helper no certifica ninguno.

API: `derive_scalar_rule(base, direction, *, focus_rc, alpha_energy, provenance, legacy_rule=None)` y su variante local `derive_scalar_rule_from_cardinals(base_values, direction_values, *, alpha_energy, provenance, legacy_rule=None)`. La API local acepta cinco alturas float32 en orden `[center,W,E,N,S]`, evitando una grilla H completa por solución. `energy_lower_from_moments` recibe q0/q1/q2 como `Fraction` exactas ya calculadas por los stencils EV92 originales. `interpolate_float32` conserva la operación EV92: interpolar en float64 y castear una vez a float32. `evaluate_focus_after`/`evaluate_focus_after_cardinals` validan ese resultado float32. `replace_focus_gate` pasa el gate antiguo de foco a diagnóstico y sustituye solo su participación en aceptación; todos los demás gates del informe shape_contract se conservan.

## Proveniencia al reutilizar rechazo

Provenance liga qid/centro, baseline, prepared, result, solución, plan, EV92, shape contract y este módulo; se exige la razón de rechazo completa exacta “final gate scalar interpolation rule unavailable: baseline focus is not prominent on both axes”. El módulo valida los pins fijos y el formato SHA. El caller aún debe demostrar vínculo del result-file con evento ledger, hash/schema del solution NPZ, valores B exactos y direction_float32 == float32(solver_x_float64). Los artefactos originales rechazados no se reescriben: alpha/delta derivados van a salidas separadas con hashes nuevos.

## Fixtures

test_crest_policy.py cubre ejes ambos/uno/ninguno, unión conectada y desconectada, singleton en alpha=1, passthrough legacy aun si la cola nueva no llega a uno, revalidación de resultado float32, preservación de todas las puertas no foco y rechazo de razón/pin incorrecto. Ejecutar solo ese archivo con GIS Python. Las pruebas validan política y metadatos, no autoría, terreno ni aceptación global.
