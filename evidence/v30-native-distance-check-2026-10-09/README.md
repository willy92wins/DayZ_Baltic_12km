# EV31 — distancia de dibujo y bruma

En EV28 byte-identico se ejecuta una secuencia cliente1600 -> vista5000 -> vista/objetos5000 ->1600, con camara y hora fijas. La bruma cercana se retira al ampliar la vista y vuelve al restaurarla. La fuente opaca queda aislada por reversibilidad del ajuste, sin cambiar geometria/materiales. El añadido de distancia de objetos tiene cambios menores en agua lejana; no prueba cobertura global ni arregla el streaming intermitente019.

La fase0 inicial y primera fase1 tenian menu de pausa: se conservan pero quedan excluidas. La secuencia valida comienza tras ui_click continuebtn, restaurando explicitamente1600; no se presenta como referencia inicial intacta. Cada bloque valido conserva >=15 muestras tras5s de asentamiento. El cliente registra ~19FPS durante la escena; no es benchmark, no se midio foco del SO. Distintas imagenes con diferencias pequeñas activan la advertencia heuristica render_frozen_signal; no ocultada.

Perfil de usuario exacto por SHA despues del cierre. Mapa y agua exactos. Run cerrado orderly cliente/servidor, lease liberado y banco libre. Este diagnostico no se incorpora al mapa. La vista lejana de EV28 deja de ser una prueba util de textura mas alla de la distancia configurada; 019 y los halos siguen abiertos.
