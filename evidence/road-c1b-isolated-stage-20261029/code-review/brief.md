Revisor Muse Wonder1.0 independiente de autor Codex. SOLO capsula, no herramientas ni escrituras. Codigo real de copia stage sin build. Dictamen max1600palabras SOUND/SOUND-with-fixes/NEEDS-WORK en180s. Encuentra bugs concretos contra contrato/plan y tests, no exigir prueba de runtime ni semantica. Contrato externo y bindings externos tienen pins CLI separados; el co-mutante cambia manifiesto pero no el pin externo de bindings. Misma stdlib IO entre lectores, recorridos separados. Identidad no es vigilancia continua. No repetir council ni reviews previas. Autor local229.387s de600. Preparacion original fallo ANTES de payload por contar58conroot vs57descendientes, continuacion27.719s preserva original. Literal description corregido antes de contrato. Manifest6892comunes223031657B, 2WRP, total4739xxKB aprox; usar cifras exactas contrato y suma. No fuentes vanilla completas en capsula.

PLAN ACTUAL
# RoadC1B — materializar los dos stages de laboratorio

Estado: REVISADO_PARA_CONTRATO_Y_STAGE_LIMITADO. 29-10-2026.
Codex planner/integrator; executor local asignado explícitamente para este corte.

## Resultado concreto y alcance

P5/P6/P8/P11: producir dos árboles privados nuevos, control0/candidato3, que sólo
difieran en `baltic_trial.wrp`. Todas las demás rutas, configuraciones y bytes deben
coincidir con un manifiesto externo congelado antes del código. No se modifica el
mapa poblado, P:, RoadC0 ni recursos vanilla. No build, paquete ni DayZ en C1B.

Hipótesis: los recursos observados bastan para armar un stage reducido verificable
por bytes. No equivale a cerrar dependencias del compilador/runtime. Si existen
dependencias adicionales, la futura sonda las registra; no se declara listo ahora.
El resultado es VERIFIED_LAB_STAGE_BYTES_ONLY, `build_ready=false`,
`dependency_closure=NOT_EVALUATED`, `compiled_terrain_decoder=NOT_VERIFIED`.

## Anclas reutilizadas sin repetir sus censos

- C0: control f00c3f57.../17307685B y candidato2fb3686b.../17307968B; prefijo
  17307629B/d16b5139 y terminador56B ya comprobados. Copiar, no regenerar.
- C1A reporte f3eb0ab1...:4775RVMAT propios/10052971B y config histórica.
  C1A1 reporte y contrato22dae243:2048PNG literales/140323829B por metadata,
  ochoPAA/40711646B por metadata; hashes de payload PNG/PAA todavía no observados.
  C1A1 recuperó strings, no un parser semántico de RVMAT. No repetirlo.
- B4A3 reporte d5ce5307...:ocho assets guardados y cuatro hojas nuevas en `leaves/`,
  con path/virtual_path/hash/size. Tres modelos instalados históricos, no identidad
  de archivos instalados hoy. Reusar copias pinadas, no abrir PBO ni P3D parser.
- Binarize/bin/config.cpp instalado dcf19f27... es distinto de P:/bin/config.cpp
  42b4cf95...; este corte elige explícitamente el instalado como entrada de ensayo
  bajo `bin/config.cpp`. No afirma equivalencia ni cambia ninguno.
- Descubrimiento puntual de metadata29-10: P:/core,58entradas/41archivos/9717421B,
  sin reparse observado, sin config.cpp. `texheaders.bin` sí presente. Se conserva
  TODO ese conjunto pequeño como soporte opaco, no se proclama cierre semántico.
  No usar ausencia de config.cpp para omitir core ni explorar todoP:.
- Config histórica stage-kit7-fc/.../config.cpp:8-12 requiredAddonsagua/piloto;
  19CAWorld;37worldName;24-55Outside/midDetail/UsedTerrainMaterials;56-212Navmesh.
  `tools/terrain/compile_visual_pilot_ev112.ps1:18-29` no se ejecuta ni se copia.

## Configuración de laboratorio explícita

[DESIGN] Nuevo texto exacto antes del código: CfgPatches/BalticRoadPivotLab y
CfgWorlds/BalticRoadPivotLab:CAWorld; requiredAddons sólo DZ_Data/DZ_Surfaces.
worldName conserva `dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp` para no
reescribir las referencias internas del WRP. Description identifica laboratorio;
longitude/latitude/center/time/date/MaxTide/MaxWave y las referencias de24-55
del config histórico se conservan. No bloque Navmesh en este ensayo elevado, ni
dependencias Baltic_Water_V30/Baltic_Stream_Pilot, ni inclusión de su población.
Config original intacta. No afirmar arranque nativo ni CAWorld resuelto en stage;
la herencia y requiredAddons son deudas explícitas para la sonda de compilación.
No aceptar co-carga con el paquete productivo del mismo prefijo en un futuro run.

Preparar el literal comparando una vez con la fuente histórica pinada; guardar
diff legible y SHA externo. Ambas ramas usan exactamente el mismo literal.
La prueba no es una autorización para retirar navmesh/población del mapa real.

## Manifiesto externo antes de autoría

Lista cerrada de fuentes y destinos normalizadosASCII lower con slash `/`:
4775RVMAT,2048PNG,8PAA; doce recursos B4A3; dos texturas exteriores y cuatro
RVMAT de UsedTerrainMaterials desde las rutas explícitas C1A; los41archivoscore;
bin/config.cpp instalado y config propio nuevo. Duplicados de destino sólo se
fusionan si SHA/bytes y fuente física observada coinciden; si no, REJECTED_COLLISION.
No normalizar `.png` a `.paa`, no basename, no inventar aliases de prefijo.

