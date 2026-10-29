Revisor Muse Wonder1.0 nativo, SOLO esta capsula y sin herramientas/escrituras. Codex planner/integrator, executor local explicitamente asignado si apruebas. Revisar plan de COMPILE_PROBE_ONLY, no acceptance de mapa ni decoder. Critica APIs verificadas vs literales, presupuesto, proceso/hijos, controlgate, portabilidad/logs y mutacion de inputs. Max1600palabras180s. Final SOUND/SOUND-with-fixes/NEEDS-WORK con hallazgos concretos y correcciones. No exigir lectorOPRW semantico para mera captura que no acepta compilado; si riesgo de circularidad, explicarlo. No repetir council. No ejecutar nada.
# RoadC1C — sonda compilada del laboratorio

Estado BORRADOR_PENDIENTE_DE_REVISION. P5/P6/P8/P11, preparación del piloto de
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
7. Observador separado60s/256MiB verifica recibos/ventanas/artefactos por relectura,
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

ANCHOR E:\DayZ-Baltic-Build\shape-repair-20261025\road-c1c-invocation-anchors-20261029\help-literal-window.json SHA 84ccfde8a5afe45e65adaed3979f77970c42e9a75b852ea8a3b39ec708c050a8
[
  {
    "offset": 82801,
    "text": "rerequirements_Body_AfterList"
  },
  {
    "offset": 82861,
    "text": "args"
  },
  {
    "offset": 82871,
    "text": "[arg{0}]={1}"
  },
  {
    "offset": 82897,
    "text": "project:"
  },
  {
    "offset": 82915,
    "text": "prefix:"
  },
  {
    "offset": 82931,
    "text": "pboversion:"
  },
  {
    "offset": 82955,
    "text": "temp:"
  },
  {
    "offset": 82967,
    "text": "sign:|signature:"
  },
  {
    "offset": 83001,
    "text": "clear:"
  },
  {
    "offset": 83015,
    "text": "help:"
  },
  {
    "offset": 83027,
    "text": "packonly:"
  },
  {
    "offset": 83047,
    "text": "dependency:"
  },
  {
    "offset": 83071,
    "text": "include:"
  },
  {
    "offset": 83089,
    "text": "exclude:"
  },
  {
    "offset": 83107,
    "text": "binarize:"
  },
  {
    "offset": 83127,
    "text": "cfgConvert:"
  },
  {
    "offset": 83151,
    "text": "fileBank:"
  },
  {
    "offset": 83171,
    "text": "dsSignFile:"
  },
  {
    "offset": 83195,
    "text": "binarizeAllTextures:"
  },
  {
    "offset": 83237,
    "text": "binarizeNoLogs"
  },
  {
    "offset": 83267,
    "text": "binarizeFullLogs"
  },
  {
    "offset": 83301,
    "text": "toolsDirectory:"
  },
  {
    "offset": 83333,
    "text": "Destination dir is mandatory."
  },
  {
    "offset": 83393,
    "text": "destination_path"
  },
  {
    "offset": 83427,
    "text": "source_path"
  },
  {
    "offset": 83452,
    "text": "Invalid number of arguments. There can be only one source_path and destination_path at the same time"
  },
  {
    "offset": 83654,
    "text": "Project dir '{0}' is not sub-path of source directory '{1}'"
  },
  {
    "offset": 83774,
    "text": "project"
  },
  {
    "offset": 83790,
    "text": "path is empty"
  },
  {
    "offset": 83818,
    "text": "Specified path does not exists. [path]={0}"
  },
  {
    "offset": 83904,
    "text": "Specified path is not absolute. [path]={0}"
  },
  {
    "offset": 83990,
    "text": "Relative path does not exists. [path]={0}"
  },
  {
    "offset": 84074,
    "text": "BuilderCommandLine"
  },
  {
    "offset": 84112,
    "text": "AddonBuilder"
  },
  {
    "offset": 84139,
    "text": "DayZ Tools path is unknown, Steam must be running or specify -toolsDirectory."
  },
  {
    "offset": 84295,
    "text": "Error during initialization."
  },
  {
    "offset": 84353,
    "text": "DayZ Tools are not installed."
  },
  {
    "offset": 84413,
    "text": "Error during steam initialization."
  },
  {
    "offset": 84483,
    "text": "Error during Steam initialization"
  },
  {
    "offset": 84551,
    "text": "Missing argument. [ArgumentName]={0}, {1}"
  },
  {
    "offset": 84635,
    "text": "Use -help to see all parameters and example"
  },
  {
    "offset": 84723,
    "text": "Invalid value for argument specified. [ArgumentName]={0}, {1}"
  },
  {
    "offset": 84848,
    "text": "=========================================================================="
  },
  {
    "offset": 84998,
    "text": "WELCOME TO ADDON BUILDER"
  },
  {
    "offset": 85048,
    "text": "Version: {0}"
  },
  {
    "offset": 85074,
    "text": "[%date] [%-5level]: %message%newline"
  },
  {
    "offset": 85148,
    "text": "DayZ Tools path forced by from command line: '{0}'."
  },
  {
    "offset": 85252,
    "text": "DayZ Tools path not set. Reverting to default path: '{0}'."
  },
  {
    "offset": 85370,
    "text": "DayZ Tools path retrived from the last use with steam '{0}'."
  },
  {
    "offset": 85497,
    "text": "Addon Builder is a packing tool created by Bohemia Interactive. The purpose of "
  },
  {
    "offset": 85659,
    "text": "this tool is to convert all data into formats readable by the Real Virtuality "
  },
  {
    "offset": 85819,
    "text": "engine and pack them into a single archive. "
  },
  {
    "offset": 85915,
    "text": "SYNTAX"
  },
  {
    "offset": 85931,
    "text": "------"
  },
  {
    "offset": 85947,
    "text": "GUI mode:"
  },
  {
    "offset": 85969,
    "text": "AddonBuilder.exe"
  },
  {
    "offset": 86009,
    "text": "CLI mode:"
  },
  {
    "offset": 86031,
    "text": "AddonBuilder.exe source_path destination_path [-help] [-packonly] [-clear] "
  },
  {
    "offset": 86185,
    "text": "                 [-temp=<temporary folder path>] [-prefix=<addon prefix>]  "
  },
  {
    "offset": 86339,
    "text": "                 [-project=<project path>] [-sign=<private key file>] "
  },
  {
    "offset": 86483,
    "text": "                 [-include=<file name>] "
  },
  {
    "offset": 86567,
    "text": "                 [-pboversion=<version>]"
  },
  {
    "offset": 86651,
    "text": "                 [-binarize=<path to binarize.exe>] "
  },
  {
    "offset": 86759,
    "text": "                 [-cfgconvert=<path to cfgConvert.exe>] "
  },
  {
    "offset": 86875,
    "text": "                 [-filebank=<path to filebank.exe>] "
  },
  {
    "offset": 86983,
    "text": "                 [-dssignfile=<path to dssignfile.exe>]"
  },
  {
    "offset": 87097,
    "text": "                 [-toolsDirectory=<path to DayZ Tools directory>]"
  },
  {
    "offset": 87231,
    "text": "                 [-binarizeAllTextures]"
  },
  {
    "offset": 87313,
    "text": "                 [-binarizeFullLogs]"
  },
  {
    "offset": 87389,
    "text": "                 [-binarizeNoLogs]"
  },
  {
    "offset": 87465,
    "text": "  source_path          Path to source folder to make PBO addon."
  },
  {
    "offset": 87595,
    "text": "                       (Mandatory parameter.)"
  },
  {
    "offset": 87689,
    "text": "  destination_path     Path to folder to save the final PBO. "
  },
  {
    "offset": 87815,
    "text": "                       (Mandatory parameter.)"
  },
  {
    "offset": 87909,
    "text": "  -help                Shows this help."
  },
  {
    "offset": 87991,
    "text": "  -packonly            Only stores the folder to a PBO. Does NOT binarize "
  },
  {
    "offset": 88143,
    "text": "                       files. (Binarization is default behaviour.)"
  },
  {
    "offset": 88279,
    "text": "  -clear               Before binarizing, the content of subfolder for the "
  },
  {
    "offset": 88433,
    "text": "                       current project is deleted."
  },
  {
    "offset": 88537,
    "text": "  -temp                Path for the folder which stores binarized files, "
  },
  {
    "offset": 88687,
    "text": "                       default destination is temp in Windows, if no value is "
  },
  {
    "offset": 88847,
    "text": "                       present then the last folder is used, if you use the "
  },
  {
    "offset": 89003,
    "text": "                       same folder, the next time you binarize the same addon "
  },
  {
    "offset": 89163,
    "text": "                       it will take less time."
  },
  {
    "offset": 89259,
    "text": "  -prefix              Relative path to files used in addon, if not present "
  },
  {
    "offset": 89415,
    "text": "                       then this value is calculated automatically."
  },
  {
    "offset": 89553,
    "text": "  -project             Path to folder where project starts from, if you are "
  },
  {
    "offset": 89709,
    "text": "                       packing only the part of the project."
  },
  {
    "offset": 89833,
    "text": "  -sign                Private BI key (*.BIPRIVATEKEY) file that will be used "
  },
  {
    "offset": 89993,
    "text": "                       to sign the addon. Addons created with a signature can "
  },
  {
    "offset": 90153,
    "text": "                       be added to secure servers."
  },
  {
    "offset": 90257,
    "text": "  -include             Directly copies matched files to PBO. Absolute path to "
  },
  {
    "offset": 90417,
    "text": "                       file with wildcard patterns. separator is ';' and ','."
  },
  {
    "offset": 90575,
    "text": "  -exclude             Absolute or relative file path. Contains patterns of "
  },
  {
    "offset": 90731,
    "text": "                       files which are excluded from final pbo. Look for "
  },
  {
    "offset": 90881,
    "text": "                       'exclude.lst' file in DayZTools install dir for "
  },
  {
    "offset": 91027,
    "text": "                       an example of exclude file content."
  },
  {
    "offset": 91147,
    "text": "  -binarize            Path to Binarize tool. Default Binarize tool is used "
  },
  {
    "offset": 91303,
    "text": "                       if not specified."
  },
  {
    "offset": 91387,
    "text": "  -cfgconvert          Path to cfg convert tool. default is used if "
  },
  {
    "offset": 91527,
    "text": "                       not specified."
  },
  {
    "offset": 91605,
    "text": "  -filebank            Path to filebank tool. Default tool from DayZ Tools "
  },
  {
    "offset": 91759,
    "text": "                       is used if not specified."
  },
  {
    "offset": 91859,
    "text": "  -dssignfile          Path to DSSignFile tool. Default tool from DayZ Tools "
  },
  {
    "offset": 92017,
    "text": "                       is used if not specified."
  },
  {
    "offset": 92117,
    "text": "  -toolsDirectory      Specifies the path to DayZ Tools directory with other "
  },
  {
    "offset": 92275,
    "text": "                       tools (Binarize, CfgConvert, Filebank, ...). By default"
  },
  {
    "offset": 92435,
    "text": "                       is the directory retrieved from Steam client."
  },
  {
    "offset": 92575,
    "text": "  -binarizeAllTextures Binarize all .TGA, .PNG textures even if they are not "
  },
  {
    "offset": 92733,
    "text": "                       referenced by any model or included in "
  },
  {
    "offset": 92861,
    "text": "                       any textures.lst file."
  },
  {
    "offset": 92955,
    "text": "  -binarizeFullLogs    Enables extended logging."
  },
  {
    "offset": 93055,
    "text": "  -binarizeNoLogs      Disables extended logging."
  },
  {
    "offset": 93161,
    "text": "  -pboversion          PBO version for FileBank (-property version=<version>)"
  },
  {
    "offset": 93323,
    "text": "EXAMPLE"
  },
  {
    "offset": 93341,
    "text": "-------"
  },
  {
    "offset": 93359,
    "text": "  C:\\addon D:\\addon_build -clear -sign=C:\\keys\\bistudio.biprivatekey -project=C: -include=C:\\include.txt -exclude=C:\\exclude.lst -binarize=C:\\MyBinarize.exe -binarizeAllTextures"
  },
  {
    "offset": 93725,
    "text": "ADDITIONAL HELP"
  },
  {
    "offset": 93759,
    "text": "---------------"
  },
  {
    "offset": 93793,
    "text": "  https://community.bistudio.com/wiki/Addon_Builder"
  },
  {
    "offset": 93901,
    "text": "DayZ Addon Builder"
  },
  {
    "offset": 93939,
    "text": "bis_DayZAddonbBuilder"
  },
  {
    "offset": 93983,
    "text": "WELCOME TO DAYZ ADDON BUILDER"
  },
  {
    "offset": 94049,
    "text": "PrerequirementsTroubleshootingUrl"
  },
  {
    "offset": 94117,
    "text": "/AddonBuilder;component/app.xaml"
  },
  {
    "offset": 94191,
    "text": "CfgConvert"
  },
  {
    "offset": 94213,
    "text": "DsSignFile"
  },
  {
    "offset": 94235,
    "text": "FileBank"
  },
  {
    "offset": 94253,
    "text": ".pbo"
  },
  {
    "offset": 94263,
    "text": "Builder starting..."
  },
  {
    "offset": 94303,
    "text": "Build failed"
  },
  {
    "offset": 94329,
    "text": "Build Successful"
  },
  {
    "offset": 94363,
    "text": "Cancellation reque"
  }
]
ANCHOR C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe.config SHA e614fcb04d8e3429fab70466261f36383de3bfcd230a058bc196ac0727482bbe
<?xml version="1.0"?>
<configuration>
  <configSections>
    <sectionGroup name="userSettings" type="System.Configuration.UserSettingsGroup, System, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089">
      <section name="AddonBuilder.Properties.Settings" type="System.Configuration.ClientSettingsSection, System, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089" allowExeDefinition="MachineToLocalUser" requirePermission="false" />
    </sectionGroup>
    <section name="steamHelperSettings" type="AddonBuilder.SteamHelperConfigurationSection, AddonBuilder" />
    <section name="addonBuilderSettings" type="AddonBuilder.AddonBuilderConfigurationSection, AddonBuilder" />
  </configSections>
  <startup>
    <supportedRuntime version="v4.0" sku=".NETFramework,Version=v4.5" />
  </startup>
  <appSettings>
    <add key="log4net.Config.Watch" value="True" />
    <add key="log4net.Config" value="logger.xml" />
    <add key="ClientSettingsProvider.ServiceUri" value="" />
    <add key="miniDumpDirName" value="DayZ AddonBuilder"/>
    <add key="PrerequirementsTroubleshootingUrl" value="http://dayz.com/launcher/troubleshooting"/>
  </appSettings>
  <addonBuilderSettings DefaultBinarizeExe="\bin\Binarize\binarize.exe" DefaultCfgConvertExe="\bin\CfgConvert\CfgConvert.exe" DefaultFileBankExe="\bin\PboUtils\FileBank.exe" DefaultDssignFileExe="\bin\DsUtils\DSSignFile.exe" />
  <userSettings>
    <AddonBuilder.Properties.Settings>
      <setting name="Binarize" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="ClearTemp" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="SignatureFile" serializeAs="String">
        <value />
      </setting>
      <setting name="Project" serializeAs="String">
        <value />
      </setting>
      <setting name="BinarizeExePath" serializeAs="String">
        <value />
      </setting>
      <setting name="CfgConvertExePath" serializeAs="String">
        <value />
      </setting>
      <setting name="FilebankExePath" serializeAs="String">
        <value />
      </setting>
      <setting name="DssignfileExePath" serializeAs="String">
        <value />
      </setting>
      <setting name="WhiteList" serializeAs="String">
        <value>*.emat;*.edds;*.ptc;*.c;*.imageset;*.layout;*.ogg</value>
      </setting>
      <setting name="TempDir" serializeAs="String">
        <value />
      </setting>
      <setting name="AddonPrefix" serializeAs="String">
        <value />
      </setting>
      <setting name="SourceDir" serializeAs="String">
        <value />
      </setting>
      <setting name="DestDir" serializeAs="String">
        <value />
      </setting>
      <setting name="UseCfgConvertDefault" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="UseBinarizeDefault" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="UseFileBankDefault" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="UseDsSignDefault" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="CreateSignature" serializeAs="String">
        <value>False</value>
      </setting>
      <setting name="IsUpgradeNeeded" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="Author" serializeAs="String">
        <value />
      </setting>
      <setting name="AuthorDefault" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="DependencyValue" serializeAs="String">
        <value />
      </setting>
      <setting name="ExcludeFilePath" serializeAs="String">
        <value />
      </setting>
      <setting name="UseDefaultExludeFilePath" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="BinarizeAllTextures" serializeAs="String">
        <value>False</value>
      </setting>
      <setting name="NoLogs" serializeAs="String">
        <value>True</value>
      </setting>
      <setting name="DayZToolsPath" serializeAs="String">
        <value />
      </setting>
      <setting name="PBOVersion" serializeAs="String">
        <value />
      </setting>
    </AddonBuilder.Properties.Settings>
  </userSettings>
  <system.web>
    <membership defaultProvider="ClientAuthenticationMembershipProvider">
      <providers>
        <add name="ClientAuthenticationMembershipProvider" type="System.Web.ClientServices.Providers.ClientFormsAuthenticationMembershipProvider, System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35" serviceUri="" />
      </providers>
    </membership>
    <roleManager defaultProvider="ClientRoleProvider" enabled="true">
      <providers>
        <add name="ClientRoleProvider" type="System.Web.ClientServices.Providers.ClientRoleProvider, System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35" serviceUri="" cacheTimeout="86400" />
      </providers>
    </roleManager>
  </system.web>
