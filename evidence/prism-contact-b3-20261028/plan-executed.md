# B3: piloto de continuidad de contacto sin aumentar geometría

Estado: REVISADO_PARA_IMPLEMENTACION_OFFLINE (Fable5.1,183.437s; adjudicación
en R/prism-contact-b3-plan-review-20261028/adjudication.md). Codex ejecutor/integrador.
Consumidor: candidato MLOD guardado y verificador independiente; sólo después,
un plan binario/nativo. P2/P7/P9/P10/P14; no cierra agua ni calidad visual.

## Evidencia e hipótesis

R=E:/DayZ-Baltic-Build/shape-repair-20261025; W=este worktree.
B2 está cerrado/publicado14f259a. No repetir misión, replay ni preparadores.
R/collision-b2-neighbourhood-discovery-20261028/report.json: IDs700/723, tres
rondas,12 consultas RV centrales con objetos vacíos y96 vecinas con el piloto.
Los108 Bullet (centrales+vecinas) devuelven el piloto. Residuo máximo RV central
frente a SurfaceY0.000087m. Esto NO identifica terreno ni una grieta geométrica.
Original2658 conserva47FAIL21inciertos; los centrales no se desplazan.

[HIPÓTESIS] Sensibilidad de RV a contactos exactos sobre vértices compartidos.
Antecedentes nativos positivos U2/kit7 en ev112-rv-vertex-contact-20261025.md y
ev112-kit7-rv-contact-20261026.md; el mecanismo interno no se da por demostrado.
Esta unidad prepara un candidato que cubra esos contactos por interiores de
caras, sin tocar agua/Visual/Roadway ni declarar reparado el resultado nativo.

## Restricción de coste y cambio de operador

[EXACT] overlap_stream_collision_v31.py:28 expanded_component hace Minkowski
horizontal; :43 selected_components(...,contact_only=True) selecciona por huella.
Descubrimiento R/collision-b3-contact-eligibility-20261028/report.json:12 prismas
seleccionados, bbox exacto, pero Minkowski sube6→18 vértices y8→32 caras por
componente máximo. No aplicar esa variante: el plan de materialización conserva
el presupuesto geométrico (ev112-dry-bank-mlod-materialization-20261027.md:55-62).

[DESIGN] Para la familia comprobable de prismas triangulares de6 puntos/8 caras,
ampliar sólo su proyección triangular, conservando tres esquinas, caras e índices.
No usar esto en componentes generales ni cambiar silenciosamente su familia.
Sea c el centroide XZ de las tres esquinas superiores, r su máximo radio a c,
delta=1/512m fijo, lambda=1+delta/r. XZ nuevo=c+lambda*(XZ viejo-c). Evaluar Y
en el MISMO plano superior original; la base sigue ese plano menos180/512m.
La homotecia contiene el triángulo original y conserva el plano de contacto en
su dominio; desplazamiento XZ máximo delta. En aritmética exacta, el prisma
original queda contenido por el ampliado. Medir de nuevo tras guardar float32;
la demostración analítica no sustituye la comprobación del archivo.

## Fuentes y alcance exacto

Fuente única actual: R/dry-road-mlod-candidate-r2-20261028/source/
baltic_stream_pilot/cs_kit_118_0000.p3d,
SHA d13069d5ec2816cdacc90891a83e5f92f517c4c33703380d534d3f7538baddef.
Origen MLOD8262,7,8934; no confundir con la traslación ODOL8257.989258,7.396484,8928.40625.
Targets salen de expected.XZ originales700/723 en R/dry-road-full-native-20261028/
probe/result.json SHA e717a124c38ff61b4af932793541ab78b7dfb703aea946d497c246b59ee33390.
700 conserva dry y723 conserva wet. El alcance no es exclusivamente seco:
Geometry cambia en el contacto723, pero sus superficies Visual/Roadway/agua
permanecen byteexactas y no se reclasifica su fallo de agua original.
Seleccionar por el operador existente y verificar los12 identificadores del
descubrimiento. No añadir anclas bbox ni mover puntos, poses o modelos vecinos.