Codex preparador autorizado a una lectura fresca de esos payloads para fijar SHA,
tamaño e identidad path/handle/dev/ino/mtime antes de código, incluida la nueva
observación de PNG/PAA/core. Copias B4A3/C0/RVMAT/bin conservan sus pins históricos;
si difieren, rechazo, no repinar. Los SHA nuevos no acreditan identidad retroactiva.
No leer ni copiar el WRP poblado ni navmesh439MB; eliminar sus dos entradas de
configC1A por selector explícito, no por patrón global. Core se enumera sólo una
vez al preparar manifiesto, contra el conjunto/números observados; no seguir enlaces.

Cotas:8192entradas comunes,32MiB por archivo,384MiB payload común,1GiB ambasramas,
8MiBmanifiesto/8MiBreporte. Preparación120s/256MiB; stream1MiB, reserva por tamaño
antes de leer/copiar, lectura real<=declarado y EOF. Raíces fuente cerradas en E:,
P:/core,P:/DZ y config instalado. No escritura en ellas. Reparse en cualquier
ancestro bloquea, salvo ninguno esperado; SUBST no se equipara a symlink.
Relativos: rechazar absolute/drive/dotsegment/backslash/control/noASCII/reservados
Windows/colisión casefold y rutas que escapen del stage. Destino absoluto nuevo enE:.

## Autor, consumidor y pruebas

Codexexecutor600s incluye contrato/oráculos/código; una revisión nativa externa180s
de contrato+código; suite120s/256MiB. Una corrección180s por contraejemplo cerrado,
una recuperación180s si no hay dictamen; no bucle abierto. C1B no lanza ninguna
herramienta DayZ: preflight fresco corresponderá antes de una sonda C1C.

Autor: CLI nuevo exige pin externo del contrato; crea sello exclusivo antes de
copiar. Cada archivo se copia a control/root y candidate/root al destino literal;
WRP0/3 bajo el mismo nombre. Compara hash de cada chunk leído/escrito, EOF y
identidad final de fuente. Conserva parciales consumidos en fallo. No sobrescribir.
Nuevo consumidor, sin importar autor: lee contrato por pin externo y recorre ambos
árboles, rechaza extra/faltante/reparse, comprueba hashes/bytes/destinos/configs y
reabre todas las fuentes por su propio flujo. No confiar en el informe del autor.
No writer/parserWRP nuevo: identidad de las fuentes C0 se hereda porSHA exacto.

Oráculo literal previo con dos archivos comunes (uno de nombre con espacio) y
control/candidato de bytes distintos, configliteral; expectedfiles por rama.
Negativos obligatorios:extra/falta/modificado en stage, source cambia, PNG redirigido
a PAA en co-mutante, colisión casefold, traversal/absolute/reservadoWindows, bool en
bytes, salida ya existente, source reparse simulado, hashcontrato erróneo, config
de una rama distinto y fuenteWRPequivocada. Consumidor se ejecuta sobre fixtures
materializados independientes, no únicamente sobre salida del autor.

Una materialización real120s/256MiB y un consumidor120s/256MiB sólo tras gates;
sin retries. FULL sólo todos los bytes verificados y únicos; timeout/fallo no
produce stage aceptado. Ni suite verde ni copia exacta prueban formatoPNG/PAA,
compilabilidad, recursos transitivos, precedencia nativa o pivote.

## Después

RoadC1C necesita plan propio COMPILE_PROBE_ONLY si sigue sin lectorOPRW completo:
preflight fresco, invocación local anclada, control primero y candidato condicionado
a artefacto/identidad del control, presupuesto de una pareja, ninguna aceptación
semántica ni despliegue. Un escáner de modelos no se convierte en lector de alturas.
NativeC2/Q05 sólo con gates propios. Nueve humanos0resueltos,C1NOT_REVIEWED.

## Adjudicación Muse 29.813s, ocho precisiones incorporadas

F1: reconciliar las cuatroPAA y cuatroRVMAT del config por rutas completas; las
dosPAA grass pueden coincidir con el conjunto8, pero no se supone sin tabla.
F2: config propio destino dayz_baltic_12km_dev/tb/narva_trial/config.cpp; WRP
dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp. bin/config.cpp es distinto.
F3: pins completos/tamaños/paths en contrato antes de código.
F4: conservar clases vacías Names/Sounds/Ambient; omitir exclusivamente Navmesh;
literal/diff guardados. Dos replacements de clase y descripción, requiredAddons
quitando sólo las dos dependencias Baltic. No reinterpretar el config histórico.
F5: conservar todos los alias-fuente observados de un destino; sólo fusionar si
comparten identidad física y SHA/bytes. Si identidades distintas, rechazo aun si
SHA coincide. Consumidor reabre todos los alias, no elimina fuentes silenciosamente.
F6: todas las cotas abortan antes del código si las entradas reales no caben.
F7: fuera del core acotado, abrir sólo las rutas individuales; reparse e identidad
revalidados en preparación/autor/consumidor, no enumerar E: o P:/DZ.
F8: consumidor separa STAGE_BYTES de SOURCE_PIN_MATCH; FULL necesita ambos;
source drift no se atribuye a corrupción del stage. Formatos y compilación abiertos.
Revisión externa de la cápsula preimagen, postimagen adjudicada por integrador;
no otra revisión externa ni consenso. No repetir el plan review consumido.

