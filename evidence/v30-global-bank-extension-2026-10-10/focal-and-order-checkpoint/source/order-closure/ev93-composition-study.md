# Estudio de composición OC sobre EV93

Fecha: 2026-10-10. Solo lectura y cálculos en memoria; no se ejecutaron solver/consumidor ni se escribió terreno.

## Anclas

- B / EV82-B: `candidate/terrain.npz`, SHA256 `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`.
- EV93 seleccionado: `compound-selection/run-02/candidate-terrain.npz`, SHA256 `6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d`.
- Selección: `compound-selection/run-02/selection.json`, SHA256 `3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b`; status `SELECTED`, 499 retenidos y 69 excluidos.
- OC: `order-closure/author-run-01/candidate-local.npz`, SHA256 `ec1df1c7749fe478f4d5fc943acdc74bb498d68123bf568d07f5aa4d88ae21ba`; matriz preparada SHA `8a8a1cf8e9b6906b1aab8053877383d01a92baa5bd2c18b54b1b9e43c8c37a21`.
- OC consumer existente: `order-closure/consumer-run-01/review.json`, status `FAIL_ORDER_CLOSURE_SECTOR_OFFLINE`, única gate falsa `all_corridor_geometry_covered`. La gate registra cobertura geométrica con error <1e-5, cero cambios en los triángulos afectados y áreas de P desconocido heredadas (Narva 238.7458 m², Luga 752.2622 m²); no atribuir este fallo de corredor a una regresión del OC.
- Focal: `focus-unit/author-run-01/candidate-terrain.npz`, SHA256 `30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1`.

## Comparación

La caja local OC cubre filas `[710,970)`, columnas `[240,500)`; tiene 40,512 variables. EV93 coincide exactamente con B en la ventana focal 17×17 `[832,849) × [362,379)`, pero no en toda la caja: difiere en 79 alturas (máximo 1.45456934 m). De esas, 39 caen en variables OC y 40 son nodos fijos del problema sectorial. El foco `(840,370)` está fuera de las variables OC y se mantiene en EV93/B a 3.73610520 m; el candidato focal está en 3.27802968 m. Por tanto, una composición que conserve la altura focal conserva esa mejora local.

Al aplicar en memoria la salida OC sobre B, el objetivo local cae de 1943.865698 a 576.463402. El soporte de la matriz es el mismo que contra EV93, pero el RHS no: 40 diferencias fijas tocan 100 filas de objetivo (237 stencils incidentes). Recalculando el objetivo sobre EV93 antes/después de sustituir las variables OC, pasa de 1943.510274 a 578.091831; esta es una comparación diagnóstica, no una aceptación.

La sustitución directa de OC sobre EV93 **no pasa D8**. Al reconstruir testigos lexicográficos contra EV93 aparecen 8 aristas violadas; entre ellas `(729,417) → (728,417)`, 1.80000007 m frente a 2.08264351 m, y `(731,418) → (732,417)`, 1.98187828 m frente a 2.06223941 m. La misma salida pasa las 43,258 aristas guardadas contra B, con 0 violaciones al reconstruir los testigos sobre B. Esto impide transferir el PASS local de B a la composición EV93.

La selección EV93 ya retuvo dos ventanas legacy que poseen los 79 cambios de EV93 dentro del contexto OC: `legacy:360` (39, de ellos 15 variables OC y 24 fijos) y `legacy:583` (40, de ellos 24 variables OC y 16 fijos). No hay propietario múltiple ni punto sin dueño. Reemplazar Q en las 39 variables cambia salidas ya seleccionadas: 14 invierten el signo de su delta respecto a B, 9 aumentan la magnitud y la mayor diferencia Q−EV93 es 0.4171655 m. Ejemplo `(727,415)`: EV93−B = +0.2072356 m; Q−B = −0.0543503 m. Hace falta recomposición/revalidación de esas unidades, no copiar la selección previa como si siguiera intacta.

Como diagnóstico simple de aristas 8-vecinas incidentes a las variables OC, el máximo de pendiente baja de 34.4795° a 28.6148° en B; no aparecen cruces nuevos de 30°/35° en ese cálculo. Es una señal parcial de forma, no sustituye hinges, p99, agua, cobertura ni aceptación global.

## Decisión de composición

1. **Sustituir solo las 40,512 variables OC y dejar el resto EV93 intacto:** no es compatible con el estado seleccionado actual. Viola D8 frente a EV93 y sobreescribe 39 valores que pertenecen a dos unidades retenidas. Requiere un nuevo consumidor de composición que vuelva a asignar propiedad y recalcule D8/shape y todas las gates afectadas.
2. **Recalcular OC con EV93 como base:** es la vía limpia si se quiere conservar las mejoras EV93 circundantes. Necesita un nuevo problema/preflight anclado a EV93: RHS de objetivo, testigos D8, cotas contra presupuesto EV79 y gates locales se reconstruyen; no se reutilizan matrices/cotas/prepared de B como si fueran equivalentes. Mantener exactos los 40 nodos fijos heredados y verificar las costuras y el agua/civil globalmente.

No se aprueba ni se propone exportar ninguna composición. El foco permanece intacto en ambas alternativas si sus valores no son variables del parche; eso no resuelve los fallos de compatibilidad ni la gate de corredor desconocido del informe OC.
