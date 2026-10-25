# Base Baltic — checkpoint de V29

Estado: persistencia nativa, paquete final y navmesh V29 verificados; consumidor regional PASS. Seis recorridos fisicos de coche en curso.
Fuente operativa: `state.json`. No hay Terrain Builder ni AddonBuilder abiertos.
Computer Use esta reseteado; lease mantenido durante la prueba fisica.

## Resultado nuevo

- V29 `ed6cdaa5`: seis puertas offline PASS; 239.126 secciones viales,
  621.260 extremos de orilla, 631.284 extremos marinos y 81.212 puntos congelados.
  Reserva, Narva, cauces e islas conservados. Siete negativos viales y cuatro hidrologicos.
- `r2.wrp` 1763facc y `r3.wrp` 9cd94334, con cierre/reapertura reales:
  alturas/materiales/poses exactos por identidad. Dos desplazamientos centimetricos
  corregidos en la capa editable. Guardar estaba deshabilitado; no se inventa un
  guardado nuevo. `road-v29-native/ui-persistence-provenance.json`.
- Los exports literales conservan FAIL estricto contra V10 por 670 residuos Y
  heredados inferiores a una micra. Derivados explicitos restituyen solo esos
  floats de agua propia, con limites sin ampliar. Dos negativos reales rechazan
  el export anterior y una pareja sin persistencia.
- Linter de paquete: 4.776 archivos, cero errores/avisos. Compilacion PASS:
  6.827 entradas, 4.775 materiales, 2.048 texturas, paridad con arbol compilado.
  `build-output/regional_road_v29`: PBO da681707, WRP 2c95ab7d.
  Dos errores de adaptacion del wrapper PowerShell corregidos: alias P:/C: por
  identidad de archivo; esquema de negativos por tests/rejected, separado de checks.
- NavMeshGenerator termino las 966.289 teselas, filtro islas y guardo la nueva
  navegacion: `facaf1e3`, 445.971.256 bytes. Estructura completa comprobada;
  generador y run 0a773e30 cerrados ordenadamente.
- @DayZ_Baltic_RoadV29 final: PBO `b3418f92`, WRP `2c95ab7d`, NM `facaf1e3`.
  FileBank conserva exactamente las otras 6.826 entradas. V10 y V33 intactos.
  `build-output/road_v29_freshnav/verification.json` y
  `road-v29-native/final-deployment.json` fijan hashes completos.
- Consumidor V7 PASS: 81.212 puntos agua/tierra, 314 muestras de navegacion,
  15 rutas, maximo error de suelo 0,463 mm. Run fe6af12e cerrado ordenadamente.
  `road-v29-consumer/acceptance.json`. Nueve controles del protocolo PASS.
  El protocolo de agua tambien acepta V33: no distingue versiones de carretera;
  identidad vial acreditada por WRP/paquete y sus consumidores especificos.

## Siguiente bloque

DriveV3 sigue sobre run propio 0c2c9d83: seis recorridos de costa/colinas/sur,
ida y vuelta. La costa ya llego y paro en ambos sentidos. Esperar terminal y
verificar log completo sin cambiar criterios. Referencia b55bd894.
Despues: agua local (referencia 6dd3e26f), carga 0/25/100/0 (f126e20c), vistas
Neva/reserva/sur con las mismas camaras y probes anteriores. Referencias fijadas
antes de ejecutar; ninguna de estas tres pruebas esta aceptada todavia en V29.

## Limites

Las fuentes y FAIL previos permanecen. No hay version1.0 ni aceptacion visual
completa. Textura provisional, vegetacion/edificios pendientes por decision del
usuario. Carga 100infectados no equivale a 80-100jugadores.
BALTIC-005/007 siguen abiertos hasta consumidores y render. HEAD4ff154b7, sin
commit; cambios previos/compartidos preservados. Skill local actualizada con la
persistencia observada y sin convertirla en evidencia de motor.
