# EV112: optimización comparada con Chernarus

Petición viva de Guillermo, 24-10: comprobar que el mapa esté bien optimizado
comparado con Chernarus. Extiende P7/P13 y `terrain-load-performance.md`.
Codex sigue como ejecutor/integrador de esta continuación. No cambia el recorte,
el bosque aprobado ni la prioridad de revisión visual del piloto.

## Estado

Inventario estático completado sobre Q desplegado y Chernarus del cliente instalado.
**Rendimiento INCONCLUSO**: no se ha ejecutado el benchmark. MCP devolvió
`daemon_unavailable: autospawn already attempted`; no se inició ningún run.
Cliente requiere foco; la revisión conjunta sigue preparada. No modificar
resolución, densidad, LOD o geometría para optimizar sin aislar primero el coste.

Evidencia: `../evidence/performance/chernarus-comparison-20261024/README.md`.
No sustituye los controles de agua/colisión ni acredita 80–100 jugadores.

## Descubrimiento ya realizado [EXACT]

- Q: 2.578.822 objetos; 2.560.922 de vegetación, incluyendo arbustos, troncos y juncos.
- Chernarus instalado: 2.971.218 objetos; 2.572.370 de vegetación.
- Q tiene 5.220 recursos distintos bajo `baltic_water_v30`, 10.264 instancias,
  además de 35 recursos/instancias del piloto. Son rutas de modelos, no draw calls.
- Máximo en celdas completas de 256 m: vegetación Q 1.948; Chernarus 2.521.
  El reparto espacial y los modelos difieren: no inferir FPS a partir de estos números.
- El WRP antiguo de `P:/DZ` difiere del instalado. El censo antiguo de 105.628
  objetos filtraba familias y no es un total comparable. Los tamaños de los PBO
  tampoco son comparables directamente: Q incluye navegación y otras entradas.
- Equipo local: Ryzen 7 7800X3D, RTX 3090, RAM física observada 67.811.479.552 bytes;
  DayZDiag 1.30.164.200. Verificar de nuevo hardware/adaptador efectivo, binario,
  mods y ajustes antes de medir. No extrapolar al servidor de producción desconocido.

## Ensayo que falta [DESIGN; instrumentación cliente aún por verificar]

1. **Identidad y condiciones.** Mismo ejecutable, GPU efectiva, controlador,
   resolución, escala de render, FOV, calidad de objetos/sombras/terreno/hierba,
   distancias de visión y objetos, límite de FPS/VSync y mods de instrumentación.
   Guardar perfiles y hashes. Mismo clima, viento y visibilidad; registrar hora,
   fecha y condiciones de luz, pues la latitud del mundo puede variar la iluminación.
   No cambiar ajustes entre mapas ni mantener herramientas pesadas de fondo.
2. **Escenarios emparejados.** Bosque representativo, bosque denso, humedal,
   río/lecho, costa/presa, carretera entre árboles y panorama desde media altura.
   Escoger pares por contenido visible, distancia y cobertura, antes de conocer
   su rendimiento. Los máximos del inventario son candidatos de estrés, no pares
   equivalentes automáticos. Separar vista fija de recorrido físico/streaming.
3. **Captura cliente.** Verificar primero un capturador de presentaciones de frames
   con proceso, reloj, unidades y completitud demostrados; aún no hay uno validado
   en esta continuación. Registrar frame time mediano/p95/p99, FPS derivados,
   eventos >50 ms y >100 ms por minuto, RAM residente/privada, VRAM y GPU si la
   fuente permite medirlas. Distinguir asignación de VRAM y residencia; dato
   no disponible queda N/D. No calcular percentiles de frames a partir de medias
   móviles de 64 frames ni de una lectura de FPS cada segundo.
