# Orilla de Narva, laguna y hueco de cobertura del delta

## Resultado

La laguna está observada en el juego sin menú. El piloto local de orilla de
Narva no se promueve: suaviza el talud pero deja una franja somera oscura.
La revisión adicional encontró BALTIC-013 en el delta; su corrección continúa
en `../v30-delta-fairways-2026-10-02/`, partiendo de la copia Luga y excluyendo
este piloto de Narva. El paquete canónico V30 69140d41 sigue intacto.

## Ensayos identificados

| Ensayo | Mundo | Evidencia | Alcance |
|---|---|---|---|
| 77d33324 | V30 69140d41 | `../v30-runtime-2026-10-02/lagoon-final/` | Laguna real, menú superpuesto; no imagen limpia |
| A 90806e21 | V30 69140d41 | `runtime-A/` | Laguna y Narva sin menú; END2; cierre orderly_close |
| B d4e404f6 | Piloto d9f585e6 | `runtime-B/` | Mismos sitios/clima; END2; cierre orderly_close |

Cada cierre conservó líneas de terminación de cliente y servidor; lease
liberado y kernel Computer Use reseteado. Los logs originales están archivados
fuera de Git, en E:/DayZ-Baltic-Build/v30-shore-pilot/runtime-{A,B}.

La misión `BalticV30ShoreCompareV1.BalticTrial` conserva dos sitios 90 s cada
uno. XY y orientación corporal iguales, pero inclinación de cámara visible
diferente: no llamar comparación píxel a píxel. La sonda temporal de menú
`@BalticVisualUIProbe` compiló y produjo END_NO_PAUSE_MENU en ambos runs;
la rama Continue no se ejercitó. El arranque limpio no se atribuye a esa rama.

## Piloto geométrico y paquete

`plans/v30-shore-pilot.md`, herramienta `tools/terrain/pilot_narva_shore_v30.py`.
NPZ bb270ecc, incluye Luga 1117b4b1. Eleva 199 vértices de agua (máximo 4 m)
en radio 150 m del mirador Narva sur, con transición y soporte del canal
congelado. Error medio de contorno 2,504→0,715 m; triángulos mixtos locales
>35° 40→6. Terreno, carreteras y 19 corredores retenidos pasan offline.

Superficie nueva de 1.024 tiles y WRP derivado bruto con todas las alturas
exactas; nueve puentes y 17.622 piezas de agua conservados. Paquete separado
`@DayZ_Baltic_ShorePilot`, mundo d9f585e6, WRP compilado 33646c3e. PBO real
verificado: 6.827 entradas y paridad con el árbol compilado. Hereda NM V29
eb0f131e: **previsualización únicamente**, no aceptación de navegación.
`preview-package.json` conserva el primer rechazo del whitelist por omitir
texHeaders.bin; se corrigió el comprobador con evidencia, sin cambiar el PBO.

En (1062,4812), B midió suelo 2,524 m, plano pond 2,625 m y profundidad
dinámica 0,0834734 m. El canal útil protegido no cambió, pero ese margen
somero y su aspecto impiden aprobar el piloto como solución global.

## Delta

`delta-audit/` conserva el fallo inicial sobre ejes OSM y los discriminadores.
La medición inicial recortaba 24 m en los extremos y excluía bocas; la
corrección posterior incluye ejes completos y conectores reales. El corte
seco del Pequeño Neva no lo causaba una carretera. El conector posterior del
tronco sí alcanza una reserva de puente: no confundir ambos ámbitos.
