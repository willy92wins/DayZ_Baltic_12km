# A/B de satélite a distancia

Autorización: petición viva de corregir los cuadros y continuar; prueba aislada,
sin cambios de producto. La prueba magenta ya mostró cortes y grandes regiones
magenta en vista aérea. Confirma participación del satélite; no identifica por
sí sola el mecanismo ni descarta agua regional incorrecta.

## Ensayo único preparado

[DESIGN] Reutilizar el satélite global existente de 2048² a 6 m/píxel, convertido
por ImageToPAA. En una copia del PBO baseline, todos los Stage0 apuntan a él con
la misma transformación worldPos sobre 12.288 m. Mantener Stage1/máscaras y
Stage2–10/detalles sin cambio. WRP, config y navegación idénticos byte a byte.
No modificar el proyecto Terrain Builder ni sus fuentes de terreno.

Contrato leído: `tb/narva_trial/data/layers/P_000-000_L00_L01_L02_L03.rvmat`:
Stage0 usa TexGen3; Stage1 usa TexGen4; ambos worldPos. La copia compilada del
material también se recuperó con CfgConvert -txt y conserva ese contrato.
El CLI instalado documenta -txt, -bin, -dst y -rvmat. No escribir binarios a mano.

## Puertas y presupuesto

1. Offline: mismo conjunto de entradas más un PAA; solo RVMAT y texHeaders
   pueden cambiar. Descompilar los RVMAT nuevos y verificar Stage1–10 y TexGen
   no satélite contra los materiales originales descompilados. Rechazar cualquier
   ruta ausente, material sin Stage0/TexGen3 único o pérdida de opacidad.
2. Motor: mismo mundo y zona, vista cercana y aérea. PASS del discriminador si
   desaparece el desplazamiento/corte de satélite con costa/río correctamente
   situados. FAIL si sigue. INCONCLUSO si no carga o no se obtiene vista comparable.
3. Un ensayo visual de esta variante. Si no discrimina, cambiar el método de
   observación o revisar selección de materiales del WRP; no cambiar alturas.
4. Restaurar baseline al terminar salvo resultado visual claro y validación
   suficiente para conservar el candidato básico. No declararlo solución final
   de arte: el satélite sigue siendo WorldCover coloreado a 6 m/píxel.

Límites: quitar la dependencia entre mosaicos mediante un Stage0 global puede
ser un remedio para la maqueta, pero no prueba cuál es el defecto del compilador,
LOD o selección de material. No demuestra rendimiento de 80–100 jugadores.
