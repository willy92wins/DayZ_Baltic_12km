# Piloto local de Flynn's Terrain Tools 1.0.5

Petición de Guillermo: «pruebala, si funciona ganamos mucho». Fecha local
03-10-2026. Prueba sobre copias de V30, sin editar terreno ni desplegar un mod.

| Capacidad | Resultado y alcance |
|---|---|
| Leer fuentes Baltic | **PASS_LECTURA.** ASC 2048², celda 6 m, origen 200000/0; satélite y máscara 12288²; cuatro superficies. Vista regional cargada en la UI. |
| Generar/exportar carretera | **PASS_EXPORT_OFFLINE.** Recta de unos 417 m, 17 piezas, exportación de objetos. Sin ajuste del terreno. |
| Importar en Terrain Builder | **INCONCLUSO.** El editor quedó «No responde» al solicitar un proyecto nuevo, antes de importar; no existe TV4P del piloto. |
| Conducción, curvas, puentes, suavizado, vegetación y navmesh | **NO ENSAYADO.** La exportación no acredita estas capacidades. |

## Identidad y reproducción

- [Release 1.0.5](https://github.com/Naviata/FTT-Releases/releases/tag/v1.0.5),
  67.726.621 bytes. Ejecutable local SHA-256
  `b15f532fe09efc33c5b3935a2183b2ce6ec1f0b7148c545e956e5fa410bc793e`.
- Piloto: `E:/DayZ-Baltic-Build/ftt-pilot-v1`; app en `app/FlynnsTerrainTools.exe`.
  Junction `P:/baltic_ftt_pilot` hacia su carpeta `project`.
- `preparation.json` conserva el recibo histórico PREPARED_NOT_RUN y los siete
  originales/copias. El resultado posterior está en [export-verification.json](export-verification.json).
- ASC `64d4f160b963c28b519a50c9c29564dbe9727facabf7b52d83970eef5b8e6eb4`;
  los siete originales y sus siete copias conservan el hash de preparación.
- [Lista exportada](ftt_roads_pilot.txt), 1.430 bytes, SHA-256
  `ca1776dadbc8e422737a6479428bf2886c22f009c498b5ec1a4a7de0a138f133`.

Flujo observado: abrir la carpeta de fuentes; comprobar rutas en Home; descargar
las bibliotecas desde Settings. La descarga añadió 188 TML, pero el catálogo
seguía en siete modelos. Seleccionar explícitamente
`P:/baltic_ftt_pilot/TerrainBuilder/TemplateLibs` en Home → Project files → Template
libraries → Browse indexó 8.138 modelos y 22 de 24 tipos de carretera.

Roads: `asf1`, 12 m; dibujar una recta corta; apagar **Shape the ground under the
road**, sin cracks, snap 15 ni dual road. Lay road indicó 17 piezas/417 m.
Export as Objects guardó `E:/DayZ-Baltic-Build/ftt-pilot-v1/ftt_roads_pilot.txt`.
No se pulsó Write heightmap. La apertura indicó 9,5 s: observación de UI, no
medición controlada de rendimiento. Las observaciones visuales constan en el
transcript de herramientas; no se guardaron capturas independientes en esta carpeta.

## Verificación de archivos

Productor: [verify_ftt_pilot.py](../../tools/terrain/verify_ftt_pilot.py).

```powershell
& 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe' -X utf8 'P:\DayZ_Baltic_12km_dev\tools\terrain\verify_ftt_pilot.py' --pilot 'E:\DayZ-Baltic-Build\ftt-pilot-v1' --out 'P:\DayZ_Baltic_12km_dev\evidence\ftt-pilot-2026-10-03'
```

- 16 `asf1_25` y una `asf1_0 2000`; ambas resuelven P3D instalados en DZ.
  Lector ODOL independiente: versión 54, sin errores al leer sus LOD.
- X local 5764,511002–6160,763717; Z 6037,191451–6037,229414. Yaw 90°,
  escala 1, pitch/roll 0, campo height 0 en todas las filas.
- Controles negativos: NaN, plantilla inexistente, fuera del marco, escala 0 y
  falta de altura rechazados. No basta contar filas para declarar PASS.
- Los TML conservan `BBRadius=-1` y límites placeholder, aunque la UI indica
  «99.9% measured». No se sabe cómo usa FTT su medición interna. La geometría
  del P3D se leyó aparte; esos XML no acreditan medición ni importación correcta.
- `native/FTT_Pilot_Roads.tml` contiene solo las dos plantillas necesarias.
  Los P3D, el ejecutable y las bibliotecas descargadas permanecen fuera de Git.

## Intento nativo y siguiente discriminador

Terrain Builder mostraba `delta_v30_native`, 10.161 objetos heredados. Se observó
Guardar deshabilitado; al elegir File → New Project dejó de responder. Tras
soltar Computer Use y esperar volvió a observarse el mismo proyecto. No se
importó la lista, no se creó proyecto nuevo y no se exportó WRP. No atribuir el
bloqueo a FTT ni al TXT: el consumidor no llegó a leerlos.

Computer Use liberado. El runtime DayZ estaba ocupado por otra sesión; este
piloto no adquirió ni modificó su lease. FTT y TB quedaron abiertos. La identidad
del editable y los paquetes desplegados se comprueba en [closure.json](closure.json).

Retomar con TB operativo: proyecto/capa aislados, importar las dos plantillas y
el TXT comprobando altura relativa; **height 0 no es una cota absoluta validada**.
Comparar posiciones, juntas y apoyo, guardar/reabrir/exportar y verificar el
consumidor antes de probar un vehículo. El espaciado y los límites del modelo
no demuestran continuidad, colisiones ni conducción. Mantener pendiente una
prueba de curva y suavizado local que preserve canales y rasantes aprobadas.

Documentación fijada en `06f75744c41ff4dd30ebd868acfe25686f4bd67a`:
[Roads](https://github.com/Naviata/FTT-Releases/blob/06f75744c41ff4dd30ebd868acfe25686f4bd67a/guide/roads.md)
y [Settings](https://github.com/Naviata/FTT-Releases/blob/06f75744c41ff4dd30ebd868acfe25686f4bd67a/guide/settings.md).
La exportación de objetos está implementada; Export Road Network figura como
futura en esa documentación. No hay CLI/MCP documentado en lo revisado.

Cierre documental: [document-validation.json](document-validation.json) registra
comprobaciones locales y el validador de skill no disponible por faltar PyYAML.
La auditoría global del vault quedó [inconclusa](vault-link-audit-status.json)
al interrumpirse tras 410 s sin informe. No afecta ni amplía el resultado del
exportador y no se presenta como PASS.
