from pathlib import Path
import re

G = Path(__file__).resolve().parent
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')

def main():
    p = W / 'bugs.md'
    original = p.read_bytes()
    text = original.decode('utf-8')
    updates = {
        'BALTIC-005': ('GEOMETRÍA PROTEGIDA; SEIS VIAJES HISTÓRICOS PASS', 'Aclaración10-10: los seis viajes son evidencia del paquete del08-10; la geometría civil protegida permanece exacta, pero la nueva preview no hereda una prueba de conducción. '),
        'BALTIC-006': ('SONDA DE FRENADA VALIDADA; VIAJES FINALES PENDIENTES', 'Aclaración10-10: la corrección de la sonda conserva sus pruebas; los seis viajes no fueron repetidos sobre EV95. '),
        'BALTIC-007': ('EV95 ESTÁTICO/NATIVO PASS; FORMA GLOBAL ABIERTA', 'Actualización10-10 EV95: 66.058 alturas modificadas, lectura nativa completa PASS. El diagnóstico local2209 reduce una arista47,95→37,20 grados, pero sigue rechazado y no se empaqueta. '),
        'BALTIC-010': ('SUPERFICIE EV95 PASS; ASPECTO FINAL PENDIENTE', 'Actualización10-10 EV95: 996PAA/7.968mips y lectura nativa PASS. El siguiente suavizado seco global aún no ha pasado su consumidor ni generado superficie. '),
        'BALTIC-015': (None, 'Recomprobación10-10 EV95: los45 intervalos históricos conservan4.592 estaciones centrales secas segúnP/F;2.426 sin plano. Se repitió el muestreo triangular actual con4controles; no es censoODOL ni explicación de los recuadros. evidence/v30-global-bank-extension-2026-10-10/diagnostic-integration-checkpoint/current-crossings/run-01/report.json. '),
        'BALTIC-019': (None, 'Actualización10-10 underlay A: tres fotogramas reproducen gris con tierra cargada; pan/restauración confirma actividad3D y1.225 alturas nativas concuerdan. ComparaciónB/A-prime pendiente de banco libre; no se atribuye causa a sombras, LOD ni foco. evidence/v30-global-bank-extension-2026-10-10/diagnostic-integration-checkpoint/underlay-A-analysis/analysis-A.md. '),
    }
    for bug, (status, prefix) in updates.items():
        lines = text.splitlines(keepends=True)
        found = 0
        for i, line in enumerate(lines):
            if line.startswith('| ' + bug + ' |'):
                parts = line.split('|')
                if prefix in parts[4]:
                    raise ValueError(f'Already updated: {bug}')
                if status:
                    parts[2] = ' ' + status + ' '
                parts[4] = ' ' + prefix + parts[4].lstrip()
                lines[i] = '|'.join(parts)
                found += 1
        if found != 1:
            raise ValueError((bug, found))
        text = ''.join(lines)
    if p.read_bytes() != original:
        raise ValueError('Concurrent bugs.md edit')
    p.write_bytes(text.encode('utf-8'))
    print('Updated six bug rows; no bug closed.')

if __name__ == '__main__':
    main()
