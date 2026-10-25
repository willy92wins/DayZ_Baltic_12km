Estado actualizado 09-10: C/C1 globales retirados. C1R3P conserva R3 y relieve general con validación offline y motor 28x62 PASS; vistas R3 mejoran taludes pero mantienen giros lejanos angulares. Guillermo confirma residual de agua junto al puente. LAND180 terminó por idle_timeout orderly, no sigue abierto ni sufrió crash. Todos los runs de este bloque están cerrados. Continúa en [censo global y reparación de halos](../v30-global-water-risk-2026-10-09/README.md). El contenido posterior es histórico.

# Valle, contorno y tierra baja — estado 09-10

La forma del mapa sigue sin aceptar. A/A1 y B/B1 son candidatos retirados; LAND160 mejora los parches sobre tierra, pero Guillermo confirma que quedan manchas. LAND180 pasa offline y la serie local R1 cargada no muestra los parches del campo. C, con conectividad nativa obligatoria, está en validación. Ninguna variante es base 1.0.

| Unidad | Resultado | Evidencia |
|---|---|---|
| A/A1: difusión y clases fijas | FAIL de contorno; presupuesto cerrado | verification-a.json, verification-a1.json, waterline-a.json, waterline-a1.json |
| B: reclasificación local | FAIL: 22 nuevos secos inundados y dos húmedos expuestos | verification-b.json |
| B1: ajuste conjunto de alturas y pendientes | Gates físicos de vértices pasan; R3 pierde conectividad y empeora giros | verification-b1.json, native-components-b1.json, contour-native-b1.png |
| LAND160 | Offline PASS; cuatro cotas en motor coinciden; mejora visual parcial | verification-land160.json, land160-visual/runtime-final-record.json |
| LAND180 | Offline PASS; cuatro cotas coinciden en motor; siete vistas R1_far en 101 s y dos vistas media/cercana sin parches de campo observados | verification-land180.json, land180-visual/runtime-record.json |
| C | Campo con 23 soportes de conexión; candidato construido, gates en curso | connected-contour-design.json, authoring-c.json |

La conectividad se mide recortando los triángulos reales contra el campo de agua visible congelado. El componente R3 de 1.938 m² se divide en seis mayores de 1 m². La sonda `flow-continuity-b1.json` mide pérdida de puntos sobre el eje anterior; por sí sola no prueba una rotura porque el cauce puede desplazarse.

LAND160/LAND180 conservan exactamente 1.077.635 vértices de soporte de caras con agua, además de las zonas de ingeniería. Las carreteras pasan sus 77.381 estaciones. No trasladan los planos del agua ni rebajan fondos. La banda protegida junto a orillas/carreteras y su transición pueden quedar bajo el objetivo de tierra. Los negativos rechazan alteración de soporte, cambio de cara con agua, bajada de suelo y entrada sin arreglo.

Runs referencia 4ff6a77f y LAND160 bcdbb4cf cerrados orderly_close, lease liberado. Capturas grises iniciales excluidas de la comparación. La referencia y LAND160 se comparan en la matriz exacta R1_far; la segunda vista centra el control de cota 1,60 m.

LAND180 usa mar normal. Su PBO de mundo es ed152261c5363ef20cbc63fadcc0259c995af0d3170ab8b038a9f2d4f206cb73; agua 542bd4e8 y terreno 88914948. Es observación local en calma, no una envolvente completa de mareas/tormenta ni aceptación global del usuario. El run d7a99c42 permanece abierto en R1_far, lease liberado. Capturas/logs copiados con SHA256 en `preserved-files.json`.

Ticket de foco pedido por Guillermo: **fb-20261008-233507-8b1c**, recibido por `pipeline_feedback`. Reproducción y criterios en `dayz-focus-ticket.json`; no se implementa aquí una toma de foco Windows.

Pendiente: validar C para conservar conexiones y anchuras del agua real, extensión global de juntas, finales, lagos y vistas restantes; después TB y navmesh. Plan y presupuesto en `plan.md`. Los fallos 007/015/016/019/020 siguen abiertos en sus ámbitos pendientes.