4. **Repeticiones.** Por escenario, 30 s mínimos de calentamiento y 120 s útiles
   de captura; tres pasadas por mapa, orden A-B-B-A-A-B. Comprobar texturas y LOD
   asentados. Registrar primera carga aparte; no llamar «fría» a una carga sin
   control de caché. Foco perdido, pausa, proceso distinto, captura incompleta o
   carga ajena contaminan esa pasada. Un frame lento real permanece en la muestra.
5. **Servidor.** A/B vacío sin CE ni jugadores con misión equivalente, 30+120 s;
   CPU por reloj monotónico y delta de tiempo de proceso, RAM y distribución de
   intervalos de simulación. El FPS nativo headless anterior fue constante y no
   está validado como tick real. Después, carga de IA activa idéntica con prueba
   de activación; exige navmesh correspondiente al mundo. CE/loot/persistencia,
   red y 80–100 jugadores reales son otra fase, no sustituible por 100 infectados.
6. **Tras carreteras/mapeado.** Repetir carretera y streaming tras las carreteras
   físicas; ciudades cuando existan. Comparar Baltic aún sin ciudades contra
   centros urbanos de Chernarus no demuestra capacidad urbana futura.

## Criterios antes del benchmark

- **Medición válida:** identidad, configuración, escenarios y cobertura temporal
  completos; tres pasadas válidas; fuente de cada métrica comprobada.
- **Objetivo de trabajo comparativo:** mediana entre pasadas de p95/p99 de frame
  time y RAM estable no mayor que 1,10× Chernarus en cada par comparable. Margen
  operativo local del 10%, no límite universal de DayZ ni aceptación multijugador.
  Exigir dispersión entre pasadas ≤5% para juzgar ese margen; más ruido = INCONCLUSO.
  VRAM se compara solo bajo la misma semántica de medición. Los tirones persistentes
  y aumentos >100 ms se investigan aunque la media cumpla.
- **FAIL del objetivo local:** exceso reproducible en dos o más pasadas válidas
  y mediana fuera de margen; localizar escena/recurso antes de editar.
- **PASS local:** métricas y cobertura válidas dentro de esos presupuestos,
  sin degradar calidad o jugabilidad y sin regresiones pendientes del escenario.
  No es PASS de producción: las ciudades, el servidor real y jugadores siguen aparte.
- **INCONCLUSO:** falta de capturador validado, foco, comparabilidad, repetibilidad,
  datos, versión concordante o carga activa demostrada. Nunca PASS por recuentos.

## Optimización si aparece un coste

Aislar geometría/LOD, agua/materiales, sombras, vegetación, streaming y simulación
con A/B de una sola causa, conservando capturas y funciones. Priorizar perfiles
del agua y del bosque continuo. Auditar LOD reales de los P3D compilados, tamaños
de piezas, materiales y colisión antes de extender el piloto. No eliminar bosque
de reserva ni bajar texturas como sustituto del diagnóstico. Repetir después el
escenario afectado y los consumidores funcionales pertinentes.

## Anclas existentes y límites

- Lector PBO: `tools/playtest/attach_navmesh.py:20`; lector de objetos compilados
  previo: `tools/terrain/package_visual_forest_ev112.py:29` (heurístico).
- Inventario nuevo: `tools/performance/compare_static_worlds_ev112.py:39` y `:127`.
- Observador host: `tools/navigation/sample_server_process.ps1:1`, PID+fecha,
  reloj monotónico, WorkingSet/PrivateMemory. No mide GPU ni frames de presentación.
- `P:/scripts/3_game/global/game.c:873`, `:880`, `:887`, `:894`, `:914`: firmas
  leídas de FPS actuales/promedios móviles y reloj. No prueban enlace o semántica
  runtime de 1.30. No reutilizar el `GetFPS()` global que falló en el ensayo antiguo.
- `plans/terrain-load-performance.md` y `plans/terrain-ai-load.md`: contratos
  anteriores conservados; sus misiones específicas de Baltic no se lanzan como
  comparador Chernarus sin adaptar y validar mundo, arranque y final de ambos.
