# Profundidad de cámara: prueba acotada

Las franjas paralelas se observan sobre el plano casi horizontal de Ládoga a
varios kilómetros. Hipótesis distinta de materiales: precisión de profundidad
de la cámara libre con relieve comprimido. No está demostrada por la forma.

API real instalada: scripts/3_game/entities/camera.c:35 SetNearPlane(float),
:40 GetNearPlane(). Conservar valor inicial y restaurarlo al finalizar o cerrar.
Mismo WRP/PBO baseline ebc60f4f, pose SPB, FOV, clima y misión. Cuatro fases:
1600/original,1600/10m,6000/original,6000/10m. Medir near efectivo en cada log.
10m es exclusivo de cámara aérea de ensayo, nunca jugador ni ajuste de entrega.

PASS del discriminador si un mismo defecto desaparece al cambiar solo nearplane
con el resto fijo; no llamarlo arreglo del mundo. FAIL si persiste; INCONCLUSO si
faltan pares o el motor no devuelve nearplane solicitado. Una ejecución; solo
repetir si hace falta aislar un resultado positivo. No alterar alturas para
esconder un defecto de profundidad sin demostrar antes su origen.
