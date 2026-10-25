# EV92 — quiebro de orilla: piloto offline aceptado por contrato

El único candidato EV92 pasa las 27 puertas del consumidor completo. Cambia 42 alturas en el entorno X2220/Z7242, conserva exactamente el collar y reduce el quiebro focal de 30° a 12,99653°. La energía de curvatura pasa de 221,22639 a 133,90771 (−39,47%). No aparecen mínimos estrictos nuevos ni plataformas constantes 2×2. Las cotas, reservas, fondo mínimo, corredores conocidos y cobertura compilada no empeoran según el contrato congelado.

Esto no resuelve toda la superficie ni certifica agua dinámica, render, navegación runtime o aceptación artística. B permanece referencia operativa; EV92 no se empaquetó. Quedan picos secundarios locales y defectos heredados explícitos. BASE1.0 no aceptada.

## Identidad y evidencia

- `candidate-terrain.npz`: SHA256 `2f068ce5c4609e551e105b589e93ea8053267c9c307de068716b77221727b60a`.
- `authoring.json`: `38cbebaae8fee20c6e79220723c55ad00076ddf37cf5bb907652e6a6820787f4`.
- `consumer/runs/attempt-01/ev92-review.json`: `8ade0780b172a61b463e5cccc2b67f15d709613537c33c26cb5b5c603bceb268`, PASS_EV92_OFFLINE_CONSUMER, 27/27, inherited FAIL_WITH_INHERITED_OPEN.
- `consumer/runs/ev92-any-wet-support-incidence.json`: `6f2433175fbc6567536ecd5511a721415b3000b2369c602ce1981d670424aa77`, incidencia de 65.955/65.955 nodos elegibles con soporte húmedo; 453.263 bisagras, >30° 11.041→11.037, nuevas >30° cero. Es diagnóstico adicional, no cobertura visual.
- `profiles-mesh.png`: `b25fdecbf1aa3e963926c85176f8dad26547b67441899ba298b7ef65411a5ee1`, perfiles/malla a escala fija, inspeccionados. Mayores picos secundarios NS: 0,242 y 0,225 m.

## Por qué difiere de los intentos rechazados

EV90 creó un mínimo y empeoró el collar; queda rechazado. EV91 conservó el collar y eliminó ese mínimo, pero creó una plataforma plana nueva de 36 m²; también queda rechazado y sin empaquetar. Sus fuentes, candidatos y reportes fallidos permanecen intactos.

EV92 aplica una sola interpolación analítica B+α(H91−B), α=0,6769237551186755 derivado del contrato local y escrito con un único cast float32. No hubo barrido de alpha ni otra llamada al optimizador. La dirección EV91 se usa como dato de un nuevo plan; no se presenta EV91 como aceptado. El consumidor verifica la interpolación en toda la cuadrícula, reutiliza explícitamente las 27 puertas congeladas y etiqueta esa adaptación.

## Continuación

`E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/plan.md`: preparar índice compilado reutilizable y cola global de quiebros agudos, antes de autoría global. No copiar el alpha ni el número de variables del piloto. Inventario de crestas 12/24 m separado, sin convertir toda colina en defecto. La prueba gráfica EV89 sigue pendiente del escritorio visible tras desktop_all_black; no hubo un nuevo run.