CONTRACT SUMMARY (la lista completa esta pinada, no cabe en capsula):
{
  "schema": "road-c1b-stage.v1",
  "caps": {
    "entries": 8192,
    "file": 33554432,
    "common": 402653184,
    "pair": 1073741824,
    "json": 8388608
  },
  "bindings": {
    "path": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1b-local-author-20261029\\bindings.json",
    "sha256": "b632818ad796320ef60c33cc65125683c2ac7f40bd6080afed8d85c98154f052"
  },
  "output": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c1b-stage-20261029",
  "claims": {
    "build_ready": false,
    "dependency_closure": "NOT_EVALUATED",
    "compiled_terrain_decoder": "NOT_VERIFIED"
  },
  "config_refs": [
    {
      "raw": "DZ\\worlds\\chernarusplus\\data\\outside_sat_co.paa",
      "source": "P:\\DZ\\worlds\\chernarusplus\\data\\outside_sat_co.paa",
      "dest": "dz/worlds/chernarusplus/data/outside_sat_co.paa"
    },
    {
      "raw": "DZ\\surfaces\\data\\terrain\\cp_grass_nopx.paa",
      "source": "P:\\DZ\\surfaces\\data\\terrain\\cp_grass_nopx.paa",
      "dest": "dz/surfaces/data/terrain/cp_grass_nopx.paa"
    },
    {
      "raw": "DZ\\surfaces\\data\\terrain\\cp_grass_ca.paa",
      "source": "P:\\DZ\\surfaces\\data\\terrain\\cp_grass_ca.paa",
      "dest": "dz/surfaces/data/terrain/cp_grass_ca.paa"
    },
    {
      "raw": "DZ\\worlds\\chernarusplus\\data\\middle_sat_mco.paa",
      "source": "P:\\DZ\\worlds\\chernarusplus\\data\\middle_sat_mco.paa",
      "dest": "dz/worlds/chernarusplus/data/middle_sat_mco.paa"
    },
    {
      "raw": "DZ\\surfaces\\data\\terrain\\cp_gravel.rvmat",
      "source": "P:\\DZ\\surfaces\\data\\terrain\\cp_gravel.rvmat",
      "dest": "dz/surfaces/data/terrain/cp_gravel.rvmat"
    },
    {
      "raw": "DZ\\surfaces\\data\\terrain\\cp_conifer_common1.rvmat",
      "source": "P:\\DZ\\surfaces\\data\\terrain\\cp_conifer_common1.rvmat",
      "dest": "dz/surfaces/data/terrain/cp_conifer_common1.rvmat"
    },
    {
      "raw": "DZ\\surfaces\\data\\terrain\\cp_grass.rvmat",
      "source": "P:\\DZ\\surfaces\\data\\terrain\\cp_grass.rvmat",
      "dest": "dz/surfaces/data/terrain/cp_grass.rvmat"
    },
    {
      "raw": "DZ\\surfaces\\data\\terrain\\cp_grass_tall.rvmat",
      "source": "P:\\DZ\\surfaces\\data\\terrain\\cp_grass_tall.rvmat",
      "dest": "dz/surfaces/data/terrain/cp_grass_tall.rvmat"
    }
  ],
  "files_count": 6894,
  "first_entries": [
    {
      "scope": "candidate",
      "dest": "dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp",
      "sha256": "2fb3686b6d86888609caeace3be14f8422cfe8c1da9d77db263c86e21ddcb426",
      "bytes": 17307968,
      "sources": [
        {
          "path": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c0-isolated-sources-20261029\\candidate.wrp",
          "identity": [
            1736162863918533152,
            1407374890122956,
            17307968,
            1793307050888783800
          ],
          "sha256": "2fb3686b6d86888609caeace3be14f8422cfe8c1da9d77db263c86e21ddcb426",
          "bytes": 17307968,
          "origin": "C0"
        }
      ]
    },
    {
      "scope": "common",
      "dest": "bin/config.cpp",
      "sha256": "dcf19f271d6537e6ba45fe6af47cc0865d52768bca05ecc9abc1b0314bc1f4ea",
      "bytes": 199732,
      "sources": [
        {
          "path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\Binarize\\bin\\config.cpp",
          "identity": [
            14582687742868402597,
            19984723346816382,
            199732,
            1757695091814734300
          ],
          "sha256": "dcf19f271d6537e6ba45fe6af47cc0865d52768bca05ecc9abc1b0314bc1f4ea",
          "bytes": 199732,
          "origin": "INSTALLED_BIN"
        }
      ]
    }
  ],
  "last_entries": [
    {
      "scope": "common",
      "dest": "dz/worlds/chernarusplus/data/outside_sat_co.paa",
      "sha256": "ef17a4753898b7de549069dc28f2ed540624edc0aab389d784fb19621e083a77",
      "bytes": 145677,
      "sources": [
        {
          "path": "P:\\DZ\\worlds\\chernarusplus\\data\\outside_sat_co.paa",
          "identity": [
            14582687742868402597,
            844424931181306,
            145677,
            1775740214635199500
          ],
          "sha256": "ef17a4753898b7de549069dc28f2ed540624edc0aab389d784fb19621e083a77",
          "bytes": 145677,
          "origin": "CONFIG_REFERENCE"
        }
      ]
    },
    {
      "scope": "control",
      "dest": "dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp",
      "sha256": "f00c3f57ab3660e93c44a1cb612c6338f87db1bfd4c047acf6f7389c61c7e6df",
      "bytes": 17307685,
      "sources": [
        {
          "path": "E:\\DayZ-Baltic-Build\\shape-repair-20261025\\road-c0-isolated-sources-20261029\\control.wrp",
          "identity": [
            1736162863918533152,
            1407374890122955,
            17307685,
            1793307050812939400
          ],
          "sha256": "f00c3f57ab3660e93c44a1cb612c6338f87db1bfd4c047acf6f7389c61c7e6df",
          "bytes": 17307685,
          "origin": "C0"
        }
      ]
    }
  ]
}
PREPARED
{
  "status": "MANIFEST_PREPARED_ONLY",
  "contract_sha256": "b7d335883f33629f8e9fc1f1b98018dadb2cb95541a33a643f6805a3bcb3d1c6",
  "bindings_sha256": "b632818ad796320ef60c33cc65125683c2ac7f40bd6080afed8d85c98154f052",
  "oracle_sha256": "677c4561ac867a0fbfc5a1edeaf1da59b6b63c03063821154cedc549b91d5429",
  "common_files": 6892,
  "common_bytes": 223031657,
  "core_entries": 57,
  "core_files": 41,
  "seconds": 27.719451904296875,
  "pins": {
    "road-c1a-research-20261029/capture/report.json": "f3eb0ab1b672ba742a82d6d7fe2114373c75e3604f30db4ddd508880efb4ce6a",
    "road-c1a1-recovery-20261029/capture/report.json": "1f5ff42fefc307de85b87e3eed8df1b5e4d04c237fad8a6a504a145f01a57b6a",
    "road-b4a3-dependencies-20261029/report.json": "d5ce5307f926ead5a6f599da96b336c5b76451372e8ebf3f742a06cc5ce930a5"
  }
}
FILE config.cpp SHA c054ff971339071ee0d5b53aa54d4adf56836ca8196a9f9e8ebb4bd5dc75fea9
1: class CfgPatches
2: {
3: 	class BalticRoadPivotLab
4: 	{
5: 		units[]={};
6: 		weapons[]={};
7: 		requiredVersion=0.1;
8: 		requiredAddons[]=
9: 		{
10: 			"DZ_Data",
11: 			"DZ_Surfaces"
12: 		};
13: 	};
14: };
15: class CfgWorlds
16: {
17: 	class CAWorld;
18: 	class BalticRoadPivotLab: CAWorld
19: 	{
20:         description = "Baltic road pivot laboratory";
21: 		MaxTide=1.5;
22: 		MaxWave=0.1;
23: 		class OutsideTerrain
24: 		{
25: 			satellite="DZ\worlds\chernarusplus\data\outside_sat_co.paa";
26: 			enableTerrainSynth=1;
27: 			class Layers
28: 			{
29: 				class Layer0
30: 				{
31: 					nopx="DZ\surfaces\data\terrain\cp_grass_nopx.paa";
32: 					texture="DZ\surfaces\data\terrain\cp_grass_ca.paa";
33: 				};
34: 			};
35: 		};
36: 		worldName="dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp";
37: 		longitude=30;
38: 		latitude=-59;
39: 		startTime="12:00";
40: 		startDate="29/09/2026";
41: 		centerPosition[]={6144,6144,100};
42: 		clutterGrid=1;
43: 		clutterDist=125;
44: 		noDetailDist=65;
45: 		fullDetailDist=10;
46: 		volFogOffset=0;
47: 		midDetailTexture="DZ\worlds\chernarusplus\data\middle_sat_mco.paa";
48: 		class UsedTerrainMaterials
49: 		{
50: 			material1="DZ\surfaces\data\terrain\cp_gravel.rvmat";
51: 			material2="DZ\surfaces\data\terrain\cp_conifer_common1.rvmat";
52: 			material3="DZ\surfaces\data\terrain\cp_grass.rvmat";
53: 			material4="DZ\surfaces\data\terrain\cp_grass_tall.rvmat";
54: 		};
55: 		class Names
56: 		{
57: 		};
58: 		class Sounds
59: 		{
60: 			sounds[]={};
61: 		};
62: 		class Ambient
63: 		{
64: 		};
65: 	};
66: };

