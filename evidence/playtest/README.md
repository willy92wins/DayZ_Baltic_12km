# Baltic 12km — primer paquete de prueba

29-09-2026. **PBO compilado y comprobado; carga en DayZ pendiente.** Este paquete es un prototipo del terreno regional con el cruce de Narva. Todavía no es la versión 1.0 jugable.

## Contenido

- `Addons/narva_trial.pbo`: mundo `BalticTrial`, 12.288 × 12.288 km, 2048² muestras de 6 m; puente vanilla y corrección local de accesos. Referencia los assets vanilla instalados.
- `mpmissions/BalticTest.BalticTrial`: misión independiente, aparición junto al acceso occidental y observador automático diez segundos después de inicializarse. Economía vacía, sin loot ni IA; sin partidas guardadas incluidas.
- `evidence/`: trazas, verificaciones y registro del build. `source/`: entrada propia exacta de la compilación. No se incluyen modelos vanilla extraídos.
- `tools/verify_playtest_probe.py`: contrasta una futura lectura de misión con la lectura V3 real de Buldozer. Un fixture sintético no acredita ejecución del juego.

## Lo comprobado

| Prueba | Resultado |
|---|---|
| Accesos de Narva en Buldozer | 612 muestras; ambos extremos de 8 m a 2 m, sin desnivel medido respecto al tablero. |
| Persistencia tras reabrir Terrain Builder | 4.194.304 alturas coinciden dentro de 5,01 mm; posición del puente conservada en el WRP exportado. |
| Compilación | AddonBuilder/Binarize concluyeron; WRP empaquetado OPRW v29 y config binaria. |
| Contenido efectivo del PBO | 420 entradas, incluidos 367 RVMAT y 50 PAA; paridad byte a byte con la salida compilada. Puente presente, pond de diagnóstico ausente. |
| Misión, offline | Un script revisado por linter, cero errores/avisos; 15 XML parseados. No equivale a compilar la misión en DayZ. |

PBO SHA-256: `6d6b1c163412e92a221d8b7580e6943eec9818f7e08e894359e84b03fca582f0` (24.806.932 bytes).

El exportador WRP incluye el pond aunque esté oculto en Buldozer. Se retiró exclusivamente su registro de una copia destinada al build; el proyecto nativo permanece intacto. Binarize aceptó esa copia. No se ha probado todavía su comportamiento dentro del juego.

## Siguiente prueba

El conector DayZ MCP rechazó `session_status` con `MCP tool call requires approval, but approval policy is never`. Es una restricción del canal de herramientas, pese a la autorización del usuario. No hubo respuesta del daemon, lease, lanzamiento ni cambio de procesos de juego. No eludir ese rechazo por otro transporte.

Cuando el canal vuelva a estar disponible:

1. Consultar el estado compartido y comprobar la política/registro del proyecto. No se ha verificado que este proyecto nuevo esté registrado para lanzamiento. Usar el runbook `dayz-mcp-agent-session-protocol.md`.
2. Preparar un destino de despliegue propio y verificar allí el SHA-256 del PBO; usar esta misión con almacenamiento nuevo. Registrar los hashes de misión y la lista efectiva de mods. No reutilizar una misión de otro proyecto.
3. Lanzar mediante `dayz_test_run`, conservar su `run_id` y adoptar el run según el protocolo. Exigir mundo `BalticTrial` y ausencia de errores de compilación tanto de servidor como de cliente.
4. Recoger `$profile:baltic_trial_probe_v1.log`. Contrastar sus 612 muestras con `evidence/narva-probe-v3.log` mediante el verificador; tolerancia máxima de paridad 2 cm. Un registro sin marcador final o de otro mundo debe fallar.
5. Comprobar visualmente las manchas, recorrer ambos accesos a pie y en vehículo y probar caída/nado/salida. Las consultas de superficie no prueban colisión ni locomoción. Cerrar solo el run propio por el lifecycle guard.

Ejemplo de verificación offline de un **registro real ya recogido**:

```powershell
python tools/verify_playtest_probe.py --log <registro-real> --baseline evidence/narva-probe-v3.log --out <resultado.json>
```

## Pendiente para la 1.0

Agua elevada y canales funcionales, corrección regional de costas si la prueba lo requiere, poblaciones y vegetación vanilla, carreteras y cruces, spawns/economía/loot, rutas de IA, diseño occidental y pruebas de rendimiento para 80–100 jugadores. La variante Z definitiva, densidad urbana y ubicación del búnker siguen sin fijar. No se cambiaron el recorte ni la escala global para resolver el ensayo local.

El pond visible estuvo asociado a dos crashes de cierre de Buldozer; oculto hubo tres terminaciones normales. El mecanismo sigue sin aislarse. Las manchas negras persistieron con cuatro y seis materiales; el build no demuestra haberlas corregido.

Referencias: [ejemplo oficial Test_Terrain fijado a commit](https://github.com/BohemiaInteractive/DayZ-Samples/tree/da5e5437c9502620d9853fb6eed14701135ab2ea/Test_Terrain), [muestras oficiales de economía](https://github.com/BohemiaInteractive/DayZ-Central-Economy). Copernicus GLO-30, ESA WorldCover y © OpenStreetMap contributors sustentan la base regional; procedencia detallada y encuadre aprobado en los entregables GIS anteriores. Google Maps se utilizó como referencia de encuadre, no como textura del terreno.
