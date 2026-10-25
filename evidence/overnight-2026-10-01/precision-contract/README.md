# Contrato acotado de precisión nativa

Implementado conforme al paso2 de plans/overnight-2026-10-01.md.
El consumidor ejecutable es prepare_foundation_package.py, que propaga
explícitamente --precision-contract native-v9-micrometre. El valor por defecto
sigue siendo strict. build_foundation_package.ps1 rechaza contratos ausentes
o mezclados. La reapertura aún debe demostrar persistencia exacta entre
exportaciones; esta opción no la sustituye.

Solo admite hasta1e-6m en última fila/columna del terreno y en Y de los dos
IDs16777218/16777219. Todo el interior y las demás componentes/objetos conservan
igualdad exacta, al igual que materiales/cabecera y los controles de agua.
El límite es un criterio geométrico explícito, seis millones de veces menor
que la celda de6m; no es una explicación demostrada del mecanismo de TB.

Prueba mediante la CLI real: tests/test_foundation_native_precision.py con
GIS Python. 16 casos PASS_CONTROLS en controls-v1/summary.json, con fuentes,
mutantes y stdout/stderr. Se conserva FAIL del contrato estricto y FAIL al
verificar alcance completo sin agua. El control sintético exacto es solo un
fixture del verificador, nunca un export nativo ni material desplegable.
Python compila; parser PowerShell sin errores; git diff --check sin errores.

La base V9 y la exportación nativa siguen pendientes de reapertura efectiva,
agua integrada, paquete compilado y consumidores del motor. No hay PASS de
producto por estos controles ni por la tolerancia nueva.
