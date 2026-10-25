# Aislamiento de `process_memory()` y caché de tipos de puntero

**Dictamen:** el helper original retiene una entrada de `ctypes._pointer_type_cache` por llamada. En 10.000 llamadas el control que solo eleva `Counters` a ámbito de módulo retiene una entrada, en vez de 10.000; además la memoria privada/RSS queda casi plana. Esto demuestra un mecanismo de crecimiento atribuible al helper en la prueba aislada. No demuestra que explique por sí solo el pico de 1,614,667,776 bytes del intento ADMM ni autoriza repetirlo.

## Evidencia reproducible

La corrida válida es `attempt-03/summary.json` (SHA-256 `E426FD1644D68A1D390A4C04A3D78947C36DF32F88C8F350DE347036690FA199`). Son dos intérpretes GIS Python frescos, 10.000 llamadas cada uno, con límite de 30 s y 256 MiB por worker. El padre PowerShell toma `Get-Process` del PID emitido por cada worker cada 20 ms; el worker se mantiene vivo un segundo después de terminar. Ambos finalizaron con código 0, sin timeout ni rebasar el límite. El SHA de `solve.py` fue `7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149` antes y después de cada worker.

| Medida | Original, PID 138368 | Clase elevada, PID 17664 |
|---|---:|---:|
| Delta `_pointer_type_cache` | +10.000 | +1 |
| Tiempo interno de 10.000 llamadas | 0,4685 s | 0,1569 s |
| Working set externo inicial → pico | 43.208.704 → 96.870.400 B (+53.661.696) | 19.804.160 → 19.828.736 B (+24.576) |
| Memoria privada externa inicial → pico | 35.467.264 → 89.743.360 B (+54.276.096) | 12.210.176 → 12.210.176 B (sin crecimiento observado) |
| Pico del working set visto por el helper | 96.841.728 B | 20.877.312 B |

El baseline difiere entre intérpretes frescos; por eso se comparan los deltas dentro de cada proceso, no los tamaños absolutos. La medición externa y la llamada nativa coinciden estrechamente en el original. En el control cacheado, el muestreador externo pudo no capturar el pico breve de inicialización que sí registró el contador nativo.

## Anclajes del mecanismo y ABI

En el `solve.py` congelado, `process_memory()` define la clase anidada en líneas 46–51 y solicita `ctypes.POINTER(Counters)` en línea 55 en cada invocación. La prueba reutiliza ese AST exacto; el único cambio del control es mover la definición de `Counters` a nivel de módulo. El lector local de ctypes importa `_pointer_type_cache` en `ctypes/__init__.py:255`; `SetPointerType` muestra cómo la caché retiene la clase y el tipo puntero en líneas 307–313. La medición directa en la prueba confirma el crecimiento, así que la conclusión no depende solo de esa lectura del runtime.

La definición también concuerda con el SDK local: `Psapi.h:466–477` declara `DWORD cb`, `DWORD PageFaultCount` y ocho campos `SIZE_T` en el mismo orden que el helper. En el intérprete GIS, `ctypes.c_ulong` mide 4 bytes y `ctypes.c_size_t` 8 bytes, correspondiente al proceso Windows de 64 bits. `PeakPagefileUsage` es el campo devuelto como `peak_commit_bytes`; es la métrica que expone el helper, no una lectura directa de RSS. El control midió RSS y memoria privada independientemente con PowerShell.

## Alcance y cautelas

- `attempt-03` es la única medición válida del padre externo: `attempt-01` midió por error el PID del launcher, y `attempt-02` no obtuvo una muestra útil al terminar el worker antes de muestrearlo. Ambos intentos se conservaron; sus datos no se usan para el dictamen.
- La sonda ejecuta solo el helper extraído del archivo congelado; no ejecuta `solve()`, ADMM, SciPy ni el CG.
- Atribución demostrada: crecimiento de la caché de tipos y ~54 MB de memoria privada en 10.000 llamadas originales frente al control cacheado. El tamaño que alcanzaría en ~160.000 llamadas y su proporción del pico observado son extrapolaciones no verificadas y no se afirman como medición.
- El archivo congelado no se modificó. Scripts de la sonda: `telemetry_pointer_cache_probe.py` SHA-256 `C5A280F389E199D0808C72FCDB142EEBDB66EB02C53EFE6963224460474F91DA`; runner `run_telemetry_pointer_cache.ps1` SHA-256 `F12D89CA0DBE5020E32A6C87838EC109FFAB84726D2F9798934F96109F8C5DC4`.

Salidas originales de la corrida: `attempt-03/original.stdout.txt` SHA-256 `018BBC664D54E267B6D1CE127C21905E147424D436E873035D3AD209F899345F`; `attempt-03/cached.stdout.txt` SHA-256 `56A06127053C35A0A63C450CDCA5266DFFBECEE51E4ED81851199C6EA8544A20`. `stderr` de ambos está vacío.
