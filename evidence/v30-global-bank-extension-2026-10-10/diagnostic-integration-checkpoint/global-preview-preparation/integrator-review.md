# Revisión del integrador — preparación de la preview seca global

Revisión de fuente, 10-10-2026. Estado: **preparado de forma condicional; sin stage, build ni aceptación del candidato**.

Se cotejaron `global_dry_build_common.py`, `stage.py`, `build_surface.py`, `package.py`, el consumidor OPRW y las pruebas de admisión con el contrato emitido por el consumidor V2. La admisión exige el estado PASS y las ocho puertas exactas, candidato y recibo REC fijados, procedencia EV95 y readset inicial/final idéntico. El recibo actual de error no habilita esta ruta.

El stage conserva el esquema NPZ y todas las matrices distintas de alturas frente a EV95 y EV82 B; exige igualdad de objetos/materiales WRP y copia P/F exactamente. La superficie calcula de nuevo la huella completa REC frente a B y sus teselas con margen, sin reutilizar las 540 teselas de EV95. El paquete sustituye solamente el WRP y las PAA seleccionadas dentro de las 6.827 entradas de B, con agua idéntica y destino separado. El consumidor OPRW prueba identidad entre compilación, paquete y despliegue; no decodifica ni certifica las alturas nativas.

Las seis pruebas de admisión y la comprobación del runner fueron ejecutadas por el autor. Esta revisión no las convierte en una prueba positiva de build: faltan el PASS real de V2, stage, generación, compilación, empaquetado, mips y lectura del motor. Ejecutar con `PYTHONOPTIMIZE=0`, pues los scripts heredados usan `assert`; el entorno GIS aprobado ya se invoca así. La RAM exigida por V2 sigue siendo 9 GiB libres y no se reduce para lanzar una preview.

No se identificó un bloqueo de integración adicional en la ruta revisada. El banco ocupado, la admisión de memoria y el consumidor V2 pendiente siguen bloqueando la ejecución. Una preview construida tampoco cerraría los recuadros grises ni la aceptación del mapa.
