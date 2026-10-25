"""Rebuild the Baltic handoff docs: one-page HANDOFF, separate history, plan, README and bugs.md update.

Usage: python apply_docs.py <checkpoint_summary.json> <variants_summary.json> [--apply]
Without --apply the results are written under scratchpad/out/ for review.
Every write is a single binary write + fsync, then read back and compared byte for byte.
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
DRAFT = os.path.join(HERE, "draft")
START, END = "<!-- LIVE-STATE:START -->", "<!-- LIVE-STATE:END -->"

OLD_ROW = ("| BALTIC-008 |INCONCLUSO|Fixture de carga, deriva del objetivo|V29 0/25/100/0 completo; "
           "deriva2.06473m>2m en fases2/3. No causa aislada ni aceptacion de rendimiento|")
NEW_ROW = ("| BALTIC-008 |POSPUESTO|Fixture de carga, deriva del objetivo|Run V29 0/25/100/0 INCONCLUSO "
           "conservado (deriva 2,06473 m > 2 m en fases 2/3). Pospuesto a un sector mapeado: decisión de "
           "Guillermo del 02-10|")
OLD_ROW_001 = "| BALTIC-001 |ABIERTO|Sonda de cámara, transición distante|V3/V4 reproducidos; carga directaSPB estable|"
NEW_ROW_001 = ("| BALTIC-001 |ABIERTO|Cámara programada: transición distante y también camera_set cercano|"
               "V3/V4 reproducidos; 02-10 run db477cf8 cae con camera_set a ~200 m del jugador; carga directa SPB estable|")
NEW_ROWS = (
    "\n| BALTIC-009 |ABIERTO|Agua incompleta y canal navegable uniforme|Faltan Vóljov, Shelón, Msta, Oredezh y otros; "
    "delta del Neva al 10–39 %; ~400 lagunas ≥300 m²; canal de ~60 m uniforme. evidence/v29-water-color-audit-2026-10-02|"
    "\n| BALTIC-010 |ABIERTO|Satélite de maqueta desalineado con el agua|8 colores WorldCover a 6 m/px; 1,10 km² azul seco "
    "y 1,29 km² de agua sin pintar; 4 materiales de suelo|"
    "\n| BALTIC-011 |ABIERTO|Bordes rectos y elipse en el relieve|Rectángulo de San Petersburgo y elipse de la reserva llanos "
    "con 330 m de transición dentro de un relieve ×5; pendiente media 15,6° frente a 2,5° en x≈6250|"
)
BUGS_APPEND = """
## Actualización 02-10 — BALTIC-008 pospuesto

Decisión de Guillermo en la revisión del handoff V29: no repetir la carga sobre
el terreno vacío. El run ebffaa12 conserva su INCONCLUSO y sus límites. La prueba
se retoma con un sector mapeado (edificios y vegetación), que es lo que condiciona
80–100 jugadores; el discriminador de la deriva del objetivo se diseña entonces,
con el contrato fijado antes del run.

## Actualización 02-10 — BALTIC-001 con cámara cercana

Run db477cf8 sobre RoadV29 con la misión limpia BalticFoundationSPBBasicV1, sin la
sonda de Codex. La captura desde la vista del jugador funcionó. Con el jugador en
tierra seca (8208, 1.4, 10590), el primer camera_set del MCP a (8175, 24, 10390)
mirando a la orilla derribó el cliente: su log termina en «client job queued …
kind=camera_set» sin texto de error. La cámara estaba a unos 200 m del jugador, así
que el fallo no exige un salto lejano. Los avisos «Unknown object class 'pond'»
(4.203 en ese run) salen por miles en todos los runs Baltic, también en los que
cierran ordenadamente: no son la causa por sí solos. Mecanismo sin aislar; hasta
entonces, capturas desde la vista del jugador. Evidencia:
`evidence/v29-visual-review-2026-10-02/run-db477cf8.json` y logs con hash.

## BALTIC-009 — Agua incompleta y canal navegable uniforme

Auditoría offline del 02-10 contra los vectores OSM del recorte, en la malla de 6 m
(`tools/audit/water_color_audit.py`). El 97 % del área de referencia está construida
y los 7 cuerpos de más de 10 ha están completos. Faltan del todo Vóljov, Shelón,
Msta, Oredezh, Grib y el canal de Sívers; un tramo del Narva está al 12 %; el delta
del Neva al 10–39 % según el brazo; faltan 520 polígonos de más de 300 m² (unas 400
lagunas y 120 tramos de río). El 86 % de los ríos dibujados como línea no tiene agua.
El Narva–Luga–Neva construido es un canal uniforme de ~60 m, más ancho que el río
comprimido. Plan: `plans/water-ground-rebuild-v1.md`, con las decisiones de Guillermo.

## BALTIC-010 — Satélite de maqueta desalineado con el agua

