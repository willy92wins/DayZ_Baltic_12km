# Un ejemplo acotado de residuo por recenter MLOD→ODOL→WRP

**Alcance:** una sola esquina del cell `(row=1425,col=1418)`, objeto WRP `16806259`; solo archivos estáticos. No es readback del motor ni evidencia de que toda la cobertura tenga la misma causa.

## Identidad y observación

- P en la esquina: `2.9250000000000003` (float64), según `coverage-precision-diagnostic.md` (sección del ejemplo `(1425,1418)`).
- MLOD `E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/compile/source/baltic_water_v30/globalvis_16806259.p3d`, SHA256 `ac09e41c3c784ab9b0cafc5b508a6f9c87f4ea59ca2c3999e61646b1a498c379`.
- ODOL `E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30/globalvis_16806259.p3d`, SHA256 `2ec236215ec543973091a5f36892fa0fe7a9abedc6227395b7f105223732f5f6`.
- `compiled-checks.jsonl` SHA256 `9d7bc7cf0e366893248570681510b0b95eece312d305db0e58dcd55c648abbf8`; su fila `object_id=16806259` da centro ODOL Y `−0.15000000596046448`, posición WRP Y `2.7749998569488525` y `visible_field_error_m=1.3709068324985196e−7`.
- WRP histórico de paquete `E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp`, SHA256 `770359d0e4f3a37b5a2103db859a562530ee611123c70bce682399108adac0f8`. Comparado con el WRP fuente B `E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp`, SHA256 `3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6`: el registro completo de id 16806259 es byte-identico en ambos (SHA256 `e2b21f2db4d4dd175c4eda867b702e43a1f0dec5e013afa50d5b8197eab12274`). En ambos apunta a `baltic_water_v30\globalvis_16806259.p3d` y Y=`2.7749998569488525`.
- En el vértice ODOL compilado #17, local `(−5.9951171875, +0.15000000596046448, 3)`, sumar el centro ODOL produce exactamente el punto MLOD #17 `(−12.000117301940918, 0, 6)`. Con la traslación WRP, el punto cae en `(x=8508,z=3726)`, esquina de la celda investigada. La suma vertical local ODOL+WRP en doble es `2.924999862909317`, `−1.3709068325e−7 m` respecto a P.

## Cadena numérica fuente y cota local

1. El registro de autoría guardó `old_center.y=0`, `old_matrix.y=2.924999952316284` y `origin.y=2.924999952316284`.
2. Para esa esquina, `P−origin=4.768371586e−8`. `author_global_visual.py:128` guarda `round(height−origin[1],7)`, que da MLOD local Y=`0`. `Point.write` serializa coordenadas como tres f32 (`py3d/__init__.py:1803-1804`); este cero es exacto. El redondeo decimal del Y local aporta `−4.768371586e−8 m` frente al punto ideal; no sumo además el error de `old_matrix`, que ya forma parte de `origin` y se cancela con el delta local no redondeado.
3. En el ODOL leído, centro Y=`−0.15000000596046448` y vértice local Y=`+0.15000000596046448`; se cancelan exactamente al reconstruir el punto MLOD Y=0. No atribuyo un error adicional a esta pareja en este vértice.
4. `verify_compiled_global.py:80` deriva `newpos = float32(oldpos + new_center − old_center)`. Antes del cast, Y=`2.7749999463558197`; tras cast, Y=`2.7749998569488525`. El redondeo de esa posición aporta `−8.940696716e−8 m` respecto al valor previo al cast.
5. Los dos términos locales medidos dan `−4.768371586e−8 − 8.940696716e−8 = −1.370906830e−7 m`, consistente con la fila de `compiled-checks.jsonl` (diferencia de ~`2.5e−16 m` por representación decimal en esta suma).

Para **este vértice y esta cadena**, una cota estática conservadora es `5e−8 m` por redondeo decimal a 7 decimales más media ULP de f32 en `2.775` (`1.192092896e−7 m`), total `1.692092896e−7 m`. El residuo medido queda dentro. Esta cota usa operaciones y formatos observados antes del motor; no es una banda global para otras coordenadas, otras caras o cualquier salida de Binarize.

## Fuentes y límite de inferencia

- `author_global_visual.py:74-89,128,142` lee centro/modelo anterior, define `origin`, cuantiza Y local y conserva centro/matriz previos en el ledger.
- `verify_compiled_global.py:79-80,92,148-149` lee centro ODOL, calcula la nueva posición WRP con cast f32 y registra los errores por campo.
- `tools/terrain/wrp0wzd.py:38,54-55` lee/escribe la matriz como 12 f32; `py3d/__init__.py:1803-1804` escribe cada coordenada P3D como f32.
- El ODOL fue leído del paquete y sus valores se cruzan con el MLOD y el `compiled-checks` por SHA. No se inspeccionó código interno de Binarize ni se midió suma/transformación del motor. Esto clasifica un mecanismo offline plausible y cuantificado para una microdiferencia; no cambia la puerta original de cobertura ni demuestra causalidad para el mapa completo.
