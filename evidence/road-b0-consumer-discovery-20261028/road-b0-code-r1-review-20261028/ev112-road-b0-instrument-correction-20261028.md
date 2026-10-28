# RoadB0 R1 — corrección del instrumento antes de extraer

Estado: PENDIENTE_REVISION. No hay nueva geometría ni cambio de producto.
Primer intento preservado en R/road-b0-discovery-20261028: errorValueError:prefix,
1.734s/716783616bytes antes de CfgConvert o extracción de caras. No repetirlo.

Mecanismo demostrado: catálogo A source-table.json contiene prefix exacto
DZ\\structures\\roads; el nuevo guard esperaba dz minúsculo. R1 exige el
literal instalado observado, manteniendo hash34c1 del PBO. No cambia identidad.
Además build_prism_b3e_ev112.py:65 lanza RuntimeError para TODO rc distinto de0;
el brief de revisión decía erróneamente que base.run_tree permitía rc2. Recibo
se escribe antes del raise. Driver R1 conserva esa excepción y acepta únicamente
rc2 sin stop_reason, dentro de120s/2GiB, reporte INCONCLUSIVE sinerror/3modelos.
Resource/error/missing receipt o reporte siguen rechazados. No cambia el helper.

Código y driver nuevos requieren revisión180s, suite120s. Una extracción R1 en
salida nueva120s/2GiB, sin reintentos; alcance3piezas/config del B0 revisado.
Casos reales de prefijo y receipt2 esperado/error/timeout/retorno contradictorio
incluidos en regresión. R0 intacto, no elevar fallo de instrumento a fallo mapa.
Todo UNKNOWN sigue abierto; no colocar, compilar, desplegar ni arrancar DayZ.
