# EV112 — piloto Q, bosque completo y carreteras — 24-10

**Servidor: 786/786 PASS en el paquete completo. Vista personal preparada, todavía no aceptada.**

Este checkpoint sustituye el bloqueo de banco y los pendientes de compilación del checkpoint B. No cierra la corrección visual de todos los ríos ni los dominios expresamente pendientes. Guillermo pidió avanzar autónomamente y continuar después las carreteras; no se han abierto subagentes ni modificado los cambios ajenos del árbol principal.

## Paquete actual

`P:/Mods/@DayZ_Baltic_EV112_VisualReviewQ`:

| Archivo | SHA256 |
|---|---|
| narva_trial.pbo | f5ffc2affe67d739b51a26f723082389f41c6b94fdf160f93ba6548ae1fd8521 |
| baltic_stream_pilot.pbo | 742fcc8d076df39a8c54cb99f86c3099976219afe00bc62561794f7cc701bec7 |
| baltic_water_v30.pbo | 97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43 |

Origen de trabajo: `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018` (B). Mundo en `B/package-visual-forest-20261024-c`; piloto final en `B/visual-pilot-collision-20261024-q/collision-package`. El intento de empaquetado B quedó interrumpido y no es una entrega. No usar tampoco el PBO Q recién compilado de `packed/`: el paquete final conserva los otros33 modelos binarios de P, porque recompilarlos cambia bytes aunque sus superficies coincidan.

El terreno sigue siendo mezcla B, `terrain-buried.npz` **bc41bd8314affc5787e827b75fd7d03b7de454c0ffaae3a7476ccc7b609fd508**. No se incorporó ninguna de las pruebas de carretera. El mod anterior RuntimeMarginsV2 permanece intacto.

## Qué fallaba y qué se corrigió

1. La primera sonda produjo siete filas corruptas y avisos `house, config class missing`; no era evidencia válida. Se añadieron las35 clases `Land_<modelo>: HouseNoDestruct`, siguiendo `P:/DZ/water/config.cpp`, y se separó la lectura de consultas nativas de la composición del texto. El paquete de esa corrección conservó los35 ODOL exactos.
2. Retener referencias WRP durante100ms dejaba referencias nulas: la comparación controlada muestra nueve nulas y, al refrescar `GetObjectsAtPosition` en el mismo fotograma, clases/cuerpos/colisión válidos. La sonda actual refresca antes de los rayos.
3. Las referencias del mar se miden junto a **cada punto**; comparar Narva con una marea anterior era incorrecto. El recorrido final abarca niveles0,65–0,85m y sus25 controles delanteros pasan.
4. Bullet tiene un margen de contacto: calibración independiente sobre `Land_streambed_leaf_long_straight`, cinco impactos y289 controles vacíos. Distancia proyectada sobre su normal:0,039991446m, dispersión<0,000007m. La normal devuelta por RaycastRV en este experimento era un desplazamiento, no se usa para calibrar. Se mantienen3cm para lecho RV y1cm de diferencia del margen Bullet respecto al referente.
5. Después de esas correcciones quedaban dos fallos estrictos de RaycastRV, IDs56 y219. Ambos caían en un vértice compartido por seis prismas. La cuadrícula±1/512m impactaba en los ocho vecinos; el centro fallaba. Q solapa solo esos12 componentes internos un1% alrededor de su centro: máximo desplazamiento8,155mm, sin cambiar sus planos superiores ni los límites del modelo. Visual, Memory y Roadway son byte-idénticos en fuente; las35 poses son exactas. El paquete final cambia únicamente dos entradas ODOL. **El mismo evaluador estricto pasa ahora los786 puntos**, sin ensanchar sus rayos ni cambiar tolerancias para ocultar los fallos.

La prueba acota dos juntas observadas; no acredita por sí sola caminar por todos los modelos ni establece una solución universal para futuros cauces. El piloto sigue limitado a kit-118 y65.0-0.

## Bosque y compilación

