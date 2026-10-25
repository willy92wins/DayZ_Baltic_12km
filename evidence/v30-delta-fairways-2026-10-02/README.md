# Corrección del delta V30 — 02-10-2026

Estado: **lecturas y tres vistas reales PASS; navmesh nueva guardada y empaquetada, carga/locomoción pendientes**. Véase `navmesh/README.md` y `runtime-45e5b57c/`. Los intentos bloqueados descritos al final son históricos; dos nuevos intentos de consultas de navegación también esperan el banco compartido.
`@DayZ_Baltic_V30` canónico sigue en mundo 69140d41 / NM 24baf069. La corrección
integra Luga 1117b4b1 y excluye el piloto visual de orilla Narva bb270ecc.

## Geometría comprobada

Plan y mecanismo: `plans/v30-delta-fairways.md`, BALTIC-013. Fuente OSM completa
de Gran/Pequeño Neva, conector way/34348577 y enlace way/78518216. La boca seca
del Pequeño Neva se debía a falta de cobertura; profundizar solo el agua existente
no la abría. Anchura media del polígono y perfil de fondo no garantizaban el
canal útil. Discriminadores previos en `../v30-shore-pilot-2026-10-02/delta-audit/`.

La primera evaluación paró antes de guardar por conflicto con una reserva de
puente. Se corrigió el plan según la fase 2 aprobada: excavar solo el cauce
dentro de la reserva, conservando accesos secos y plataformas fuera de ella.
No se ha colocado ese puente ni se acepta circulación en ese cruce.

- NPZ `a84dfff053523b94717b2068a96845193d01a21f0ea7ff01e0f9111280630081`;
  ASC `64d4f160b963c28b519a50c9c29564dbe9727facabf7b52d83970eef5b8e6eb4`,
  en `E:/DayZ-Baltic-Build/v30-delta-candidate/`, relectura float32 exacta.
- 924 vértices cambiados respecto a Luga, 358 nuevos de agua. 39 cambios dentro
  de la reserva, incluidos 13 vértices secos de plataforma convertidos a cauce.
  Rebaje máximo 8,088286 m allí. Narva, plataformas fuera de reserva, accesos
  secos y alturas fuera de 36 m de los ejes, intactos; planos pond idénticos.
- Cuatro corredores completos con extremos redondeados: 1.237 caras antes de
  deduplicar solapes; cero fallos, calado mínimo 3,04999995 m con mar a 0,50 m.
  Plano afín, muestreador independiente y obstáculo somero negativo verificados.
- Anchura visible muestreada a bajamar: mínimos 50,25/49,75 m en los dos brazos
  y 45,50 m en el enlace al tronco. Medición cada ≤1 m y transversal cada 0,25 m;
  no se presenta como extremo continuo. Ensanches y bocas abiertos conservados.
- Ningún componente seco preexistente desaparece. La apertura separa una isla
  de 45.828 m², núcleo (8364,10200) a 1,40 m intacto. Ver gráfico antes/después.
  La comprobación final distingue agua interior elevada: 188→189 componentes
  secos en la malla, `island-components-water-aware.json`. Los 61→62 del
  productor/gráfico inicial solo separaban terreno por encima del mar; no
  representaban las islas de lagos interiores. No hubo cambio de alturas.
- Terreno PASS; carreteras PASS sobre las mismas 76.536 estaciones anteriores,
  con la máscara de elegibilidad original. Los 19 corredores retenidos también
  pasan; Luga mínimo 3,030104 m. Los taludes mixtos locales >35° pasan de 118 a
  113; quedan escarpes, incluido el cruce previsto. No aceptación visual global.

## Paquete

1.024 tiles regenerados, 1 m/px; cuatro superficies y 4.775 materiales completos.
WRP bruto `3e7d298f` con alturas exactas. Objetos/poses idénticos al V30 previo:
17.622 piezas de agua y nueve tramos de puente. El PBO compilado contiene
6.827 entradas, todas idénticas al árbol compilado; config/materiales estables.

- Mod aislado: `P:/Mods/@DayZ_Baltic_DeltaV30`.
- Mundo: `8b2d404a72f30150c62463e85868360cc9fa34f610aaca6719255154f3fa9ef1`.
- WRP compilado: `daca4196fb368c1a8b8176aa9db560806010c62630bc8e74fe58b6b2288b220c`.
- Agua: `e9b52b8c4fc07df8bc4854dcd9e144e16875af8006221f16efaa6ab95de56681`.
- NM heredada V29 `eb0f131e`, **obsoleta para este terreno**. Sirve para arrancar
  la previsualización; generar la propia usando el WRP anterior antes de probar
  navegación. Reempaquetar por paridad de entradas, sin recompilar el mundo.

## Comprobación preparada en el motor

Misión `BalticV30DeltaV1.BalticTrial`, bytes idénticos en DayZServer/mpmissions.
1.678 puntos congelados de los extremos de intersección corredor/triángulo,
más cuatro controles secos: 1.682 lecturas. Tres sitios de cámara desde jugador,
90 s cada uno, sin camera_set. El log requiere QBEGIN, todas las identidades,
QEND y END3; tolerancia de altura 2 cm, calado nominal ≥2,99 m y suelo seco
≥0,25 m sobre pleamar. El linter pasa un archivo; no prueba compilación del motor.

`tools/playtest/verify_delta_water_v30.py` pasa controles sintéticos independientes
y rechaza 17 negativos. El primer recibo de 15 negativos tenía una sustitución
que comprobaba otro terminal; corregido antes del run y conservado como histórico.
El resultado vigente es `query-verifier-controls-v2.json`. Ningún positivo
sintético se etiqueta como aceptación del juego.

Tres intentos de lanzamiento no arrancaron, con esperas de 20/45/45 s:
banco compartido ocupado (takeover_required).
No se interviene en el run ajeno. Pendientes lectura real, revisión visual,
navmesh nueva y desplazamiento físico; 80–100 jugadores sigue pospuesto al mapeado.

Checkpoint de código/evidencia `32eb24c`, bundle completo verificado en E:.
`checkpoint-runtime-blocked.json` conserva el tercer resultado y la consulta
de las 14:20 UTC: sin lease/run propio, sin posición en cola, escritorio liberado.
