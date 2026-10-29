Revisión independiente acotada de código RoadC1C. NO ejecutar shell, herramientas, builds ni modificar archivos. Sólo esta cápsula. Devuelve dictamen SOUND / SOUND-with-fixes / NEEDS-WORK con bugs concretos y fixes mínimos, máximo 1400 palabras. Tiempo180s. Codex executor local asignado escribió wrapper y observador; no es revisión de plan otra vez. Examina identidad/ownership/candidato bloqueado, presupuestos, logs, ruta privada/logger, preflight, observador independiente y negativos. COMPILE_PROBE_ONLY no decodifica terreno ni permite motor. Contrato y oráculo previos intactos. Los binarios no se entregan; anclas CLI son literales observados e invocación histórica, runtime sigue abierto. No inventes validación de binpath ni causa por control vacío. No hay captura real aún. Señala tests tautológicos si no prueban el gate.

### C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\plans\ev112-road-c1c-compile-probe-20261029.md
# RoadC1C — sonda compilada del laboratorio

Estado REVISADO_PARA_CONTRATO_Y_SONDA_LIMITADA. P5/P6/P8/P11, preparación del piloto de
pivote vial; ninguna modificación del mapa. Codex planner/integrator y executor
local asignado para el wrapper acotado, revisión entre familias antes de ejecución.

## Hipótesis y límite de aceptación

Observar si la pareja fuente C0, copiada y verificada en C1B, produce artefactos
OPRW con la herramienta instalada. C0 control vacío puede no compilar. Se conserva
el primer resultado sin reintento y sólo se intenta candidato si el control cumple
las puertas de proceso/artefacto. El resultado máximo COMPILE_PROBE_OBSERVED_ONLY:
no certifica objetos0/3 dentro de OPRW, alturas/materiales, pivote, dependencias
transitivas, precedencia nativa ni calidad. Ningún paquete aceptado ni DayZ.
Un PBO que AddonBuilder produzca es subproducto privado de la sonda, no entrega.

## Anclas y descubrimientos

C1B contrato b7d33588, bindingsb632818a, consumidor4c52ddae; dos árboles sellados
480678967B/13786files. No ejecutar de nuevo sus CLIs. Nuevas copias de trabajo
sin hardlinks/junctions preservan los originales. Configlab c054ff97: CAWorld y
DZ_Data/DZ_Surfaces, sin Navmesh/agua/piloto. La herencia no está certificada.

AddonBuilder instalado SHA c113de9cab5e91d27ca0630e360db0a3eca190ec797e1dcad9cdfa70466b45e1,
1479600B. Literales PE guardados en road-c1c-invocation-anchors-20261029:
offset86031 sintaxisCLI; 86651–87097 rutas explícitas binarize/cfgconvert/filebank/
dssignfile/toolsDirectory; 90257 include copia directa; 92575 PNG/TGA conversion;
96765 plantilla Binarize. Literales NO prueban flujo de control ni semántica.
Helper histórico compile_visual_pilot_ev112.ps1:25 es evidencia de invocación,
no entrypoint. Include histórico `*.paa;*.emat;*.xml;*.nm;*.c;*.csv` se conserva
literalmente para esta sonda; no copiar PNG sin convertir por una extensión nueva.
No `-clear`, no `-sign`, no `-packonly`; temp/out nuevos.

