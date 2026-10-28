# Consumidor detenido por contexto de ruta

La producción Visual201 terminó80.703s,201modelos/185744caras de lecho y4760
de agua; hashes finales inmutables. No se repite.
El consumidor original falló antes del primer modelo: el pin relativo
evidence/deployed-surface-prototypes-20261028/artifact-hashes.json se resolvía
desde R aunque el productor se ejecutó desde W con worktree='.'.
No es discrepancia de geometría. Reporte failure.json conservado.

Modificación mínima revisada: consumidor nuevo *_resolved_20261028.py resuelve
sólo pins relativos contra W explícito. No sustituye hashes ni archivos.
Presupuesto adicional: una ejecución600s/2GiB. Fallo nuevo detiene, sin bucle
de reintentos. Output nuevo pilot-visible-surface-consumer-resolved-20261028.
Consumidor anterior CONSUMIDO. Las rutas relativas del manifiesto de entrada
se interpretan en el worktree usado por el productor, documentado aquí.
