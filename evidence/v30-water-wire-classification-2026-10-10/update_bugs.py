from pathlib import Path
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
p=W/'bugs.md'
with p.open(encoding='utf-8',newline='') as f:s=f.read()
first=s.splitlines(keepends=True)[0];assert first.startswith('> Actualización EV73/74')
new='> Actualización EV75/76 (10-10): revisión Luna localiza dos transiciones gris/ondas en bordes globalvis; los cuatro modelos comparten material y flags. ROI gris345/345 y controlondulado378/378 están sobre fondo bajo el mar: factor común, no causa suficiente. Proyección nativa contrastada. Dos terrenos diagnósticosEV75 rechazados antes de empaquetar; no relajar gates. EV77 comparación wire única en curso, primera referencia inválida por carga, foco manual pendiente. No cerrar018/019 ni promoverEV68. Evidencia: `evidence/v30-water-cause-investigation-2026-10-10/README.md`; estado de motor en HANDOFF.\r\n'
value=new+s[len(first):]
with p.open('w',encoding='utf-8',newline='') as f:f.write(value)
with p.open(encoding='utf-8',newline='') as f:assert f.read()==value
print('Bug register current header updated.')
