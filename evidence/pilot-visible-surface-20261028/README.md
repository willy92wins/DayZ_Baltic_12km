# Visual201: procedencia y extremos verificados

Los201modelos de los cuatro cauces conservan equivalencia exacta de caras:
185744de lecho y4760de agua. No se comparan sólo nubes de vértices.
El consumidor independiente confronta triángulos indexados MLOD y el Roadway
sellado de A; verifica201modelos,4864caras CAP y180880caras de cuerpo.

Las4864caras CAP pertenecen a64filas extra (8por extremo,8extremos). No están
en los NPZde cuerpo. Ahora cada cara desplegada tiene correspondencia con
su fuente y categoría, sin regenerar las alturas CAP.0caras sin mapear.
Normales,UV,texturas renderizadas,oclusiones/transparencia y terreno compilado
completo no quedan aceptados por esta equivalencia geométrica.

25fixtures pasan en fuente; prueba adicional en checkout público antes de commit.
Fable5.1nativo306.469s: SOUND-with-fixes, adjudicados y comprobados. Extracción
80.703s/102.2MB; consumidor45.719s/163.3MB, debajo de600s/2GiB.
El primer consumidor se detuvo por una ruta relativa antes de comparar modelos;
se conserva su fallo y la corrección explícita del contexto de lectura.

Reproducción: usar PythonGIS -I y pasar root, worktree y output NUEVO a
tools/quality/pilot_visible_surface_ev112.py. --preflight sólo verifica entradas.
Los pins relativos se resuelven contra el worktree del productor. No relanzar
las carpetas consumidas. Modelos/NPZ externos por hashes; no se publican mallas.

**Pendiente:** subdivisión común Visual/H/W, agua Visual real, corredor±4m,
capas/pliegues, candidato seco y viabilidad de reparación. El núcleo geométrico
de subdivisión tiene12fixtures iniciales en desarrollo, no integra este commit.
No se ha reparado ni desplegado terreno. C1sinrevisar, RAM/aceptación visual/global
y council ampliado continúan abiertos. Las nueve regresiones no quedan cerradas.

Orientación: los vectores geométricos de las185744caras de lecho ODOL son
los opuestos exactos a los de la fuente. Visual y Roadway desplegados coinciden
en orientación. No se ha aislado si la inversión pertenece al formato/lector/
binarización ni se atribuye un defecto de render. La prueba de superficies
comunes usa geometría no orientada y conserva esta diferencia explícita.
