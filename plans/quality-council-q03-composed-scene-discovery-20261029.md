Investigación CONSUMIDA: Muse40.485s, integración y fuentes en evidence/composed-scene-q03a-20261029. No relanzar. Siguiente Q03B plan revisado para preparar contrato; sin arrays/código todavía.

# Q03A — preparar geometría de escena compuesta para lechos y cruces

Estado: REVISADO_PARA_INVESTIGACION_DE_FUENTES_GUARDADAS. Muse Wonder1.0 nativo25.704s SOUND-with-fixes adjudicado. No autoriza extracción, build, DayZ ni reparación.

## Problema y trazabilidad

Q03/Q05/Q11 del council requieren medir superficie visible, agua nativa y 3D, lechos, caps y Roadway con poses y ambos accesos. La medición de compresión Q02B4 ya termina; no convertir su siguiente formato en dependencia artificial de este frente. P9/P10/P11 permanecen: mar al pie de Narva con apoyos laterales autorizado; no transferir el corredor navegable de24m a todos los cauces ni usar el antiguo corredor vial de8m como huella de piezas12/9m.

[EXACT] `tools/quality/collision_scene_b2a_ev112.py:244-270` selecciona Geometry y guarda metadatos, cuentas, bounds y referencias de proxies; no guarda las caras Visual/Roadway completas. `:413-438` filtra poses por AABB de los rayos diagnósticos; `:471-473` escribe modelos/poses. Por tanto `models.json`6318366B con5509modelos y `poses.json`3667B con cuatro candidatos NO constituyen una escena completa para exposición superficial. Reutilizar el catálogo guardado, no volver a ejecutar B2A.

[EXACT] RoadB4B0 comprobó5509referencias fuente y5512candidato; B4B1 fija4equivalencias de contenido sobre28instancias pero conserva METHOD_UNVERIFIED/METHOD_DECLARED. No es prueba de precedencia instalada. RoadB3 añade tres piezas elevadas de diagnóstico, no pavimento. B4A3 fija doce recursos de tres modelos, no recursos completos de escena.

[EXACT] `evidence/road-water-census-20261028/README.md`:770aristas de contacto en29cadenas/124totales, no770puentes. Dominio nativo; kit118 no evaluado por ese censo. `inputs.json` externo fija terreno, agua y referencia vial. No reutilizar la lista de puentes generados como universo esperado. Los nueve IDs de Q01 permanecen abiertos; fotos y personaje no localizan caras/instancias.

## Hipótesis y primer discriminador [DESIGN]

Las pruebas del eje y de Geometry pueden omitir exposición lateral y agua3D. Para medirlo hay que obtener geometría de superficies y poses del MISMO mundo, sin mezclar instalado actual con identidad retrospectiva. Esta unidad prepara ese contrato desde fuentes/lectores reales; no decide todavía qué altura/anchura está bien.

Primera entrega acotada: investigación de firmas, almacenamiento y consumidores existentes, sólo lectura. Producir una tabla con las fuentes exactas de: terreno/agua nativa, caras Visual de lechos/caps, caras y semántica de agua3D, Roadway de puentes/piezas, poses completas y proxies. Cada fila indica archivo/hash/selector/API real, qué bytes se guardaron, identidad histórica o actual, marco asumido, cobertura y carencias. Referencias por nombre sólo localizan recursos; no seleccionan qué modelos se excluyen del futuro universo.

Entradas: contratos y resúmenes B2A/B4B0/B4B1/B4A3, código del lector ODOL y WRP ya fijado por esas unidades, Q01 con su snapshot exacto, inputs/report/contexts del censo carretera-agua y los recibos de kit118/cont65. Buscar esos recibos por ID literal antes de diseñar selectores. No rehacer catálogos, censo WRP, rayos, consultas Q02B ni reinterpretar resultados consumidos. No abrir todavía PBO/P3D/WRP ni caras vanilla completas; los índices/metadata guardados bastan para comprobar qué falta. No editar P:.

Si una semántica de agua3D/LOD o un campo del lector no existe, registrar UNKNOWN con ancla; no completar la API por intuición. Las dos hipótesis raw/plus_bounding_center de B2A no certifican el marco nativo. La futura composición debe conservar hipótesis y ambigüedad, o justificar una calibración separada con el piloto de poses Q04; no escoger la que dé menor exposición.

## Salida necesaria para pasar a extracción [DESIGN]

Un contrato posterior, revisado ANTES de autoría, fijará:

