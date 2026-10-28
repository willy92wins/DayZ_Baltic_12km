**Veredicto: SOUND-with-fixes** (alcance: contrato offline, productor y preparador; sin compilación de motor, sin captura B1 nativa, sin binder/lifecycle; no autoriza lanzamiento).

## Qué verifiqué de forma independiente

- **Vínculo fuente.** `source_points` en `tools/quality/water_query_diag_b1_ev112.py:51-79` exige original FAIL/2658, 115 IDs ordenados y únicos, cobertura de los 68 fallidos+inciertos, 47 positivos íntegros, y re-contrasta `expected` y `original_states` contra el 2658 por ID. El CSV se regenera byte a byte (`check_csv`, línea 95), no se acepta un hash autoinformado. En `selected-points.json` real no hay ningún ground ni roadway FAIL, solo roadway INCONCLUSIVE, así que el chequeo de referencia no invalida el run por construcción.
- **Esquema y formato nativo.** Q26/O7/S11, booleans solo `true/false`, vectores `<x, y, z>` con aridad 3, enteros sin signo, finitud en todos los campos numéricos, relojes no decrecientes, END;345 sin cola. Contrasté con `dry-road-full-native-20261028/probe/native.log`: el motor imprime `false;false` y `<8264.171875, 8.632256, 8913.769531>`, compatible con el parser. Escalares salen con 6 cifras significativas, bien dentro de las bandas 0.01/0.03.
- **Orígenes float32.** El productor (`init.c:148-153`) calcula H+0.01, S+0.01, max(S,Wref)+0.25, H+100, S+2 en float32 nativo; el consumidor replica con `f32` y compara a 0.01 solo como precisión de log (`evaluate`, líneas 165-168). Correcto, y no es aceptación física.
- **Nulos vs 0.** CSV lleva flags separados (`csv_for`, línea 88); el productor usa `bed = ground` si flag 0 y solo eleva `upper` con Wref si flag 1. Test `test_float32_csv_preserves_zero_and_missing` cubre el caso 0.0 con flag 1.
- **No tautología.** El fixture del log es literal (valores analíticos H=10, B=12, W=11, fake=11.1), no llama al generador; residuos se calculan para las cuatro variantes, incluidos negativos (`depths` −0.91, −1.15 se conservan). `surface_class` devuelve `identity='NOT_DETERMINED'` siempre; `AMBIGUOUS/OTHER` testeados. Roadway INCONCLUSIVE persiste como confusor y nunca se compara contra A. Ground>0.01 o Roadway decisiva>0.03 dan REFERENCE_MISMATCH para todo el run (3 mismatches en 3 rondas, test línea 103-107). Cambio de reloj o fase → INCONCLUSIVE_DIAGNOSTIC.
- **Productor sigue el precedente.** Meteorología (`init.c:5-15`) idéntica a `BalticVisualProbeV1/init.c:5-15`; carga WRP a 40 m, espera 100 ms y refresco en el fotograma de consulta (`init.c:124-136` = precedente 104-116); mismas tres referencias marinas; `SurfaceRoadY3D(...UNDER)` desde H+100. Solo servidor: sin entidades, RPC ni cámara. Fail-closed: si falla la apertura de archivo no se escribe END y el consumidor rechaza por truncación.
- **Preparador.** Pinea hashes de A, 2658, plan, módulo, tests, misión y su propio código antes de trabajar y los reverifica al final (línea 31); ejecuta tests con `-I` y exige `Ran 22 tests`; lint exige exactamente 1 archivo, sin errores ni warnings. El `report.json` declara `OFFLINE_CONTRACT_ONLY_NOT_READY_FOR_DAYZ`. Coherente con el límite de que lint ≠ compilación.

## Hallazgo que exige cambio (uno)

**H1. Instantánea de objetos vacía pasa en silencio.** `evaluate` (`water_query_diag_b1_ev112.py:181-182`) solo marca `object_snapshot_incomplete` si hay objetos inválidos o con forma vacía. Si `object_count` es 0, no hay filas O, no hay confusor y el run puede quedar `CAPTURE_COMPLETE_DIAGNOSTIC_ONLY`. En el 2658 real estos mismos puntos devolvieron ~90-99 objetos a 40 m; un 0 significa que la carga WRP no ocurrió, es decir, dato ausente convertido en cobertura completa. Viola “datos incompletos nunca pasan”.

Repro (mutante que hoy NO lanza ni confunde; debe fallar hasta aplicar el fix):

```python
# tools/quality/test_water_query_diag_b1_ev112.py, añadir:
def test_empty_object_snapshot_is_confounder(self):
    lines=self.log.splitlines()
    fields=lines[2].split(';'); fields[12]='0'; lines[2]=';'.join(fields)
    del lines[3]  # quita la única fila O del primer registro
    r=self.report('\n'.join(lines)+'\n')
    self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC')
    self.assertTrue(any(c['reason']=='object_snapshot_empty' for c in r['confounders']))
```
```
python -I tools\quality\test_water_query_diag_b1_ev112.py -k empty_object
```

Fix mínimo (una línea tras la 182):

```python
if r['object_count'] == 0:
    reasons.append('object_snapshot_empty')
```

Impacto: el estatus “completo” deja de ser alcanzable con el snapshot a 40 m vacío. No cambia tolerancias ni etiquetas.

## Observaciones sin cambio exigido

- **CAPTURE_COMPLETE es inalcanzable con la selección real.** Hay 20 puntos con roadway INCONCLUSIVE y cada uno añade `original_roadway_inconclusive` como confusor, así que todo run real será a lo sumo INCONCLUSIVE_DIAGNOSTIC. Es conservador y cumple el plan; solo señalo que el estado superior no discrimina nada en la práctica. No propongo relajarlo.
- **Reloj intra-fotograma.** Si `GetTime()` avanza entre `startMs` y `endMs` dentro del mismo OnUpdate, las 345 filas quedan confundidas. Es lo que el plan pide (conservar, no simular simultaneidad). El orden estricto `start > last_end` queda garantizado por la espera de 100 ms entre puntos.
- **`low_below_ref` se compara por igualdad booleana** derivada de un ground redondeado a 6 cifras. Para los 115 puntos reales Wref ≈ 6.82 y S+2 ≥ 8.5, margen de metros, sin riesgo real.
- **Riesgos de compilación no verificables aquí.** `m_SeaPoints.Insert("2400 100 7000")` pasa un literal string a un método de plantilla `array<vector>`; el precedente solo prueba literal→vector en argumento de función nativa. `GetShapeName`/`GetPosition` se usan como en el precedente (Object.c:503/287 declarados; la declaración no acredita linking). Si no compila, no hay log y el consumidor rechaza: fallo cerrado, no falso PASS.
- **Formato de shape.** El parser no escapa `;` dentro de `GetShapeName`; rutas .p3d no lo contienen en el inventario actual. Aceptable.

## Requisitos previos a DayZ (no implementados en este lote, ni se exige que lo estén)

Binder/lifecycle revisado que fije hashes desplegados de misión, `points.csv`, 4 PBO y engine; preflight vigente; gate de inputs; recibo de run propio; revisión del binder. Hasta entonces: 2658 sigue FAIL, producto INCONCLUSIVE_PRODUCT_REFERENCE, H3 INCONCLUSIVE, B2 NOT_TESTED. Nada de lo revisado habilita integrar el candidato ni editar el original.

FIN_REVISION