[EXACT] dry_road_mlod_ev112.py:27 patch_lod verifica P3DM, cabecera28bytes,
puntos de16bytes y normales de12bytes. Ese parche sólo admiteY: NO usarlo como
si aceptaseXYZ. [DESIGN] un parche específico de XYZ y normales de Geometry,
con comprobación de cabecera, bytes originales y límites; copiar todo lo demás.
Leer el archivo guardado por review_compact_collision_v31.load (:17) antes de
aceptar. Visual,Memory,Roadway y todos los bytes no autorizados quedan exactos.
No regenerar terreno, agua, carretera, árboles, WRP, config ni otros200modelos.

## Criterios mecánicos y pruebas

El verificador recibe source/candidate/targets, reconstruye selección y planos
desde source; no recibe máscaras o booleanos de éxito del autor.
- Fuente, targets y dependencias por SHA; salida nueva; ninguna entrada cambia.
- Familia6/8 y emparejamiento techo/base inequívocos; componentes cerrados,
  convexos, winding válido, normales correctas; toda cara/punto asignado una vez.
- Mismos conteos de componentes/puntos/caras y masa por punto; bbox Geometry
  min/max exacto. Fuera de los12 componentes, XYZ/normales exactos.
- Releer float32: esquinas antiguas contenidas en proyección nueva y techo/base
  originales conservados dentro de1e-6m (error aritmético, no tolerancia física).
- Contactos700/723 dentro estrictamente de al menos una cara superior ampliada,
  no sólo en su borde; reportar distancia firmada en metros y ULP mundial.
  No convertir un interior MLOD en certeza de interior compilado/motor.
- Exigir también interior estricto al sumar origen y redondear XZ a float32
  mundial. Es un discriminador aritmético explícito, no el marco del motor.
  No imponer 2ULP como condición necesaria: el antecedente nativo U1 aceptó
  cuatro contactos con margen menor de1ULP (plan de contacto25-10:54-57).
- Mantener1e-6m para plano; reportar además el error de redondeo previsto por
  los ULP locales y la pendiente. No sustituir el límite por uno más permisivo.
- Normales seleccionadas recalculadas desde XYZ guardadas (error<=1e-6),
  pues la cuantización puede cambiar el plano/normal. Resto de normales exacto.
  Los solapes entre prismas vecinos son intencionales; convexidad no significa
  disjunción. La numeración de componente del motor NO se presupone.
- Overlay independiente contra Visual guardado, con los límites ya vigentes
  ±0.02m vertical y0.01m horizontal, cobertura completa, sin ampliarlos.
- Datos de agua, extremos y todos los otrosLOD byteexactos.

Fixtures independientes: prisma plano y prismas inclinados de plano conocido;
control idéntico conserva identidad pero no gana interior en contacto de esquina;
mutantes de cara invertida, cara retirada, punto externo al dominio permitido,
Y de techo alterada, normal incorrecta, cambio enVisual/Roadway y target extra.
Un umbral fallido => REJECTED_OFFLINE; dato faltante/timeout => INCONCLUSO.
OFFLINE_CANDIDATE_ONLY exige todos los criterios. No representa PASS del mapa.
Añadir mutante de contracción y de desplazamiento XZ fuera del operador.
El centroide XZ de techo y base es idéntico: no es un mutante observable.
verify_dry_road_mlod_ev112.py NO es consumidor de B3 (volumen/rejilla antiguos);
no modificarlo ni adaptarlo a este candidato.

## Presupuesto y continuación

Una revisión de plan600s, una implementación con revisión independiente600s,
tests120s, autor60s/2GiB, consumidor/overlay180s/2GiB. Un candidato, como máximo
una corrección por repro de implementación; no ajustar delta, límites o targets.
Si una restricción del diseño no converge, conservar rechazo y cambiar de hipótesis.
No hay presupuesto de DayZ/build en esta unidad. Posteriormente: compilar en
salida nueva, verificar ODOL/poses/agua y que los centrales conservados resultan
interiores tras cuantización; sólo entonces diseñar revisión/nativa FIFO.

Es un piloto del operador procedural para prismas elegibles, no dos parches
manuales ni solución de todas las juntas. La extensión al generador y censo de
todo el mapa exige el resultado nativo, controles y presupuesto global. RAM,
cliente, navegación, visual, agua, C1 y council ampliado siguen pendientes.