- Universo esperado desde referencias/instancias WRP, independiente de puente/cauce generado; inclusión de proxies y capa de agua3D aun si no hay Geometry. La clasificación semántica desconocida no equivale a ausencia.
- Proveedores y bytes concretos de todos los recursos que se abrirán; si se usa instalado actual, identidad nueva y diferencia con la escena histórica explícitas. No promover los metadatos B4B1 a identidad física actual.
- Poses/marcos, vértices/índices/materiales/resoluciones necesarios por capa; conservación de winding, degenerados y transformaciones. AABB sólo broad phase, jamás área útil, calzada, superficie expuesta ni volumen sólido.
- Dominio de interacción completo por huella de caras, incluidos extremos y accesos. Longitud de acceso y reglas de ancho vienen de producto/referente o quedan UNKNOWN; sin buffer arbitrario para fabricar cobertura.
- Salida acotada y unidades: m, m² y m³ diferentes; perfiles puntuales no prueban exposición de área. Superficies verticales/coplanarias y falta de referente conservan estados inconclusos. No elegir máximo de rayos como prueba de escena compuesta.
- Mutantes independientes: cap lateral fuera del eje, puente omitido/girado/corto, superficie3D sin Geometry, proxy con pose no resuelta y falso positivo diseñado. Q01 nunca se resuelve sólo por un sintético y las nueve localizaciones siguen GEOMETRY_UNBOUND hasta evidencia exacta.
- Qué preparación sirve a carreteras: pose/pivote/huella real de piloto, material y precedencia; colocación, pavimentado y conducción requieren unidades posteriores, no permisos abstractos repetidos.

No fijar un umbral geométrico durante esta investigación. No podar árboles, mover controles, soldar saltos de agua ni alterar etiquetas. El resultado esperado es DISCOVERY_FOR_COMPOSED_SCENE_CONTRACT, build_ready=false/map_repaired=false; no una prueba global de calidad ni un gate nuevo que apruebe por ausencia de datos.

## Presupuesto y parada

Una investigación nativa read-only120s, entrega<=1200palabras más tabla de fuentes. Sólo fuentes de texto/JSON previamente localizadas: <=16MiB por archivo/64MiB total de lecturas, sin cargar transcripciones/corpus completo. No scripts nuevos de censo. Root integra y verifica citas; revisión del contrato de extracción120s antes de código. Si no se cierra una firma/identidad, conservar el hueco y elegir el discriminador mínimo con plan separado. No retries internos ni ampliar recursos por defecto. La investigación no autoriza extracción aunque encuentre todo.

En paralelo lógico permanecen Q02B formato/ángulos y Q08/Q17 referentes naturales/agua; ninguna unidad de serialización acepta naturalidad. Nav8hist607,47FAIL21inciertos,RH349/350/1425,agua723,RAM/Bullet/calidadglobal y C1NOT_REVIEWED intactos.

## Adjudicación de revisión y puerta de salida

Cada fila llevará OBSERVED_SAVED, LOCATED_NOT_OPENED, UNKNOWN o CONTRADICTED, época e identidad. Sólo OBSERVED_SAVED acredita los bytes realmente guardados; localizar un proveedor/lector no certifica recursos no abiertos. En esta fase extraction_ready=false SIEMPRE. Documentar huecos no habilita la siguiente fase: necesita contrato revisado propio.

Se REFUTA la premisa de que los5509modelos fueron seleccionados por Geometry. collision_scene_b2a_ev112.py:411-420 recorre todos los nombres y añade metadata ANTES de `if not len(v)`. B4B0 además comprobó independientemente5509referencias fuente. Ese universo de nombres histórico sí está medido; lo ausente son las caras de superficie completas y las poses de toda la escena. No se sustituye un denominador medido por UNDETERMINED. La correspondencia a un mundo instalado actual y la geometría compuesta siguen sin certificar; el futuro contrato fija explícitamente si usa fuente5509 o candidato5512, y cuenta proxies por separado.

El marco no certificado bloquea la aceptación mundial, no la mera lectura futura de vértices locales bajo un contrato propio. No imponer calibración nativa como requisito para poder obtener la geometría que ayudaría a calibrar. Q04 discriminador y extracción de caras son unidades separadas, con sus hipótesis y sin dependencia circular; no escoger raw/plus_center por el resultado deseado.

Orden de investigación: poses/marco y caras Visual/Roadway; luego agua3D sin Geometry; después proxies y recibos kit118/cont65 por ID literal. Al agotar120s o64MiB, terminar con tabla parcial y huecos explícitos, sin ampliar presupuesto ni declarar contratos listos. Mutantes aquí son discriminadores diseñados, NO pruebas ejecutadas. La investigación siguiente todavía no ha empezado.
