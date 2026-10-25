# Contorno triangular directo — EV13

Consumidor: optimización local R1/R2 y verificación independiente del terreno guardado. Unidad parcial de P14/P2/P9/P11, no aceptación de toda la base.

## 1. Descubrimiento y alcance

La petición viva autoriza continuar el suavizado completo. EV9 A/B/C ajustaban alturas a formas objetivo; no se reabre su presupuesto. EV13 minimiza los giros de la propia línea de intersección entre los triángulos nativos de 6 m y el campo visible EV12. Mantiene la malla, clases, niveles y representación del agua. Primera unidad: R1/R2; el resto del mapa queda exacto. La mejora de taludes y extensión global requieren unidades posteriores con sus consumidores.

Fuente terreno e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c; campo visible 7a5d0900533670a1e533965b36a6dcf28be2715f96f94ccbfbe6a846bdf98e37; planos físicos congelados d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803. discovery.json identifica 149/207 soportes inicialmente movibles. No demuestra viabilidad del suavizado.

## 2. Método [DESIGN]

Optimizar desplazamientos de altura en los soportes de la orilla, conservando signos de profundidad en todas sus celdas incidentes. Extremos, carretera, plataformas, puentes, corredores, cumbres, mar y controles históricos permanecen fijos. Desplazamiento máximo 2 m heredado de EV9; fondos >=1 m no bajan de 1 m, excepciones no se excavan y ningún vértice físicamente mojado se eleva. Tierra seca conserva al menos min(altura actual, 1,8 m y margen físico previamente exigido). El agua visible y física no cambian.

SLSQP con límites de altura y discos de gradiente por cada cara triangular afectada: pendiente <=max(35 grados, pendiente original). La función usa giros del contorno a intervalos equivalentes a 6 m, penaliza especialmente los mayores de 30 grados y añade una regularización pequeña de desplazamiento. Muestras normalizadas por cadena mantienen dimensión fija; el consumidor final remuestrea por distancia métrica real.

APIs verificadas: scipy/optimize/_minimize.py:54; scipy/optimize/_slsqp_py.py:220-257. Geometría nativa y medición independiente previas: EV9/scripts/verify_contour_valley.py:56-93, measure_waterline.py:27-36. El campo de EV9 ya era el visible: no se atribuye su rechazo a un plano equivocado.

## 3. Puertas cerradas antes de ejecutar

- PLAN §1-2: identidades exactas, metadatos y regiones ajenas exactos, controles/ingeniería/corredores intactos.
- PLAN §2 y EV9: límites de desplazamiento, pendiente, signos de agua, fondo y no reducción de calado.
- P14 y EV9: consumidor reconstruye polígonos triangulares desde el NPZ final, no desde el grafo del optimizador. P90 debe bajar al menos 10% en cada R1/R2; proporción >30 grados y giro máximo no empeoran. Distancia Hausdorff <=4,1 m. El 10% es criterio de utilidad de esta prueba, no una nueva tolerancia del producto.
- P2/EV12: cuerpos significativos, islas y contactos conservados; solape por cuerpo >=90%; sin nueva inundación fuera de las orillas editadas ni huecos de cobertura.
- Contraejemplos cerrados en verify_native_turns.py: plano húmedo completo y triángulo con un cuarto mojado conocidos; contorno recto/codo; alteración de vértice fijo; fondo <1 m; inversión de signo; pendiente excesiva; pérdida de componente/área. No sustituir por comparación contra la transformación autora.
- Runtime pendiente: paquete desplegado con hashes propios, consultas nativas/corridores, vistas R1/R2 y navegación. No promoción a TB ni cierre 007 por PASS offline.

## 4. Presupuesto y parada

Un candidato, máximo 160 iteraciones o 180 segundos por tramo. Una sola reparación adicional únicamente si hay defecto concreto de implementación con repro; no variantes de pesos, sigma, cotas ni umbrales ante un candidato geométricamente fallido. Si no pasa, conservar diagnóstico de las restricciones activas y trabajar otros pendientes; no ampliar resolución o niveles silenciosamente.

Python GIS C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe. Árbol propio claude/codex-handoff-review-74f290, HEAD 7d2cff6 al empezar. Scratch B13 en E:, sin desplegar durante optimización.
