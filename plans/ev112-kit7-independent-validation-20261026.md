# EV112 — kit-7, validación independiente tras el reinicio

Continúa la unidad de ríos del plan `ev112-shape-repair-20261025.md:14` bajo la petición de Guillermo de corregir y comprobar autónomamente. C/F desplegado permanece intacto. El candidato aislado está en `E:/DayZ-Baltic-Build/shape-repair-20261025/river-kit7-a-on-f-20261026`.

## Corrección de alcance, sin cambiar el candidato

El plan inicial del ejecutor (`river-kit7-candidate-plan.md`, conservado en evidencia) añadió T±0,75 m como condición para el soporte del río. Fable identifica que esa cota procede del piloto de **relieve alrededor de picos/pozos**, `ev112-guarded-relief-neighbours-20261025.md:22-25`; no figura en el contrato de autoría de ríos. Se corrige esa aplicación indebida, no el umbral del detector ni las protecciones ni el diseño aprobado del cauce. La autorización vigente para continuar el cauce permite esta corrección de alcance del ejecutor; no se cambia una decisión de Guillermo.

La comparación con T se conserva como diagnóstico condicional: 2.164 vértices exceden 0,75 m y 475 cotas serían incompatibles **si se impusiera esa envolvente**. No prueba imposibilidad global ni aceptación del río. El alisado de relieve mantiene T±0,75 m y radio24m. No se retoca el autor para fabricar un PASS.

## Puertas y presupuesto

Un autor aislado, máximo1.800s, ya terminó; no nueva regeneración automática. Revisión de MLOD guardado, máximo600s: extremos recuperados del eje original, agua visual y `water_ext`, continuidad, ausencia de pliegues, cierre de colisión y control negativo de cola eliminada. Lectura independiente de terreno: máscaras congeladas, carreteras, agua antigua, disco015-45, reparaciones previas F, picos/pozos/aristas. Medir separadamente el cambio de `envelope.npy`/`cover.npy` y distinguir soporte enterrado de terreno exterior visible. Una revisión de visibilidad muestreada, máximo600s, registra geometría real y bordes expuestos; no acepta estética por contadores.

Antes de cualquier integración siguen siendo obligatorias la reducción y revisión del coste de colisión, regeneración de huella/bury y pruebas del agua nueva, bosque, compilación/poses y sondas del paquete exacto. La navegación debe pertenecer al nuevo paquete, sin heredar E ni C. Vista conjunta posterior. Con cualquier fallo se conserva la evidencia y se investiga el mecanismo; no se bajan umbrales ni se repite el mismo intento sin un discriminador.
