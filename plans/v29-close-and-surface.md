# Cerrar la base V29 y preparar la superficie

Plan aprobado por Guillermo el 02-10-2026 tras la revisión de Claude del handoff
V29 de Codex. Aprobado: fase A completa, fase B a continuación y BALTIC-008
pospuesto. Las fases C y D y los cambios de proceso son propuesta: cada uno
necesita su propia aprobación antes de ejecutarse.

## Por qué este orden

El terreno V29 pasa sus gates offline y sus consumidores en el motor, pero nadie
lo ha mirado todavía, y lo que ve un jugador sigue siendo maqueta: satélite
WorldCover coloreado a 6 m/px y cuatro materiales (`tools/prepare_prototype.py`,
bloque «four-material prototype»; `source/layers.cfg`). La prueba de carga sobre
un terreno vacío no informa sobre 80–100 jugadores (`tools/navigation/verify_ai_load.py`,
lista `limits` del veredicto). Primero se protege lo hecho, después se mira, y
la siguiente inversión va a lo visible.

## A. Poner a salvo — 02-10

1. Commit de texto en la rama `v29-base` (master intacto en `4ff154b`): tools,
   plans, misiones y evidencia de texto de hasta 2 MiB. Quedan fuera los binarios,
   ASC y logs grandes, `diagnostics/` (marcado como ajeno) y 36 logs de runtime
   con SteamID. Todo eso se conserva byte a byte en el checkpoint externo.
2. Checkpoint V29 en `E:\DayZ-Baltic-Archive\checkpoint-v29-2026-10-02`,
   verificado por SHA-256 en origen y destino. Contiene el mod, el proyecto TB,
   la cadena de intermedios V10 → V33 → V29, el build, la evidencia, las misiones,
   el espacio de trabajo de Codex con las fuentes originales y el entorno GIS, su
   intérprete base y un bundle de git.
3. Copia de las variantes antiguas (`tb`, `tests`, `build-*`) en
   `E:\DayZ-Baltic-Archive\workspace-variants-2026-10-02`, misma verificación.
   Borrar originales de C: solo con confirmación aparte, sobre una lista concreta.
4. HANDOFF de una página, histórico aparte en `HANDOFF-history.md` y README
   apuntando a V29.

## B. Cerrar la base V29

- Una ejecución con teleports de jugador: Narva → Neva → reserva → sur →
  orillas donde aparecía agua. Capturas con `camera_set` y `capture_screenshot`
  del MCP, que capturan sin robar el foco: no hace falta Computer Use, solo que la
  sesión de Windows esté desbloqueada.
- La misma secuencia sirve de discriminador de BALTIC-001. El handoff de Codex
  pedía no mover la cámara entre regiones lejanas; aquí se prueba a propósito
  porque un teleport de administrador hace un salto parecido. Si el cliente cae,
  se registra en BALTIC-001 y se vuelve a un grupo por ejecución.
- Criterio: Guillermo juzga las capturas. Se juzgan la forma de la orilla y el
  agua; la textura es maqueta y no entra en este juicio.
- Si pasa: «base de terreno V29 aceptada», con sus límites escritos en el HANDOFF.

### Resultado de B — 02-10

- Run `db477cf8` sobre RoadV29 con la misión limpia `BalticFoundationSPBBasicV1`.
  La captura por MCP desde la vista del jugador funcionó. El cliente cayó al primer
  `camera_set` (cámara de Codex sobre la orilla de San Petersburgo, a ~200 m del
  jugador): BALTIC-001 aparece también sin salto lejano. Run cerrado, lease liberado.
- A mitad de B, Guillermo pidió revisar el agua («cuadrada o poligonal», ¿está donde
  debe?) y los colores del suelo. Se auditó offline todo el mapa contra la referencia:
  `evidence/v29-water-color-audit-2026-10-02/`, scripts en `tools/audit/`.
- La base V29 no se acepta todavía: la auditoría abre BALTIC-009 a 011.

## C. Agua y suelo — sustituida

Sustituida por [water-ground-rebuild-v1.md](water-ground-rebuild-v1.md), con las
decisiones de agua que tomó Guillermo el 02-10.

## D. Antes de mapear — propuesta

Decidir cruces de río, densidad de San Petersburgo y zonas llanas para POI
(aeródromo, base, ciudades grandes). Después, un sector piloto Narva + frontera
con objetos vanilla. Ahí se retoma la medida de rendimiento (BALTIC-008).

## Cambios de proceso — propuesta

- Una diferencia de hasta 1 ULP de float32 cuenta como igualdad. Los 670
  «residuos» de agua de V33/V29 (2,98e-8 a 9,537e-7 m) son exactamente 2⁻²⁵ y
  2⁻²⁰. Los criterios de jugabilidad se miden en centímetros.
- En futuras ediciones del terreno, restricciones flexibles: el cálculo devuelve
  siempre un terreno y una lista de incumplimientos, que se arreglan en su sitio.
  Una sola fila imposible no debe obligar a otra versión.
- Una batería de humo fija (lancha, coche, IA, carga) para regresión, en lugar de
  controles negativos nuevos para cada ensayo.
- Un script con parámetros por fase, en lugar de una copia por versión.
