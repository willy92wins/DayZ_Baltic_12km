**Veredicto: SOUND-with-fixes.** El plan es coherente con los dos textos y las primitivas leídas, no inventa semántica y separa bien texto, PBO y afirmaciones nativas. Las correcciones siguientes son concretas y caben en el presupuesto.

**Correcciones necesarias antes de implementar**

1. **Blancos: incluir tabulador.** Ambos textos indentan con tab (0x09). "Espacios ASCII" debe fijarse como el conjunto {0x20, 0x09, 0x0D, 0x0A}; de lo contrario el parser emite UNSUPPORTED_SYNTAX sobre las muestras reales. Aceptar EOF con o sin salto final y registrarlo.

2. **Números: no añadir signo.** Ningún literal observado lleva signo ni exponente. Fijar la gramática a dígitos con un único punto opcional (`0.1`, `60`, `130`). Signo, exponente o `.` sin dígitos ⇒ UNSUPPORTED_SYNTAX. El "signo opcional" del plan es semántica no leída.

3. **Sufijo de array.** La gramática debe tokenizar `identificador[]` explícitamente; el plan menciona llave y coma pero no el `[]`. Dentro del array sólo números y comas, sin coma final.

4. **Strings.** Cerrar al primer `"` sin interpretar ninguna barra. `\"` nunca se trata como escape: termina el string y el `;` esperado falla ⇒ UNSUPPORTED_SYNTAX con offset. Consistente con el plan, pero hay que escribirlo así en el código.

5. **Inventario esperado del consumidor codificado a mano, no derivado.** Si el consumidor obtiene las cuentas "derivadas de muestras fijadas" ejecutando el parser del autor, es circular. Fijar literales: 20 asignaciones (8 top, 6 por Stage), 4 clases, 6 strings (2 shaders, 2 texture, 2 uvSource), 8 arrays de 3 valores, 5 arrays de 4 valores, 2 escalares, 24 `;`. El consumidor cuenta con su propio escáner y compara.

6. **Cobertura de bytes verificada por el consumidor, no afirmada por el parser.** El manifiesto debe exportar cada token con [inicio, fin). El consumidor relee el archivo, comprueba SHA pin, marca los bytes cubiertos y exige que todo byte no blanco esté en exactamente un token sin solapes. Un parser que omite Stage2 deja bytes sin cubrir; eso es lo que detecta la fixture.

7. **Asimetría de rutas de entrada.** El primer texto está bajo `snapshot/decoded/dz/structures/roads/parts/data/`, el segundo bajo `decoded/` sin subárbol. Fijar ambas literalmente tal como aparecen en report.json y registrar la asimetría; no normalizar ni "corregir" a una estructura común.

8. **Resolución de prefix con normalización simétrica.** pbo_table lowercasea y normaliza las entradas, pero no la propiedad `prefix`. Normalizar ambos lados igual (backslash→slash, lower), exigir que exista `prefix` y que valga `dz/structures/roads`, quitar ese prefijo del literal y buscar `parts/data/<nombre>.paa` en la tabla.

9. **Comparación de tabla completa.** Al abrir roads comparar las 501 entradas (name, mime, size, offset) y las propiedades contra entries.json pinado, no sólo las cuatro. Cualquier diferencia ⇒ INCONCLUSIVE_DEPENDENCIES.

10. **Nuevo lector de rango, sin tocar read_payload.** Como no hay digest previo, añadir una primitiva que exija mime==0, 0 < size ≤ 16 MiB, offset+size ≤ 318217469, lea exactamente size bytes, calcule SHA y lo registre como primera observación. Size 0 debe fallar; rechazar reutilizar read_payload con digest ficticio.

11. **"Proveedor ambiguo" sólo es comprobable contra un inventario global.** Esta unidad abre únicamente roads. O se consulta en lectura la tabla global guardada ya existente, o se declara `provider_ambiguity=NOT_TESTED`. No afirmar unicidad desde una sola PBO.

12. **Modelos raíz: herencia, no reverificación.** El cierre SAVED_PILOT exige "tres modelos acreditados", pero esta unidad no relee modelos. Etiquetar explícitamente `models_evidence=inherited_by_hash(models.jsonl 84c3aafb, entries.json 465aa354)` para evitar un falso cierre.

**Guardas correctas tal como están**
Hash streaming antes/después, límites 16/64 MiB, no extracción de modelos/RVMAT, UNRESOLVED para `.rvmat` o `#()` nuevos, `emmisive` conservado, nombres de shader/uvSource registrados sin afirmar compatibilidad, build_ready=false y native_resolution=NOT_TESTED.

**Presupuesto**
Dos hashes streaming de 318 MB caben con holgura en 120 s. Implementación 240 s es ajustada por las 12 fixtures negativas; si falta tiempo, priorizar 5, 6 y 9, que son las que impiden cierres falsos.
