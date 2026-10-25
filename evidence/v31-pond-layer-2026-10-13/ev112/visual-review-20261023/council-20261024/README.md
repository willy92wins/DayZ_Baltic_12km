# EV112: council y controles reforzados — 24-10-2026

**Resultado: implementaciones verificadas offline; mapa todavía no aceptado.** Muse Wonder1.0 ha participado mediante el CLI nativo autenticado, modelo confirmado en `wonder/identity.json`. La conclusión previa sobre autenticación de OpenCode/Cline no describía ese CLI. Fable5.1 sustituye a Opus por instrucción expresa de Guillermo.

Council completado: Fable5.1, Grok4.7, Gemini4ArgonHigh, Muse Wonder1.0, GLM5.3FlashEXL3 y Qwen3.8. Siete informes de seis familias; MuseGlimmer es suplementario. [Cobertura](coverage.json), [adjudicación de propuestas](ADJUDICATION.md), [revisión de implementación](implementation-review/fable/report.md). No se interpreta consenso como prueba. Los recibos y los informes se conservan por familia.

## Qué cambia

- Los verificadores rechazan entradas no finitas, cero cobertura, expectativas/IDs inválidos y cambios de la cobertura vial fijada. Se mide sobre las aristas de la malla nativa, además del muestreo anterior.
- Colisión: cierre orientado de cada componente, caras degeneradas/duplicadas y conectividad. Comparación fuente/compilado en ambos sentidos; recuento de componentes contra MLOD. Los extremos del piloto se reconstruyen desde fuentes EV107 fijadas por hash, independientes del autor actual.
- Relieve: métricas a 6/12/24/48m y prominencia, por dominio, incluidos los protegidos. Ríos: inventario de angulosidad y anchura de modelos colocados. Estas métricas son diagnósticas; no se inventa un umbral estético de aceptación.
- Bosque: matrices del WRP verificadas con límites G5 y soporte G4. Un mínimo infinito o un disco fuera de la malla ya no produce un falso PASS.

[47 pruebas](results/tests.json), cero fallos/errores/skips, con positivos y negativos. `git diff --check` correcto. Copias exactas de los consumidores y pruebas en `sources/`; hashes de esta entrega en `FINAL-MANIFEST.json`. Los artefactos grandes y los intentos rechazados permanecen en `E:/DayZ-Baltic-Build/qc-council-20261024`.

## Carreteras: R no supera el control nuevo; S3 sí

El muestreo anterior aceptaba R. El consumidor de aristas encuentra **15 incumplimientos**: rango transversal hasta0,042336m y pendiente hasta0,071757, frente a0,03m y0,065. [Fallo reproducido](results/candidate-r/road-mesh-edges-stable.json).

S3 corrige56 vértices, entre−0,041286 y+0,076456m, sin nuevas aristas fuertes empeoradas ni cambio de mar, huellas de agua o protecciones. Las tres etiquetas históricas de agua afectadas son actualmente secas: se comprueba la estrella completa del vértice y la huella actual. Las plataformas afectadas son viales (`build_v30.py:386-407`), no edificios.

- [Consumidor nativo final](results/road-mesh-final.json):77.559 secciones,130.534 intervalos, cero fallos; rango máximo0,0295013m, pendiente0,0645519.
- [Juez P11](results/road-judge-final/review.json):0 fallos transversal/pendiente/cuerda. Cobertura fijada405173842d6066934ded15607e67676ef5c74f6f7725bcd3d1d7e248966c7fb2.
- [Bury/huellas](results/road-merged-s3/merge-verification.json):0 cambios de bury, cuatro matrices exactamente iguales a R.
- [Fuente WRP preparada](results/stage-s3/road-stage-verification.json):2.578.822 objetos conservados,24 alturas forestales ajustadas; resto de bytes de objetos intactos.

