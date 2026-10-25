**Veredicto: SOUND-with-fixes.** El verificador no emite un PASS falso: el estado S3 es `REVIEW_REQUIRED`, los NaN/vacíos se rechazan y las máscaras solo etiquetan. Pero tres puntos rompen el contrato de cobertura y uno más contamina la adjudicación. Una ronda de reparación debería bastar.

## Hallazgos P1 (con repro del contrato)

**P1-1. Las cadenas se fragmentan por una tolerancia de 1e-5 m que el propio kit no cumple.** `screen_shapes_ev112.py:97` exige coincidencia de 1e-5 m entre el final recortado de una pieza y el inicio de la siguiente. El kit solapa piezas por diseño. Las estaciones de kit-records muestran, por ejemplo, la pieza 0 en 8.685 a 20.565 y la pieza 1 en 17.37 a 24.656, así que las líneas centrales corren paralelas con desfase submétrico. El resultado real lo confirma: cero `centreline_join_gap`, pero 47 de 49 sitios construidos quedan abiertos y las cadenas típicas miden 6 a 17 m, menos que una pieza. Las rectas encadenadas y las escaleras entre piezas solo se detectan cuando dos líneas centrales se cruzan por azar numérico. Esto viola el plan punto 1 ("rectas largas encadenadas") y punto 3 ("división de una misma ruta en piezas"), y no existe prueba de división. El estado sigue siendo bloqueante, pero el inventario de patrones encadenados es mayormente vacío y el informe no lo dice.

```python
import numpy as np, unittest, sys
sys.path.insert(0,'tools/quality')
from screen_shapes_ev112 import stitch_for_screen
from shape_patterns_ev112 import join_screen, route_screen
class Division(unittest.TestCase):
    def test_three_collinear_pieces_keep_long_straight(self):
        for dy in (0.0, 1e-4):          # 1e-4 m < join_gap_m, > tolerancia de cadena
            lines=[np.array([[0,0],[25.44,0]]),np.array([[25.44,dy],[50.88,dy]]),np.array([[50.88,0],[76.32,0]])]
            joins=[join_screen(a,b) for a,b in zip(lines,lines[1:])]
            self.assertEqual([j['findings'] for j in joins],[[],[]])
            chains,opened=stitch_for_screen(lines,joins)
            kinds=[f['kind'] for c in chains for f in route_screen(c)['findings']]
            self.assertIn('long_straight_run',kinds, msg=f'dy={dy} opened={opened}')
```
Con dy=1e-4 el test falla: cero cadenas, cero hallazgos, solo `centreline_gap_not_bridged`. Reparación mínima: puentear huecos ya medidos por `join_screen` por debajo de un umbral versionado en `POLICY`, anotando `bridged_gap_m` en la cadena. No es inferir conectividad: el hueco ya está medido y declarado bajo umbral.

**P1-2. El delantal seco del piloto se descarta en silencio.** `screen_shapes_ev112.py:80-81` devuelve solo `axis[required]` tras `wet_span`, y `paths[sid]` guarda esa versión recortada. El docstring de `wet_span` en `audit_stream_visibility_ev112.py:39-40` promete que el delantal "sigue inventariado"; aquí no se inventaría ni se cribó ni se declara en `coverage_open` ni en `limits`. Para kit-118 el eje cribado mide 290.7 m frente a 26 piezas de 12 m colocadas. Viola plan punto 1 (piezas realmente colocadas) y punto 5 (informar vacíos).

```python
import numpy as np, unittest
from audit_stream_visibility_ev112 import wet_span
from shape_patterns_ev112 import route_screen
class Apron(unittest.TestCase):
    def test_corner_in_apron_is_screened_or_declared(self):
        axis=np.array([[0,0],[10,0],[10,10],[20,10],[30,10],[40,10]],float)  # codo 90° en x=10
        required,_=wet_span(axis,[[20,10],[40,10]])
        self.assertEqual(route_screen(axis[required])['findings'],[])          # el codo desaparece
        self.assertTrue(route_screen(axis)['findings'])                        # pero está colocado
```
Reparación: cribar el eje completo y etiquetar cada hallazgo con `in_wet_span`, o añadir una entrada `coverage_open` con los metros de delantal excluidos.

**P1-3. La vinculación WRP es unidireccional: piezas colocadas sin registro nunca se criban.** `bind_matrix` en `screen_shapes_ev112.py:52-59` comprueba que cada registro tiene pose en el WRP, pero nada comprueba que cada pose de agua del WRP tiene registro. `placed_water` recoge todas las poses con prefijo streambed o piloto; el informe solo publica `bound_poses`, no el total colocado. Una pieza huérfana de una pasada anterior quedaría fuera del inventario sin aviso. Viola plan punto 1. Comando propuesto, no ejecutado, desde el worktree con el intérprete gis-env:

```powershell
python -I -c "import sys,json,numpy as np;sys.path[:0]=['tools/quality','tools/water','tools/terrain'];from screen_shapes_ev112 import placed_water;H=np.load(r'E:\DayZ-Baltic-Build\qc-council-20261024\road-merged-s3\terrain-buried.npz')['heights'];p,_=placed_water(r'E:\DayZ-Baltic-Build\qc-council-20261024\stage-s3\root\dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp',H);print({k:len(v) for k,v in p.items()});print('placed',sum(map(len,p.values())),'bound',json.load(open(r'E:\DayZ-Baltic-Build\shape-gates-20261025\s3-v2\rivers.json'))['bound_poses'])"
```
Reparación: publicar `placed_total` y marcar `coverage_open` si difiere de `bound_poses` más las piedras registradas.

## Hallazgos P2

- **Falsa alarma masiva por la pieza slanted.** Los 6271 `abrupt_route_turn` de alcance pieza repiten dos valores, 52.67° y 53.63°, y coinciden en xy con los 2305 `join_tangent_break` de hueco 0. El array `centre` de las piezas slanted en el JSON de geometría arranca con un salto lateral de 0.57 m en 0.43 m de avance, porque el punto medio del travesaño diagonal se desplaza. Es un artefacto de la representación por travesaños, no un codo del cauce. El contrato permite positivos adjudicables, pero un verificador cuyo backlog está dominado por su propia definición de línea central engaña sobre el tamaño del problema. Repro: `route_screen(K.centreline_world(dict(model='dz\\water\\streambed\\streambed_leaf_short_slanted.p3d',matrix=[1,0,0,0,1,0,0,0,1,0,0,0]),K.load_models(),.25))` debe devolver un codo sobre una pieza recta. Opciones: excluir el travesaño diagonal del `centre`, o etiquetar `representation_artifact` sin ocultar.
- **Pirámide sobre pendiente rechazada.** `shape_patterns_ev112.py:95` descarta cualquier ajuste cuyo plano de fondo supere la mitad de la pendiente de cara. Un montículo facetado sobre una ladera del 5 % con caras del 4 % tiene residuo cero y no se detecta. Repro: `pyramid_fit(10-.04*(abs(x)+abs(y))+.05*x)` con la malla del test debe ser True y hoy es False. Sustituir por una condición sobre el residuo del ajuste sin la restricción de fondo, o restringir solo el modo de cuatro pendientes.
- **Ápice fuera de vértice.** Si el ápice cae en el centro de una celda, los cuatro vértices iguales son candidatos pero el ajuste está centrado 3 m fuera. Estimo un rms relativo cercano a 0.03 a radio 48 m, por encima de 0.025. Repro a ejecutar: `pyramid_fit(10-.04*(abs(x-3)+abs(y-3)))`. Confianza media; si se confirma, probar también desplazamientos medios de celda o añadir el centro como parámetro.
- **Escalera con esquinas redondeadas no es escalera.** `route_screen` exige tres giros de 60° o más en un vértice simplificado. Una zigzag ortogonal con filetes de radio 8 m produce giros de 28° por segmento y reparte longitud fuera de los ejes, así que ni escalera ni codo. Repro: cinco tramos de 50 m con cuartos de arco de radio 8 m muestreados cada metro; esperar `orthogonal_staircase`. Es mejora de alcance, pero describe el artefacto del kit en malla mejor que el control sintético actual.
- **Terraza rectangular adyacente a otro escalón se pierde.** `rectangle_components` etiqueta con conectividad 8; una plataforma pegada a un terraplén de carretera se fusiona, el relleno de la envolvente baja de 0.9 y no se reporta. Repro: añadir al test del rectángulo una franja `h[40:42,:]=3` tangente al rectángulo y esperar la detección.
- **Umbrales fuera de POLICY.** Balance 0.10 en `shape_patterns_ev112.py:48`, tolerancia de cadena 1e-5 y de pose 0.001 en `screen_shapes_ev112.py:58,97`, prominencia 0.30 en la línea 164, 16 vértices y 3 apoyos en las líneas 112 y 125, razones 0.25 y 0.5 en las líneas 93 y 95, paso angular 3° y radios 2,4,8. El plan punto 4 exige umbrales fijados y versionados; estos no están en policy.json.
- **Dependencia externa sin hash.** `screen_shapes_ev112.py:63` inserta una ruta py3d fuera del worktree y no la incluye en `inputs`. La reproducibilidad por SHA queda incompleta.

## Backlog sin repro

Orientación de piezas por proyección sobre la lattice puede invertir piezas cortas y generar `join_tangent_break` de 180°. El orden por estación puede intercalar ramas si un sitio tiene más de una. Registros de sitios ausentes de kit-report no se criban. Pirámides truncadas y plataformas en L quedan fuera por diseño; conviene declararlo en `limits`. Coste: el bucle de ejes en `route_screen` es cuadrático en estaciones simplificadas; aceptable hoy, vigilar si el piloto continuo crece.

## Límites de esta revisión

No ejecuté nada; los repros son propuestas y la estimación del ápice fuera de vértice no está verificada numéricamente. El JSON de geometría es una sola línea y solo pude inspeccionar fragmentos. No revisé py3d ni render. rivers.json y terrain.json se leyeron por muestreo acotado.

Rutas externas modificadas: ninguna. Solo se usaron Read, Glob y Grep.