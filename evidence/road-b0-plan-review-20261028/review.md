Reviso el plan B0 en modo lectura, sin herramientas, escrituras ni Git. Entrego el review completo a continuación.

```markdown
# review.md — Plan RoadB0 (consumidor/pivotes/huella)

Identidad: Claude Fable 5.1 (claude-fable-5-1), lane única, CLI nativo, 2026-10-28.
Modo: read-only, sin herramientas, hijos, escrituras ni Git. Adjudica Codex.
Entradas leídas íntegras: plans/ev112-road-consumer-discovery-b0-20261028.md (L1-62);
evidence/road-catalog-installed-20261028/README.md; evidence/road-preparation-receipts-20261028/README.md;
product-spec.md (P5/P6/P9/P10/P11). No verifiqué hashes ni binarios: no hay herramientas en esta lane.

## Veredicto: SOUND-with-fixes

El plan descubre antes de colocar, admite INCONCLUSIVE y no usa el TXT FTT como prueba de ruta.
Referentes (L12-18) coinciden con los recibos: P9 fondo1m/calado0.95m/corredor24m,
bed-report 23.9566m² como cobertura histórica de 8m, extensión 12/9m con ancho útil UNDETERMINED.
Sin contradicciones con product-spec. Las correcciones son de acotación y observables, no de rumbo.

## Correcciones requeridas

1. **L22 y L52: "una unidad de lectura" contra "una extracción 120s/2GiB".** Leer WRP instalado,
   extraer caras ODOL y censar cuatro corredores en un solo presupuesto puede exceder 2GiB
   (el censo A usó 675MB sólo con tablas P3D). Fix: un presupuesto por componente (WRP, ODOL,
   corredores), cada uno con elapsed_s/peak_rss registrados y salida parcial declarada
   (por ejemplo WRP: sólo objetos cuyo modelo coincide con roads/* y conteo de red vial por celda,
   con truncated=true si se corta). No ampliar tolerancias ni reiniciar catálogo.

2. **L23-26: fuentes sin identidad.** El plan no nombra qué WRP ni qué config se leen.
   Fix: fijar PBO roads 34c1cabe como única fuente de piezas; WRP vanilla local con hash a registrar;
   P:/DZ/structures/roads/config.cpp como nominal (no identidad instalada); FTT TXT y
   tools/terrain/verify_ftt_pilot.py declarados explícitamente NO EVIDENCIA de consumidor.
   Campo de salida obligatorio: consumer_observed ∈ {WRP_OBJECT, WRP_ROADNET, AMBOS, UNKNOWN}
   con path:offset o path:line de donde se observó. Si config instalada no se decodifica,
   UNKNOWN, no PASS.

3. **L27-31: pivote sin observables suficientes.** ODOL guarda centro de bounding y
   desplazamientos por LOD; sin registrarlos, cualquier "pivote real" sería inferencia por bbox,
   justo lo que L31 prohíbe. Fix: registrar por pieza bounding_center, offset aplicado a vértices
   de cada LOD, id de resolución de la Roadway, selecciones nombradas y número de caras.
   La convención de pivote sólo se declara si N≥3 instancias WRP de la misma pieza muestran
   transformación coherente con la altura nativa leída; en otro caso pivot_convention=UNKNOWN.
   Sólo d72224ed; no mezclar con 7eb9f894.

4. **L36-39: "intersecciones exactas" sin fuentes.** Fix: nombrar las dos geometrías que se
   intersecan (polilíneas de referencia vial y superficies de agua geométricas), con hash,
   método segmento-segmento y tolerancia 0 declarada. Los puntos del personaje sólo contexto,
   como ya dice L37. Narva71 sin tablero ni tabla de puentes, correcto.

5. **L55-56: guardas contra falsos PASS incompletas.** Fix: lista cerrada de campos del
   entregable con UNKNOWN permitido (consumer_observed, pivot_convention, usable_width,
   shoulder_material, roadway_present, crossings_exact). Test de que la fixture "Roadway ausente"
   produce roadway_present=false y ancho ausente, nunca 0 ni defaults. Cierre
   DISCOVERY_COMPLETE_NOT_PLACEMENT exige todos los campos medidos; cualquier UNKNOWN fuerza
   INCONCLUSIVE_DISCOVERY.

## Observables menores

- L4: añadir una línea de estado abierto sin cambios (RAM, nueve regresiones, C1 sin revisar),
  igual que el README del catálogo, para que el plan no sugiera cierre implícito.
- L33-35: las dos alternativas de ancho deben incluir conflicto medido con arcén de material
  distinto y curva con bbox mayor que ancho útil, ya listadas en L53-54; enlazarlas.
- L58-59: tolerancias cross0.03/grade0.065/chord0.03 pertenecen al plan B; mantenerlas aquí
  sólo como referencia, no como criterio de B0.

## Qué NO exige este review

No exige extractor nuevo antes de descubrir ni decodificación de config como precondición;
ambos son salidas posibles de B0, con suite 120s si se crean. No exige puentes, poses,
compilación ni DayZ. B3F 201 no interviene en permiso vial.

FIN_REVISION
```

Veredicto SOUND-with-fixes. Las cinco correcciones son acotación por componente, identidad de fuentes WRP/config, observables ODOL para pivote, fuentes de intersección y guardas contra defaults PASS. No modifiqué ningún archivo ni ejecuté herramientas. Codex debe verificar hashes y adjudicar.