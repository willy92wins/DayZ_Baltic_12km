# EV112 · sonda compilada y soporte del bosque · 24-10

Trabajo abierto, bloqueado para motor por una prueba ajena con actividad humana.
Esto sustituye el estado pendiente de build del checkpoint A, no sus hallazgos.

## Candidato listo para sonda

- Piloto **P**, relieve general **C**, Narva **B** y mezcla **B** conservan sus
  identidades del checkpoint A. La lectura binaria de P termina en BINARY_PASS:
  35 modelos, error geométrico y separación 3D de juntas exactamente cero.
- Compilado el mundo **sin bosque** de la sonda. Lectura OPRW v32: 17.900 objetos,
  mismas identidades y poses que el WRP editable; máximo delta de ejes nativos
  9,54e-7, poses de las 35 piezas nuevas exactas. Negativos de pieza eliminada,
  añadida y trasladada rechazados. El lector de objetos es heurístico; no lee
  las alturas comprimidas. La sonda contrasta alturas contra el terreno final.
- Empaquetado desde el PBO desplegado pineado: 6.825 entradas byte-idénticas;
  solo cambian baltic_trial.wrp y config.bin. Único delta de config:
  requiredAddons añade Baltic_Stream_Pilot.
- Instalado **P:/Mods/@DayZ_Baltic_EV112_VisualProbeP** en carpeta nueva:
  mundo c43e68fd1db82ccd5bb8a91a9a8c5de0e7d5435edaa56e75b1d170efe7bfeb6d;
  piloto b2c1799d7edb7adf2deb55f3f3b76e0c0c82f608bcf1673f47074da93c6eeea1;
  agua 97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43.
  RuntimeMarginsV2 no se sobrescribe. No se lanzó esta sonda.
- Misión desplegada BalticVisualProbeV1.BalticTrial: **786 puntos** (4 extremos
  originales, 96 centros, 192 bancos secos, 99 controles de juntas, 364 puntos
  de relieve, 25 frente Narva, 3 mar de referencia y 3 apoyos). Carga cada zona,
  retiene objetos y espera 100ms entre fotogramas antes de medir. Registra suelo,
  mar/charca, nivel/profundidad, Roadway, RaycastRV Geom y RayCastBullet BUILDING
  con GetShapeName. Todo se lee en servidor, sin RPC ni estado de cliente.
- El primer punto de referencia marina elegido sobre tierra se sustituyó
  antes de lanzar. Las tres referencias finales tienen suelo < -0,5m y no están
  en charca. Se añadió el frente a 5cm de la cara de presa (z=6944,09).
- init.c final 9bbac717cbebf0a85b6282fdbefdb70d8400d668b1fac820594b2a0475d6cf42.
  Linter estructural: 1 archivo, PASS, cero errores/avisos. No es compilación
  Enforce en motor. Evaluador: 3 tests analíticos PASS; incluye controles de
  agua, alturas, colisión/identidad equivocadas y logs incompletos/corruptos.

## Bosque preparado, pendiente de integración completa

- Stage A recoloca la vegetación por la **raíz original** T-M*bc, según la
  definición real forest_v31.transforms:678-710; usar el centro de caja era
  incorrecto en pendiente. Admite los modelos plants_bliss de la referencia.
- G4 de soporte y separación nativa pasa para 2.561.015 elementos, pero el
  margen del nuevo lecho falla en 74 usando solo el cuerpo. Al leer el LOD
  visual guardado completo, con tapas, los casos son **93**. No se excluyen
  las tapas para obtener PASS.
- Stage B retira solo esos 93 por el margen ya vigente base_radius_plan*scale
  +0,5m. Todos los demás registros, alturas, materiales y config se conservan
  byte por byte frente a Stage A. Tras releer el artefacto: 2.560.922 elementos,
  cero fallos de raíz/apoyo/inclinación/agua nativa/franja marina/agua del piloto/
  margen del lecho completo. Error máximo raíz-suelo 0,000313m. Alcance: soporte
  y separación de agua/lecho del WRP fuente, no PASS de todo el bosque.
- Stage B WRP 19e1a63711080d4214b1d8aef5de874d873fe00d128076e5f2092b65595375e9
  en stage-visual-forest-20261024-b. Aún sin compilar ni desplegar. La retirada
  cambia XY/densidad/contexto: **G2/G3/G8 afectados no están revalidados**.
  Tampoco se acredita navmesh ni rendimiento.

## Extremos y relieve todavía abiertos

Inventariados 102 extremos de 51 sitios (49 construidos). La base no cubre 70;
P recupera sus cuatro y quedan 66 candidatos de pérdida por revisar. Son
medidas de puntos originales mojados, no prueba de conexión al receptor ni
permiso para enlazar al cauce más cercano. Dos sitios no están construidos:
67.0-0 y98.0-2. No se ha extendido el piloto a los demás sitios.

Sigue vigente el diagnóstico P: 30 aristas nativas expuestas >20 grados,
27 empeoradas respecto a la base, y 9 aristas visibles del lecho >20 grados.
No hay umbral estético inventado ni aceptación visual. Los 14.922 vértices
retirados del suavizado general, dominios protegidos (incluido el pico de Narva),
015-45 y las 271 juntas antiguas siguen abiertos según el alcance anterior.

## Reanudar

1. Releer session_status. A22:42UTC del23-10 (00:42 del24-10 local): self none,
   banco ocupado por Claude LF_CodeLockFix, run391a8224-55a8-4a45-8785-c8bc1c62cc10,
   con usuario probando. El run009de5fe del picker anterior ya se sustituyó.
   No se adquirió lease, no se lanzó ni se cerró ningún DayZ en esta continuación.
2. Con banco libre, usar launch-request.json, preflight=false, mediante la tool
   dayz_test_run. La misión requiere ruta ABSOLUTA; el nombre corto fue rechazado
   mission_not_allowed. El preflight final con ruta absoluta supera validación,
   pero informa box_busy. No takeover. Adoptar solo el run propio por el protocolo.
3. Archivar log nuevo baltic_visual_probe_v1.log del perfil devuelto por la tool;
   exigir fin completo y hash actual de PBOs/misión. Ejecutar
   tools/water/eval_visual_probe_v31.py con probe-visual-20261024-b/points.json.
   Los resultados en motor aún no existen. Si no hay agua/lecho/colisión correctos,
   corregir antes de expandir. La sonda de servidor no prueba caminar en cliente.
4. Revalidar densidad/contextos/bosque/pintado afectados sobre la huella de agua
   propia; compilar/leer/empaquetar la vista completa solo con esos gates cerrados.
   Después: vista desde suelo y media altura, corrección de encuentros restantes,
   aprobación visual y expansión con extremos/receptores explícitos.

Sin commit: integración y motor pendientes; no se publica un cierre parcial.
Cambios en el worktree propio y artefactos aislados, sin modificar la parada
ajena del árbol principal ni memoria Codex compartida. Todos los procesos de
build/revisión propios terminaron. Una petición de parada de staging propio
no encontró ya el PID coincidente y no detuvo ningún proceso.
