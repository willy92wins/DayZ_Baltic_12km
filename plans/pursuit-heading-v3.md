# Puente V10: comprobar el signo del rumbo del controlador

Extensión acotada de foundation-acceptance-2026-10-01-followup.md §2.
No cambia WRP, agua, navmesh, geometría del puente, límites ni movimiento de IA.

## Evidencia y discriminador

En `evidence/foundation-followup-2026-10-01/pursuit-heading-analysis.json`,
141 muestras cliente de V2 con rumbo reconstruido distinto de cero predicen
el desplazamiento como `ángulo_solicitado - rumbo`: error mediano0.136°.
La hipótesis opuesta tiene error mediano171.765°. El control sin infectado
anterior solo ejercitó rumbo cero: no separaba ambos signos. El rumbo se
reconstruye de la fórmula fuente, no era un getter registrado; es evidencia
cinemática y no una causa interna demostrada del motor.

[EXACT] `P:/scripts/3_game/human.c:24-28,234-237` define GetMovement, rumbo en
radianes y overrides de velocidad/ángulo. `:1435-1439` expone estado/ID de
comando. `PlayerBase.IsFighting` se implementa en
`P:/scripts/4_world/entities/manbase/playerbase.c:5382-5385`.
El consumidor cliente/server actual resta el rumbo en
`tools/navigation/continuous_pursuit_client.c:62` y
`continuous_pursuit_init.c:106`.

[HIPÓTESIS] Con ese signo, un rumbo no nulo desvía la orden. [DESIGN] Variante
V3 cambia exclusivamente la resta por suma en ambos consumidores, y registra
el getter real, orientación corporal, comando nativo, estado de combate,
entrada y posición en ficheros diagnósticos separados. Mantiene formato y
verificador físico V2, con encabezados V3. No se escriben poses ni velocidades
durante el recorrido. Se conserva V2 como FAIL.

Datos de diagnóstico: cada lado registra su propio movimiento/rumbo/comando;
la fase sigue en la variable sincronizada existente. Salud y aceptación física
siguen en servidor. No se sincronizan nuevos campos ni se toca daño/percepción.

VERDE: control local y ambos cruces completos con los límites originales V2,
positivo real y15contrapruebas existentes adaptadas solo al nuevo encabezado.
La hipótesis del signo solo queda apoyada en motor si hay muestras con rumbo
no nulo que siguen el rumbo geográfico previsto; rumbo cero da INCONCLUSO para
esa hipótesis aunque los cruces pasen. No declarar causa de IA por este control.

Atención a tasas: los picos9.2m/s de V2 salen de eventos NOISE intercalados a11ms
con pasos de0.10m; sus muestras regulares200ms alcanzan2.082m/s. No convertir ese
cociente aislado en prueba de impulso físico. El FAIL original se conserva y
no se modifica ahora su verificador. El diagnóstico nuevo permite distinguir
problemas de medida de trayectorias reales.

Presupuesto: una ejecución V3 (20min máximo), más una repetición discriminante
solo si una causa concreta lo justifica. Si no separa causas, cerrar diagnóstico
INCONCLUSO y pasar al siguiente gate. Sin Computer Use salvo necesidad observada.
