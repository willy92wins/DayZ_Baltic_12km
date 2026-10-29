## Adjudicación y precisiones obligatorias antes de C1A

Muse nativo Wonder1.0,30.860s, SOUND-with-fixes/CONVERGE. F1/F2/F4/F5
aceptados; F3 aceptado con alcance de no seguir reparse para leer contenido;
F6 significa un nuevo plan técnico revisado, no pedir otra autorización humana
de producto ya concedida. Postimagen adjudicada por Codex, no nueva review externa.

- F1 [EXACT]: header24B; alturas hasta16777240; índicesu16 hasta16908312;
  countu32LE en16908312; filas desde16908316; cada fila es cero o más pares
  (u32LE longitud>0, bytesASCII), terminados por u32LE0. Final17307629.
  Cap de cadena4096 y bytesrestantes antes de slice; aceptar sólo cero final
  opcional en texto, no cero interior. Countdistinto/estructura/truncamiento =>
  REJECTED_SOURCE_STRUCTURE; límite operativo => INCONCLUSIVE_RESOURCE.
- F2: prefijo propio dayz_baltic_12km_dev/ conserva el camino completo bajo
  stage-kit7-fc-20261026/root; dz/ conserva todo bajo P:/, observado sólo por
  lstat de ancestros y localización, sin lectura de texturas ni fallback.
  Separadores se normalizan a /, comparación de namespace ASCII lower; se guarda
  raw. Otros namespaces UNRESOLVED_NAMESPACE. No búsqueda de basename.
- F3: sólo rutas derivadas de esa tabla/config y los tres configs explícitos.
  Ancestros desde raíz antes del hijo; reparse => BLOCKED_REPARSE, registrar
  metadata sin abrir su destino. Enumeración de herramientas sólo los directorios
  bin Binarize y Mikero/DePboTools/bin, no recursiva,<=256entradas en total.
  No enumeración globalP: ni pruebas que sigan enlaces. SUBST no se equipara a
  symlink; la lectura P: no prueba identidad física actual de un paquete instalado.
- F4: leer config propia antes de localizar referencias; sus rutas de archivos
  se incluyen (con origen config), incluidas worldName/navmesh como localización,
  sin leer WRP poblado/navmesh. Includes de bin/core se registran sin expandir.
- F5:64MiB incluye hash/lectura completa de control y cada texto, cada lectura
  cuenta aunque repita bytes;1MiB/texto salvo config8MiB.16384materiales únicos;
  32768rutas de archivo distintas (no número de usos); conservar por-material
  índices al catálogo de rutas y multiplicidad de usos. Preguard antes de copia.
  SalidaJSON compacta<=4MiB; snapshot privado de tabla de399313B separado dentro
  del mismo límite total de salida. Contenido de configs/vanilla no se publica.
- F6: éxito C1A nunca habilita stage/build. C1B o COMPILE_PROBE_ONLY requiere
  nuevo plan técnico, review y contrato externo verificable, antes de autoría.
  No inventar lectorOPRW ni aceptar un escáner de patrones como altura decodificada.

La reconciliación usa el snapshot de la tabla, no una segunda apertura del control:
cursor independiente comprueba4776filas, nombres y término; coteja los conteos del
reporte y hashes de archivos guardados. No certifica resolución semántica de RVMAT.
