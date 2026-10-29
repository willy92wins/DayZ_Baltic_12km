# Carreteras B2 — ensayo aislado del consumidor de objetos WRP

Estado: BORRADOR_PENDIENTE_DE_REVISION; no autoriza todavía autoría ni motor.
Petición viva: preparar carreteras mientras continúan pruebas de orillas.
P5/P6/P9/P10/P11: pavimento y accesos completos, navegación conservada; no
introduce puentes por proximidad ni modifica la intención de agua del producto.

## Hipótesis y fuentes

[EXACT] B0/B1 conservan caras Visual/Roadway instaladas de asf1_25, asf2_25 y
asf1_10 100, centro local distinto en la curva. Reutilizar archivos por sus hashes
de evidence/road-b1-source-discovery-20261029; no repetir catálogo/extracción.
La tabla compilada actual no contiene esas piezas. Shapes roads.tv4s existe;
su esquema ALB1 y RoadNetwork siguen sin decodificar ni descartar.

[EXACT] tools/terrain/wrp0wzd.py:58 escribe fuente 0WZD;
tools/terrain/package_visual_pilot_ev112.py:22 lee tabla OPRW heurística con
ancla y comprobaciones. No ejecutar sus CLI históricos ni suponer sus límites
de cantidad compatibles con 2.578.398 objetos; revisar lector antes de reutilizar.
tools/terrain/package_visual_forest_ev112.py:117 aplica una hipótesis de centro
al bosque; NO certifica el pivote de una carretera.

[EXACT] P:/scripts/3_Game/entities/object.c:873 declara ModelToWorld(vector);
P:/scripts/3_Game/global/game.c:930 declara GetObjectsAtPosition3D y :718
ObjectModelToWorld. Son anclas de fuente desempaquetada, NO identidad instalada.
Antes de implementar sonda, verificar las mismas firmas en scripts.pbo fijado
del motor real. GetModelName usa GetType y configuración; su utilidad para un
objeto vial estático aún no está demostrada. No inventar una clase de carretera.

## Unidad propuesta [DESIGN]

1. Fijar referencia original/compilada, herramientas, tres modelos instalados y
   tablas B0. Escribir receta independiente con tres instancias: recta identidad,
   recta girada 90 grados y curva. Explicitar las dos hipótesis de centro frente
   a origen y publicar predicciones distintas, sin seleccionar la que mejor ajuste.
2. Ensayo en mundo/carpeta nuevos, elevado sobre el suelo en un banco aislado:
   sólo tres objetos añadidos; terreno, agua, reservas, objetos previos y P10
   exactos. No pavimentado de producción. Resolver IDs y nombre de modelo por
   censo completo del origen, sin colisión; conservar cada cara y material.
3. Leer fuente y binario guardados. Probar conteos, poses y huellas mundiales
   completas Visual/Roadway, incluidos arcenes y extremos. Las dos hipótesis
   deben seguir siendo distinguibles tras serialización. Si no, no lanzar.
4. Sonda nativa separada, plan y presupuesto propios antes de admisión: identificar
   cada instancia inequívocamente en el vecindario y registrar origen y bases
   transformadas mediante el consumidor del motor, además de impactos sobre
   caras interiores y fuera de la huella. No elegir objeto por el personaje ni
   por el más cercano. Si el motor no expone identidad suficiente, INCONCLUSIVE.
   La lectura del WRP y su transformación en Python no constituyen ese oráculo.
5. Sólo después de certificar consumidor/pivote, preparar huella y accesos en
   tramo49 (5296,6000), cruce49/301, Narva71 y extremo kit118/cadena76.
   Censo carretera-agua independiente de lista de puentes. No colocar esas
   carreteras dentro de este ensayo. El ancho útil y conducción siguen abiertos.

## Gates y presupuesto propuestos

Revisión180s antes de implementar. Unidad offline inicial120s/2GiB para receta,
predicciones y fixtures; no build ni DayZ en esa primera unidad. Antes del build
se debe cerrar un plan específico con presupuesto y preflight actuales.
Conservar cross0.03m/grade0.065/chord0.03m y P9 1m/.95m/24m; no derivar ancho útil
de bbox ni usar la antigua banda8m como cobertura de piezas12/9m.

Positivos y negativos: identidad/rotación conocida, centro desplazado, curva con
bbox mayor que huella, inversión de matriz, eje intercambiado, esquina/arcén
fuera del antiguo buffer, accesos completos y candidato sin Roadway. No declarar
convención certificada con fixtures. Sin pruebas de conducción/FPS/RAM todavía.

Salida inicial permitida: RECIPE_HYPOTHESES_READY o INCONCLUSIVE_DISCOVERY;
salida nativa futura por instancia, con campos verificados/asumidos/no observados.
El ensayo WRP_OBJECT no afirma implementar ni validar RoadNetwork/ALB1.
