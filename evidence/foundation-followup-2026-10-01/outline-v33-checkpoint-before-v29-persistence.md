# Base Baltic — checkpoint 2026-10-01T19:13:42.937701+00:00

Estado actual: V29 pasa las seis puertas offline y está importado en una copia de
Terrain Builder. La primera exportación tiene alturas/materiales correctos, pero
dos láminas de agua subieron 5,5 y 6,2 cm. Se corrigieron dos offsets de la capa
editable; su exportación y persistencia todavía no están verificadas. V33 sigue
siendo el candidato desplegado; V10 permanece intacto.

## Evidencia nueva

- ASC V29 `ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6`.
  25.668 vértices cambiados, máximo 5,079304 m frente a V33; límite compuesto
  de 6 m frente a V10 conservado. Mismo encuadre, clasificación y criterios.
- Consumidor vial: 239.126 secciones, cero fallos de ancho, pendiente y cuerda.
  Orillas: 621.260 extremos secos y 631.284 marinos sin violaciones;
  81.212 puntos congelados y 13/13 puertas geométricas PASS.
  Reserva, Narva, cauces e islas PASS; siete negativos viales y cuatro hidrológicos.
- Las 19 caras que intersectan agua se aceptan por nueva prueba continua física,
  no por igualdad con V33. V24–V28 y sus FAIL/certificados quedan conservados.
- Export nativo `tb/regional_road_network_v29/r1.wrp`, SHA `81d46989`:
  alturas, materiales, identidades y todas las matrices salvo Y de agua exactas.
  Dos desplazamientos nuevos frente a V33; 670 residuos submicrométricos heredados.
  `road-v29-native/first-export.json` conserva FAIL estricto de objetos.
- Capa corregida SHA `98a9bed6`; backup anterior y tres controles negativos.
  `relative-offset-correction.json` no acredita el resultado en el consumidor.
  Los 9.036 archivos originales de V33 permanecen iguales por hash.
- Seis recorridos de sedan preparados en `regional-drive-v3/reference.json`,
  SHA `b55bd894`; XY/criterios originales, Y de V29, controlador V2 ya ejercitado.
  Linter PASS, un archivo y cero errores/avisos. NO ejecutados.
  Consumidor regional V7 también congelado antes del ensayo.

## Punto de reanudación

Computer Use detenido y kernel reseteado. TB PID321476 mantiene `road_v29` y
el diálogo de exportación Select; nombre vacío. No existe `r2.wrp`.
Dos observaciones tras seleccionar/activar TB devolvieron píxeles de otra app.
No se envió más entrada tras verificar esa discrepancia. Pregunta al usuario
pendiente para poner Terrain Builder delante; no faltan permisos nuevos.
No hay DayZ ni NavMeshGenerator activos, session self=none y pending_commands=0.

Cuando el destino sea fiable: exportar `r2.wrp`, verificar todas las poses;
guardar, cerrar/reabrir y exportar `r3.wrp` para persistencia. Solo si quedan los
residuos heredados de agua <=1 micra, usar la derivación explícita documentada;
conservar los exports y sus FAIL. Después build aislado, navmesh nueva sobre ese
WRP, empaquetado con paridad, V7 regional, seis viajes V3, agua dinámica,
revisión visual y carga sin trabajos concurrentes. No reutilizar la NM de V33.

## Límites y conservación

V33 desplegado `38ebe847`, WRP `2ccb8dc4`, NM `425b8488`: 966.289 teselas;
consumidor regional V6 y agua local (15.936 muestras, margen seco 0,28706 m) PASS.
Neva, reserva y sur tienen capturas y protocolos completos; textura provisional,
aceptación visual global y rendimiento multijugador siguen pendientes.
V10 estable `d1008dd6` no se tocó. La reserva está protegida, aún sin vegetación.
BALTIC-005/007 permanecen abiertos; no versión 1.0 ni mapa terminado.

Skill local `dayz-terrain-workflow/references/regional-relief.md` actualizada:
medir alturas bajo orígenes de objetos es diagnóstico de riesgo; manda la pose
exportada. Etiqueta explícita de mecanismo desconocido y corrección pendiente.
UTF-8/enlaces/entrypoint sin cambios PASS; validador YAML completo no disponible
por falta de PyYAML, sin instalar dependencias. Recibo `road-v29-native-skill-update.json`.

HEAD `4ff154b7`, cambios previos/compartidos conservados; sin commit.
Cuota 19:07UTC: 15% semanal restante, ningún reset nuevo.
Ventana nocturna anterior completada y automatización PAUSED, sin reactivarla.
Estado anterior preservado en `outline-v33-checkpoint-before-v29-native.md`.
