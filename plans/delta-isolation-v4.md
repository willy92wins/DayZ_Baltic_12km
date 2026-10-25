# Delta V4: aislar la interacción entre pruebas

El runV3 repetido conserva FAIL8/10 por desviación>7m antes de entrar en los
últimos20m. No llegó a actuar la nueva desaceleración terminal. Salud600.
Ambas rutas comparten extremo; el alineamiento nominal de los relojes, basado
en CallLater60s, sitúa sus centros a3.11m durante el desvío. La posición relativa
no prueba contacto ni causa raíz. Evidencia: full-river-v3/repeat-closed-3.

[DESIGN] Un único run nuevo, solo casos8 y10, secuenciales. Mantener exactamente
geometría, física, mando, criterios y bytes del addon/mapa. Esperar EndCase y
borrado de la embarcación anterior antes de crear la siguiente. Registrar reloj
absoluto del servidor para spawn y fin. Este discriminador cambia la coexistencia
de las lanchas; no modifica el cauce ni aumenta el corredor admisible.

PASS individual: mismos gates físicos y de transicionesV3. PASS conjunto exige
además inicio10 posterior al fin8. Si falla, conservar el run y parar este
discriminador; no retocar de nuevo el controlador dentro de la misma prueba.
Si pasa, atribución limitada al cambio de aislamiento en esta repetición, no
demostración directa de colisión. El runV3 de Narva6 sigue hasta terminar.

Presupuesto: preparación/lint y una ejecución física secuencial (4200s máximo
por caso, normalmente unos15min en total), cierre exacto y archivo de evidencia.
Sin cliente, Computer Use ni nuevas operaciones sobre el terreno.
