# Lecho seco sobre carretera: modelo guardado verificado

MLOD_OFFLINE_VERIFIED. El candidato numérico publicado en42eebfea ya se ha
materializado en cs_kit_118_0000.p3d (d13069d5).82vértices porLOD visible/roadway
y203prismas físicos actualizados, sin variar agua, XZ, juntas, bounds, UV, masa
ni los200modelos restantes. No se ha desplegado ni probado en el motor.

Autor3.594s; consumidor10.171s:1520prismas cerrados/convexos, cobertura total
del lecho, error vertical0, masa9120.9tests y seis mutantes reales rechazados
en30.765s: aguaY, lechoX, UV, normal invertida, techo+5cm, media cubierta
colapsada. Positivo real anterior y posterior. Ningún rechazo depende sólo
de un hash. Revisión independiente Fable5.1 en262.687s, fixes adjudicados
en el plan. El primer autor se detuvo sin escribir por ruta de config ausente;
se sustituyó la suposición por config/prefijo del PBO vigente.

Siguiente: compilación aislada, verificación ODOL/poses/paquete y motor.
No equivale a aceptación visual o global. RAM, c1 y el council ampliado siguen
pendientes; el piloto seco1e85 permanece separado. Ninguna tolerancia rebajada.
