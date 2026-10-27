# Próxima materialización: anclas verificadas, todavía sin plan de build aprobado

Descubrimiento27-10 durante el piloto seco. No se ha generado ningún modelo.

- La base aceptada de colisión es **river-kit7-contact-only-20261026**, no
  river-kit7-rv-capped-v2 ni rv-overlap. package-kit7-contact-only-20261026/
  verification.json: NINETEEN_GEOMETRY_DELTA_PACKAGE_PASS, PBO
  3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6.
- checkpoint_kit7_contact_repair.py:38-75 conserva fuentes/recibos de
  contact-only y los fallos de las variantes anteriores: anclas con exceso
  de coste/horizontal. El helper cap_stream_collision_v31.py NO está en tools
  vivos; sólo en discarded-cap-experiment y evidencia rejected. No recuperarlo
  como dependencia ni tratar su ausencia como un fallo de instalación.
- build_kit7_contact_only.py:44 usa overlap_stream_collision_v31 con
  --contact-only sobre19modelos; pipeline mide límites72vértices/140caras por
  componente, preserva bbox, materializa y verifica overlay/compilado.
  Sus rutas son consumidas; sólo es evidencia para un adaptador NUEVO.
- continuous_stream_pilot_v31.py:340-389 conserva topología visual/Roadway,
  UV, origen y water_ext. Hay8filas exteriores de CAP por extremo que NO
  están en kit-7-surfaces.npz; deben heredarse exactas del modelo fuente.
- midpoint_stream_collision_v31.py:16 define partition_midpoint(grid,*,
  max_vertices_per_component,max_faces_per_component,vertical_budget=.015,
  horizontal_budget=.002,max_states=20000,timeout_s=60.). El adaptador histórico
  author_kit7_midpoint_collision.py:61 usa .03/.01 y centra el error vertical.
  Debe trazarse al consumidor vigente antes de fijar un nuevo presupuesto;
  no copiar defaults o asumir que una tolerancia distinta está aprobada.
- review_compact_collision_v31.py:19 load lee cuatro LOD y rechaza trailer;
  :51 overlay evalúa cobertura completa, no sólo vértices. La geometría de
  colisión anterior no sirve sin modificar cuando baja el lecho seco visual.

Siguiente unidad: plan revisado para trasladar la nueva Y de orilla a visual y
Roadway mediante correspondencia exacta de XZ/estación, heredando agua/lecho,
CAP exterior, UV/materiales/orígenes. Rehacer colisión con límites vigentes y
comprobar todos los LOD/paquete guardados. Las139piezas kit7 del paquete201
requieren manifiesto explícito; el resto debe permanecer byteexacto.
No reutilizar una colisión flotante ni los scripts de candidatos descartados.
Sólo después pasan las pruebas de agua/forma/bosque, navegación12.5/607 y RAM
seisABBAAB nuevas. No hay permiso mecánico para saltarse esos gates por el PASS
offline. FIFO DayZ directo al estar preparado, sin sondeo/prelease.