S3: `road-candidate-s3/terrain.npz` SHA5cfe6a7fa4d7f0c88e00a47d6a27027fa74476f212536e20bdaf7aee3a7b06fd. Integrado: `road-merged-s3/terrain-buried.npz` SHA6a081028120778d3821574878d4b3845f419c411e661a97d1dc17f3440a4c8a1. WRP `stage-s3/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp` SHAf07926200627c24f26a8da4df54a03df03e5776f92e2821dd676bbb07dab3f77. Todos bajo el directorio E: anterior.

**S3 no está compilado ni desplegado.** P11 comprueba la reserva de terreno; no acredita colocación de carreteras físicas, cruces excluidos, conducción ni navmesh.

## Ríos y bosque

Los dos pilotos pasan [visibilidad entre sus extremos originales](results/pilot-visibility-s3.json) y [topología MLOD](results/pilot-topology-final/review.json), con33.060 componentes de colisión cerrados. Los aprons secos de6m más allá de esos extremos se contabilizan por separado. El [PBO realmente desplegado](results/deployed-pilot-binary-final.json), SHA742fcc8d076df39a8c54cb99f86c3099976219afe00bc62561794f7cc701bec7, pasa35 modelos y comparación bidireccional. Esto no prueba caminar, navegar, todos los receptores ni la calidad visual a media altura.

Bosque R/S3:2.560.922 registros; cero fallos medidos interiores de los límites comprobados. **3.727 discos cruzan el dominio nativo0..12282**, mismos IDs en ambos candidatos: [resultado S3 INCONCLUSIVE_BOUNDARY_SUPPORT](results/forest-s3.json). Parte de sus raíces cae entre12282 y12288; no se presume la extrapolación del motor, no se borran árboles ni se sustituye el consumidor por clamp para aprobarlos.

## Prueba del borde y estado del banco

MCP130 vuelve a responder. Su raíz autorizada actual es `C:/temp/DayZ_MCP_130_dev/mpmissions`; la misión antigua en DayZServer/mpmissions fue rechazada como `mission_not_allowed`. La copia idéntica `BalticQCBoundaryR.BalticTrial` supera preflight:216 puntos,24 raíces reales y192 controles/transectos, con el mundo R y tres hashes verificados. `init.c` es el consumidor V3 existente, sin modificaciones. El valor `clamped_hypothesis` es una hipótesis diagnóstica, nunca verdad esperada para aprobar.

El lanzamiento quedó esperando el lease de LFSkateboard. `wait_for_box_s` limita el banco, no la espera interna del lease. Se canceló exclusivamente nuestro ticket mediante la API de coordinación del supervisor de este chat; no se tomó el lease ni se tocó otra sesión. [Comprobación final](results/boundary-probe-r/final-session-status.json):`self=none`, ambas colas vacías, sin run propio; la otra sesión conserva su lease. **No existe resultado en motor de esta sonda.**

Para retomar: comprobar owner/grace/colas y banco antes de lanzar `results/boundary-probe-r/launch-130.json`; usar el flujo oficial launch→acquire→medir→close→release. El preflight no acredita disponibilidad futura. No volver a ejecutar el helper puntual de cancelación. La misión y sus puntos están copiados en esta evidencia.

## Trabajo pendiente, sin falso cierre

1. Medir el borde y establecer su semántica antes de cerrar los3.727 apoyos;216 muestras por sí solas no prueban todo el dominio. Si requiere corrección, conservar IDs y revalidar soporte/agua.
2. Compilar S3, contrastar WRP/PBO desplegado y ejecutar sonda completa nueva. No atribuirle los786/786 históricos de Q ni aceptar R por el juez antiguo.
3. Revisión visual/caminar de ambos pilotos antes de extenderlos;66 candidatos de extremos, ramas y receptores, dominios protegidos,015-45 y271 labios históricos siguen abiertos.
4. Carreteras físicas/cruces, conducción y navmesh. A/B Chernarus en condiciones equivalentes y carga80–100jugadores: el inventario estático y PresentMon offline no prueban FPS.

Sin commit/push por estas puertas abiertas. Cambios ajenos del worktree conservados. Plan vigente: `plans/ev112-quality-council-20261024.md`; estado actualizado en HANDOFF y sesión canónica. No se modifica memoria Codex compartida.