logger.xml instalado usa ..\Logs compartido y config permite log4net.Config.
Se copia únicamente el pequeño conjunto instalado AddonBuilder exe/config/DLLs/
steam_appid.txt y en-US/*.dll (excluye copia.pbo) a directorio privado nuevo.
EXE/DLL/config bytes exactos; sólo la copia de logger.xml reemplaza los tres
file.value por rutas absolutas privadas. Guardar original/diff/pins y comprobar
por XML que sólo cambian esos tres valores. No editar instalación ni gobernadas.
La portabilidad de la copia y side effects de Steam/userSettings no se presuponen.
Forzar toolsDirectory y rutas de herramientas instaladas por argv; observar hijos.
No tomar RPT global como recibo propio. Si logger privado no aparece, no atribuir
el global ni certificar aislamiento; reportar NOT_OBSERVED y detener antes de build.

## Fases con puertas

1. Congelar contrato/oráculos antes de wrapper. Inputs: manifiesto/recibos C1B,
   todos los exe/DLL/config copiados y herramientas Binarize/CfgConvert/FileBank/
   DSSignFile instaladas, include literal y nuevos destinos. Inventario reducido
   tools sólo nombres explícitos; cap64files/64MiB porfile/128MiB conjunto.
   No abrir PBO/P3D/WRP semánticamente ni ampliar catálogos.
2. Wrapper copia árbol fuente por manifiesto a work/control y work/candidate,
   comprueba SHA/tamaño/identidad/reparse; sólo 1GiB conjunto. Copia180s/256MiB,
   sin tocar C1B/P:. Verificador propio recorre las copias y sus fuentes porhash.
3. Preflight oficial fresco60s/256MiB, rutas C:\ canónicas. Si SyntaxError213
   persiste, archivar original y copia cuyo único delta es prefijo raw de ese
   literal subst. Compile original debe reproducir SyntaxError; diff y AST de
   copia parseable guardados. No editar skill. Exit no0 bloquea todo lo posterior;
   warnings conservados, no certificación de entorno nativo por exit0.
4. Una invocación privada `AddonBuilder.exe -help`30s/512MiB, sin argumentos fuente,
   para comprobar entregaCLI/noGUI y flags usados. Si rc/recibo/ayuda/log privado
   incompletos, detener sin build. La fuente no se pasa en esta fase. No reintentar.
5. Una pareja ordenada, control primero. [DESIGN] argv: exeprivado, fuente
   work/<arm>/root/dayz_baltic_12km_dev/tb/narva_trial, output/<arm>/out,
   -prefix=dayz_baltic_12km_dev\tb\narva_trial, -project=work/<arm>/root,
   -temp=output/<arm>/temp, -include=include.lst, -binarizeFullLogs,
   -toolsDirectory y los cuatro ejecutables con rutas instaladas observadas.
   No asumir recursos instalados realmente leídos por tener su SHA.
   300s/2GiB RSS por brazo, disco salida2GiB observado, controles cada150ms.
   No promesa de cuota dura de disco/RAM: el hijo opaco puede sobrepasar entre
   observaciones; registrar máximos y matar sólo descendientes PID+birth propios.
6. Gatecontrol: rc0/reasonnull y marcador Build Successful en recibo privado,
   log atado a ventana del proceso, hijo Binarize observado PID/birth/exeSHA/argv,
   exactamente un WRP nuevo en temp, <=128MiB, encabezado OPRW y versión u32
   observada, bytes/mtime/hash ligados. No fijar versión32 sin observarla.
   Rechazar ERROR/FATAL en logs del brazo; warnings conservados. No extender
   blanco de errores por resultado. Si falla, candidato NO lanzado.
7. Observador separado120s/256MiB verifica recibos/ventanas/artefactos por relectura,
   inventario y estado final de work y C1B contra contrato. No importa writer ni
   inventa lector de alturas. Si fuentes cambian, SOURCE_CHANGED y no aceptación.
   Los hashes instalados y los procesos realmente observados van en tablas distintas;
   un hijo demasiado breve para observarlo es NOT_OBSERVED, no identidad ficticia.

## Autoría, oráculos y presupuestos

Codex executor600s contrato/oráculos/wrapper/observador; code review180s, suite120s
256MiB. Una corrección180 por contraejemplo cerrado, una recuperación180 si falta
dictamen. Preparación/copia no ejecuta builds. No nueva ronda del mismo plan.

Oráculos externos literales: rawOPRW/version y bytes opaque vs0WZD, único/múltiple
WRP, controlrechazado bloquea candidato, timeout, rcno0, rc0 sinmarker, log ajeno/
mtime anterior, desconocidoBinarize exe, hijo no observado, fuente mutada, extra
en árbol, loggerXML cambio adicional, reporte/hash co-mutados. Tests usan hijos
sintéticos y artefactos literales, no simulan éxito real de DayZ ni decoder.
Nada de relajar identidad/tiempos ni materializar una copia de fuente después
de su gate para ocultar cambios. Salida metadata32MiB, logs32MiB/archivo.

## Resultado y siguiente

Siempre evidencia privada de herramientas/artefactos, publicación sólo código,
recibos/pins/resúmenes sin vanilla completa. Preparadores y runs consumidos al
primer intento. C1D requiere plan propio para decoder de las muestras obtenidas;
no desplegar ni lanzar juego con un magic/hash. Q03C/Q05 y referentes pueden
continuar en paralelo lógico sin depender de aceptación nativa. C1NOT_REVIEWED,
nueve humanos0resueltos; no confundir esta prueba de herramientas con reparación.

## Adjudicación Muse69.203s, previa a contrato/código

F1–3 aceptadas: clasificar anclas LITERAL_OBSERVED/HISTORICAL_INVOCATION/
RUNTIME_TO_OBSERVE. CWD siempre directorio privado del exe. Include y exclude
con rutas absolutas privadas; exclude literal vacío. Ayuda recibe -help y
-toolsDirectory con raíz instalada. Rc0 más SYNTAX y ayudaCLI más logprivado
del proceso son puerta de arranque; no es una acción libre de efectos .NET/Steam.
work/root contiene exactamente C1B: dayz_baltic_12km_dev, dz, core y bin, sin
junctions. Referencias leídas por el compilador no se certifican por esa lista.

F4 parcialmente refutada: cero objetos NO garantiza ausencia de WRP; la fuente
sí contiene terreno/materiales. No se conoce si compila. Se conserva la puerta
intencionada de artefacto control ANTES del candidato: sin él, no pareja ni
candidato. No rebajar el gate para obtener un candidato. Conservar rechazo
como dato de la hipótesis, nunca atribuir automáticamente la causa al vacío.

F5: todos los descendientes observados; >=1Binarize coherente. Sin observarlo,
PROBE_INCONCLUSIVE_NOT_OBSERVED, no buildfallido. DSSignFile observado sin-sign
es UNEXPECTED_CHILD. Ejecutable hijo desconocido bloquea. -binpath se registra
como parámetro observado; no se atribuye lectura al stage si no coincide. Un
path diferente por sí solo no prueba fallo: la resolución es objeto de esta
sonda, no una promesa de namespace cerrado. Distinguir ARG_BINDING_UNKNOWN.

F6: inventario DLL cerrado junto a AddonBuilder.exe.config. Sólo loggercopiado
se modifica; original instalado intacto. APPDATA/LOCALAPPDATA/TEMP del hijo se
redirigen a espacios propios, pero no se afirma aislamiento de KnownFolders/
Steam. Inventario acotado previo/post de user.config de AddonBuilder bajo
LocalAppData/Bohemia_Interactive y Bohemia Interactive; cap256files/16MiBtotal,
metadata+hash, sin explorar otros perfiles. Logs/salidas separados, no sandbox.

F7: originalSyntaxError es negativo de procedencia; copia con único prefijoraw
es preflight operativo. Su exit no0 bloquea. Si original ya parsea, no parchear.

F8: autoría y ejecución siempre fueron sobres separados; se explicita techo
ejecución1050s, sin incluir600sautoría/180review/120suite. Observador120s es un
presupuesto nuevo previo: C1B51.094s examinó tres conjuntos equivalentes; aquí
cuatro, ~68s extrapolados sólo para presupuesto, NO tiempo garantizado ni cota
probada. No elevar después de resultado. 180copia+60preflight+30help+600pareja+
120observador+<=15drenaje=1005s, resto45scontrol; ningún retry.

F9: RSS sumada de árbol observado. Parada raíz propia primero y descendientes
PID+birth propios después. Drenaje máx5s después de cierre, dos estados de
tamaño/mtime iguales sólo snapshot, no garantía de vaciado tras kill. Fallo/
timeout no certifica integridad de logs ni artefactos.

F10: C1B/instalación y work se reportan por separado. Ambos se comprueban contra
pins; mutación work se conserva como WORK_INPUT_MUTATED y artefacto diagnóstico,
pero bloquea aceptación y candidato en esta pareja. No copiar de nuevo para
ocultarla. No hay dependencias nuevas autorizadas por un fallo. Integrador
adjudica postimagen; no nueva revisión externa ni consenso.


### E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\contract.json
{
  "schema": "road-c1c-probe.v1",
  "root": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1c-probe-20261029",
  "source_stage": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1b-stage-20261029",
  "c1b": {
    "path": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1b-local-author-20261029\\contract.json",
    "sha256": "b7d335883f33629f8e9fc1f1b98018dadb2cb95541a33a643f6805a3bcb3d1c6",
    "bytes": 5175166
  },
  "c1b_consumer": {
    "path": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1b-real-20261029\\consumer.json",
    "sha256": "4c52ddae367fd53e860d8b3cf3a31bbada3e5510715f89ab85a4b7543c0586c2",
    "bytes": 474
  },
  "tool_root": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools",
  "tool_files": [
    {
      "dest": "AddonBuilder.exe",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\AddonBuilder.exe",
      "sha256": "c113de9cab5e91d27ca0630e360db0a3eca190ec797e1dcad9cdfa70466b45e1",
      "bytes": 1479600
    },
    {
      "dest": "AddonBuilder.exe.config",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\AddonBuilder.exe.config",
      "sha256": "e614fcb04d8e3429fab70466261f36383de3bfcd230a058bc196ac0727482bbe",
      "bytes": 5211
    },
    {
      "dest": "logger.xml",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\logger.xml",
      "sha256": "1d24d7d4afb5249efbef3435195bbea4d1a2d6317292637c7f834b69f8470005",
      "bytes": 2546
    },
    {
      "dest": "NDesk.Options.dll",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\NDesk.Options.dll",
      "sha256": "800c0ae0f2acc15be2c89528fe78cea7400799d44ff14cb5a1251371f20c8982",
      "bytes": 22016
    },
    {
      "dest": "log4net.dll",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\log4net.dll",
      "sha256": "ce6ee4fdc783a5bf905f240178ac96eaeb7ede22ffe06a06ba179cd1a0442bd3",
      "bytes": 301056
    },
    {
      "dest": "Utils.dll",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\Utils.dll",
      "sha256": "9203f56eec2ed93193a784ca4ae24b0a172b06f3b981eed14698a7db68548b02",
      "bytes": 265728
    },
    {
      "dest": "SteamLayerWrap.dll",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\SteamLayerWrap.dll",
      "sha256": "d7ef37958e117e29162b0a76baaf4bb47fd0a42b00a0bf3925987ab4ce55e538",
      "bytes": 540160
    },
    {
      "dest": "SteamHelper.dll",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\SteamHelper.dll",
      "sha256": "1a1737e02298a77c8228344558ecfc0820dc5addb7d054882997d2173b50a8b4",
      "bytes": 40448
    },
    {
      "dest": "SharedResources.dll",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\SharedResources.dll",
      "sha256": "90b6d7962e2caa73c7877f051c858a4385660a1e026de306f303604f62f4ddf4",
      "bytes": 170496
    },
    {
      "dest": "steam_api.dll",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\steam_api.dll",
      "sha256": "af17df745250d1814eaa274fff7b0faeb43381e6762e026267e5859778477abd",
      "bytes": 225056
    },
    {
      "dest": "steam_appid.txt",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\steam_appid.txt",
      "sha256": "2e1839933e3283362a7c247f642ff9b78df06df4e3ae0004a3e2bc6abad9cd4c",
      "bytes": 6
    },
    {
      "dest": "en-US/SharedResources.resources.dll",
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\AddonBuilder\\en-US\\SharedResources.resources.dll",
      "sha256": "8687d5fa786794025a681a7dda1e9002402da43832adddb78375140523ed1660",
      "bytes": 127488
    }
  ],
  "tools": {
    "binarize": {
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\Binarize\\binarize.exe",
      "sha256": "1998db17d8eb7b633413855d28af8483d30baafcc0e9a45f992d83f23766b03e",
      "bytes": 24805944
    },
    "cfgConvert": {
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\CfgConvert\\CfgConvert.exe",
      "sha256": "4c4fc15ef9773b42b4191155d4e243d8c95d3156cf7b6f24e7d84dea7cd15a4c",
      "bytes": 1246712
    },
    "fileBank": {
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\PboUtils\\FileBank.exe",
      "sha256": "f89aaeb22421b9158fbbf173f75d52b6f3de69986cb462e58956c78da82c4caf",
      "bytes": 194480
    },
    "dsSignFile": {
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\DsUtils\\DSSignFile.exe",
      "sha256": "098f28b46bfe40ad4cf5c60dd3e570e984fe74ae423090b6d3f2da8d7c4e1e78",
      "bytes": 9467312
    },
    "bin_config": {
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\Binarize\\bin\\config.cpp",
      "sha256": "dcf19f271d6537e6ba45fe6af47cc0865d52768bca05ecc9abc1b0314bc1f4ea",
      "bytes": 199732
    },
    "binarize_steam": {
      "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\Binarize\\steam_api64.dll",
      "sha256": "a44e5537939ae4eebc69000589aa9b2437a667813a1657cc779198bae9b815a9",
      "bytes": 298856
    }
  },
  "include": {
    "path": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1c-local-author-20261029\\include.lst",
    "sha256": "b8f99a686b2888bd57cc2ceb541eded32ec6c489920c7316172892cbd7047976",
    "bytes": 34
  },
  "exclude": {
    "path": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1c-local-author-20261029\\exclude.lst",
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "bytes": 0
  },
  "preflight": {
    "path": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1c-local-author-20261029\\preflight-local.py",
    "sha256": "812e68aa2744428b3fce1b8016b552252e13244fa37eec7084e42763ab446646",
    "bytes": 10744
  },
  "preflight_original": {
    "path": "C:\\Users\\guill\\.agents\\skills\\dayz-preflight\\preflight.py",
    "sha256": "9f8786a5f37b6b2abbd206bce51d4cad44d58536e766b97fd93bae692804c9a7",
    "bytes": 10743
  },
  "profile_roots": [
    "C:\\Users\\guill\\AppData\\Local\\Bohemia_Interactive",
    "C:\\Users\\guill\\AppData\\Local\\Bohemia Interactive"
  ],
  "caps": {
    "copy_seconds": 180,
    "preflight_seconds": 60,
    "help_seconds": 30,
    "arm_seconds": 300,
    "observe_seconds": 120,
    "total_seconds": 1050,
    "rss": 2147483648,
    "disk": 2147483648,
    "log": 33554432,
    "wrp": 134217728,
    "metadata": 33554432,
    "drain_seconds": 5
  },
  "claims": {
    "build_ready": false,
    "decoder_verified": false,
    "map_changed": false,
    "native_acceptance": false
  },
  "prefix": "dayz_baltic_12km_dev/tb/narva_trial"
}


### E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\oracle.json
{
  "schema": "road-c1c-oracle.v1",
  "valid_header_hex": "4f5052572000000001020304",
  "source_header_hex": "30575a442000000001020304",
  "positive_log": "Build Successful\n",
  "negative_logs": [
    "Build failed\n",
    "Build Successful\nERROR: missing texture\n",
    "Build Successful\nFATAL: test\n"
  ],
  "expected_positive": "ARTIFACT_OBSERVED_ONLY",
  "expected_source_header": "WRP_MAGIC",
  "expected_no_child": "PROBE_INCONCLUSIVE_NOT_OBSERVED",
  "expected_bad_image": "UNEXPECTED_CHILD",
  "expected_nonzero": "PROCESS_REJECTED",
  "expected_timeout": "TIMEOUT",
  "expected_missing_marker": "NO_MARKER",
  "expected_old_log": "LOG_WINDOW",
  "expected_multiple": "WRP_COUNT",
  "expected_changed_source": "SOURCE_CHANGED",
  "expected_changed_work": "WORK_INPUT_MUTATED",
  "expected_co_mutant": "ARTIFACT_PIN",
  "expected_extra_logger_change": "LOGGER_DELTA",
  "candidate_requires": "control.status == ARTIFACT_OBSERVED_ONLY"
}


### E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\probe_road_compile_c1c.py
"""One consumed compile probe, no semantic WRP acceptance."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,stat,subprocess,sys,time,xml.etree.ElementTree as ET
sys.path.insert(0,'E:/DayZ-Baltic-Build/shape-repair-20261025/dry-road-build-dependencies-20261028')
import psutil

class Stop(Exception):pass
def need(x,code):
    if not x:raise Stop(code)
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);b=json.dumps(v,indent=2).encode();need(len(b)<=33554432,'METADATA_CAP')
    with p.open('wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def guard(p):
    p=Path(p)
    for q in [p,*p.parents]:
        s=q.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,'REPARSE')
def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def read_hash(p,cap=67108864,deadline=float('inf'),copy=None):
    p=Path(p);guard(p);pre=ident(p.stat());need(pre[2]<=cap,'FILE_CAP');h=hashlib.sha256();n=0;out=None
    try:
        if copy is not None:copy.parent.mkdir(parents=True,exist_ok=True);guard(copy.parent);out=copy.open('xb')
        with p.open('rb') as f:
            need(ident(os.fstat(f.fileno()))==pre,'IDENTITY')
            while True:
                need(time.monotonic()<deadline,'BUDGET');b=f.read(min(1048576,cap-n+1))
                if not b:break
                n+=len(b);need(n<=cap,'FILE_CAP');h.update(b)
                if out:need(out.write(b)==len(b),'WRITE')
            need(ident(os.fstat(f.fileno()))==pre,'IDENTITY')
        guard(p);need(ident(p.stat())==pre and n==pre[2],'IDENTITY')
        if out:out.flush();os.fsync(out.fileno())
    finally:
        if out:out.close()
    return {'path':str(p),'bytes':n,'sha256':h.hexdigest(),'identity':pre}
def pincheck(record,deadline=float('inf')):
    got=read_hash(record['path'],max(record['bytes'],1),deadline);need((got['bytes'],got['sha256'])==(record['bytes'],record['sha256']),'PIN');return got
def load(p,pin):
    p=Path(p);need(p.stat().st_size<=33554432,'METADATA_CAP');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==pin,'CONTRACT_PIN');return json.loads(b)
def logger_bytes(raw,paths):
    tree=ET.fromstring(raw);nodes=tree.findall('./appender/file');need(len(nodes)==3 and len(paths)==3,'LOGGER_DELTA')
    # Byte replacements preserve every token except the three file values.
    out=raw
    for node,dest in zip(nodes,paths):
        before=node.attrib['value'].encode();need(out.count(before)==1,'LOGGER_DELTA');out=out.replace(before,str(dest).encode())
    a=ET.fromstring(raw);b=ET.fromstring(out)
    for x,y in zip(a.findall('./appender/file'),b.findall('./appender/file')):y.attrib['value']=x.attrib['value']
    need(ET.tostring(a)==ET.tostring(b),'LOGGER_DELTA');return out
def verify_logger(raw,candidate,paths):
    need(candidate==logger_bytes(raw,paths),'LOGGER_DELTA')
def profile_snapshot(roots):
    rows=[];count=0;total=0
    for root in map(Path,roots):
        if not root.exists():continue
        guard(root)
        for app in root.glob('AddonBuilder*'):
            stack=[app]
            while stack:
                p=stack.pop();guard(p);count+=1;need(count<=256,'PROFILE_CAP')
                if p.is_dir():stack.extend(p.iterdir())
                elif p.name=='user.config':
                    row=read_hash(p,4194304);total+=row['bytes'];need(total<=16777216,'PROFILE_CAP');rows.append(row)
    return rows
def proc_run(command,cwd,out,seconds,rss_cap,diskroot=None,env_extra=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);started=time.time();tick=time.monotonic();owned={};images={};reason=None;peak=0;disk_peak=0
    env=os.environ.copy();env.update(env_extra or {});env.pop('PWD',None)
    def live():
        result=[]
        for pid,birth in list(owned.items()):
            try:
                p=psutil.Process(pid)
                if p.create_time()==birth and p.is_running():result.append(p)
            except psutil.NoSuchProcess:pass
        return result
    with (out/'stdout').open('wb') as stdout,(out/'stderr').open('wb') as stderr:
        child=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,creationflags=0x08000000)
        try:p=psutil.Process(child.pid);owned[p.pid]=p.create_time()
        except psutil.NoSuchProcess:pass
        dump(out/'running.json',{'pid':child.pid,'birth':owned.get(child.pid),'started':started,'command':command,'budget':seconds})
        next_disk=0
        try:
            while True:
                for p in live():
                    try:
                        for q in p.children(recursive=True):owned[q.pid]=q.create_time()
                    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                now=live();rss=0
                for p in now:
                    try:
                        rss+=p.memory_info().rss
                        if p.pid not in images:
                            exe=p.exe();args=p.cmdline();r=read_hash(exe);images[p.pid]={'pid':p.pid,'birth':owned[p.pid],'exe':exe,'argv':args,'observed_at':time.time(),'image_path_sha256':r['sha256'],'image_identity':r['identity']}
                    except (psutil.NoSuchProcess,psutil.AccessDenied,OSError,Stop):pass
                peak=max(peak,rss);elapsed=time.monotonic()-tick
                if elapsed>seconds:reason='TIMEOUT';break
                if rss>rss_cap:reason='MEMORY_LIMIT';break
                if diskroot and elapsed>=next_disk:
                    count=0;size=0
                    roots=diskroot if isinstance(diskroot,list) else [diskroot]
                    for base in roots:
                        for p in Path(base).rglob('*'):
                            count+=1;need(count<=32768,'OUTPUT_ENTRY_CAP')
                            if p.is_file():
                                amount=p.stat().st_size;size+=amount
                                if Path(base).name in ('help','control','candidate') and Path(base).parent.name=='logs':need(amount<=33554432,'LOG_LIMIT')
                    disk_peak=max(disk_peak,size);next_disk=elapsed+1
                    if size>2147483648:reason='DISK_LIMIT';break
                if any((out/n).stat().st_size>33554432 for n in ['stdout','stderr']):reason='LOG_LIMIT';break
                if child.poll() is not None and not now:break
                time.sleep(.15)
        except Exception as e:reason='MONITOR_ERROR:'+type(e).__name__
        finally:
            # Stop the owned root first; never match by executable name.
            for pid in [child.pid,*reversed(list(owned))]:
                if pid not in owned:continue
                try:
                    p=psutil.Process(pid)
                    if p.create_time()==owned[pid] and p.is_running():p.kill()
                except psutil.NoSuchProcess:pass
            child.wait(timeout=5)
    r={'rc':child.returncode,'reason':reason,'started':started,'finished':time.time(),'seconds':time.monotonic()-tick,'peak_rss':peak,'observed_disk_peak':disk_peak,'identities':owned,'observed_processes':list(images.values()),'command':command,'cwd':str(cwd),'stdout':read_hash(out/'stdout',33554432),'stderr':read_hash(out/'stderr',33554432),'sampling_seconds':.15,'loaded_image_attestation':False}
    dump(out/'completion.json',r);return r
def snapshot_logs(folder,receipt):
    paths=[Path(receipt[k]['path']) for k in ['stdout','stderr']]+sorted(p for p in Path(folder).iterdir() if p.is_file());need(len(paths)<=64,'LOG_COUNT')
    until=time.monotonic()+5;previous=None
    while True:
        state=[(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in paths]
        if state==previous:break
        need(time.monotonic()<until,'LOG_UNSTABLE');previous=state;time.sleep(.15)
    return [read_hash(p,33554432) for p in paths]
def gate(receipt,logs,wrps,binarize_sha,allowed_images,help_mode=False):
    if receipt['reason']:return receipt['reason']
    if receipt['rc']!=0:return 'PROCESS_REJECTED'
    if not any(Path(r['path']).suffix=='.rpt' for r in logs):return 'LOG_NOT_OBSERVED'
    marker=False;syntax=False;tools_flag=False
    for r in logs:
        if not(receipt['started']<=r['identity'][3]/1e9<=receipt['finished']):return 'LOG_WINDOW'
        pincheck(r);text=Path(r['path']).read_text(encoding='utf-8',errors='replace')
        if re.search(r'\b(?:ERROR|FATAL)\b',text,re.I):return 'LOG_ERROR'
        marker=marker or 'Build Successful' in text;syntax=syntax or 'SYNTAX' in text;tools_flag=tools_flag or '-toolsDirectory' in text
    if help_mode:return 'HELP_OBSERVED' if syntax and tools_flag else 'NO_HELP'
    if not marker:return 'NO_MARKER'
    observed=receipt['observed_processes']
    if any(r['image_path_sha256'] not in allowed_images for r in observed):return 'UNEXPECTED_CHILD'
    if not any(r['image_path_sha256']==binarize_sha for r in observed):return 'PROBE_INCONCLUSIVE_NOT_OBSERVED'
    if len(wrps)!=1:return 'WRP_COUNT'
    p=Path(wrps[0]);r=read_hash(p,134217728)
    if not(receipt['started']<=r['identity'][3]/1e9<=receipt['finished']):return 'ARTIFACT_WINDOW'
    with p.open('rb') as f:b=f.read(8)
    return 'ARTIFACT_OBSERVED_ONLY' if len(b)==8 and b[:4]==b'OPRW' else 'WRP_MAGIC'
def expected(c):
    old=load(c['c1b']['path'],c['c1b']['sha256']);return {arm:{e['dest']:(e['bytes'],e['sha256']) for e in old['files'] if e['scope'] in ('common',arm)} for arm in ['control','candidate']}
def trees(c,targets,deadline):
    ex=expected(c);rows=[]
    for target in targets:
        for arm in ['control','candidate']:
            base=Path(target)/arm/'root';seen=set();seen_dirs=set();guard(base)
            for p in base.rglob('*'):
                need(time.monotonic()<deadline,'BUDGET');guard(p)
                if p.is_file():
                    rel=p.relative_to(base).as_posix();need(rel in ex[arm],'EXTRA');r=read_hash(p,ex[arm][rel][0],deadline);need((r['bytes'],r['sha256'])==ex[arm][rel],'SOURCE_CHANGED');seen.add(rel)
                elif p.is_dir():seen_dirs.add(p.relative_to(base).as_posix())
            need(seen==set(ex[arm]),'MISSING');rows.append({'tree':str(base),'files':len(seen)})
            wanted_dirs={p.as_posix() for name in ex[arm] for p in Path(name).parents if str(p)!='.'};need(seen_dirs==wanted_dirs,'EXTRA')
    return rows
def mainrun(c,pin):
    root=Path(c['root']);need(not root.exists(),'EXISTS');guard(root.parent);need(shutil.disk_usage(root.parent).free>3221225472,'DISK_FREE');root.mkdir();dump(root/'consumed.json',{'contract_sha256':pin,'started':time.time(),'no_retries':True});begin=time.monotonic();deadline=begin+c['caps']['total_seconds'];report={'contract_sha256':pin,'status':'IN_PROGRESS','claims':c['claims'],'phases':{}}
    def save():dump(root/'report.json',report)
    try:
        report['profile_before']=profile_snapshot(c['profile_roots']);until=time.monotonic()+180;work=root/'work'
        for arm,files in expected(c).items():
            for rel,(size,h) in files.items():
                source=Path(c['source_stage'])/arm/'root'/rel;dest=work/arm/'root'/rel;r=read_hash(source,size,until,dest);need(r['sha256']==h,'SOURCE_CHANGED');need(read_hash(dest,size,until)['sha256']==h,'WRITE')
        portable=root/'tools/AddonBuilder'
        for row in c['tool_files']:
            pincheck(row,until);r=read_hash(row['path'],67108864,until,portable/row['dest']);need(r['sha256']==row['sha256'],'PIN')
        for row in c['tools'].values():pincheck(row,until)
        for k in ['include','exclude','preflight','preflight_original']:pincheck(c[k],until)
        report['copy_seconds']=time.monotonic()-begin;need(report['copy_seconds']<=180,'BUDGET');save()
        py=sys.executable;pre=proc_run([py,'-I','-X','utf8',c['preflight']['path']],root,root/'preflight',60,268435456);report['phases']['preflight']=pre;save();need(pre['rc']==0 and pre['reason'] is None,'PREFLIGHT')
        exe=portable/'AddonBuilder.exe';raw=(portable/'logger.xml').read_bytes();need(hashlib.sha256(raw).hexdigest()==next(x['sha256'] for x in c['tool_files'] if x['dest']=='logger.xml'),'PIN')
        def launch(phase,args,seconds,rss,output=None):
            logdir=root/'logs'/phase;logdir.mkdir(parents=True);paths=[logdir/n for n in ['AddonBuilder.rpt','AddonBuilderProcess.rpt','AddonBuilder.User.rpt']];lb=logger_bytes(raw,paths);(portable/'logger.xml').write_bytes(lb)
            env={n:str(root/'profile'/phase/n) for n in ['APPDATA','LOCALAPPDATA','TEMP','TMP']}
            for v in env.values():Path(v).mkdir(parents=True)
            remain=deadline-time.monotonic();need(remain>=seconds,'TOTAL_BUDGET')
            receipt=proc_run([str(exe),*args],portable,root/'process'/phase,seconds,rss,[output,logdir] if output else [logdir],env);logs=snapshot_logs(logdir,receipt);return receipt,logs,hashlib.sha256(lb).hexdigest()
        helper,logs,lh=launch('help',['-help','-toolsDirectory='+c['tool_root']],30,536870912);st=gate(helper,logs,[],c['tools']['binarize']['sha256'],[],True);report['phases']['help']={'receipt':helper,'logs':logs,'logger_sha256':lh,'status':st};save();need(st=='HELP_OBSERVED',st)
        allowed={row['sha256'] for key,row in c['tools'].items() if key in ['binarize','cfgConvert','fileBank']}|{next(x['sha256'] for x in c['tool_files'] if x['dest']=='AddonBuilder.exe')}
        for arm in ['control','candidate']:
            tick=time.monotonic();out=root/'output'/arm;out.mkdir(parents=True);(out/'out').mkdir();project=work/arm/'root';src=project/c['prefix']
            args=[str(src),str(out/'out'),'-prefix='+c['prefix'].replace('/','\\'),'-project='+str(project),'-temp='+str(out/'temp'),'-include='+c['include']['path'],'-exclude='+c['exclude']['path'],'-binarizeFullLogs','-toolsDirectory='+c['tool_root']]+['-'+k+'='+c['tools'][k]['path'] for k in ['binarize','cfgConvert','fileBank','dsSignFile']]
            receipt,logs,lh=launch(arm,args,300,2147483648,out);wrps=list((out/'temp').rglob('*.wrp')) if (out/'temp').exists() else [];st=gate(receipt,logs,wrps,c['tools']['binarize']['sha256'],allowed)
            artifacts=[]
            for p in wrps[:2]:
                a=read_hash(p,134217728)
                with p.open('rb') as f:a['header_hex']=f.read(8).hex()
                artifacts.append(a)
            report['phases'][arm]={'status':st,'receipt':receipt,'logs':logs,'logger_sha256':lh,'artifacts':artifacts,'argv_binding':'OBSERVED_NOT_INTERPRETED'};save()
            need(st=='ARTIFACT_OBSERVED_ONLY',st)
            # Full gates are inside the arm envelope, before authorizing the next arm.
            trees(c,[c['source_stage']],min(tick+300,deadline))
            try:trees(c,[work],min(tick+300,deadline))
            except Stop as e:raise Stop('WORK_INPUT_MUTATED:'+str(e))
            for row in c['tools'].values():pincheck(row,min(tick+300,deadline))
            for row in c['tool_files']:pincheck(row,min(tick+300,deadline))
            need(time.monotonic()-tick<=300,'ARM_BUDGET')
        report['status']='COMPILE_PROBE_OBSERVED_ONLY'
    except (Stop,OSError) as e:report['status']='PROBE_STOPPED';report['reason']=str(e)
    finally:
        try:report['profile_after']=profile_snapshot(c['profile_roots'])
        except Exception as e:report['profile_after_error']=type(e).__name__
        report['seconds']=time.monotonic()-begin;save()
    return report
def main():
    a=argparse.ArgumentParser();a.add_argument('--contract',required=True);a.add_argument('--sha',required=True);x=a.parse_args();c=load(x.contract,x.sha);need(c['schema']=='road-c1c-probe.v1','SCHEMA');r=mainrun(c,x.sha);print(json.dumps({'status':r['status'],'reason':r.get('reason'),'seconds':r['seconds']}));return 0 if r['status']=='COMPILE_PROBE_OBSERVED_ONLY' else 2
if __name__=='__main__':sys.exit(main())


### E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\observe_road_compile_c1c.py
"""Read only artifact and input observer; not a terrain decoder."""
from pathlib import Path
import argparse,hashlib,json,os,re,stat,sys,time
class Reject(Exception):pass
def require(x,s):
    if not x:raise Reject(s)
def pathcheck(p):
    p=Path(p)
    while True:
        s=p.lstat();require(not stat.S_ISLNK(s.st_mode) and not(getattr(s,'st_file_attributes',0)&1024),'REPARSE')
        if p.parent==p:break
        p=p.parent
def fileid(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
def checkfile(p,expected=None,cap=134217728,until=float('inf')):
    p=Path(p);pathcheck(p);before=fileid(p.stat());require(before[2]<=cap,'SIZE');h=hashlib.sha256();size=0
    with p.open('rb') as f:
        require(fileid(os.fstat(f.fileno()))==before,'IDENTITY')
        while True:
            require(time.monotonic()<until,'BUDGET');b=f.read(min(524288,cap-size+1))
            if not b:break
            size+=len(b);require(size<=cap,'SIZE');h.update(b)
        require(fileid(os.fstat(f.fileno()))==before,'IDENTITY')
    pathcheck(p);require(fileid(p.stat())==before and size==before[2],'IDENTITY');digest=h.hexdigest()
    if expected:require((size,digest)==(expected['bytes'],expected['sha256']),'ARTIFACT_PIN')
    return {'bytes':size,'sha256':digest,'mtime':before[3]/1e9}
def readjson(p,pin):
    r=checkfile(p,cap=33554432);require(r['sha256']==pin,'PIN');b=Path(p).read_bytes();require(hashlib.sha256(b).hexdigest()==pin,'PIN');return json.loads(b)
def stage_check(base,expected,until):
    base=Path(base);pathcheck(base);files=set();dirs=set()
    for folder,subdirs,names in os.walk(base,followlinks=False):
        for name in subdirs:pathcheck(Path(folder)/name);dirs.add((Path(folder)/name).relative_to(base).as_posix())
        for name in names:
            p=Path(folder)/name;rel=p.relative_to(base).as_posix();require(rel in expected,'EXTRA');size,digest=expected[rel];checkfile(p,{'bytes':size,'sha256':digest},size,until);files.add(rel)
    require(files==set(expected),'MISSING');allowed=set()
    for key in files:
        p=Path(key).parent
        while str(p)!='.':allowed.add(p.as_posix());p=p.parent
    require(dirs==allowed,'EXTRA');return len(files)
def arm_check(c,phase,arm='control'):
    r=phase['receipt'];require(r['reason'] is None and r['rc']==0,'PROCESS_REJECTED');allowed={v['sha256'] for k,v in c['tools'].items() if k in ('binarize','cfgConvert','fileBank')};allowed.add(next(v['sha256'] for v in c['tool_files'] if v['dest']=='AddonBuilder.exe'))
    processes=r['observed_processes'];require(all(p['image_path_sha256'] in allowed for p in processes),'UNEXPECTED_CHILD');require(any(p['image_path_sha256']==c['tools']['binarize']['sha256'] for p in processes),'PROBE_INCONCLUSIVE_NOT_OBSERVED')
    for p in processes:
        require(str(p['pid']) in r['identities'] and r['identities'][str(p['pid'])]==p['birth'] and r['started']<=p['birth']<=p['observed_at']<=r['finished'],'PROCESS_WINDOW')
        q=checkfile(p['exe'],cap=67108864);require(q['sha256']==p['image_path_sha256'],'IMAGE_CHANGED')
    marker=False;private=False;root=Path(c['root']);allowed_logs={root/'process'/arm/n for n in ['stdout','stderr']};logdir=root/'logs'/arm;actual_logs={p for p in logdir.iterdir() if p.is_file()} if logdir.exists() else set();require(len(actual_logs)<=62,'LOG_COUNT');allowed_logs|=actual_logs
    require({Path(log['path']) for log in phase['logs']}==allowed_logs,'LOG_BINDING')
    for log in phase['logs']:
        now=checkfile(log['path'],log,33554432);require(r['started']<=now['mtime']<=r['finished'],'LOG_WINDOW');private=private or Path(log['path']).suffix=='.rpt';text=Path(log['path']).read_text(encoding='utf-8',errors='replace');require(not re.search(r'\b(ERROR|FATAL)\b',text,re.I),'LOG_ERROR');marker=marker or 'Build Successful' in text
    require(private,'LOG_NOT_OBSERVED');require(marker,'NO_MARKER');require(len(phase['artifacts'])==1,'WRP_COUNT');a=phase['artifacts'][0]
    wrps=list((root/'output'/arm/'temp').rglob('*.wrp'));require(len(wrps)==1 and Path(a['path'])==wrps[0],'WRP_COUNT')
    q=checkfile(a['path'],a);require(r['started']<=q['mtime']<=r['finished'],'ARTIFACT_WINDOW')
    with open(a['path'],'rb') as f:header=f.read(8)
    require(len(header)==8 and header[:4]==b'OPRW','WRP_MAGIC');require(header.hex()==a['header_hex'],'ARTIFACT_PIN')
    return {'path':a['path'],'sha256':q['sha256'],'bytes':q['bytes'],'raw_header_hex':header.hex(),'semantic_status':'NOT_EVALUATED'}
def observe(c,r,until):
    findings=[];arms={};input_rows=[];old=readjson(c['c1b']['path'],c['c1b']['sha256']);root=Path(c['root'])
    for role,target in [('SEALED_SOURCE',Path(c['source_stage'])),('WORK',root/'work')]:
        for arm in ['control','candidate']:
            expected={x['dest']:(x['bytes'],x['sha256']) for x in old['files'] if x['scope'] in ('common',arm)}
            try:input_rows.append({'kind':role,'arm':arm,'files':stage_check(target/arm/'root',expected,until),'state':'MATCH'})
            except (Reject,OSError) as e:findings.append({'kind':role,'arm':arm,'error':str(e)});input_rows.append({'kind':role,'arm':arm,'state':'NOT_MATCHED'})
    for item in [*c['tool_files'],*c['tools'].values(),c['include'],c['exclude'],c['preflight_original']]:
        try:checkfile(item['path'],item,67108864,until)
        except (Reject,OSError) as e:findings.append({'kind':'INSTALLED_OR_FIXED_INPUT','path':item['path'],'error':str(e)})
    for arm in ['control','candidate']:
        if arm not in r['phases']:arms[arm]={'status':'NOT_LAUNCHED'};continue
        try:arms[arm]={'status':'ARTIFACT_OBSERVED_ONLY','artifact':arm_check(c,r['phases'][arm],arm)}
        except (Reject,OSError) as e:arms[arm]={'status':'NOT_VERIFIED','reason':str(e)}
    complete=not findings and all(x['status']=='ARTIFACT_OBSERVED_ONLY' for x in arms.values())
    require(not complete or r['status']=='COMPILE_PROBE_OBSERVED_ONLY','REPORT_STATUS')
    return {'status':'VERIFIED_COMPILE_PROBE_ONLY' if complete else 'INCONCLUSIVE_PROBE_DIAGNOSTIC','arms':arms,'inputs':input_rows,'findings':findings,'producer_status':r['status'],'producer_reason':r.get('reason'),'claims':c['claims'],'decoder':'NOT_IMPLEMENTED','continuous_identity':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--report',required=True);p.add_argument('--report-sha',required=True);p.add_argument('--out',required=True);a=p.parse_args();start=time.monotonic()
    try:
        c=readjson(a.contract,a.sha);r=readjson(a.report,a.report_sha);require(r['contract_sha256']==a.sha,'BINDING');result=observe(c,r,start+120);result['report_sha256']=a.report_sha;result['contract_sha256']=a.sha;result['seconds']=time.monotonic()-start;b=json.dumps(result,indent=2).encode();require(len(b)<=33554432,'OUTPUT_CAP')
        with open(a.out,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        print(json.dumps({'status':result['status'],'arms':result['arms']}));return 0 if result['status'].startswith('VERIFIED') else 2
    except (Reject,OSError) as e:print('REJECTED:'+str(e));return 3
if __name__=='__main__':sys.exit(main())


### E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\test_probe_road_compile_c1c.py
from pathlib import Path
import hashlib,importlib.util,json,os,sys,tempfile,time,unittest,copy
D=Path(__file__).parent
def mod(name):
 s=importlib.util.spec_from_file_location(name,D/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=mod('probe_road_compile_c1c');V=mod('observe_road_compile_c1c')
ob=(D/'oracle.json').read_bytes();assert hashlib.sha256(ob).hexdigest()=='0a809df80c7766f114a5c330418145fa9a831dab80ccd593486a9e5a84de236b';O=json.loads(ob)
def rec(p):
 b=p.read_bytes();s=p.stat();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]}
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.r=Path(self.t.name);self.image=self.r/'image.exe';self.image.write_bytes(b'SYNTHETIC IMAGE ONLY');self.ih=rec(self.image)['sha256'];self.logs=[]
  for rel,text in [('process/control/stdout',O['positive_log']),('process/control/stderr',''),('logs/control/AddonBuilder.rpt',O['positive_log'])]:
   p=self.r/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode());self.logs.append(rec(p))
  self.w=self.r/'output/control/temp/probe.wrp';self.w.parent.mkdir(parents=True);self.w.write_bytes(bytes.fromhex(O['valid_header_hex']));self.art=rec(self.w);self.art['header_hex']=self.w.read_bytes()[:8].hex();now=time.time()
  self.receipt={'started':now-2,'finished':now+2,'rc':0,'reason':None,'identities':{'123':now-1},'observed_processes':[{'pid':123,'birth':now-1,'observed_at':now,'exe':str(self.image),'image_path_sha256':self.ih,'argv':['literal synthetic']}]}
  self.phase={'receipt':self.receipt,'logs':self.logs,'artifacts':[self.art]};self.c={'root':str(self.r),'tools':{'binarize':{'sha256':self.ih}},'tool_files':[{'dest':'AddonBuilder.exe','sha256':self.ih}]}
 def tearDown(self):self.t.cleanup()
 def gate(self,wrps=None):return A.gate(self.receipt,self.logs,[self.w] if wrps is None else wrps,self.ih,{self.ih})
 def test_literal_positive(self):self.assertEqual(self.gate(),O['expected_positive']);self.assertEqual(V.arm_check(self.c,self.phase)['raw_header_hex'],O['valid_header_hex'][:16])
 def test_nonzero_and_timeout(self):
  self.receipt['rc']=1;self.assertEqual(self.gate(),O['expected_nonzero']);self.receipt['reason']='TIMEOUT';self.assertEqual(self.gate(),O['expected_timeout'])
 def test_logs_fail_closed(self):
  for text in O['negative_logs']:
   p=Path(self.logs[0]['path']);p.write_text(text);self.logs[0]=rec(p)
   q=Path(self.logs[2]['path']);q.write_text('');self.logs[2]=rec(q)
   self.assertNotEqual(self.gate(),O['expected_positive'])
 def test_no_marker(self):
  for i in [0,2]:p=Path(self.logs[i]['path']);p.write_text('diagnostic');self.logs[i]=rec(p)
  self.assertEqual(self.gate(),O['expected_missing_marker'])
 def test_no_child(self):
  self.receipt['observed_processes']=[];self.assertEqual(self.gate(),O['expected_no_child'])
  with self.assertRaisesRegex(V.Reject,O['expected_no_child']):V.arm_check(self.c,self.phase)
 def test_bad_child(self):self.receipt['observed_processes'][0]['image_path_sha256']='0'*64;self.assertEqual(self.gate(),O['expected_bad_image'])
 def test_old_log(self):
  p=Path(self.logs[2]['path']);os.utime(p,(1,1));self.logs[2]=rec(p);self.assertEqual(self.gate(),O['expected_old_log'])
 def test_source_magic_and_comutation(self):
  self.w.write_bytes(bytes.fromhex(O['source_header_hex']));self.phase['artifacts'][0]=rec(self.w);self.phase['artifacts'][0]['header_hex']=self.w.read_bytes()[:8].hex();self.assertEqual(self.gate(),O['expected_source_header'])
  with self.assertRaisesRegex(V.Reject,'WRP_MAGIC'):V.arm_check(self.c,self.phase)
 def test_multiple_unreported_wrps(self):
  other=self.w.parent/'extra.wrp';other.write_bytes(self.w.read_bytes());self.assertEqual(self.gate([self.w,other]),O['expected_multiple'])
  with self.assertRaisesRegex(V.Reject,'WRP_COUNT'):V.arm_check(self.c,self.phase)
 def test_artifact_pin(self):
  self.phase['artifacts'][0]['sha256']='0'*64
  with self.assertRaisesRegex(V.Reject,O['expected_co_mutant']):V.arm_check(self.c,self.phase)
 def test_foreign_log(self):
  p=self.r/'unrelated.rpt';p.write_text(O['positive_log']);self.phase['logs'][2]=rec(p)
  with self.assertRaisesRegex(V.Reject,'LOG_BINDING'):V.arm_check(self.c,self.phase)
 def test_changed_and_extra_tree(self):
  p=self.r/'tree/data';p.mkdir(parents=True);q=p/'x';q.write_bytes(b'literal');expected={'data/x':(7,hashlib.sha256(b'literal').hexdigest())};self.assertEqual(V.stage_check(p.parent,expected,float('inf')),1)
  q.write_bytes(b'changed')
  with self.assertRaisesRegex(V.Reject,'ARTIFACT_PIN'):V.stage_check(p.parent,expected,float('inf'))
  q.write_bytes(b'literal');(p/'extra').write_bytes(b'x')
  with self.assertRaisesRegex(V.Reject,'EXTRA'):V.stage_check(p.parent,expected,float('inf'))
 def test_logger_delta(self):
  raw=(D/'logger-fixture.xml').read_bytes();dest=[self.r/n for n in ['a.rpt','b.rpt','c.rpt']];out=A.logger_bytes(raw,dest);A.verify_logger(raw,out,dest)
  with self.assertRaisesRegex(A.Stop,O['expected_extra_logger_change']):A.verify_logger(raw,out.replace(b'DEBUG',b'ERROR'),dest)
 def test_candidate_requires_control(self):
  for status in ['WRP_COUNT','PROCESS_REJECTED','TIMEOUT','PROBE_INCONCLUSIVE_NOT_OBSERVED']:
   self.assertFalse(status==O['expected_positive'])
  self.assertEqual(O['candidate_requires'],'control.status == ARTIFACT_OBSERVED_ONLY')
 def test_real_child_receipt_and_timeout(self):
  ok=A.proc_run([sys.executable,'-I','-c','print("literal child")'],self.r,self.r/'child',5,268435456);self.assertEqual((ok['rc'],ok['reason']),(0,None));self.assertTrue(ok['identities']);self.assertEqual(Path(ok['stdout']['path']).read_text().strip(),'literal child')
  bad=A.proc_run([sys.executable,'-I','-c','import time;time.sleep(4)'],self.r,self.r/'timeout',.25,268435456);self.assertEqual(bad['reason'],'TIMEOUT')
  for pid,birth in bad['identities'].items():
   try:p=A.psutil.Process(int(pid));self.assertNotEqual(p.create_time(),birth)
   except A.psutil.NoSuchProcess:pass
if __name__=='__main__':unittest.main()


### E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\logger-fixture.xml
<?xml version="1.0"?>
<log4net>
  <appender name="VSConsole" type="log4net.Appender.TraceAppender">
    <layout type="log4net.Layout.PatternLayout">
      <conversionPattern value="%5level [%thread]: %message%newline" />
    </layout>
  </appender>

  <appender name="RollingFile" type="log4net.Appender.RollingFileAppender">
    <file value="..\Logs\AddonBuilder.rpt" />
    <appendToFile value="true" />
    <maxSizeRollBackups value="10" />
    <layout type="log4net.Layout.PatternLayout">
      <conversionPattern value="%date [%level] %thread: %class.%method - %message%newline" />
    </layout>
  </appender>

  <appender name="ProcessRollingFile" type="log4net.Appender.RollingFileAppender">
    <file value="..\Logs\AddonBuilderProcess.rpt" />
    <bufferSize value="512" />
    <appendToFile value="true" />
    <maxSizeRollBackups value="10" />
    <layout type="log4net.Layout.PatternLayout">
      <conversionPattern value="%message%newline" />
    </layout>
  </appender>
  
  <appender name="UserRollingFile" type="log4net.Appender.RollingFileAppender">
    <file value="..\Logs\AddonBuilder.User.rpt" />
    <appendToFile value="true" />
    <maxSizeRollBackups value="10" />
    <layout type="log4net.Layout.PatternLayout">
      <conversionPattern value="%date [%5.5level] %3.3thread: %message%newline" />
    </layout>
  </appender>
  
  <appender name="Console" type="log4net.Appender.ConsoleAppender">
    <layout type="log4net.Layout.PatternLayout">
      <conversionPattern value="%date [%level] %thread: %class.%method - %message%newline" />
    </layout>
  </appender>
  
  <appender name="UserConsole" type="log4net.Appender.ConsoleAppender">
    <layout type="log4net.Layout.PatternLayout">
      <conversionPattern value="[%date] [%level]: %message%newline" />
    </layout>
  </appender>

  <appender name="StatusAppender" type="AddonBuilder.StatusAppender">
    <layout type="log4net.Layout.PatternLayout">
      <conversionPattern value="%message%newline" />
    </layout>
  </appender>
  
  <root>
    <level value="DEBUG" />
    <appender-ref ref="RollingFile" />
  </root>
  <logger name="user" additivity="false">
    <level value="INFO" />
    <appender-ref ref="UserRollingFile" />
    <appender-ref ref="StatusAppender" />
  </logger>

  <logger name="process" additivity="false">
    <level value="INFO" />
    <appender-ref ref="RollingFile" />
  </logger>

  <logger name="SteamLayer">
    <level value="OFF" />
  </logger>
</log4net>

### E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-local-author-20261029\author-completion.json
{
  "seconds": 455.78111815452576,
  "budget": 600,
  "files": {
    "observe_road_compile_c1c.py": "e37cc1c0c586342da8433d06713ef6a0f3f677d69defa77a3e9862878cbb2b11",
    "preflight-local.py": "812e68aa2744428b3fce1b8016b552252e13244fa37eec7084e42763ab446646",
    "preflight-original.py": "9f8786a5f37b6b2abbd206bce51d4cad44d58536e766b97fd93bae692804c9a7",
    "probe_road_compile_c1c.py": "46f1acf5b57e15f7e35edfd5c617fa4ce24b4d70cea0ab41cc74f253163f2dfd",
    "test_probe_road_compile_c1c.py": "eed5ea636b2d16ed7f68d6ff80dcf9060d1d683bc069a90f6b53ad3e43a2a7fe"
  },
  "within_budget": true
}