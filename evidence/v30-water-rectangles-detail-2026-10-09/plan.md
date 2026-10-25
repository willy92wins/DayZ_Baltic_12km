# EV74 — rectángulos grises dentro del agua

Petición viva: eliminar las teselas grises a media distancia; tierra ya texturada. Reproducido en EV72, cámara [2417,65,6745] mirando [2417,0,6950], fov solicitado1.1. EV32 estudió halos sobre tierra con otro encuadre; no resuelve este síntoma.

Discriminador único: detalle del terreno original -> máximo -> original con cámara fija. Addon existente BalticDetailProbeV1, sin Apply, watchdog90s; verificar valores/etiquetas reales y readback. No cambios en geometría, planos, materiales ni perfil persistido. Consumidor físico EV73 aprobado pero no certifica render. Al menos3 capturas separadas por fase; control es agua próxima con ondas y tierra adyacente, además de los rectángulos interiores. Si cambia el síntoma y regresa, dependencia del detalle aislada, no mecanismo interno. Si persiste, descartar este control y usar wireframe/material para distinguir terreno visible de agua sin dibujar. Una secuencia, no barrido de opciones.

APIs locales leídas: P:/scripts/3_game/gameplay.c:1320-1478 OptionsAccess Test/Revert, ListOptionsAccess GetIndex/SetIndex/GetItemsCount/GetItemText, GameOptions GetOptionByType. Script existente E:/DayZ-Baltic-Build/v30-native-terrain-detail-20261009/baltic_detail_probe_v1/scripts/5_Mission/BalticDetailProbe.c.
