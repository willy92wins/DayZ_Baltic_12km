**Veredicto: SOUND-with-fixes.** El extractor respeta el alcance acotado (3 piezas, una extracción, sin WRP ni colocación), conserva caras degeneradas, no inventa pivote ni ancho, y el estado nunca puede llegar a DISCOVERY_COMPLETE porque los campos UNKNOWN están cableados. El driver distingue error de INCONCLUSIVE. No encuentro falsos PASS alcanzables en la ejecución real. Sí hay huecos en el validador reutilizable y una fragilidad de importación.

**Hallazgos con fix propuesto**

- `road_consumer_discovery_ev112.py:46` acepta booleanos como ancho. `isinstance(True,(int,float))` es cierto y `True>0` pasa, así que `usable_width=True` validaría como ancho positivo. Fix: añadir `and not isinstance(row['usable_width'],bool)`. Caso falso PASS del validador (no de la corrida actual).
- `road_consumer_discovery_ev112.py:40-47` no valida la enumeración de `consumer_observed` que fija la adjudicación (WRP_OBJECT / WRP_ROADNET / AMBOS / UNKNOWN) ni el tipo de `crossings_exact`. Una fila con `consumer_observed='si'` y resto conocido daría DISCOVERY_COMPLETE_NOT_PLACEMENT. Fix: `require(row['consumer_observed'] in ENUM,'invalid_consumer')` y exigir que un valor distinto de UNKNOWN venga acompañado de cita path:offset y hash en la fila.
- `road_consumer_discovery_ev112.py:47` permite `roadway_present=False` con `usable_width` numérico. El plan dice Roadway ausente implica ancho UNKNOWN. Fix: `require(row['roadway_present'] or row['usable_width']=='UNKNOWN','width_without_roadway')`. El test `test_missing_roadway` no cubre este cruce.
- `road_consumer_discovery_ev112.py:27` descarta del footprint cualquier quad cuya proyección sea inválida (pajarita por torsión o por orden de vértices). Se retiene como fila, bien, pero el área unida queda infraestimada sin señalarlo por LOD. Fix determinista: proyectar quads como dos triángulos (0,1,2)/(0,2,3) para el footprint, manteniendo la fila original; o al menos distinguir `INVALID_PROJECTION` de `ZERO_AREA` en `projection`.
- `road_consumer_discovery_ev112.py:69-71` no exige que cada modelo aporte al menos un LOD Visual. Un modelo sin Visual produciría `lods=[]` y aun así `coverage.all_visual_lods_and_roadway=True` en la línea 75. Fix: `require(any(r['role']=='Visual' for r in local),'no_visual_lod:'+name)` y calcular esa bandera por modelo.
- `road_consumer_discovery_ev112.py:75` cablea `selected=3` y `catalog_models=265`. No es error, pero `selected=len(SELECTED)` evita deriva y `catalog_models` debería citar el recibo del catálogo A como origen, no presentarse como medido aquí.
- `road_consumer_discovery_ev112.py:62` filtra por `'StaticObj_Roads_Partasf'` y por subcadena `asf1_25`, que también casa con `asf1_250` o similares. Es ruido en observaciones nominales, sin efecto en estado. Fix opcional: regex con límite de palabra.
- `road_consumer_discovery_ev112.py:10` importa shapely desde un proceso lanzado con `-I` por el driver (línea 14). `-I` desactiva el site de usuario. Si shapely está en user-site, el fallo ocurre antes del `try`, rc 1, y el driver aborta en `returncode in (0,2)`. No hay falso PASS, pero sí corrida perdida. Fix: preflight `python -I -c "import shapely"` desde el driver antes de `run_tree`, o importar shapely dentro de `run`.
- `road_consumer_discovery_ev112.py:78` hace `mkdir` fuera del `try`. Si falla, no hay `report.json` y el driver muere en la línea 18 con FileNotFoundError en vez de un mensaje. Cosmético.

**Comprobaciones que considero correctas**

- Línea 21: la igualdad raw float32 contra vértices decodificados es estricta y falla también con NaN, con el test de nofinito cubierto por `cat.xyz`.
- Línea 24: índices validados por cara y arity 3/4 antes de indexar.
- Líneas 30-33: unión, no suma, por footprint y por material; el walrus se evalúa antes de `wkt=g.wkt` por orden de kwargs.
- Línea 59: el tiempo de CfgConvert se recorta al restante del presupuesto único de 120 s; salida sólo en el directorio local, firma y hash fijados.
- Líneas 54-57 y 73: hashes de PBO, config y piezas verificados antes y pins re-verificados después.
- Driver líneas 7-19: no reanuda, verifica pins pre y post, exige suite TESTS_PASS con postimágenes, rc en (0,2) y ausencia de `error`.

**Casos de falso PASS evaluados**

- Corrida real: no alcanzable. `discovery_fields` fija UNKNOWN en cinco campos, por lo que `status` devuelve INCONCLUSIVE y rc 2 siempre.
- Validador `status` reutilizado en B futuro: alcanzable con ancho booleano, enum de consumidor libre, o Roadway ausente con ancho numérico. Los tres fixes anteriores lo cierran.

**Pruebas que añadiría**

- `status` con `usable_width=True` debe fallar con `invalid_width`.
- `status` con `consumer_observed='WRP'` debe fallar.
- Fixture quad pajarita: una cara, footprint distinto de cero tras triangulación, o marca explícita de proyección inválida.
- Fixture de modelo sin LOD Visual contra la bandera de cobertura.

FIN_REVISION