# Revisión independiente y adjudicación — 25-10-2026

Fable5.1, CLI nativo, Read/Grep/Glob, sin ejecución, terminó en617,62s con SOUND-with-fixes. Modelo canónico claude-fable-5-1/firstParty; sin denegaciones; coste de lista3,6640835USD. Uso:290 input,38.104 output (24.947 thinking incluidos),487.454 cacheRead,81.706 cacheCreation. No son costes de factura confirmados. Informe original y recibo preservados. Esta tabla es la adjudicación del integrador, no una segunda aprobación de Fable.

| Hallazgo | Disposición y evidencia |
|---|---|
| P1-1 tolerancia de cadena1e-5m | Repro confirmado; reparado. POLICY v3 permite conectores medidos≤0,50m exclusivamente para detectar patrones. Cada conector publica longitud y alcance; no demuestra agua. División de76,32m en3piezas con desfase0/0,0001/0,20m conserva detección; hueco3m queda abierto. |
| P1-2 delantal omitido | Reparado. Se criban eje completo y tramo mojado original, con scope por hallazgo y longitud seca. Test introduce codo solo en delantal; aparece en informe aunque tramo mojado esté limpio. |
| P1-3 piezas huérfanas | La comprobación unilateral ya se había reparado durante la revisión; reforzada con igualdad exacta de IDs WRP/consumidos y enlace de piedras, descontando únicamente sitios retirados por el staging acreditado. Tests rechazan pieza/piedra omitida e ID duplicado. |
| P2 artefacto de extremos slanted | Confirmado por los8rungs del JSON de geometría y sus cotas: los extremos diagonales desplazan el punto medio, mientras el cuerpo plano tiene eje recto. Para forma macroscópica se extrapola ese eje medido a las estaciones originales. Eje bruto, offset y hallazgos originales se conservan como diagnósticos de representación; no se altera modelo ni WRP. Cuatro variantes calibradas. |
| P2 pirámide con pendiente de fondo | Repro confirmado; reparado el ajuste y la selección de candidatos. El plano ya se ajustaba pero tenía veto de pendiente; ahora se elimina ese veto y se buscan también máximos del residuo contra media centrada. Plano/rampa/cresta/colina redonda siguen negativos. Fixture NPZ2048² verifica detección sobre ladera5%. |
| P2 ápice entre vértices | Repro confirmado; fases de media celda alrededor de la mejor orientación detectan±3m. Test con y sin pendiente. No se certifican todas las fases subcelda. |
| P2 escalera con filetes8m | Reparado: detector de anclas rectas largas alternadas sobre dos ejes ajustados, independiente de giros por vértice. Positivo rotado0/17/45grados; meandro/arco suave permanecen negativos. |
| P2 rectángulo unido a otro borde | Límite reconocido, no reparado por relajar un umbral: el detector certifica componentes de borde aislados/cerrados; una unión cambia el componente y puede escapar. Publicado en terrain.json/report.json. Sigue en backlog de cobertura; no se declara detector exhaustivo ni mapa aceptado. |
| P2 umbrales fuera de policy | Umbrales de aceptación/candidatos principales movidos a POLICYv3: empalmes, poses, prominencia, aspecto/orientación/radios piramidales, soporte/perímetro rectangular y ejes. Tolerancias numéricas del algoritmo permanecen en fuente fijada por SHA. |
| P2 py3d sin hash | Su módulo real importado ahora figura por SHA entre inputs. |
| Backlog sitios/ramas | Los IDs declarados deben coincidir con51sitios del original fijado; registros ajenos bloquean. Orden por estación/orientación por lattice conserva su limitación: no certifica receptores ni conectividad entre ramas. |

Calibración previa adicional: rectángulo girado17grados no pasaba una tolerancia de un píxel aplicada al stencil de diferencia centrada. Su borde marca ambos lados y ocupa hasta2celdas; POLICYv2 corrigió ese límite geométrico. POLICYv3 conserva el cambio y pasa rectángulos0/17/45/73grados y cuatro círculos negativos. Ningún umbral se ajustó para mejorar el resultado del mapa.

71tests ejecutados (53previos+18nuevos),0fallos/errores/skips. El cribado S3 se ejecuta separadamente y puede/debe quedar REVIEW_REQUIRED. Presupuesto de revisión cumplido: una revisión independiente y una ronda de reparaciones con regresiones; no se solicita otra opinión para cambiar el veredicto.