- 2.560.922 elementos de bosque; soporte/raíz/inclinación/agua/margen del lecho completo: cero fallos. Se mantienen las93 exclusiones medidas en B.
- G2/G3 generales: PASS con **su regla estadística existente**, no con cero ventanas fuera del intervalo. G2 tiene67/384 ventanas fuera y G3 tiene29/384, dentro de las reglas comparadas con Livonia. No se modificaron sus jueces ni bandas.
- G2/G3 estrictos de los dos sectores piloto: PASS con cero métricas fallidas; se mantiene la exigencia de densidad de A-reserva.
- G7:47 turberas abiertas juzgadas, cero fallos; no hay turberas arboladas juzgadas. G8:475 ventanas de bosque, cero fallos; claro máximo1250m² frente al límite de2000m² del referente.
- Lectura del WRP compilado:2.578.822 IDs/modelos conservados,35 poses del piloto exactas; negativos de objeto perdido, extra y desplazado rechazados. Solo un tronco caído supera el anterior umbral absoluto de10micras: diferencia Y de15,259micras, exactamente dos ULP float32. Se admite esa precisión únicamente para Y de modelos del bosque, con comprobación adicional de raíz≤5mm: error real de este objeto11,795micras; XY y rotación exactos. No se relaja el contrato de apoyo ni el de los pilotos.
- Paquete:6825 entradas anteriores byte-idénticas. Solo cambian WRP/config; config únicamente añade la dependencia del piloto. El lector OPRW sigue siendo heurístico y no decodifica alturas comprimidas. La sonda comprueba los puntos de altura especificados; no cada vértice.

## Motor y limpieza

Run **30260b11-2850-4f1a-b2e4-cc9693fe7730**,24-10 a00:25UTC. `runtime-e/result.json`: **SERVER_PROBE_PASS,786 puntos,0 fallos**. Incluye extremos, centros, bancos, juntas, relieve, Narva y apoyos. El RPT no presenta clases de casa ausentes, errores de compilación ni excepciones en el barrido guardado; cierre ordenado confirmado.

La lista de puntos conserva la procedencia de su cálculo original sobre P: esas superficies/poses son exactas en Q. La identidad de lo efectivamente desplegado está en `deployment.json` y los recibos actuales, no en los hashes históricos de `points.json.inputs`.

Los runs anteriores, incluidos los diagnósticos, están retirados. Después del cierre: `self=none`, sin propietario, banco libre, ninguna limpieza degradada. No se cerró ninguna partida ajena. No hay prueba de cliente, conducción, navmesh nueva ni rendimiento para80–100 jugadores.

## Carreteras: avance y límite real

P10/P11 mantienen la reserva del terreno antes del mapeado físico. Consumidor existente sobre el agua actual:77.559 estaciones,102 cadenas;11 fallos transversales heredados en la cadena49, (5294,5997)–(5307,6031), máximo0,472556m. Pendiente máxima0,062468 y ondulación0,024596m pasan. La base anterior da los mismos resultados.

Plan y diagnóstico: `plans/ev112-road-followup-20261024.md`. Cuatro capas separadas A–D cumplen el juez vial, pero generan18/14/12/13 aristas nuevas o empeoradas>20grados: **todas rechazadas y ninguna integrada**. Los cinco vértices históricamente etiquetados como agua están secos en sus estrellas completas; C prueba esa condición, D la extiende a cuatro vecinos del collar. No se ha rellenado agua real ni cambiado la topología.

Reanudar por una solución conjunta del perfil y las normales de la transición. No seguir cambiando radios para perseguir un PASS del contador vial: la extensión armónica no controla los pliegues. El tramo actual conserva sus11 fallos, no queda cerrado por los candidatos rechazados.

## Revisión conjunta preparada y pendientes

Solicitud personal: `B/personal-view-visual-20261024-q/launch-personal.json`. Misión nueva `BalticBasicEV112VisualQ.BalticTrial`,16 archivos verificados, sin copiar persistencia. Aparición Narva (2392,6948). Recorrido en `personal-view/receipt.json`: Narva, kit-118,65.0-0, controles de bosque/turbera, cruces y tramo vial pendiente. Consultar `place_safely` y la altura real antes de cada traslado; no `camera_set`. El cliente requiere foco de Guillermo; no se ha lanzado.

Antes de expandir el cauce: vista desde suelo/media altura y caminar sus juntas/extremos. Siguen abiertos66 candidatos de pérdida de extremos de otros sitios, la naturalización de otros ríos,14.922 vértices retirados del suavizado, pliegues de dominios protegidos y el pico de Narva,015-45/disco60m,271 labios/juntas anteriores y conducción. La sonda no sustituye la aceptación visual.

Sin commit ni push: entrega visual y carreteras abiertas. Cambios en el worktree asignado; evidencia en este checkpoint y en B, con `MANIFEST.json`. No se escribió memoria Codex compartida.
