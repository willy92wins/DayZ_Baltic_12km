# Q03B — adjudicación final de código

Estado: NO_APROBADO_PARA_CAPTURA. No se ejecutó productor ni consumidor reales, no se abrió NPZ histórico ni se cambió el mapa.

R0 Muse125.000s: cuatro archivos; suite15 casos,3PASS/9FAIL/3ERROR,3.265s. Fable116.141s NEEDS-WORK. R1 Muse207.547s: suite23 casos,6PASS/12FAIL/5ERROR,15.688s. No se confunden errores de fixtures con rechazo geométrico ni se acredita cobertura por conteo.

Fable delta144.922s entregó SOUND-with-fixes/CONVERGE, pero tres repros ejecutados en1.313s contradicen cierres concretos: descr_json reduce formato<i4 a<; NPY2.0 válido se rechaza porque unpack('<I',extra) recibe2bytes; proxy real {'model':nombre,'matrix':...} no se resuelve y acepta hijo distinto del source_model. Los hashes de postimagen están en q03b-r1-integration-repros-20261029/report.json. Esto demuestra una entrega de revisión demasiado optimista en estos puntos, no una causa global del mapa ni un juicio sobre toda la familia del modelo.

Se aceptan los hallazgos delta sobre path/relative, bucle muerto, consumer incompleto y fixture two_instances. Se refuta la recomendación de retirar dev/ino para ganar PASS: no hay evidencia de inode cero en este runtime y no se rebaja identidad. La suite se detuvo por META antes de demostrar el resto. El fallo de two_instances actual alcanza SELECTED_PIN, anterior al COVERAGE previsto por Fable; hay que reparar la cadena de fixtures antes de atribuir cobertura a esa guarda.

Salida del bucle: RETIRAR_POSTIMAGEN_R1, no tercera reescritura masiva de los cuatro archivos. La familia proxy/literal sigue abierta después de corrección; el verde externo no sustituye los contraejemplos. Contrato externoR1 e9672092 y oráculosb4ba70a4 siguen intactos; consumidores Q03C/Q05 aún no reciben índice. Se preservan R0/R1 y se cambia estrategia a cortes funcionales pequeños con fixtures externos y lectura NPY estándar. Siguiente plan Q03B1 prepara lector+pruebas, después semántica productor y consumidor por separado; no se repiten capturas inexistentes ni se promueve código pendiente.

Integrador Codex con contexto compartido frente a autor Muse, revisión Fable independiente de hallazgos Codex hasta la entrega; no lane ciega del integrador ni consenso ficticio. Fuentes/contrato no repinados para PASS. Sin DayZ/run/lease.
