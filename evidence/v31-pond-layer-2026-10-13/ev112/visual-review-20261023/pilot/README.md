# Piloto continuo y relieve — trabajo abierto

Guillermo aprobó el piloto con geometría propia y materiales vanilla, y amplió
explícitamente el repaso de pirámides a todo el terreno. No hay aceptación visual.

## Estado comprobado

- Inventario global de las tres familias de aristas: 18.757 aristas secas >20°,
  16.154 incidentes en la máscara de terreno modificada por el kit. No son bugs
  individuales ni un umbral estético. Cuatro pruebas analíticas pasan, incluido
  un pliegue entre celdas que la diagonal interior no detectaría.
- Candidato I: kit-118 y 65.0-0, este último NE/SW con once codos anteriores.
  35 modelos MLOD propios; lecho, lámina visual, water_ext y colisión cerrada.
  Conserva los extremos mojados originales y termina en la siguiente celda.
- Revisión del MLOD: sin inversiones de la cinta, agua conectada y extremos
  presentes; eliminar los modelos de la cola da el fallo esperado conservando
  agua en el cuerpo. Esto NO prueba agua/colisión en motor.
- 865 vértices de soporte modificados; reserva, plataformas, Narva, puentes,
  presa, pasos y esquinas de estanques existentes quedan protegidos.
- Se retiran 81 celdas inactivas de envolvente y 27 de cobertura dentro del piloto;
  la huella REAL resultante es idéntica en plane, field y visible. Bury cambia cero
  vértices y no crea bordes expuestos. La envolvente cambia deliberadamente.
- AddonBuilder terminó con Build Successful. Sus modelos son ODOL56: el lector
  instalado de ODOL54 no los admite. Verificación binaria en curso con el lector
  local v56 de review_g3, sin instalarlo y añadiendo la comprobación de índices
  de secciones que su revisión identificó como ausente.

## Límites que bloquean la integración

La geometría de soporte nativa reduce el total local >20°, pero aparecen aristas
nuevas y algunas peores (hasta57,23°). Incluye triángulos enterrados bajo el lecho:
falta medir el compuesto VISIBLE terreno+malla y corregir lo que quede expuesto.
No ocultar este resultado tras el PASS limitado del MLOD. Candidatos B/C fallaron
por pliegues y/o juntas; D solo pasó geometría, pero alteraba15 celdas de huella.
E falló por NaN de una entrada al max de celdas; F/G/H localizaron obstáculos
en los finales/dominio anterior. I corrige entrada NaN, cap natural y envolvente
inactiva. Los intentos quedan preservados en E:; ninguno se desplegó.

Último banco: self none, sin runs propios, procesos ajenos LFDeathRagdoll en2302.
No se ha tomado lease ni cerrado proceso. Runtime, WRP del piloto y visita aún
pendientes. Narva mar al pie de presa, relieve general, extensión al resto del
mapa y consumidores globales siguen abiertos. Sin FPS ni aceptación EV112.

Artefactos completos: E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/visual-pilot-20261023-i/.
