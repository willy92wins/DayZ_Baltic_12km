# Auditoría de P desconocido contra caras de agua compiladas EV93

## Alcance

Solo las áreas `P=NaN` de `Narva_23` y `Luga_0` del GeoJSON contractual. No se cambia P, H, WRP, PBO, geometría ni umbrales; no se ejecuta DayZ. La salida describe cobertura XZ de triángulos estáticos ODOL y su relación vertical con H. No afirma comportamiento del agua en runtime.

## Identidad de EV94

La consulta usa el índice EV93 completo (manifest y nueve shards pinneados). Se admite para EV94 solo si: el `stage.json` es el esperado; `source_wrp_sha256` coincide con la fuente del índice; el stage conserva los 18.033 registros de objeto WRP byte por byte (`stage.py` compara `obj['bytes']` antes/después); el PBO de agua del stage coincide con `base_identity.water_pbo_sha256`; y el WRP staged/candidato de alturas y P/H coinciden con los hashes del stage. Los 18.024 objetos del índice son los objetos que el builder seleccionó por nombre `baltic_water_v30` y enlazó en bijección con bounds; los nueve restantes son objetos WRP fuera de ese selector, no caras de agua omitidas por un conteo supuesto.

## Método

1. Rehash de manifest/shards EV93 y fuentes de entrada al inicio y al final. Una sola carga de `FaceRangeIndex`.
2. Para cada corredor, reproducir el recorte nativo de EV88: `x=c*6`, `z=12282-r*6`, dos triángulos NW-SE `((0,1,3),(0,2,3))`; conservar solo las porciones dentro de celdas donde P no es finito.
3. Agrupar celdas desconocidas contiguas por fila y consultar el índice con `kind=physical` y `kind=visible`. El índice es solo broadphase: recortar cada cara candidata exactamente contra la porción corredor∩celda∩triángulo nativo. Distinguir caras degeneradas/contactos de área positiva.
4. Medir por tipo de LOD y celda: área P desconocida, unión cubierta, hueco XZ, área superpuesta por al menos dos caras y la diferencia física-visible. En superficies superpuestas, registrar cada cara y el rango de separación Y entre pares realmente solapados.
5. Para cada recorte de cara, evaluar su plano Y(X,Z) menos el plano H del triángulo nativo en todos los vértices del polígono recortado. Al ser la diferencia afín, esos vértices contienen los extremos; etiquetar arriba, enterrada o cruce/contacto. No convertir el resultado en una cota de calado de navegación ni inferir que P=NaN significa seco.

## Controles

Fixture analítica positiva: dos triángulos horizontales coincidentes cubren exactamente media celda desconocida; el cálculo debe dar media área cubierta, media sin cara y media área con capas superpuestas, con separación Y conocida. Control negativo: un triángulo cuyo bbox intersecta la celda pero cuya geometría no toca el recorte debe contribuir cero área. Control altura: cara a Y=2 sobre H=0 da clearance 2; cara a Y=-1 da clearance -1. El test ejecuta los mismos helpers de clipping/overlay del consumidor.

## Presupuesto y salida

Una carga del índice (118.383.540 bytes en los nueve shards), solo las máscaras desconocidas de estos dos corredores (aprox. 991,008 m² según el informe previo), máximo 5 minutos tras cargar el índice y máximo 250.000 caras candidatas únicas. Si se rebasa un límite o deriva una identidad, cerrar `INCONCLUSIVE` sin clasificar NaN. Salidas nuevas: `audit_unknown_corridors.py`, `test_unknown_corridor_geometry.py`, `unknown-p-audit.json`. Ninguna otra superficie se recorre.
