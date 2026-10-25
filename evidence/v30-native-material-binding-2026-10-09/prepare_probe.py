from pathlib import Path
import json, hashlib, shutil
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
old=Path('E:/DayZ-Baltic-Build/v30-native-pond-material-20261009')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
E=W/'evidence/v30-native-pond-material-2026-10-09'
shutil.copyfile(old/'profile-changes.json',E/'profile-changes.json')
p=E/'README.md';t=p.read_text(encoding='utf-8');t += '\nEl hash completo del perfil cambia solo por uiTopLeftX (0.12500001 a 0.11997001) y uiBottomRightX (0.875 a 0.88002998), al ampliar la ventana antes de la referencia. No cambian los cuatro ajustes de render. Se conserva profile-changes.json; no se revierte el estado de ventana del usuario.\n';p.write_text(t,encoding='utf-8')
p=E/'preservation.json';manifest=json.loads(p.read_text());manifest['README.md']=sha(E/'README.md');manifest['profile-changes.json']=sha(E/'profile-changes.json');p.write_text(json.dumps(manifest,indent=2)+'\n')
p=W/'HANDOFF.md';t=p.read_text(encoding='utf-8');lines=t.splitlines()
replacements={
'runtime_lock:':'runtime_lock: EV33 cerrado orderly, parametros restaurados; lease liberado, banco libre. EV34 prepara control de consumo de material; aun sin run. El perfil EV33 cambia solo dos limites horizontales de UI al ampliar ventana antes de medir, render intacto.',
'next:':'next: EV34: lectura estatica identifica lookup Graphics/Materials/water/<basename-RVMAT>.emat, luego ruta local y reserva pond_clear. Control reversible de color en los dos recursos para verificar consumidor real. EV33 WetFloor no supera variacion temporal; sin arreglo promovido. Continuar contornos y resto de superficie.',
'handoff:':'handoff: EV31 bruma por distancia reversible; EV32 detalle no resuelve halos; EV33 WetFloor sin supresion estable. EV34 nuevo discriminador por mecanismo de enlace leido. Base completa aun no aceptada.',
'git:':'git: Rama claude/codex-handoff-review-74f290; HEAD3d8bca9 EV31/32; evidencia EV33 preparada para checkpoint, sin push ni subagentes.'}
for i,line in enumerate(lines):
 for prefix,value in replacements.items():
  if line.startswith(prefix):lines[i]=value
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
(B/'plan.md').write_text('''# EV34: comprobar consumidor nativo de CalmWater

Alcance: solo diagnostico cliente reversible; mapa EV28 y agua compilada intactos. No cambia geometria, agua fisica, preferencias ni vanilla. Un run, secuencia original / marcador moss / reset / marcador clear / reset. Maximo dos recursos, un control por recurso; no barrido de parametros. Watchdog90s en cada control. Si no hay marcador inequivoco, INCONCLUSO y siguiente via exige fixture local unico, sin atribuir el fallo a WetFloor.

Mecanismo leido: DayZDiag_x64.exe SHA34f6377be4fd065d104e67263e0c96ac2cb2e348119a4838eba08d2e61b7a69a, binding-function.json. En 0x140b22b16..2b26 shader111(0x6f, registro CalmWater) u8, sujeto a flags r12b&7==0. 0x140b22b4a..2c89 construye Graphics/Materials/water/<basename sin extension>.emat. Si null, 0x140b22cc4..2e49 cambia extension de ruta original por .emat. Si null usa recurso por 0x140b2b3b0, cuyo inicializador referencia pond_clear.emat. Registro/cache final0x140b1dfa0. Los nombres de campos y el handle compartido con GetMaterial siguen siendo inferencia hasta el control.

Referencias de API: P:/scripts/1_core/proto/proto.c267-294 SetParam(string,void)->bool, ResetParam y GetParamIndex; no hay getter. P:/scripts/3_game/ppeffects.c430-443 muestra float color[4] y SetParam. RVMAT instalado pond_moss_1 usa CalmWater; EMAT define Color, ReflectionColor, WaterExtinction y NormalPower. Se alteran conjuntamente solo como marca diagnóstica, no como arreglo.

PASS control: marcador cromatico espacialmente coherente sobre agua o residual, ausente en ambas referencias, con camara/viewport/hora fijos, set_return true y parametros indices validos. Baseline/reset y negativo de parametro inexistente. FAIL control: el parametro falla. INCONCLUSO: hay handle/retorno pero no cambio visible inequivoco. No se acepta la base por esta prueba. Mantener tambien log de viento/mar, hashes PBO y cierre orderly/release/status.
''',encoding='utf-8')
src=B/'baltic_material_binding_probe_v1';(src/'scripts/5_Mission').mkdir(parents=True,exist_ok=False)
(src/'config.cpp').write_text('class CfgPatches { class baltic_material_binding_probe_v1 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };\nclass CfgMods { class BalticMaterialBindingProbeV1 { type="mod"; dependencies[]={"Mission"}; class defs { class missionScriptModule { value=""; files[]={"baltic_material_binding_probe_v1/scripts/5_Mission"}; }; }; }; };\n')
(src/'scripts/5_Mission/BalticMaterialBindingProbe.c').write_text('''modded class MissionGameplay
{
 protected bool m_BalticBindingStarted;
 protected bool m_BalticBindingRefused;
 protected int m_BalticBindingPhase;
 protected int m_BalticBindingNext;
 protected int m_BalticBindingDeadline;
 protected Material m_BalticMoss;
 protected Material m_BalticClear;
 void BalticBindingLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_material_binding_probe_v1.log", FileMode.APPEND);
  if (!file) return;
  FPrintln(file, message);
  CloseFile(file);
 }
 bool BalticBindingCheck(Material mat, string name)
 {
  if (!mat) return false;
  int color = mat.GetParamIndex("Color");
  int reflection = mat.GetParamIndex("ReflectionColor");
  int extinction = mat.GetParamIndex("WaterExtinction");
  int normal = mat.GetParamIndex("NormalPower");
  int absent = mat.GetParamIndex("__baltic_absent_param__");
  BalticBindingLog("INDEX;" + name + ";" + color + ";" + reflection + ";" + extinction + ";" + normal + ";missing;" + absent);
  return color >= 0 && reflection >= 0 && extinction >= 0 && normal >= 0 && absent == -1;
 }
 void BalticBindingRestore(int phase, int now, string reason)
 {
  Material mat = m_BalticMoss;
  if (m_BalticBindingPhase == 3) mat = m_BalticClear;
  mat.ResetParam("Color");
  mat.ResetParam("ReflectionColor");
  mat.ResetParam("WaterExtinction");
  mat.ResetParam("NormalPower");
  m_BalticBindingPhase = phase;
  BalticBindingLog("PHASE;" + phase + ";" + now + ";reset_default;" + reason);
 }
 void BalticBindingMark(int phase, int now)
 {
  Material mat = m_BalticMoss;
  float color[4];
  color[0] = 1; color[1] = 0; color[2] = 1; color[3] = 1;
  if (phase == 3)
  {
   mat = m_BalticClear;
   color[0] = 0; color[1] = 1;
  }
  bool a = mat.SetParam("Color", color);
  bool b = mat.SetParam("ReflectionColor", color);
  bool c = mat.SetParam("WaterExtinction", 100.0);
  bool d = mat.SetParam("NormalPower", 0.0);
  m_BalticBindingPhase = phase;
  m_BalticBindingDeadline = now + 90000;
  BalticBindingLog("PHASE;" + phase + ";" + now + ";marker;returns;" + a + ";" + b + ";" + c + ";" + d);
  if (!a || !b || !c || !d) BalticBindingRestore(9, now, "set_failed");
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || !GetGame().GetPlayer() || m_BalticBindingRefused) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  int now = GetGame().GetTime();
  if (now < m_BalticBindingNext) return;
  m_BalticBindingNext = now + 1000;
  if (!m_BalticBindingStarted)
  {
   FileHandle first = OpenFile("$profile:baltic_material_binding_probe_v1.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_MATERIAL_BINDING_PROBE_V1;EV34");
   CloseFile(first);
   m_BalticMoss = GetGame().GetWorld().GetMaterial("graphics/materials/water/pond_moss_1");
   m_BalticClear = GetGame().GetWorld().GetMaterial("graphics/materials/water/pond_clear");
   if (!BalticBindingCheck(m_BalticMoss, "moss") || !BalticBindingCheck(m_BalticClear, "clear"))
   {
    BalticBindingLog("REFUSED;parameter_contract");
    m_BalticBindingRefused = true;
    return;
   }
   m_BalticBindingStarted = true;
   BalticBindingLog("PHASE;0;" + now + ";untouched");
  }
  if ((m_BalticBindingPhase == 1 || m_BalticBindingPhase == 3) && now >= m_BalticBindingDeadline) BalticBindingRestore(9, now, "watchdog");
  FileHandle command = OpenFile("$profile:baltic_material_binding_probe_v1.phase", FileMode.READ);
  if (command)
  {
   string marker;
   string requested;
   FGets(command, marker);
   FGets(command, requested);
   CloseFile(command);
   marker = marker.Trim(); requested = requested.Trim();
   if (marker == "EV34-20261009")
   {
    if ((requested == "1" && m_BalticBindingPhase == 0) || (requested == "3" && m_BalticBindingPhase == 2)) BalticBindingMark(requested.ToInt(), now);
    if (requested == "2" && m_BalticBindingPhase == 1) BalticBindingRestore(2, now, "requested");
    if (requested == "4" && m_BalticBindingPhase == 3) BalticBindingRestore(4, now, "requested");
   }
  }
  vector camera = GetGame().GetCurrentCameraPosition();
  vector direction = GetGame().GetCurrentCameraDirection();
  BalticBindingLog("SAMPLE;" + m_BalticBindingPhase + ";" + now + ";" + GetGame().SurfaceGetSeaLevel() + ";" + camera.ToString() + ";" + direction.ToString());
 }
};
''')
t=(old/'build_probe.py').read_text().replace('baltic_pond_material_probe_v1','baltic_material_binding_probe_v1').replace('balticpondmaterialprobe.c','balticmaterialbindingprobe.c').replace('BalticPondMaterialProbe.c','BalticMaterialBindingProbe.c').replace('@BalticPondMaterialProbeV1','@BalticMaterialBindingProbeV1').replace('BUILT_ISOLATED_CLIENT_POND_MATERIAL_PROBE','BUILT_ISOLATED_MATERIAL_BINDING_PROBE')
(B/'build_probe.py').write_text(t)
t=(old/'set_phase.py').read_text().replace('baltic_pond_material_probe_v1','baltic_material_binding_probe_v1').replace('EV33-20261009','EV34-20261009');(B/'set_phase.py').write_text(t)
print(json.dumps({'prepared':str(B),'ev33_profile_keys':2,'bank':'free'}))
