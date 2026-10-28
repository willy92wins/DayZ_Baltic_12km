Decisión: delegar revisión de plan a Fable 5.1 por CLI nativo, versión 2.1.310 sondeada hoy 28-10. Codex ejecutor/integrador. Read-only, sin herramientas, hijos ni cambios. Una entrega180s <=650palabras; SOUND/SOUND-with-fixes/NEEDS-WORK, riesgos concretos y modificaciones mínimas, límites, termina FIN_REVISION. No es council, no reabrir producto ni geometría. Fuente completa plan debajo y función preflight vigente. B3E código tiene41testsPASS, revisión271.875s adjudicada. El intento NOcompiló: watchdog60.047s lo detuvo después de logoficialOK, antes de report/contrato/control. No causalidad demostrada. Nueva unidad sólo lectura cincoarchivos con hashes esperados: AddonBuilder1479600B, FileBank194480B,CfgConvert1246712B,Binarize24805944B,P:/bin/config.cpp201417B. Se persigue localizar la fase que agota, no certificar entorno ni repetir intento. Sin aumentar tolerancia/timeout ni tocar skills/procesosajenos. Revisa diseño, límite60s, estado exacto y tests necesarios; código diagnóstico aún NOimplementado.

PLAN
# B3E: localizar el agotamiento de preflight

Estado: BORRADOR_PENDIENTE_DE_REVISION. Sólo lectura y nuevos recibos. No build.

## Hechos e hipótesis

B3E dispone de 41 tests PASS y code review Fable adjudicada. La única ejecución
se detuvo por INCONCLUSIVE_RESOURCE: 60.047 s, pico residente 86.49 MB. El log
oficial confirma P:, Tools, DayZDiag, vanilla y junction Mods. No report.json de
preflight, contrato B3E, carpeta control ni candidato: no hubo compilación.
No se atribuye causa a Steam, antivirus, OneDrive, corrupción ni caché.

[HIPÓTESIS] El bloqueo está en una lectura o hash posterior al log oficial.
El consumidor actual no guarda fases intermedias, así que no permite localizarlo.
La comprobación de cinco metadatos muestra cuatro ejecutables de 0.19–24.81 MB
y P:/bin/config.cpp de 201417 bytes. Tamaño pequeño no prueba lectura rápida.

## Unidad independiente propuesta

[DESIGN] Un script stdlib de diagnóstico, sin importar ni ejecutar el preparador
consumido, carga sólo los dos recibos anteriores fijados por SHA256 y obtiene las
cinco rutas exactas: AddonBuilder, FileBank, CfgConvert, Binarize y P:/bin/config.cpp.
No búsquedas recursivas ni seguimiento de junctions fuera de esas rutas. Verifica
cada SHA256 esperado y registra inicio, primer bloque, final, tamaño y duración.
Cada evento se vacía al disco para conservar el último paso si agota presupuesto.
Conserva también tiempo antes/después de leer los dos recibos. Los recibos se
copian por bytes al nuevo directorio, sin modificar originales.

Un padre propio lanza ese script sin ventana, identidad PID/nacimiento y timeout
total de 60 s desde Popen; el hijo no lanza descendientes. Al agotar, termina sólo
ese hijo, guarda timeout y bytes parciales; no reintenta. No aumentar este límite.
No invocar preflight oficial otra vez ni mover/montar P:, editar skills, compilar,
empaquetar, desplegar, solicitar lease o iniciar DayZ. Sin caché que sustituya hashes.

## Interpretación y presupuesto

HASHES_MATCH: los cinco hashes coinciden en esta lectura; no demuestra qué ocurrió
en el intento anterior ni certifica todo el preflight. HASH_MISMATCH: conservar
archivo/ruta/esperado/observado y bloquear continuación. INCONCLUSIVE_TIMEOUT o
INCONCLUSIVE_IO: preservar fases, no declarar válido el entorno. Un fallo de
formato, ruta, esquema o hash de los recibos también es inconcluso.