</configuration>
ANCHOR C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\logger.xml SHA 1d24d7d4afb5249efbef3435195bbea4d1a2d6317292637c7f834b69f8470005
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
ANCHOR C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\terrain\compile_visual_pilot_ev112.ps1 SHA 86d156594d10d77d8c3a961ac999e0356d29dc3d3f0727efbd7fed974c6c39d2
param([Parameter(Mandatory=$true)][string]$Stage,[Parameter(Mandatory=$true)][string]$Pilot)
$ErrorActionPreference='Stop'
$stagePath=(Resolve-Path -LiteralPath $Stage).Path
$pilotPath=(Resolve-Path -LiteralPath $Pilot).Path
$project=Join-Path $stagePath 'root'
$source=Join-Path $project 'dayz_baltic_12km_dev\tb\narva_trial'
$out=Join-Path $stagePath 'out'
$temp=Join-Path $stagePath 'temp'
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$water='E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev112-build-20261018\water-prepared-fp49ee\temp\baltic_water_v30'
$pilotModels=Join-Path $pilotPath 'temp\baltic_stream_pilot'
$include='C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\packages\baltic-road-v29\tools\include.lst'
foreach($required in @($source,$builder,$water,$pilotModels,$include,'P:\DZ','P:\bin','P:\core')) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing dependency: $required"}
}
if((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $temp)){throw 'Fresh build directories required'}
New-Item -ItemType Directory -Path $out | Out-Null
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $project $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $project 'baltic_water_v30') -Target $water | Out-Null
New-Item -ItemType Junction -Path (Join-Path $project 'baltic_stream_pilot') -Target $pilotModels | Out-Null
$log=Join-Path $stagePath 'addonbuilder.log'
$ErrorActionPreference='Continue'
& $builder $source $out '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$project" "-temp=$temp" '-binarizeFullLogs' "-include=$include" > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
Write-Output "World compiled for readback: $out"

Notas actuales: el helper historico NO se relanza. LiteralesPE permiten -help,-toolsDirectory y rutas4exe pero no prueban rama/helpantesbuild. Guardar una ayuda sin fuentes es una observacion prevista, no asegurar exito. -binpath en plantillaBinarize tiene placeholder no resuelto: registrar argv hijo antes de atribuir lectura del bin/config copiado. Se puede fijar -exclude vacio propio para evitar ajustes user previos; no se asume el significado de variables internas. Ningun preflight/ayuda/build nuevo ha corrido. No suite/gate de mapa.
