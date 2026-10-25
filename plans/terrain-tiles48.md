# Ensayo nativo de generación de mosaicos

Objetivo: aislar los cortes y selección incorrecta del satélite a distancia.
La prueba magenta demostró participación del satélite. La variante Stage0 global
fue rechazada y se restauró baseline3c3a; no se adopta como solución.

[DESIGN] Regenerar las capas mediante Terrain Builder cambiando solo el tamaño
de capa de textura de 12 m a 48 m (8 celdas del terreno de 6 m). Conservar
2048² alturas, lado12.288 km, resolución de satélite6 m/píxel, tile512 y solape
deseado16. El solape real se recalcula en TB. Es una hipótesis de compatibilidad
del mosaico/LOD, no un límite universal demostrado del motor.

Referencia de autor: Treee/DayZDocs MapFrames/DayZGoodMapFrameValues.md y
pennyworth12345/A3_MMSI/wiki/Mapframe-Information; orientan capas próximas a40 m.
No convertir la guía de Arma en contrato DayZ. Aquí48 m es una opción derivada
de la celda6 m y debe validarse en el editor y en el motor.

Antes: backup completo de los516 archivos del proyecto TB en
`work/distant-render/tb-before-tiles48`, fuera del repo y sin reparse points;
TV4P SHA5f9390837b3a503977bf9a5f1a67f3a92ad9a066778207f5e1b7076ccec4feeb.
Antes de restaurar comprobar que solo se revierten cambios de este ensayo.

Gates: exportar WRP nuevo y exigir igualdad byte a byte del array de4194304
alturas y registros de objetos con el WRP anterior. Solo pueden cambiar cuadrícula
de texturas, índices y materiales. Completar los slots TerrainX vacíos con el
workaround ya verificado antes de empaquetar. Conservar navmesh propia, porque
el terreno y objetos deben ser idénticos; rechazar si dejan de serlo.

Motor: misión BalticRender y sonda de cuatro poses, clima0.1/0/0/0. Comparar
capturas cercanas y lejanas contra baseline. Si persisten cortes, FALLA y no
adoptar; si faltan pose/clima/captura, INCONCLUSO. Un ensayo de esta configuración;
no variar otros parámetros hasta juzgarlo. Restaurar estado aceptado al terminar.

## Preparación verificada

TB regeneró 318 materiales, 25 satélites y25 máscaras; solape real32px,
cuadrícula256² a48m. La primera generación usó el selector4materiales y
produjo Terrain15/máscaras_lco: rechazada antes de empaquetar por diferir
del contrato aceptado. Se regeneró con6materials per cell(Arma2), que
produce TerrainX/máscaras_lca, y se completaron293materiales/1136slots
vacíos con la paleta existente. No se cambió la paleta de cuatro superficies.

WRP v2 exportado por TB: alturas yambos registros de objetos idénticos
al baseline; evidencia tiles48-native-v2.json. La copia de empaquetado
omite únicamente el pond diagnóstico85bytes, igual que el baseline jugable.
Navmesh yconfig se toman del PBO3c3a, no de fuentes antiguas prenavegación.
Verificación de conteos del PBO parametrizada conservando defaults367/50;
para este caso se exigen318/50 derivados del WRP nativo ylos tiles generados.
La aceptación visual continúa pendiente.
