# EV18 — consumidores físicos del candidato EV16

Seis viajes de lancha y seis de sedán pasan sobre el terreno desplegado actual. La conducción aporta 4337 muestras activas, salud mínima 1000.0, error máximo de suelo 0.00009167 m y de contacto 0.00471597 m. Los recorridos, controladores y umbrales se fijaron antes de probar; solo se actualizó la referencia de terreno.

Los controles negativos se ejecutaron sobre los logs reales positivos: 11 de lancha y 18 de conducción rechazan daños, falta de motor/movimiento, teletransporte, suelo incorrecto, huecos de reloj y otras corrupciones pertinentes.

La auditoría independiente de caras nativas cubre los 19 corredores principales (36.494 caras; mínimo 0,955609 m) y los cuatro del delta (1.237 caras; mínimo 3,05 m). No aparecen nuevas excepciones de fondo ni inundación seca. La primera implementación del verificador queda preservada como FAIL de instrumentación: mezclaba 19+4 casos con una cuenta esperada de 19 y no era el consumidor exacto aprobado. `geometry-current-exact.json` utiliza ese consumidor y comprueba cobertura poligonal completa.

No se declara toda la red físicamente recorrida, capacidad de barcos medianos, conducción humana, navmesh final ni carga de jugadores. El nombre histórico del estado PASS del verificador no describe las rutas actuales: son costa, colinas y sur, en ambos sentidos. Todos los procesos de esta unidad cierran normalmente.