FILE oracle.json SHA 677c4561ac867a0fbfc5a1edeaf1da59b6b63c03063821154cedc549b91d5429
1: {
2:   "schema": "road-c1b-literal.v1",
3:   "common": {
4:     "data/a space.png": "PNG literal\n",
5:     "config.cpp": "class Lab {};\n"
6:   },
7:   "control": {
8:     "lab.wrp": "control zero\n"
9:   },
10:   "candidate": {
11:     "lab.wrp": "candidate three\n"
12:   },
13:   "claims": {
14:     "build_ready": false,
15:     "dependency_closure": "NOT_EVALUATED",
16:     "compiled_terrain_decoder": "NOT_VERIFIED"
17:   },
18:   "negatives": [
19:     "EXTRA",
20:     "MISSING",
21:     "STAGE_HASH",
22:     "SOURCE_PIN",
23:     "BINDING",
24:     "COLLISION",
25:     "PATH",
26:     "SIZE_TYPE",
27:     "EXISTS",
28:     "REPARSE",
29:     "CONTRACT_PIN",
30:     "CONFIG",
31:     "WRP_PIN"
32:   ]
33: }

FILE stage_road_lab_c1b.py SHA 856bfbfe39c55acc7ac35a073f9e9a4d497777a98f14002b0580ebd5a717904b
1: """One-shot byte stage. No DayZ tool, format or native acceptance."""
2: from pathlib import Path
3: import argparse, hashlib, json, os, re, stat, sys
4: 
5: CAPS={'entries':8192,'file':33554432,'common':402653184,'pair':1073741824,'json':8388608}
6: CLAIMS={'build_ready':False,'dependency_closure':'NOT_EVALUATED','compiled_terrain_decoder':'NOT_VERIFIED'}
7: class Rejected(Exception): pass
8: def need(ok,code):
9:     if not ok: raise Rejected(code)
10: def pairs(seq):
11:     d={}
12:     for k,v in seq:
13:         need(k not in d,'SCHEMA');d[k]=v
14:     return d
15: def safe_rel(s):
16:     need(type(s) is str and s and s.isascii() and s==s.lower() and '\\' not in s and ':' not in s,'PATH')
17:     for c in s.split('/'):
18:         need(c not in ('','.','..') and c[-1] not in '. ' and not any(ord(x)<32 or x in '<>"|?*' for x in c),'PATH')
19:         need(not re.fullmatch(r'(con|prn|aux|nul|com[1-9]|lpt[1-9])',c.split('.')[0]),'PATH')
20:     return s
21: def guard(p):
22:     for q in [p,*p.parents]:
23:         s=q.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024,'REPARSE')
24: def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
25: def blob(path,sha):
26:     p=Path(path);guard(p);need(p.stat().st_size<=CAPS['json'],'JSON_CAP')
27:     with p.open('rb') as f:b=f.read(CAPS['json']+1)
28:     need(len(b)<=CAPS['json'] and hashlib.sha256(b).hexdigest()==sha,'CONTRACT_PIN')
29:     return json.loads(b,object_pairs_hook=pairs)
30: def contract(path,pin,binding_pin):
31:     c=blob(path,pin);need(type(c) is dict and set(c)=={'schema','caps','bindings','files','output','claims','config_refs'},'SCHEMA')
32:     need(c['schema']=='road-c1b-stage.v1' and c['caps']==CAPS and all(type(v) is int for v in c['caps'].values()),'SCHEMA')
33:     need(c['claims']==CLAIMS and c['claims']['build_ready'] is False,'SCHEMA')
34:     need(type(c['bindings']) is dict and set(c['bindings'])=={'path','sha256'} and c['bindings']['sha256']==binding_pin,'BINDING')
35:     binding=blob(c['bindings']['path'],binding_pin)
36:     fs=c['files'];need(type(fs) is list and 2<=len(fs)<=CAPS['entries']+2,'ENTRY_CAP')
37:     seen=set();common=0;cb=0;branches={'control':[],'candidate':[]};observed=[]
38:     for e in fs:
39:         need(type(e) is dict and set(e)=={'scope','dest','sha256','bytes','sources'},'SCHEMA')
40:         need(e['scope'] in ('common','control','candidate'),'SCHEMA');d=safe_rel(e['dest']);key=(e['scope'],d)
41:         need(key not in seen,'COLLISION');seen.add(key)
42:         need(type(e['bytes']) is int and 0<=e['bytes']<=CAPS['file'],'SIZE_TYPE')
43:         need(type(e['sha256']) is str and re.fullmatch('[0-9a-f]{64}',e['sha256']),'SCHEMA')
44:         ss=e['sources'];need(type(ss) is list and 1<=len(ss)<=16,'SCHEMA')
45:         for s in ss:
46:             need(type(s) is dict and set(s)=={'path','identity','sha256','bytes','origin'},'SCHEMA')
47:             need(type(s['path']) is str and Path(s['path']).is_absolute() and type(s['origin']) is str,'SCHEMA')
48:             need(type(s['identity']) is list and len(s['identity'])==4 and all(type(i) is int and i>=0 for i in s['identity']),'SCHEMA')
49:             need(type(s['bytes']) is int and s['bytes']==e['bytes'] and s['sha256']==e['sha256'] and s['identity'][2]==e['bytes'],'SCHEMA')
50:             need(s['identity']==ss[0]['identity'],'COLLISION')
51:         observed.append({'scope':e['scope'],'dest':d,'sources':[s['path'] for s in ss]})
52:         if e['scope']=='common':common+=1;cb+=e['bytes']
53:         else:branches[e['scope']].append(e)
54:     need(observed==binding,'BINDING')
55:     need(common<=CAPS['entries'] and cb<=CAPS['common'],'TOTAL_CAP')
56:     need(all(len(v)==1 for v in branches.values()),'WRP_PIN')
57:     x,y=branches['control'][0],branches['candidate'][0]
58:     need(x['dest']==y['dest'] and x['sha256']!=y['sha256'] and ('common',x['dest']) not in seen,'WRP_PIN')
59:     need(2*cb+x['bytes']+y['bytes']<=CAPS['pair'],'TOTAL_CAP')
60:     need(type(c['output']) is str and Path(c['output']).is_absolute(),'PATH')
61:     return c
62: def transfer(s,targets):
63:     p=Path(s['path']);guard(p);need(ident(p.stat())==s['identity'],'SOURCE_PIN')
64:     streams=[];h=hashlib.sha256();n=0
65:     try:
66:         for t in targets:
67:             t.parent.mkdir(parents=True,exist_ok=True);guard(t.parent);streams.append(t.open('xb'))
68:         with p.open('rb') as f:
69:             need(ident(os.fstat(f.fileno()))==s['identity'],'SOURCE_PIN')
70:             while True:
71:                 b=f.read(min(1048576,s['bytes']-n+1))
72:                 if not b:break
73:                 n+=len(b);need(n<=s['bytes'],'SOURCE_PIN');h.update(b)
74:                 for out in streams:need(out.write(b)==len(b),'WRITE')
75:             need(ident(os.fstat(f.fileno()))==s['identity'],'SOURCE_PIN')
76:         guard(p);need(ident(p.stat())==s['identity'] and n==s['bytes'] and h.hexdigest()==s['sha256'],'SOURCE_PIN')
77:         for out in streams:out.flush();os.fsync(out.fileno())
78:     finally:
79:         for out in streams:out.close()
80:     for t in targets:
81:         h2=hashlib.sha256();count=0;guard(t)
82:         with t.open('rb') as f:
83:             for b in iter(lambda:f.read(1048576),b''):count+=len(b);need(count<=s['bytes'],'WRITE');h2.update(b)
84:         need(count==s['bytes'] and h2.hexdigest()==s['sha256'],'WRITE')
85: def run(c,pin):
86:     out=Path(c['output']);guard(out.parent);need(not out.exists(),'EXISTS');out.mkdir()
87:     (out/'consumed.json').write_text(json.dumps({'contract_sha256':pin,'retry':False}),encoding='utf-8')
88:     receipts=[]
89:     for e in c['files']:
90:         arms=('control','candidate') if e['scope']=='common' else (e['scope'],)
91:         targets=[out/a/'root'/e['dest'] for a in arms]
92:         transfer(e['sources'][0],targets)
93:         for s in e['sources'][1:]:transfer(s,[])
94:         receipts.append({k:e[k] for k in ('scope','dest','bytes','sha256')})
95:     result={'status':'LAB_STAGE_WRITTEN_ONLY','contract_sha256':pin,'claims':CLAIMS,'files':receipts}
96:     b=json.dumps(result,indent=2).encode();need(len(b)<=CAPS['json'],'OUTPUT_CAP');(out/'producer.json').write_bytes(b);return result
97: def main():
98:     p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--bindings-sha',required=True);a=p.parse_args()
99:     try:
100:         c=contract(a.contract,a.sha,a.bindings_sha);r=run(c,a.sha);print(json.dumps({'status':r['status'],'entries':len(r['files'])}));return 0
101:     except Rejected as e:print('REJECTED:'+str(e));return 2
102:     except OSError as e:print('IO_ERROR:'+str(e));return 3
103: if __name__=='__main__':sys.exit(main())

