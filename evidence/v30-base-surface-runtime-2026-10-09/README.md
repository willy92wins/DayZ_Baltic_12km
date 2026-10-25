# EV73 — EV72 leído en motor; defecto de agua reproducido

BaseSurfacePreviewV1: mundo a08b96a1f952edca98e525221ed48790051291b8fcc9db7cc7661ea8bacc1335, agua3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14. Run ef3f2fe4-98bb-4878-9a06-1f532934f111, servidor+cliente.

Censo 4.194.304 vértices y1.212 puntos/1.205 planos PASS, error máximo de altura1.52588e-5m. Cero anomalías físicas sobre vértices secos durante el muestreo. Veinticuatro flags de agua ausentes frente al diseño:23ya presentes enEV61 y un punto de costa adicional [2220,9282], suelo y nivel0.65m. No se igualaron fase de ola ni topología servidor/cliente conEV61; no se atribuye esa diferencia al nuevo terreno. Siete controles negativos rechazan registros alterados. Snapshot inmutable evita que el log creciente altere hash/contenido; consumidor solo cambia su ruta de entrada, conserva gates.

La captura233431 reproduce rectángulos grises en el río con tierra texturada, en cámara[2417,65,6745] hacia[2417,0,6950], FOVsolicitado1.1. Agua de planos añadidos, cerca2.1m en el centro del puente, terreno hasta-2.65m. No se ha correlacionado todavía cada borde proyectado con cada objeto. Censo físico, cobertura estática y mipmaps de satélite no certifican render del agua.

La primera cámara reportaba jugador aunque la captura mostraba una vista aérea: pose anterior no preservada con certeza. camera_setid4 quedó sin respuesta y el cliente desapareció; no hay causa aislada. Reattach oficial documentó client_process_dead, conservó servidor y permitió cámara con lectura correcta. No atribuirlo automáticamente al fallo histórico de saltos lejanos. Run cerrado orderly cliente/servidor, logout confirmado; lease liberado y banco libre.

Comparación preliminar full48/vanilla conserva materiales/LODs/flags generales; no es auditoría completa. El lector devuelve property_class='ond' incluso vanilla, por lo que ese campo no se usa como prueba de corrupción.

Continúa EV74 y revisión independiente solicitada por Guillermo. Base1.0 y fallos016/019 abiertos; no se ha corregido el render.
