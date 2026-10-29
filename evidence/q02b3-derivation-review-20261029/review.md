**Revisor:** Claude Fable 5.1 (claude-fable-5-1), solo lectura, sin herramientas.

**Veredicto: SOUND-with-fixes.** La derivación es equivalente al caminante sellado L146-169 en todos los casos que pude cubrir; las fallas son de especificación de contrato, no de la prueba.

**Rangos de árbol.** El descenso L=M+a, R=M+b con selección de bordes impares y división entre 2 es la descomposición canónica semiabierta. Invariante correcto: seleccionados disjuntos ∪ restante = [a,b). Como b≤m, ninguna hoja de padding i≥m entra jamás en un rango. Igualdad con Plo[b]−Plo[a] y Phi[b]−Phi[a] vale por asociatividad entera exacta. Correcto no afirmar Plo[b]−Phi[a]. Falta: la comprobación de bits antes de sumar debe aplicarse también a cada nodo interno al construir; un fallo ahí debe ser Resource (inconcluso), igual que L143, nunca Bad.

**Costura.** Forward cruzado [c,m)+[0,c+k−m) y reverse cruzado [0,c)+[m+c−k,m) coinciden con _edge_at L137: en reverse el paso i toca la arista to=(c−i−1)%n, de modo que k pasos cubren c−1…c−k mod n, que es exactamente esa unión. Abierto: steps=c o n−1−c garantiza c+k≤m y c−k≥0. Correcto.

**Localización por bisección.** Equivalencia probada con el bucle L154-165:
- Sea cand el primer i con prefijo_lo(i+1)>h. Para j<cand, N_lo(j)≤h, así que el interior (S_hi<h<N_lo) falla, y el inicio exacto S_lo(j)=h implicaría prefijo_lo(j+1)=h+lj>h, contradicción si lj>0.
- Para j>cand, S_lo(j)≥prefijo_lo(cand+1)>h: ni exacto ni interior.
- Si cand no cumple ninguno de los dos predicados, el sellado termina el bucle y cae en L166-169; la regla "T exacto=h y abierto → última arista t=1; h>T_hi → OUT_OF_RANGE; resto BOUNDARY_UNCERTAIN" reproduce esas líneas.
- Observación: la equivalencia no requiere li>0 en realidad (aristas con lo=0 nunca cumplen ninguno de los dos predicados ni en sellado ni en bisección), pero exigirlo como contradicción explícita es conservador y aceptable. La justificación del piso: q≥(1e-8)² ⇒ floor(2^48·√q)≥2.8·10⁶>0. Fix: el contrato debe definir el umbral como comparación racional exacta sobre q, no sobre float.
- Vecinos cand±2: por el argumento anterior jamás pueden cumplir el predicado; son coste puro. Aceptable si se declara no normativo, pero sugiero quitarlos para que ops sea predecible.

**Igualdad y fronteras.** h=0 con steps>0 → arista 0, t=(0,0) coincide con L151-152. steps=0 → centro o OUT_OF_RANGE coincide con L148-150. El caso T exacto=h en cerrado no se alcanza porque SUPPORTED exige 2h<per_lo. Fix de orden: el sellado evalúa DEGENERATE (L190) y soporte (L193-204) antes de localizar; el diseño enuncia la localización de h=0 como si fuera incondicional. Debe mantenerse el orden sellado.

**Estación.** t=([h,h]−[Slo,Shi])/[li,ui] coincide con L159; con li>0 el denominador es estrictamente positivo, y el rechazo fuera de [0,1] coincide con L163. Correcto distinguir esta resta local de la resta cruzada de prefijos.

**Caps.** 2M−1=32767 nodos con M≤16384 es coherente. Fix: cadenas con m>16384 deben producir estado inconcluso registrado con causa, no silencio ni truncado. Fix: el campo ops del consumidor diferirá del sellado por construcción (ticks por nodo vs. por arista recorrida); los 54 fixtures deben excluir ops de la comparación y comparar solo estado/estación/soporte, o la regresión fallará sin error matemático.

**Formato parcial.** Prefijo 0..k con terminal íntegro y fsync previo es consistente; correcto que una cadena a medias no cuente y que TIMEOUT externo no certifique el último terminal. Universo corecount×5 y 538390 quedan correctamente diferidos a metadatos sellados.

**Correcciones mínimas antes de contrato:**
1. Chequeo de bits también en construcción de nodos, fallo → Resource.
2. Umbral li>0 definido como comparación racional exacta sobre q.
3. Orden DEGENERATE → soporte → localización, idéntico al sellado.
4. m>16384 → estado inconcluso explícito.
5. Excluir ops de la regresión contra fixtures; retirar o declarar no normativos los vecinos cand±2.

Con estas cinco, la derivación es suficiente para pasar a contrato. No se afirma rendimiento ni naturalidad; los frentes humanos siguen abiertos.