FILE verify_road_lab_c1b.py SHA 6d99b58fd5f072a83ba320207880583fa33aa99966cfb12e96746dda879c94d8
1: """Independent inventory/source walk; standard-library I/O shared with author."""
2: import argparse,hashlib,json,os,re,stat,sys
3: from pathlib import Path
4: 
5: class Invalid(Exception):pass
6: def check(x,code):
7:     if not x:raise Invalid(code)
8: def obj(items):
9:     d={}
10:     for k,v in items:
11:         check(k not in d,'SCHEMA');d[k]=v
12:     return d
13: def ancestry(p):
14:     while True:
15:         s=p.lstat();check(not stat.S_ISLNK(s.st_mode) and (getattr(s,'st_file_attributes',0)&1024)==0,'REPARSE')
16:         if p.parent==p:return
17:         p=p.parent
18: def identity(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
19: def hashed(p,limit,expected_id=None):
20:     p=Path(p);ancestry(p);before=identity(p.stat());check(stat.S_ISREG(p.stat().st_mode) and before[2]<=limit,'FILE_CAP')
21:     if expected_id is not None:check(before==expected_id,'SOURCE_PIN')
22:     h=hashlib.sha256();n=0
23:     with p.open('rb') as f:
24:         check(identity(os.fstat(f.fileno()))==before,'IDENTITY')
25:         while n<=limit:
26:             b=f.read(min(524288,limit-n+1))
27:             if not b:break
28:             n+=len(b);check(n<=limit,'FILE_CAP');h.update(b)
29:         check(identity(os.fstat(f.fileno()))==before,'IDENTITY')
30:     ancestry(p);check(identity(p.stat())==before and n==before[2],'IDENTITY');return n,h.hexdigest()
31: def load(p,pin):
32:     n,h=hashed(p,8388608);check(h==pin,'CONTRACT_PIN')
33:     # Parse a second bounded buffer, independently pin the exact parsed bytes.
34:     with open(p,'rb') as f:b=f.read(8388609)
35:     check(len(b)==n and hashlib.sha256(b).hexdigest()==pin,'CONTRACT_PIN');return json.loads(b,object_pairs_hook=obj)
36: def relative(s):
37:     check(type(s) is str and s and s.isascii() and s==s.lower(),'PATH')
38:     check(not any(ord(c)<32 or c in '\\:<>"|?*' for c in s),'PATH')
39:     for a in s.split('/'):
40:         check(a not in ('','.','..') and a[-1] not in '. ','PATH')
41:         check(a.split('.')[0] not in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]},'PATH')
42:     return s
43: def read_contract(path,pin,binding_pin):
44:     c=load(path,pin);check(type(c) is dict and set(c)=={'schema','caps','bindings','files','output','claims','config_refs'},'SCHEMA')
45:     caps={'entries':8192,'file':33554432,'common':402653184,'pair':1073741824,'json':8388608}
46:     check(c['schema']=='road-c1b-stage.v1' and c['caps']==caps and all(type(v) is int for v in c['caps'].values()),'SCHEMA')
47:     check(c['claims']=={'build_ready':False,'dependency_closure':'NOT_EVALUATED','compiled_terrain_decoder':'NOT_VERIFIED'} and c['claims']['build_ready'] is False,'SCHEMA')
48:     check(type(c['bindings']) is dict and set(c['bindings'])=={'path','sha256'} and c['bindings']['sha256']==binding_pin,'BINDING')
49:     bind=load(c['bindings']['path'],binding_pin);check(type(bind) is list,'BINDING')
50:     check(type(c['files']) is list and len(c['files'])<=8194,'ENTRY_CAP');expected={'control':{},'candidate':{}};sources=[];bseen=[];keys=set();amount=0;common=0;arms={}
51:     for row in c['files']:
52:         check(type(row) is dict and set(row)=={'scope','dest','sha256','bytes','sources'},'SCHEMA')
53:         scope=row['scope'];check(scope in ('common','control','candidate'),'SCHEMA');dest=relative(row['dest']);check((scope,dest) not in keys,'COLLISION');keys.add((scope,dest))
54:         size=row['bytes'];digest=row['sha256'];check(type(size) is int and 0<=size<=33554432,'SIZE_TYPE');check(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest),'SCHEMA')
55:         aliases=row['sources'];check(type(aliases) is list and 1<=len(aliases)<=16,'SCHEMA')
56:         ids=[]
57:         for s in aliases:
58:             check(type(s) is dict and set(s)=={'path','identity','sha256','bytes','origin'},'SCHEMA')
59:             check(type(s['path']) is str and Path(s['path']).is_absolute() and type(s['origin']) is str,'SCHEMA')
60:             si=s['identity'];check(type(si) is list and len(si)==4 and all(type(i) is int and i>=0 for i in si),'SCHEMA')
61:             check(type(s['bytes']) is int and s['bytes']==size and si[2]==size and s['sha256']==digest,'SCHEMA');ids.append(si);sources.append(s)
62:         check(all(i==ids[0] for i in ids),'COLLISION');bseen.append({'scope':scope,'dest':dest,'sources':[s['path'] for s in aliases]})
63:         if scope=='common':common+=1;amount+=size;use=['control','candidate']
64:         else:check(scope not in arms,'WRP_PIN');arms[scope]=(dest,digest,size);use=[scope]
65:         for arm in use:check(dest not in expected[arm],'COLLISION');expected[arm][dest]=(size,digest)
66:     check(bseen==bind,'BINDING');check(common<=8192 and amount<=402653184,'TOTAL_CAP')
67:     check(set(arms)=={'control','candidate'} and arms['control'][0]==arms['candidate'][0] and arms['control'][1]!=arms['candidate'][1],'WRP_PIN')
68:     check(amount*2+arms['control'][2]+arms['candidate'][2]<=1073741824,'TOTAL_CAP')
69:     check(type(c['output']) is str and Path(c['output']).is_absolute(),'PATH');return c,expected,sources
70: def verify(c,expected,sources,pin):
71:     root=Path(c['output']);stage_errors=[];source_errors=[];count=0
72:     for arm in ('control','candidate'):
73:         base=root/arm/'root';seen=set()
74:         try:
75:             ancestry(base);check({p.name for p in (root/arm).iterdir()}=={'root'},'EXTRA')
76:             dirs=set();wanted_dirs={str(p).replace('\\','/') for name in expected[arm] for p in Path(name).parents if str(p)!='.'}
77:             stack=[base];nodes=0
78:             while stack:
79:                 parent=stack.pop()
80:                 for p in parent.iterdir():
81:                     nodes+=1;check(nodes<=32768,'TREE_CAP');ancestry(p)
82:                     if p.is_dir():dirs.add(p.relative_to(base).as_posix());stack.append(p);continue
83:                     name=p.relative_to(base).as_posix();check(name not in seen,'COLLISION');seen.add(name)
84:                     check(name in expected[arm],'EXTRA');n,h=hashed(p,expected[arm][name][0]);check((n,h)==expected[arm][name],'STAGE_HASH');count+=1
85:             check(seen==set(expected[arm]),'MISSING')
86:             check(dirs==wanted_dirs,'EXTRA')
87:         except (Invalid,OSError) as e:stage_errors.append({'arm':arm,'error':str(e)})
88:     for s in sources:
89:         try:check(hashed(s['path'],s['bytes'],s['identity'])==(s['bytes'],s['sha256']),'SOURCE_PIN')
90:         except (Invalid,OSError) as e:source_errors.append({'path':s['path'],'error':str(e)})
91:     good=not(stage_errors or source_errors)
92:     return {'status':'VERIFIED_LAB_STAGE_BYTES_ONLY' if good else 'REJECTED','contract_sha256':pin,'STAGE_BYTES':'MATCH' if not stage_errors else 'REJECTED','SOURCE_PIN_MATCH':'MATCH' if not source_errors else 'REJECTED','stage_errors':stage_errors,'source_errors':source_errors,'stage_files_verified':count,'source_aliases_checked':len(sources),'claims':c['claims'],'continuous_monitoring':False}
93: def main():
94:     p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--bindings-sha',required=True);p.add_argument('--report',required=True);a=p.parse_args()
95:     try:
96:         c,expected,sources=read_contract(a.contract,a.sha,a.bindings_sha);r=verify(c,expected,sources,a.sha);b=json.dumps(r,indent=2).encode();check(len(b)<=8388608,'OUTPUT_CAP')
97:         with open(a.report,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
98:         print(json.dumps({k:r[k] for k in ['status','STAGE_BYTES','SOURCE_PIN_MATCH','stage_files_verified','source_aliases_checked']}));return 0 if r['status'].startswith('VERIFIED') else 2
99:     except Invalid as e:print('REJECTED:'+str(e));return 2
100:     except OSError as e:print('IO_ERROR:'+str(e));return 3
101: if __name__=='__main__':sys.exit(main())

FILE test_road_lab_c1b.py SHA 567d1c4922e80b38f3e48a749e670c52ef0cae3fc545f50a4ce4464b2a3b37c2
1: import copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile,unittest
2: from pathlib import Path
3: from unittest.mock import patch
4: from types import SimpleNamespace
5: D=Path(__file__).parent
6: def module(name):
7:  s=importlib.util.spec_from_file_location(name,D/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
8: A=module('stage_road_lab_c1b');V=module('verify_road_lab_c1b')
9: ORACLE=D/'oracle.json';ORACLE_SHA='677c4561ac867a0fbfc5a1edeaf1da59b6b63c03063821154cedc549b91d5429'
10: assert hashlib.sha256(ORACLE.read_bytes()).hexdigest()==ORACLE_SHA
11: L=json.loads(ORACLE.read_bytes())
12: def digest(b):return hashlib.sha256(b).hexdigest()
13: class Tests(unittest.TestCase):
14:  def setUp(self):
15:   self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.out=self.d/'pair';files=[]
16:   for scope in ('common','control','candidate'):
17:    for name,text in L[scope].items():
18:     src=self.d/'source'/scope/name;src.parent.mkdir(parents=True,exist_ok=True);src.write_bytes(text.encode());s=src.stat();b=text.encode()
19:     files.append({'scope':scope,'dest':name,'bytes':len(b),'sha256':digest(b),'sources':[{'path':str(src),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns],'bytes':len(b),'sha256':digest(b),'origin':'LITERAL'}]})
20:   self.bind=self.d/'bindings.json';self.bind.write_text(json.dumps([{'scope':f['scope'],'dest':f['dest'],'sources':[s['path'] for s in f['sources']]} for f in files]));self.bp=digest(self.bind.read_bytes())
21:   self.c={'schema':'road-c1b-stage.v1','caps':{'entries':8192,'file':33554432,'common':402653184,'pair':1073741824,'json':8388608},'claims':L['claims'],'config_refs':[],'files':files,'bindings':{'path':str(self.bind),'sha256':self.bp},'output':str(self.out)};self.cp=self.d/'contract.json';self.write()
22:  def tearDown(self):self.tmp.cleanup()
23:  def write(self):self.cp.write_text(json.dumps(self.c));self.pin=digest(self.cp.read_bytes())
24:  def independent_stage(self):
25:   for arm in ('control','candidate'):
26:    for name,text in {**L['common'],**L[arm]}.items():
27:     p=self.out/arm/'root'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
28:  def check_stage(self):
29:   c,e,s=V.read_contract(self.cp,self.pin,self.bp);return V.verify(c,e,s,self.pin)
30:  def both_reject(self,code):
31:   self.write()
32:   for f,ex in [(A.contract,A.Rejected),(V.read_contract,V.Invalid)]:
33:    with self.subTest(reader=f.__module__),self.assertRaisesRegex(ex,'^'+code+'$'):f(self.cp,self.pin,self.bp)
34:  def test_independent_literal_pair(self):
35:   self.independent_stage();r=self.check_stage();self.assertEqual(r,{'status':'VERIFIED_LAB_STAGE_BYTES_ONLY','contract_sha256':self.pin,'STAGE_BYTES':'MATCH','SOURCE_PIN_MATCH':'MATCH','stage_errors':[],'source_errors':[],'stage_files_verified':6,'source_aliases_checked':4,'claims':L['claims'],'continuous_monitoring':False})
36:  def test_author_and_consumer_cli(self):
37:   for file,extra in [('stage_road_lab_c1b.py',[]),('verify_road_lab_c1b.py',['--report',str(self.d/'consumer.json')])]:
38:    r=subprocess.run([sys.executable,'-I','-X','utf8',str(D/file),'--contract',str(self.cp),'--sha',self.pin,'--bindings-sha',self.bp,*extra],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
39:   self.assertEqual(json.loads((self.d/'consumer.json').read_bytes())['stage_files_verified'],6)
40:  def test_stage_tamper(self):
41:   self.independent_stage();(self.out/'candidate/root/config.cpp').write_bytes(b'class Xab {};\n');r=self.check_stage();self.assertEqual((r['STAGE_BYTES'],r['SOURCE_PIN_MATCH']),('REJECTED','MATCH'));self.assertIn('STAGE_HASH',str(r['stage_errors']))
42:  def test_missing(self):
43:   self.independent_stage();(self.out/'control/root/lab.wrp').unlink();r=self.check_stage();self.assertIn('MISSING',str(r['stage_errors']))
44:  def test_extra_file(self):
45:   self.independent_stage();(self.out/'control/root/extra.txt').write_bytes(b'x');self.assertIn('EXTRA',str(self.check_stage()['stage_errors']))
46:  def test_extra_empty_directory(self):
47:   self.independent_stage();(self.out/'control/root/unlisted').mkdir();self.assertIn('EXTRA',str(self.check_stage()['stage_errors']))
48:  def test_source_drift_separated(self):
49:   self.independent_stage();Path(self.c['files'][0]['sources'][0]['path']).write_bytes(b'changed\n');r=self.check_stage();self.assertEqual((r['STAGE_BYTES'],r['SOURCE_PIN_MATCH']),('MATCH','REJECTED'))
50:  def test_co_mutant_png_redirect(self):
51:   f=self.c['files'][0];src=self.d/'unapproved.paa';src.write_bytes(b'fake PAA');s=src.stat();f['sha256']=digest(src.read_bytes());f['bytes']=s.st_size;f['sources']=[{'path':str(src),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns],'sha256':f['sha256'],'bytes':f['bytes'],'origin':'LITERAL'}];self.both_reject('BINDING')
52:  def test_closed_path_set(self):
53:   orig=copy.deepcopy(self.c)
54:   for bad in ['../outside','/outside','c:/outside','data\\a.png','nul.txt','data/end.','data/UP.png','data/a:stream','data/../x']:
55:    with self.subTest(bad=bad):self.c=copy.deepcopy(orig);self.c['files'][0]['dest']=bad;self.both_reject('PATH')
56:  def test_collision(self):
57:   self.c['files'].insert(1,copy.deepcopy(self.c['files'][0]));self.both_reject('COLLISION')
58:  def test_bool_size(self):self.c['files'][0]['bytes']=True;self.both_reject('SIZE_TYPE')
59:  def test_wrong_contract_pin(self):
60:   for f,ex in [(A.contract,A.Rejected),(V.read_contract,V.Invalid)]:
61:    with self.assertRaisesRegex(ex,'CONTRACT_PIN'):f(self.cp,'0'*64,self.bp)
62:  def test_existing_output(self):
63:   self.independent_stage()
64:   with self.assertRaisesRegex(A.Rejected,'EXISTS'):A.run(A.contract(self.cp,self.pin,self.bp),self.pin)
65:  def test_wrong_wrp(self):
66:   self.independent_stage();(self.out/'candidate/root/lab.wrp').write_bytes(L['control']['lab.wrp'].encode());self.assertEqual(self.check_stage()['STAGE_BYTES'],'REJECTED')
67:  def test_reparse_simulated(self):
68:   target=Path(self.c['files'][0]['sources'][0]['path']);original=Path.lstat
69:   def patched(p,*a,**kw):
70:    s=original(p,*a,**kw)
71:    return SimpleNamespace(st_mode=s.st_mode,st_file_attributes=1024) if p==target else s
72:   with patch.object(Path,'lstat',patched):
73:    with self.assertRaisesRegex(A.Rejected,'REPARSE'):A.transfer(self.c['files'][0]['sources'][0],[])
74:    with self.assertRaisesRegex(V.Invalid,'REPARSE'):V.hashed(target,1000)
75:  def test_alias_identity_and_caps(self):
76:   orig=copy.deepcopy(self.c);s=copy.deepcopy(self.c['files'][0]['sources'][0]);s['identity'][1]+=1;self.c['files'][0]['sources'].append(s);self.both_reject('COLLISION')
77:   self.c=orig;self.c['caps']['file']=33554433;self.both_reject('SCHEMA')
78: if __name__=='__main__':unittest.main()
