# Cierre exacto float32 de caja y orden D8

Decisión del integrador en el encargo autónomo de completar el relieve. Unidad nueva y separada del cierre anterior, que queda rechazado y archivado en bbbd31f. No es otra continuación ADMM ni cambia su funcional, tolerancias, dominio o solución continua. No autoriza otra altura focal ni un cambio de agua. Estado: diseño revisado matemáticamente; fuente por revisar antes de una sola exportación.

## Mecanismo aislado

`solve-run-03-continuation/solve-result.json` termina CONVERGED en10477, pero REJECTED_LOCAL_NUMERIC_GATES. Estado `solver-state.npz` SHA8618d5941d7c8b235bedce6ad5e21a0053ec61a2a32c17532fec98ff9db3dfa9. Preparado: los19arrays SHA8a8a1cf8e9b6906b1aab8053877383d01a92baa5bd2c18b54b1b9e43c8c37a21. El cierre raw/+1ULP es inviable en una cadena D8 de12aristas. Subir hasta hi tampoco basta: otra cadena alcanza un centro fijo. B sí satisface exactamente las43258relaciones D8 y40512cotas; el dominio no es inviable.

Un diagnóstico en memoria de las dos propagaciones descritas abajo satisface caja/D8/fijos:752nodos distintos al raw,300suben/452bajan; máximo2.0266e-6m,17ULP arriba/3abajo. Aumento de objetivo5.6401e-7 frente al presupuesto existente5.7646e-5. Es diagnóstico, sin candidato; no sustituye la ejecución reproducible ni consumidor. No utilizar estos valores como umbrales ajustables.

## Algoritmo y prueba [DESIGN]

Grafo completo de los witnesses reconstruidos del preparado: arista w→c exige q[c]>=q[w], sin epsilon. Incluir todos los nodos leídos, variables y fijos. Fijos con lo=hi=B; variables con cotas inward float32 del preparado. Raw: cast float32 del x64 guardado sobre B; comprobarlo contra raw_float32 guardado.

1. U=hi. Propagar hacia atrás por todas las aristas U[w]=min(U[w],U[c]) hasta punto fijo. Equivale al mínimo hi entre todos los descendientes alcanzables, incluidos ciclos. Verificar lo<=U en todos los nodos; B debe ser testigo independiente de factibilidad.
2. r=clip(raw,lo,U), con valores float32 exactos. Antes del cierre calcular b=max(abs(r-raw)) y V=sum(max(0,r[w]-r[c])) en float64 sobre todas las aristas.
3. q=r. Propagar hacia delante q[c]=max(q[c],q[w]) hasta punto fijo. Es el menor majorante de r que respeta el orden. U monotónico garantiza q<=U y por ello caja y fijos. Los valores proceden de un conjunto finito; los ciclos adoptan el máximo r de su componente.
4. Comprobar exactamente caja, D8, fijos, no nuevos mínimos y max(abs(q-raw))<=b+V. Esta última cota se deriva ANTES del cierre: cada diferencia a lo largo de un camino simple queda acotada por la suma de violaciones de sus aristas. No usar una cota elegida después de ver q ni limitar artificialmente la corrección a1ULP.

Se sustituye exclusivamente la regla de cierre unilateral raw/+1ULP por este cierre de orden acotado. Se mantienen coste(q)-coste(raw)<=1e-7*max(1,coste(raw)), mejora estricta frenteB, cotas físicas, mínimos, KKT original de x64, geometría/civiles/agua/perfiles y todos los demás gates. No se permite redondeo posterior ni reparación manual de q. No se mueve agua ni dominio/protecciones.

## Fuente, consumidor y límites

Autor separado en `order-closure/`, sin tocar solve.py, solve_resumable.py ni resultados anteriores. Una única salida fresca `order-closure/author-run-01`, con candidato local, estado/procedencia parent exactos y recibo propio. No fingir que solve03 emitió candidato o que pasó su cierre original. Presupuesto120s de operación numérica, sin contar lectura/hash de fuentes; memoria1.5GiB y RAM libre3GiB antes. Si falla un gate, no variar umbrales ni repetir exportación automáticamente.

Antes del caso real: fixtures de cadena, fixed-center, ciclos compatibles, cotas incompatibles, orden invertido, NaN/dimensiones/fijos; contrastar resultados contra reachability exhaustiva en grafos pequeños. Autor puede usar colas; consumidor debe reconstruir y comprobar con una implementación distinta (por ejemplo relajaciones síncronas sobre arrays) y no importar el proyector para decidir PASS. Comprobar también una perturbación que viola cotas/orden y otra que incumple objetivo/corrección.

Consumidor del sector: adaptar explícitamente el contrato de `verify_real_sector_continuation.py` a una procedencia nueva de cuantización, manteniendo reconstrucción de matrices/dominio/witnesses, KKT del estado continuo real, geometría global/sector, agua seca fija, civiles y fuentes/deploy. Comparar q real contra la proyección independiente y su bound previo. Un PASS se llama PASS_ORDER_CLOSURE_SECTOR_OFFLINE, no PASS de la continuación anterior ni del mapa. Fuente y fixture revisados antes de la única exportación/consumo.

La integración EV93 es posterior:39variables y40nodos fijos difieren deB en el contexto260; no sustituir el contexto entero. Componer delta y volver a comprobar contraEV93 antes de compilar. Foco Narva se tramita aparte. Sin cliente gráfico mientras siga desktop_all_black; sin aceptación BASE1.0.
