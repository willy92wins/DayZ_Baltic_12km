# EV112 — reparar los contactos nativos del kit7

Continuación de la unidad física autorizada. Estado anterior inmutable: run
28ea0f2f-ff51-4248-ad01-eca78a4300d7,6801puntos,19fallos. Agua, terreno y
Roadway no fallan;18rayos RV llegan al terreno y uno alcanza una cara inferior
a la detectada por Bullet. Los19XZ son vértices exactos del ODOL a la pose usada.
Diagnóstico R/kit7-native-contact-diagnosis-20261026. R es
E:/DayZ-Baltic-Build/shape-repair-20261025.

[HIPÓTESIS] Intersección RV en vértices/aristas compartidas; el algoritmo interno
no está identificado. Hay antecedente nativo positivo U2 en
ev112-rv-vertex-contact-20261025.md. El arreglo se juzgará por el motor.

[DESIGN] Reutilizar overlap_stream_collision_v31.py sobre los19modelos fallidos:
expansión convexa horizontal de semilado1/512m solo en componentes próximos a
los contactos más extremos XZ que conservan el centro del bbox. Masa y número
de componentes constantes; Visual,Memory,Roadway byteexactos. Conservar los
otros182ODOL,config y todo el mundo/agua/terreno/árboles/carreteras byteexactos.
No cambiar puntos, expectativas, tiempos de asentamiento ni tolerancias nativas.

Puertas antes de desplegar: revisión Fable5.1 del plan y operador; MLOD cerrado,
convexo,orientado,union superior completa con límites existentes ±2cm/1cm;
ODOL equivalente al MLOD, poses existentes exactas y no Geometry igual;
coste registrado, máximos por componente72vértices/140caras como referencia C.
Si se supera un máximo no desplegar ni ocultarlo: reducir intervención o
reformular con evidencia. Paquete aislado que sustituye exactamente19entradas;
base y candidato preservados; hashes host y manifiestos ligados a cada corrida.

Validación nativa: nueva calibración vanilla y6801puntos originales. El punto5791
se conserva: expansión podría hacer que RV alcance el techo superior, pero aún
es hipótesis. No modificar el margen para acomodar ese resultado. Si falla,
preservar informe y discriminar geometría antes de una nueva corrección.

Presupuesto: un candidato; autor120s; overlay900s; compile900s; binario900s;
review600s con una ronda de correcciones concretas; calibración180s y sonda1200s,
startup300s cada una. Sin reintentos ciegos. Timeout/error = INCONCLUSO; FAIL
de calidad queda abierto. Cliente,navmesh,FPS y aceptación visual separados.
Solo tras física PASS se retoma la generación de navmesh del kit7.
