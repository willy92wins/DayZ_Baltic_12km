# Q03B — código rechazado antes de leer la escena real

**No se generó un índice de escena ni se modificó el mapa.** El contrato externo quedó fijado y revisado; las dos postimágenes de código no superaron sus pruebas. Se retiraron de tools/quality y tests; source/R0 y source/R1 son archivos de investigación, no entrypoints aprobados.

| Entrega | Suite real | Resultado |
|---|---|---|
| Muse R0,125.000s |15casos,3PASS/9FAIL/3ERROR,3.265s | Rechazo prematuro del esquema de pin; positivos y negativos no probados |
| Muse R1,207.547s |23casos,6PASS/12FAIL/5ERROR,15.688s | META mal descrito; fixtures interrumpen guardas posteriores |
| Repros independientes,1.313s |3defectos reproducidos | Descriptor<i4 truncado a<; NPY2 válido rechazado; hijo de proxy incorrecto aceptado |

Fable revisó contrato98.438s, códigoR0116.141s y delta144.922s. El delta SOUND-with-fixes/CONVERGE quedó contradicho en tres afirmaciones por los repros, documentado en code-adjudication.md. No se presenta ese dictamen como aceptación ni se atribuye causa global del mapa a estos fallos del instrumento.

Los204archivos NPZ declarados (12,537,057bytes guardados; cota expandida262,434,599) NO se abrieron. Se leyeron JSON y fuentePython guardados, se trabajó con fixtures sintéticos. ContratoR1e9672092 y oráculosb4ba70a4 intactos. No cambio de tolerancias ni repinado de fuente para PASS.

Siguiente: recuperación Q03B1 por corte funcional lector+tests, con oráculos externos y parsingNPY estándar antes de integrar semántica. El consumidor independiente y todos los casos de proxy siguen pendientes. La ejecución real seguirá condicionada a código revisado y suites completas.

Repro guardado (sin tocar escena): ejecutar repro.py con raíz source/R1 como primer argumento y un archivo JSON nuevo como segundo. Su exit0 significa **que los tres defectos del código retirado se reprodujeron**, nunca código aprobado.

Nueve rechazos humanos siguen abiertos; C1NOT_REVIEWED. Q03C/Q05, carreteras, ángulos y referentes naturales/agua continúan pendientes. Nav8607PASS es histórico.
