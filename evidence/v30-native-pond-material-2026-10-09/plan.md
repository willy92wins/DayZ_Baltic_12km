# EV33 — separar el material de las charcas del oceano

Descubrimiento: EV17 cambio WetFloor/NormalPower/FoamPower solo en oceanold/nice/storm. Las caras visibles compiladas de la base usan dz/water/ponds/data/pond_moss_1.rvmat (water_mesh.py:51). Su material nativo Graphics/materials/water/pond_moss_1.emat es MatWaterPool y declara WetFloor0.962, distinto de MatOceanOld WetFloor0.5. Hipotesis: parte del halo sigue el material de la charca, no la humedad del oceano ya ensayada. No es otra cota ni un barrido del material del mar.

[EXACT] Material API P:/scripts/1_core/proto/proto.c:267–294 GetParamIndex,SetParam(bool),ResetParam. No getter del valor; no llamar readback a SetParam. GetWorld.GetMaterial usado y compilado en EV17. EV28 fuente, alturas, agua, materiales y paquete exactos. Addon cliente diagnostico independiente, sin cambios en vanilla ni preferencias.

Una secuencia0(original intacto)->1(WetFloor0 solo pond_moss_1)->2(ResetParam WetFloor). Al menos6 capturas/ciclos de ola por fase, camara constante. Si el efecto es ambiguo, un control de consumo3(NormalPower0 solo mismo handle)->4(reset) en esta misma sesion; no mas propiedades. Watchdog90s restaura lo cambiado. Sin agua congelada ni cambio meteorologico mezclado. Si falta handle/indice: FAIL instrumental y no buscar nombres por tanteo.

Salida: vinculo causal local solo si el halo responde y regresa tras reset; Ocean y ShoreFoam permanecen sin tocar. Si no hay respuesta, no recomendar este parametro. La fisica no depende de este shader y conserva controles EV25. Cualquier correccion de produccion exigira antes demostrar el recurso que consume el motor, el alcance de las charcas afectadas y ausencia de degradacion de la orilla legitima. No cerrar el mapa con este ensayo.
