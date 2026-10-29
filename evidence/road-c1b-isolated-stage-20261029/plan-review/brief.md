REVISOR independiente Muse Wonder1.0, CLI nativo. SOLO lectura de esta capsula, sin herramientas, codigo ni archivos. Codex planner/integrator y executor local explicitamente asignado al corte si se aprueba. Revisar el plan concreto antes de implementarlo: seguridad/rutas/contrato/cotas/dos ramas/consumidor. No repetir council ni investigacion. Presupuesto dictamen180s, max1200palabras. Entrega final SOUND / SOUND-with-fixes / NEEDS-WORK, hallazgos concretos con ancla y correccion, limites. No exigir certificacion de compilacion para una copia por bytes que declara build_ready=false. Si alcance imposible explica mecanismo. No inventes APIs ni lectura de binarios. Esta capsula no contiene geometria vanilla.

PLAN:
# RoadC1B — materializar los dos stages de laboratorio

Estado: BORRADOR_PENDIENTE_DE_REVISION. 29-10-2026.
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


CONFIG HISTORICO PROPIO (se propone literal nuevo, no editar original):
1: class CfgPatches
2: {
3: 	class BalticTrialWorld
4: 	{
5: 		units[]={};
6: 		weapons[]={};
7: 		requiredVersion=0.1;
8: 		requiredAddons[]=
9: 		{
10: 			"DZ_Data",
11: 			"DZ_Surfaces",
12: 			"Baltic_Water_V30", "Baltic_Stream_Pilot"
13: 		};
14: 	};
15: };
16: class CfgWorlds
17: {
18: 	class CAWorld;
19: 	class BalticTrial: CAWorld
20: 	{
21: 		description="Baltic 12km - V30";
22: 		MaxTide=1.5;
23: 		MaxWave=0.1;
24: 		class OutsideTerrain
25: 		{
26: 			satellite="DZ\worlds\chernarusplus\data\outside_sat_co.paa";
27: 			enableTerrainSynth=1;
28: 			class Layers
29: 			{
30: 				class Layer0
31: 				{
32: 					nopx="DZ\surfaces\data\terrain\cp_grass_nopx.paa";
33: 					texture="DZ\surfaces\data\terrain\cp_grass_ca.paa";
34: 				};
35: 			};
36: 		};
37: 		worldName="dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp";
38: 		longitude=30;
39: 		latitude=-59;
40: 		startTime="12:00";
41: 		startDate="29/09/2026";
42: 		centerPosition[]={6144,6144,100};
43: 		clutterGrid=1;
44: 		clutterDist=125;
45: 		noDetailDist=65;
46: 		fullDetailDist=10;
47: 		volFogOffset=0;
48: 		midDetailTexture="DZ\worlds\chernarusplus\data\middle_sat_mco.paa";
49: 		class UsedTerrainMaterials
50: 		{
51: 			material1="DZ\surfaces\data\terrain\cp_gravel.rvmat";
52: 			material2="DZ\surfaces\data\terrain\cp_conifer_common1.rvmat";
53: 			material3="DZ\surfaces\data\terrain\cp_grass.rvmat";
54: 			material4="DZ\surfaces\data\terrain\cp_grass_tall.rvmat";
55: 		};
56: 		class Navmesh
57: 		{
58: 			navmeshName="dayz_baltic_12km_dev\tb\narva_trial\navmesh\baltic_trial.nm";
59: 			filterIsolatedIslandsOnLoad="true";
60: 			visualiseOffset=0;
61: 			class GenParams
62: 			{
63: 				tileWidth=12.5;
64: 				cellSize1=0.25;
65: 				cellSize2=0.1;
66: 				cellSize3=0.1;
67: 				filterIsolatedIslands="true";
68: 				seedPosition[]={6144,0,6144};
69: 				class Agent
70: 				{
71: 					diameter=0.60000002;
72: 					standHeight=1.5;
73: 					crouchHeight=1;
74: 					proneHeight=0.5;
75: 					maxStepHeight=0.44999999;
76: 					maxSlope=60;
77: 				};
78: 				class Links
79: 				{
80: 					class ZedJump387_050
81: 					{
82: 						jumpLength=1.5;
83: 						jumpHeight=0.5;
84: 						minCenterHeight=0.30000001;
85: 						jumpDropdownMin=0.5;
86: 						jumpDropdownMax=-0.5;
87: 						areaType="jump0";
88: 						flags[]=
89: 						{
90: 							"jumpOver"
91: 						};
92: 						color=1727987712;
93: 					};
94: 					class ZedJump388_050
95: 					{
96: 						jumpLength=1.5;
97: 						jumpHeight=0.5;
98: 						minCenterHeight=-0.5;
99: 						jumpDropdownMin=0.5;
100: 						jumpDropdownMax=-0.5;
101: 						areaType="jump0";
102: 						flags[]=
103: 						{
104: 							"jumpOver"
105: 						};
106: 						color=1725781248;
107: 					};
108: 					class ZedJump387_110
109: 					{
110: 						jumpLength=3.9000001;
111: 						jumpHeight=1.1;
112: 						minCenterHeight=0.5;
113: 						jumpDropdownMin=0.5;
114: 						jumpDropdownMax=-0.5;
115: 						areaType="jump0";
116: 						flags[]=
117: 						{
118: 							"jumpOver"
119: 						};
120: 						color=1711308800;
121: 					};
122: 					class ZedJump420_160
123: 					{
124: 						jumpLength=4;
125: 						jumpHeight=1.6;
126: 						minCenterHeight=1.1;
127: 						jumpDropdownMin=0.5;
128: 						jumpDropdownMax=-0.5;
129: 						areaType="jump0";
130: 						flags[]=
131: 						{
132: 							"jumpOver"
133: 						};
134: 						color=1711276287;
135: 					};
136: 					class ZedJump265_210
137: 					{
138: 						jumpLength=2.45;
139: 						jumpHeight=2.5;
140: 						minCenterHeight=1.8;
141: 						jumpDropdownMin=0.5;
142: 						jumpDropdownMax=-0.5;
143: 						areaType="jump0";
144: 						flags[]=
145: 						{
146: 							"climb"
147: 						};
148: 						color=1720975571;
149: 					};
150: 					class Fence50_110deer
151: 					{
152: 						typeId=100;
153: 						jumpLength=8;
154: 						jumpHeight=1.1;
155: 						minCenterHeight=0.5;
156: 						jumpDropdownMin=1;
157: 						jumpDropdownMax=-1;
158: 						areaType="jump2";
159: 						flags[]=
160: 						{
161: 							"jumpOver"
162: 						};
163: 						color=1722460927;
164: 					};
165: 					class Fence110_160deer
166: 					{
167: 						typeId=101;
168: 						jumpLength=8;
169: 						jumpHeight=1.6;
170: 						minCenterHeight=1.1;
171: 						jumpDropdownMin=1;
172: 						jumpDropdownMax=-1;
173: 						areaType="jump3";
174: 						flags[]=
175: 						{
176: 							"jumpOver"
177: 						};
178: 						color=1713700856;
179: 					};
180: 					class Fence50_110hen
181: 					{
182: 						typeId=110;
183: 						jumpLength=4;
184: 						jumpHeight=1.1;
185: 						minCenterHeight=0.5;
186: 						jumpDropdownMin=0.5;
187: 						jumpDropdownMax=-0.5;
188: 						areaType="jump4";
189: 						flags[]=
190: 						{
191: 							"jumpOver"
192: 						};
193: 						color=-22016;
194: 					};
195: 					class Fence110_160hen
196: 					{
197: 						typeId=111;
198: 						jumpLength=4;
199: 						jumpHeight=1.6;
200: 						minCenterHeight=1.1;
201: 						jumpDropdownMin=0.5;
202: 						jumpDropdownMax=-0.5;
203: 						areaType="jump4";
204: 						flags[]=
205: 						{
206: 							"jumpOver"
207: 						};
208: 						color=-22016;
209: 					};
210: 				};
211: 			};
212: 		};
213: 		class Names
214: 		{
215: 		};
216: 		class Sounds
217: 		{
218: 			sounds[]={};
219: 		};
220: 		class Ambient
221: 		{
222: 		};
223: 	};
224: };

HECHOS GUARDADOS: C1A1 4775RVMAT 10052971B;2048PNG metadata140323829B;8PAA metadata40711646B. B4A3 8assets+4leaves, virtual_path y SHA individuales. Core metadata observada este turno:58entradas/41files/9717421B; no reparse observado. No identidades de payload PNG/PAA/core todavia; se fijan en contrato antes del codigo. Dos stages unas450MB previstos, cap1GiB. Referencias OutsideTerrain son outside_sat_co.paa y cp_grass_nopx.paa/cp_grass_ca.paa; midDetail middle_sat_mco.paa; lista exacta se extrae de config historico, no basename. Plan dice dos texturas exteriores de addon mas cuatroRVMAT, las otras PAA pueden estar en8PAA; requerir reconciliacion exacta. P:/DZ puede tener junctions historicos: guardas deben fallar sin asumir la causa, sin tocarP:.
