# Q03B2 — snapshot y sesión NPZ verificados con fixtures

**ARCHIVE_SESSION_FIXTURE_VERIFIED_ONLY**. Wrapper nuevo usa el header sellado051436d9. Comprueba identidad path/handle, reparse, reservas previas, directorioZIP real antes de construirZipFile, schema exacto, NPY1/2 y ZIP64local acotado. Todas las cabeceras preceden arrays; signedzero/META35/matriz y bytes de payload se cotejan con literales independientes.

Se cerraron dos defectos reales: CRC mal clasificado y EOF lógico de ZipExtFile que ocultaba bytes decodificados. R0 y repros se conservan; no se cambió tolerancia, oracle ni evidencia histórica. La nueva verificaciónDEFLATE exige terminación y consumo exactos con memoria acotada por chunks. Decoders comparten biblioteca; no diversidad de implementación.

Autor Codex local469.155s; revisorFable180.063s sin dictamen, recuperaciónMuse105.953s completa SOUND-with-fixes. Corrección local47.399s propuesta/adjudicada, sin nueva revisión externa de postimagen. Suite privada10métodos (9PASS,1SKIPprivilegio symlink; reparse simulado sí)1.531s/54.65MB. Dos checks de frontera64KiB adicionales0.547s. Fuentes de prueba y contratos públicos permiten reproducción desde copia aislada; snapshots source/R0 son historia, no entrypoints aprobados.

No NPZ histórico leído ni mapa modificado. No índice semántico/proxy/época ni aceptación geométrica o nativa. Nueve reportes humanos0resueltos y C1NOT_REVIEWED. Próxima unidad: productor semántico y consumidor con recorrido independiente, sobre contratoescenae967 y fixtures de joins/proxy, antes de autorizar captura histórica; Q03C/Q05 necesitan ese índice. Carreteras, ángulos y referentes siguen abiertos.

Copia pública de los mismos bytes:10métodos (9PASS/1SKIP) en2.422s; dos patrones de frontera de salida64KiB exactos en2.031s. Estos patrones comprimibles no ejercitan todas las fronteras posibles de entrada. Todas las fuentes/oráculos de los tests públicos se leyeron en public-repo; sin fallback privado. Identidades observadas retiradas29, no operación propia/run/lease.