El proyecto V29 sigue usando `source/sat_preview.png` del 29-09: WorldCover coloreado
en 8 tonos planos a 6 m/px con borde duro. Pinta de azul 1,10 km² de tierra seca y
deja sin pintar 1,29 km² de agua real (el fondo del canal sale verde). El 58 % del
mapa lleva el color de arbolado sin árboles. El suelo usa cuatro materiales (grava,
hierba, coníferas, hierba alta) en 4.775 materiales de tile (`tools/audit/pbo_materials.py`).

## BALTIC-011 — Bordes rectos y elipse en el relieve

`tools/navigation/prepare_regional_outline.py` protege íntegros el rectángulo de San
Petersburgo y la elipse de la reserva, con 330 m de transición, mientras fuera el
relieve se lleva a ×5 de base y hasta ×20–24 en dos zonas. En V29 se ve como una
línea recta en x≈6250 (pendiente media 15,6° al oeste y 2,5° al este), otra en
z≈7950 y una elipse llana alrededor de la reserva
(`evidence/v29-water-color-audit-2026-10-02/relief-zone-edges.png`).
"""


def read(path):
    with open(path, "rb") as f:
        return f.read().decode("utf-8")


def summary_numbers(path):
    s = json.load(open(path, encoding="utf-8"))
    files = sum(j["files"] or 0 for j in s["jobs"])
    gib = sum(j["bytes"] or 0 for j in s["jobs"]) / 2**30
    return files, gib, s["verdict"]


def build_history(handoff):
    i, j = handoff.index(START), handoff.index(END)
    live = handoff[i + len(START):j].strip("\n")
    rest = handoff[j + len(END):]
    rest = rest.replace("\n\n\n\n", "\n").strip("\n")
    lines = []
    for line in rest.split("\n"):
        if line.startswith("#"):
            if lines and lines[-1] != "":
                lines.append("")
            lines.append("#" + line)  # demote one level under the history title
            lines.append("")
        else:
            lines.append(line)
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip("\n")
    head = (
        "# DayZ Baltic 12km — historia del handoff (29-09 a 01-10)\n\n"
        "Retirado de `HANDOFF.md` el 02-10-2026 para dejar allí solo el estado vivo. Describe\n"
        "ensayos anteriores: no decide procesos, permisos ni el estado actual. Los bytes\n"
        "originales están en git: `git show 9d8a5dc:HANDOFF.md`. Aquí se han normalizado los\n"
        "saltos de línea, que el original tenía cuadruplicados.\n\n"
        "## LIVE-STATE de Codex al cierre del 01-10 (literal)\n\n"
        "```text\n" + live + "\n```\n\n"
        "## Historia anterior al 01-10\n\n"
    )
    return head + body + "\n"


def build_bugs(bugs):
    assert bugs.count(OLD_ROW) == 1, "BALTIC-008 row not found exactly once"
    assert bugs.count(OLD_ROW_001) == 1, "BALTIC-001 row not found exactly once"
    out = bugs.replace(OLD_ROW, NEW_ROW + NEW_ROWS).replace(OLD_ROW_001, NEW_ROW_001)
    return out.rstrip("\n") + "\n" + BUGS_APPEND


def write_verified(path, text):
    data = text.encode("utf-8")
    assert b"\0" not in data and b"\r" not in data
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    with open(path, "rb") as f:
        back = f.read()
    assert back == data, f"read-back mismatch: {path}"
    return len(data)


def main():
    ck_files, ck_gib, ck_verdict = summary_numbers(sys.argv[1])
    var_files, var_gib, var_verdict = summary_numbers(sys.argv[2])
    apply = "--apply" in sys.argv
    target = REPO if apply else os.path.join(HERE, "out")

    handoff_old = read(os.path.join(REPO, "HANDOFF.md"))
    assert "\r" not in handoff_old
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    handoff_new = read(os.path.join(DRAFT, "HANDOFF.md"))
    for key, value in {
        "{{UPDATED}}": now,
        "{{CK_FILES}}": f"{ck_files:,}".replace(",", "."),
        "{{CK_GIB}}": f"{ck_gib:.1f}".replace(".", ","),
        "{{CK_VERDICT}}": ck_verdict,
        "{{VAR_FILES}}": f"{var_files:,}".replace(",", "."),
        "{{VAR_GIB}}": f"{var_gib:.1f}".replace(".", ","),
        "{{VAR_VERDICT}}": var_verdict,
    }.items():
        handoff_new = handoff_new.replace(key, value)
    assert "{{" not in handoff_new
    live = handoff_new[handoff_new.index(START) + len(START):handoff_new.index(END)].strip()
    assert len(live) <= 4000, f"LIVE-STATE too long for the injector: {len(live)}"

    outputs = {
        "HANDOFF.md": handoff_new,
        "HANDOFF-history.md": build_history(handoff_old),
        "README.md": read(os.path.join(DRAFT, "README.md")),
        os.path.join("plans", "v29-close-and-surface.md"): read(os.path.join(DRAFT, "plans", "v29-close-and-surface.md")),
        "bugs.md": build_bugs(read(os.path.join(REPO, "bugs.md"))),
    }
    report = {"target": target, "live_state_chars": len(live), "files": {}}
    for rel, text in outputs.items():
        report["files"][rel] = write_verified(os.path.join(target, rel), text)
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
