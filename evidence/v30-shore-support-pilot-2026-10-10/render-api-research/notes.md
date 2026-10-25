# BALTIC-019: posible discriminador de culling sin otra variante del mapa

Solo lectura, 2026-10-10. No prueba de motor ni causa raíz nueva.

- [EXACT] `P:/scripts/3_game/entities/object.c:97-122`: GetLODS enumera los LOD disponibles; GetLODByName selecciona por nombre. Ninguno informa el LOD que dibujó el renderer.
- [EXACT] `P:/scripts/1_core/proto/enentity.c:774-782`: SetFixedLOD aparece dentro de `#ifdef ENF_DONE`. La búsqueda realizada no encuentra definición de ENF_DONE ni usos vanilla de SetFixedLOD. No tratarlo como API callable para una prueba.
- [EXACT] `P:/scripts/1_core/proto/enentity.c:48-63,117-119,180-188`: existen EntityEvent.VISIBLE / NOTVISIBLE y callbacks EOnVisible / EOnNotVisible; el primero retorna int. Sus comentarios relacionan el evento con participación de la entidad en render cuando se habilita la máscara. `P:/scripts/1_core/proto/enworld.c:182` comenta que las entidades que reciben VISIBLE ya pasan visibilidad de cámara.
- [NO VERIFICADO] Si los ponds estáticos del WRP son instancias de script Object que admiten habilitar esos eventos y si se despachan en este build. La existencia de la firma no demuestra el comportamiento. Tampoco un evento de entidad demostraría por sí solo que su material de agua produjo píxeles.
- [DESIGN] Si se verifica ese contrato, un registro de eventos por objeto en el mismo frame para el rectángulo gris y un control ondulado podría discriminar culling de entidad sin variar geometría/materiales. Exige IDs/objetos inequívocos, control positivo visible, negativo fuera del frustum y evidencia de frame cliente fresco. No implementar aún, ni llamar a un flag VISIBLE prueba de píxeles dibujados.

La página oficial [DayZ Diag Menu](https://community.bistudio.com/wiki/DayZ%3ADiag_Menu) confirma opciones de occluders, entidades ocluidas y modos wire/overdraw con colores distintos para Water y Ocean. Es la vía gráfica ya prevista en EV77; no resuelve la falta de una referencia texturada válida de aquel intento. [RVMAT](https://community.bistudio.com/wiki/RVMAT) describe CalmWater, pero no documenta aquí una causa de los rectángulos. No copiar recetas de WaterSimple antiguo al material de DayZ sin evidencia.

Siguiente investigación acotada, cuando haya lane: confirmar posibilidad de callbacks sobre estos objetos estáticos o rechazarla en fuente; no reiniciar ciclos de variantes de alturas/LOD/materiales. EV73/74 siguen demostrando el defecto visual, no su causa.
