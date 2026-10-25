from pathlib import Path
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8');a=s.index('<!-- LIVE-STATE:START -->');b=s.index('<!-- LIVE-STATE:END -->');block=s[a:b]
updates={
 'status':'BASE_1_0_NO_ACEPTADA. EV87-S estático incremental/superficie/nativo PASS, preview aislado instalado; agua dinámica sigue ABIERTA. La serie60s demuestra que rebajar tierra próxima al agua aumenta profundidad escalar fake-wave aunque no haya flags. B sigue referencia operativa. No promover S como arreglo del agua.',
 'candidate':'Referencia EV82-B @DayZ_Baltic_IncrementalBankPreviewV1 f9fb23de; preview EV87-S @DayZ_Baltic_StrictBankPreviewV1, terreno8e239f8e, mundo727fadeaf1a26fb4ae8362cc894e80e83194c64d5062ac7c2512b79879721420; agua3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14 idéntica. Sin aceptación artística/dinámica.',
 'smoothing':'EV87-S334parches/4987alturas,384parches conflictivos excluidos;1110celdas preservadas aB. PASS_INCREMENTAL_NONREGRESSION cc2b94b1, no nuevos>30 ni extremos débiles, cruces≤.468685m. RMS² banco1.42257→1.40929 e interior.75729→.75650. PicoX2220/Z7242 intacto. EV88-Q piloto ancho desdeB en trabajo, no integración conS.',
 'surface':'EV87-S352teselas/1904solapes,615PAA+WRP,6211entradasintactas,4920mipsPASS. Lectura4194304vértices/1212puntos/1205planosPASS V2. Preparadoromitió points enJSON:V1FAILpreservado,V2 corrige referencias sin cambiar misión/snapshot/tolerancia; maxvértice1.52588e−5m,calibrado.000480m.',
 'runtime_lock':'Runs20c41dc7-ac5b-411b-9f9c-04fe28af199d y a1f95dd7-d460-43f0-82e8-8410f5e7c37d SERVER_ONLY cerrados orderly. Lease liberado, ownernull/selfnone/pending0/bancolibre. Ninguna espera de foco.',
 'next':'EV87/build/scalar-probe:241muestras60.002s/178puntos (162todoscambiadosmargenP<.25m+16controles),fake-wave≤.19325m OBSERVADO, no límite universal. 22profundidades>2cm aalturaH frente12consultandoalturaB en mismoH;0flags. Investigar margen dinámico antespromoción. EV88-Q plan50a94dac/autor532373:único solveoffline autorizado trasfixXZcentral; consumidor independiente en curso. No apilar sobreS sinrevalidación. No construiroriginalEV87a714.',
 'handoff':'evidence/v30-global-strict-bank-relief-2026-10-10/README.md +manifest; fuenteexternaE:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/WORKING_STATE.md. 007/016/019/020 ybaseglobal siguen abiertos.'}
for key,value in updates.items():
 lines=block.splitlines();matches=[i for i,line in enumerate(lines) if line.startswith(key+':')];assert len(matches)==1,key
 lines[matches[0]]=key+': '+value;block='\n'.join(lines)+'\n'
p.write_text(s[:a]+block+s[b:],encoding='utf-8')
p=W/'bugs.md';s=p.read_text(encoding='utf-8')
lead='> Actualización EV87-S (10-10): 334 parches/4987 alturas; no-regresión estática, 352 teselas/4920 mips y lectura nativa completa PASS. El JSON de referencias nativas V1 omitía puntos nuevos; FAIL conservado, V2 corregido sin alterar mapa/snapshot/tolerancias. Serie adicional60s: fake-wave alcanza19.325cm nominal,22/162 consultas secas positivas aalturaH frente12 consultandoalturaB;0flags. Agua dinámica y aceptación siguen abiertas. Ver `evidence/v30-global-strict-bank-relief-2026-10-10/README.md`.\n\n'
assert not s.startswith(lead);s=lead+s
lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| BALTIC-007 |'):
  pieces=line.split('|');pieces[2]=' EV87-S ESTATICO/NATIVO PASS; FORMA Y MARGEN DE OLEAJE ABIERTOS ';pieces[4]=' EV87-S334parches/4987alturas, sin nuevos>30; pico piramidal residual enX2220/Z7242 sigue intacto. EV88-Q piloto ancho en revisión. '+pieces[4];lines[i]='|'.join(pieces)
 if line.startswith('| BALTIC-016 |'):
  pieces=line.split('|');pieces[4]=' EV87-S: nueva evidencia temporal de fake-wave hasta.19325m observado, no límite global.22/162consultas con profundidad>2cm frente12 aalturaB; no flags. Rebajes no aceptados como arreglo del shader. '+pieces[4];lines[i]='|'.join(pieces)
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Updated LIVE-STATE and bug registry; prior history preserved.')
