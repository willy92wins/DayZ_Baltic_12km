# EV112 · continuación del repaso de relieve · 24-10

Trabajo abierto; no es una entrega ni aceptación visual. Piloto actual P en
`visual-pilot-20261024-p`; terreno combinado B en `visual-merged-20261024-b`.

- Junta binaria: I tenía separaciones de hasta 0,000976m al redondear el centro
  de cada modelo en el WRP. J y O verificaron las 35 piezas con error y junta
  3D exactamente cero. La rejilla de autoría de 1/512m hace representable el
  centro de caja en posiciones float32 >8192m. P vuelve a comprobarse.
- P: MLOD pasa continuidad, ambos extremos originales, ausencia de cruces XY,
  componentes de colisión cerrados y negativo de cola. 35 modelos,865 vértices
  nativos. Banco seco propio sobre el soporte; materiales vanilla. Corregidos
  la cresta falsa de la tapa y el segmento final de 0,011m mediante muestreo
  uniforme. En 65.0-0 el optimizador del margen agotó500 iteraciones, pero
  conserva cotas; se guarda como candidato, no como solución óptima probada.
- Diagnóstico visible P:2 aristas del lecho>20° en kit-118 y7 en65.0-0; ninguna
  >45°. Quedan30 aristas nativas expuestas>20°,27 empeoradas respecto a la base.
  Estos números describen la malla; no aceptan su aspecto. Falta la vista.
- Relieve general C:2.903.159 vértices cambiados, escala12m. Orillas, charcas,
  reserva/plataformas/Narva/estructuras, collar del piloto y015-45 exactos;
  clasificación mar/tierra idéntica y cero regresiones del control de aristas
  fuertes.14.922 vértices de collar rechazados se conservan en la base. Las
  zonas excluidas siguen pendientes, no son PASS por exclusión.
- Narva B:37 vértices rebajados dentro de las33celdas retiradas; los21 del
  contrato antiguo quedan exactos.241 muestras del frente quedan a0,25–0,482m
  frente al mar de referencia0,75m. Apoyos laterales exactos; margen mínimo
  medido bajo muro3,531m. Falta comprobar la marea real, no afirmar todos sus
  estados. Contrato antiguo intacto.
- Mezcla B: las tres máscaras son disjuntas,2.904.061 vértices en total.
  Bury0, sin vértices nuevos expuestos;27 heredados. Huella real se verificará
  de nuevo como precondición del staging. El agua PBO no se regenera si es exacta.

Banco leído a22:05UTC aprox.: self none, owner null, runs vacío; ocupado por
sesión ajena LF_CodeLockFix/LF_CodeLockFix_Test en2302 (ya no LFDeathRagdoll).
No se adquirió lease ni se cerró/lanzó DayZ. El mod desplegado sigue siendo
EV112 RuntimeMarginsV2. No WRP ni nuevo despliegue todavía.

Siguiente: terminar lectura binaria P, comparar el compuesto, preparar WRP
aislado y sonda. Stage/compile se han escrito pero aún no ejecutado. El mundo
de sonda sin bosque es técnico; la vista completa exige recolocar el bosque
AE con el delta de suelo y volver a ejecutar sus consumidores. Después de
probar agua/lecho/colisión se podrá extender la representación a otros sitios.
Navmesh, aceptación visual y rendimiento no se acreditan aquí.

Pruebas analíticas:3 del soporte y4 del censo pasaron con el Python GIS -I.
Sin commit: implementación en curso y gates de integración/runtime pendientes.
No hay cambios al árbol principal ni a memoria Codex compartida.
