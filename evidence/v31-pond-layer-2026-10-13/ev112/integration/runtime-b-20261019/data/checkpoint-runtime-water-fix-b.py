from pathlib import Path
import hashlib,json,datetime
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=O/'checkpoint-runtime-water-fix-b';D.mkdir(exist_ok=False);changes=[]
def write(p,transform):
 raw=p.read_bytes();text=raw.decode('utf-8');newline='\r\n' if b'\r\n' in raw else '\n';s=text.replace('\r\n','\n');new=transform(s);assert new!=s and len(new)>=.9*len(s)
 data=new.replace('\n',newline).encode('utf-8');backup=D/f'{len(changes)}-{p.name}';backup.write_bytes(raw);assert p.read_bytes()==raw;p.write_bytes(data);assert p.read_bytes()==data
 changes.append(dict(path=str(p),before=hashlib.sha256(raw).hexdigest(),after=hashlib.sha256(data).hexdigest(),backup=str(backup)))
def live(s):
 a=s.index('<!-- LIVE-STATE:START -->');b=s.index('<!-- LIVE-STATE:END -->',a);old=s[a:b];new=old
 replacements={'status:':'EV112 offline/OT7 revisado. OT8 ejecutada: 4114 filas validas, puentes10/10 y presa PASS; estricto FAIL por 4 controles con oleaje y271 labios/juntas de hormigon. Correccion fisica aislada de4vertices en validacion, no desplegada. Vista personal instalada, no lanzada.', 'blocker:':'Banco ya liberado por Guillermo; dos runs propios cerrados ordenadamente y leases liberados. No bloqueo de disponibilidad. Pendiente corregir/revalidar los4controles sin relajar gates;015-45/60m sigue PENDIENTE.', 'cleanup:':'Runs8ac2dd30(sonda) ybc28e1e4(temporal) retirados con orderly_close. Capturas preservadas. Sin lease/run propios. Misiones de sonda/vista y diagnostico instaladas. Candidato water-fix-b solo scratch; paquete AE desplegado intacto.', 'next:':'Continuar water-fix-b: validar gates afectados y bosque, integrar solo si invariantes PASS, recompilar/revisar paquete y repetir sonda. Mantener FAIL original y271 juntas como pendiente segun plan5. No usar la propuesta descartada de flags/NoFakeWave. No lanzar cliente.'}
 lines=[]
 for line in new.splitlines():
  key=next((k for k in replacements if line.startswith(k)),None);lines.append(key+' '+replacements[key] if key else line)
 new='\n'.join(lines)+'\n';print(p.name if False else 'LIVE span',len(old),'->',len(new));return s[:a]+new+s[b:]
for path in (P/'HANDOFF.md',Path('P:/DayZ_Baltic_12km_dev/HANDOFF.md')):write(path,live)
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-18-dayz-baltic-ev112-ot1-execution.md')
def update_session(s):
 marker='## Histórico de ejecución, conservado';i=s.index(marker)
 top='''# EV112 — sonda ejecutada; correccion local del margen de agua en curso

Estado vigente19-10,23:35: el usuario libero el banco. Sonda original4114 capturada y servidor cerrado ordenadamente;10/10 puentes y presa PASS,015-18 mejora6/9→9/9. Estricto FAIL: eje30424 seco, old_bed66055/66056 mojados, orilla0 seca,271 labios/juntas de hormigon pendientes por plan§5. No convertir este FAIL en PASS.

Diagnostico temporal30x8 durante58s: los cuatro controles cambian de signo con el oleaje; profundidad = superficie con ola artificial - suelo -0.01, error maximo0.0000051m. No demuestra comportamiento del jugador ni todos los climas. La regla alternativa de flags y NoFakeWave fue descartada: genera190 rechazos adicionales. No se ha cambiado ningun gate.

Correccion fisica experimental water-fix-b: cuatro vertices, terreno07054c46…; eje−0.15m, dos antiguos lechos+0.19m y un vertice enteramente submarino−1.577m. Mantiene linea de costa, control seco vecino, signos de agua nativos/topologia, todas las mascaras, protecciones y pendientes≤35°. Replay exacto con tools/terrain/apply_engine_water_margins_v31.py. Bosque:2.561.015 registros examinados, cero alturas de origen afectadas; falta consumidor completo. G2/G3/G4/G7kit PASS, bury0; G10piedras PASS. G9/G11 son gates de fase que fallan sobre el final: comparacion contra C en curso, sin dispensarlos ni atribuir aun al parche.

Paquete AE original permanece desplegado y sin cambios; OT7R1SOUND-with-fixes sigue vinculado a C, no aprueba automaticamente B. Vista personalBalticBasicEV112.BalticTrial instalada con16archivos, no lanzada.015-45/60m y visual/FPS siguen pendientes. Sin lease/run propio; no push.

Evidencia en E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/: runtime-capture-ae-20261019/, runtime-eval-ae-20261019/, water-temporal-ae/ y water-fix-b/. Continuar desde HANDOFF del worktree. El primer candidato water-fix-a no se integra: bajaba tambien el control seco vecino.

'''
 return top+s[i:]
write(session,update_session)
(D/'manifest.json').write_text(json.dumps(dict(time=datetime.datetime.now().astimezone().isoformat(),changes=changes),indent=2)+'\n');print('Checkpoint',len(changes),'files')
