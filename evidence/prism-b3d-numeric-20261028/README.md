# B3D — candidato MLOD numérico validado offline

El archivo guardado cumple las puertas de esta unidad. Resultado:
**OFFLINE_CANDIDATE_ONLY**. No se ha binarizado, empaquetado ni ejecutado en DayZ.
La identidad exacta de los marcos es un cálculo con centro y pose fijados;
no certifica el centro que producirá una compilación futura ni el motor.

## Resultado reproducible

- Candidato `f2b7018bea6a692ef5964bae4894172e0a73eeabe8be55ea68244a774cb7e634`.
- Contrato `b44553ee67478e597511e6a075452b07858d6f2457f9a035c3f1101d4bdbf31a`.
- 17 valores Y modificados; 50 caras/normales incidentes. Ningún X/Z cambiado.
- 9.120 puntos, 12.160 caras y 1.520 componentes conservados.
- 4.560 pares de grosor EXACTO 180/512 en el MLOD, mediante resta racional.
- Error máximo de plano/base 2.7824641812834727e-8 m, límite 1e-6 m.
- Cajas, partes protegidas de Geometry y otros LOD conservados exactamente.
- Overlay completo de 1.520 triángulos de lecho y 1.520 techos: 18.842 pares,
  sin área faltante/excedente; error entre -0.0007552973696061116 y
  +0.00017500188924568505 m. Límites originales ±0.02 m / 0.01 m.
- 700 seco y 723 mojado conservan sus coordenadas y márgenes X/Z originales.
  Márgenes mundiales float32: 0.0006409918344828816 y 0.0005226926610255875 m.

Autor y consumidor son procesos separados; el consumidor relee el archivo y
no importa ni el autor ni el solver B3C. Verifica invariantes geométricas y
bytes protegidos, no sólo la coincidencia con el testigo del autor.
Autor: 3.25 s; consumidor: 10.063 s de proceso, pico residente 438.72 MB.

## Revisión y pruebas

Fable 5.1 nativo revisó el plan (151.5 s) y el código (135.25 s). Se conservan
dictámenes, identidad, adjudicaciones y la cápsula del código revisado.
Una primera revisión de código no lanzó el modelo por error del wrapper;
la siguiente agotó 300.032 s sin dictamen. No se les atribuye aprobación.
La única recuperación acotada entregó SOUND-with-fixes. Se corrigieron en un
grupo la clasificación de errores internos, la escritura pendiente antes de
promover el candidato y las guardas finales de caras/normales. El mutante de
normal usa nextafter y demuestra cambio de bytes. No se redujo ninguna tolerancia.

35 tests finales PASS: 27 sobre archivos guardados y 8 de los CLI reales.
Cubren cambios no autorizados, grosor no exacto, discrepancia de marcos,
normales, controles, cajas, overlay, binding, entradas malformadas y reutilización
de salidas. No se afirma cobertura exhaustiva de todas las ramas.

## Límites y siguiente puerta

B3B permanece REJECTED_BINARY; B3C permanece FEASIBILITY_ONLY. Este archivo
nuevo no reinterpreta esos recibos. La corrección documental del grosor de
c769 (20/36 pares seleccionados exactos) permanece vigente; B3D acredita
4.560/4.560 para su nuevo archivo, no para el histórico.

Se requiere un plan binario separado, revisión y preflight fresco antes de
compilar. Debe comprobar el ODOL guardado, otros LOD, caras orientadas, centro,
pose y contactos reales del binario antes de proponer paquete o prueba nativa.
No reutilizar los preparadores/consumidores consumidos de B3B/B3C/B3D.

Original2658 conserva 47 FAIL y 21 inciertos. Nav8 conserva 607 PASS históricos.
RAM, referente independiente de agua, nueve regresiones visuales y aceptación
global siguen abiertos. C1 continúa SIN REVISAR. Sin run ni lease DayZ.

Los modelos y binarios permanecen fuera del repositorio público; sus hashes
permiten vincular la evidencia. El manifiesto fija cada archivo de esta unidad.