Una revisión independiente de plan de hasta 180 s, entrega breve. Tras adjudicar,
implementación stdlib pequeña revisada antes de una única lectura de hasta 60 s.
Positivo y negativos de hash/ruta/error/timeout en archivos temporales antes del
censo real, agrupados en una suite de hasta 30 s. Ninguna repetición de B3E ni
reclasificación de su INCONCLUSIVE_RESOURCE. Una futura continuación de binarización
requerirá plan y evidencia propios; B3D continúa sólo OFFLINE_CANDIDATE_ONLY.

ANCLA preflight actual
67: 
68: def preflight(output):
69:     output.mkdir(exist_ok=False);meter.STARTED=time.monotonic();meter.MAX_SECONDS=60;stop=meter.bounded(output)
70:     try:
71:         old=json.loads((R/'dry-road-build-preflight-20261028/report.json').read_bytes());src=Path(old['original_source']);fixed=R/'dry-road-build-preflight-20261028/preflight_syntax_repaired.py'
72:         gate.bind(sha(src)==old['original_sha256'] and sha(fixed)==old['local_sha256']=='5fb698727b6c70e8dfa21267963b54cafa60b1ade8b4df3ebfe6b8124e5fc7f2','preflight_sources')
73:         a=src.read_text();b=fixed.read_text();gate.bind(b.replace("        r'subst P:","        'subst P:")==a,'preflight_literal_only')
74:         try:compile(a,str(src),'exec');syntax='original_compiles'
75:         except SyntaxError as e:syntax=f'{type(e).__name__}:line{e.lineno}:{e.msg}'
76:         spec=importlib.util.spec_from_file_location('b3e_official_preflight',fixed);pf=importlib.util.module_from_spec(spec);spec.loader.exec_module(pf)
77:         log=io.StringIO()
78:         with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):code=pf.main();mods=pf.validate_p_mods();tools=pf.find_dayz_tools()
79:         (output/'official-checks.log').write_text(log.getvalue(),encoding='utf-8')
80:         gate.bind(code==0 and mods is None and str(tools)==old['tools_root'],'preflight_failed')
81:         for p in ('P:/DZ','P:/bin','P:/core','P:/scripts'):gate.bind(Path(p).is_dir(),'dependency_missing:'+p)
82:         pins={str(src):sha(src),str(fixed):sha(fixed)}
83:         for p,h in old['tools_sha256'].items():gate.bind(sha(p)==h,'tool_changed:'+p);pins[p]=h
84:         prior=json.loads((R/'prism-b3-binary-replay-20261028/contract-r1.json').read_bytes())
85:         for p in [tools/'Bin/Binarize/Binarize.exe',Path('P:/bin/config.cpp')]:
86:             key=str(p);gate.bind(key in prior['pins'] and sha(p)==prior['pins'][key],'prior_tool_or_config:'+key);pins[key]=sha(p)
87:         result=dict(status='FRESH_PREFLIGHT_B3E',tools_root=str(tools),pins=pins,original_parse=syntax,
88:                     installed_skill_modified=False,repair='Archived display-literal raw-prefix only; exact source/diff binding verified.',native_environment_certified=False,measurement=meter.memory())
89:         dump(output/'report.json',result);return result
90:     finally:stop.set()
91: 
92: def sequence(build_control,check_control,build_candidate,check_candidate):
93:     build_control();check_control();build_candidate();check_candidate()
94: 
95: def execute(output):
RECIBOS
{
  "status": "INCONCLUSIVE_RESOURCE",
  "measurement": {
    "pid": 63796,
    "parent_pid": 57076,
    "seconds": 60.04699999999866,
    "peak_resident_bytes": 86491136,
    "peak_commit_bytes": 67411968
  }
}
DayZ preflight

[OK]    P:\ is mounted
[OK]    DayZ Tools found: C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools
[OK]    DayZDiag_x64.exe found: C:\Program Files (x86)\Steam\steamapps\common\DayZ\DayZDiag_x64.exe
[OK]    Vanilla data found: P:\dz
[OK]    P:\Mods -> C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop

Preflight complete.
