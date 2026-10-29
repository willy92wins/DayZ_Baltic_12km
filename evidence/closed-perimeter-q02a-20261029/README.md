# Q02A: todos los giros de perímetros cerrados

DIAGNOSTIC_ONLY.48testsPASS; autor8.578s/179511296bytes, consumidor independiente5.906s/149639168bytes. NPZ original inmutableSHA b6612009ff531ef2f3932240ea52cf0660bce97f7904b7d667f962ce0fd95847. Recorre1030cadenas(993cerradas,37abiertas),107641aristas y102320vértices evaluables. Una cadena degenerada;12sinvérticeevaluable separadas de sinhallazgo.

876cadenas con giro crudo>=45grados,11921testigos;141sin esehallazgo NO son aceptadas.287contornos tienen testigo en el cierre; en uno es el único: cadena278,vértice0,(4164;7281.750661609603),65.04836517079175grados,perímetro59.885011540322935m. Su cierre no se evaluaba en la rutina anterior. Este correlato no identifica por sí solo ninguno de los9reportes humanos.

Umbral45exacto con racionales de coordenadasfloat64. Productor dot/cross; consumidor identidad algebraica distinta, noimportación ni misma función. Comprueba cada arista,testigo,orden,coordenada,cierre y resumen.4ULP/16ULP son acuerdos numéricos longitud/perímetro; no tolerancias nuevas de calidad. Controles metamórficos y mutaciones incluyen cierreomitido,rotación90,reversión,subdivisiónamboslados y vecinos de45. No RDP ni remuestreo.

Informe completo privadoSHA 3fc0b5079ed4bd5f475263ba223bd3139bcc7e159fe9adb37736e5c3fb8465d7. El resumen público está ligado a sus bytes. No se publica NPZ ni contornos completos vanilla. No regeneró el censo ni cambió geometría. Conteos no comparables directamente con screenDP histórico793hallazgos; usan algoritmos distintos. Un giro crudo no equivale a defecto visual.

Revisión cruzada Fable y adjudicación propia conservadas. SuiteR0=34PASS;R1=47/48 y falló bindingCRLF; corrección4líneas escrituraUTF8binaria, R2=48PASS. Capturas históricas intactas. No reclasifica47FAIL21inciertos,9rechazos,RAM,C1 ni607PASS históricos. Q02B multiescala/calibración y reparación aúnpendientes.
