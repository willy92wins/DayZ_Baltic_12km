## Veredicto: SOUND-with-fixes

Recibo: revisión nativa de Muse Code, powered by muse-wonder-1.0. Solo lectura; sin código ni aprobación de código futuro.

### Bloqueantes antes de autoría

1. **Contrato `stream`/`member_bytes` incompleto.** El inspector no lee payload, por lo que no puede detectar truncamiento real del stream: solo puede verificar `payload_offset + payload_bytes == member_bytes`. Debe declararse que `member_bytes` es longitud exacta atestada por el llamador, definir lecturas parciales de streams (`read(n)` corto no es EOF hasta confirmarlo) y la posición final del stream tras inspeccionar.

2. **Codificación de parámetros sin asignar.** `member_bytes` bool, negativo o >128MiB no tiene código adjudicado. Debe asignarse explícitamente a un código existente, presumiblemente `MEMBER_SCHEMA`, o el conjunto cerrado queda incompleto. Igual para `shape` con bools, no enteros, `()` escalar y dimensiones cero: fijar si son válidos y su producto.

3. **Precedencia de errores ambigua.** Fijar tabla cerrada etapa→código: EOF en magia/longitud/cabecera/payload-aritmético, `OSError`, diccionario malformado, claves ausentes/extra, dtype malformado frente a dtype válido que no coincide con schema, endian/fields/titles/subarrays, Fortran y versiones `(3,x)`/`(x,1)`. `INTERNAL_ERROR` debe ser solo excepción inesperada tras ese mapeo; no la vía normal para `ValueError` de NumPy al parsear entrada inválida.

4. **Parser público y límite 16384.** Precisar la API pública exacta sobre la copia desde posición 8 y cómo evita helpers privados. NumPy no impone ese cap: es política propia sobre el campo `header_len`, excluyendo prefijo 10/12. La fixture válida de exactamente 16384 será artesanal, no salida normal de writer con alineación a 64 bytes; debe aceptarse esa lectura o el borde es intestable como está enunciado. Rechazo `>16384` tras leer solo prefijo, demostrado por spy de bytes solicitados.

5. **Offsets y aritmética.** Definir si `0/4/8/12/16/20/21/22/23/27` e `itemsize 35` son offsets de campos del dtype, offsets de payload o cortes de bytes. Fijar `payload_offset = 10|12 + header_len`, orden de validación shape→producto acotado→`× itemsize`, y que ningún dtype con fields desplace ese cálculo.

6. **Preasignación y separación.** Sound en no abrir ZIP/filesystem ni cargar arrays, pero debe prohibirse expresamente `np.load`/allocación de payload en el inspector y limitar copias a prefijo + ≤16384 bytes. La reserva expandida sigue siendo deber no probado del wrapper posterior; el resultado no puede insinuarla cerrada.

7. **Independencia del oráculo.** Un hash `79b946…` sin ubicación/acceso no basta. Tests con bytes y códigos esperados literales congelados; `numpy.load` solo como comprobación posterior en positivos. En negativos no puede ser oráculo: el inspector ya usa el parser de NumPy, habría fallo de modo común. La suite debe fijar `numpy==2.5.3`.

8. **Factibilidad.** Viable en 120s solo con la matriz ya congelada como tabla parametrizada única antes de autorizar. Si cada offset/fixture exige construcción ad hoc distinta, el corte excede autoría + una corrección de 90s.

Con esas adjudicaciones textuales, el alcance es entregable corto y el techo `NPY_HEADER_FIXTURE_VERIFIED_ONLY` es honesto.