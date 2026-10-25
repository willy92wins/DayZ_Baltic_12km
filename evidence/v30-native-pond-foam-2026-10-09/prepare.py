from pathlib import Path
import shutil
B=Path(__file__).parent;old=Path('E:/DayZ-Baltic-Build/v30-native-material-binding-20261009')
src=B/'baltic_pond_foam_probe_v1';(src/'scripts/5_Mission').mkdir(parents=True,exist_ok=False)
t=(old/'baltic_material_binding_probe_v1/scripts/5_Mission/BalticMaterialBindingProbe.c').read_text().replace('BalticBinding','BalticFoam').replace('m_BalticBinding','m_BalticFoam').replace('baltic_material_binding_probe_v1','baltic_pond_foam_probe_v1').replace('BALTIC_MATERIAL_BINDING_PROBE_V1','BALTIC_POND_FOAM_PROBE_V1').replace('EV34','EV35')
t=t.replace('"Color"','"FoamColor"').replace('"ReflectionColor"','"FoamPower"')
a=t.index(' void BalticFoamMark(');b=t.index(' override void OnUpdate',a)
t=t[:a]+''' void BalticFoamMark(int phase, int now)
 {
  m_BalticMoss = GetGame().GetWorld().GetMaterial("graphics/materials/water/pond_moss_1");
  m_BalticClear = m_BalticMoss;
  Material mat = m_BalticMoss;
  m_BalticFoamPhase = phase;
  m_BalticFoamDeadline = now + 90000;
  if (!BalticFoamCheck(mat, "moss"))
  {
   BalticFoamLog("CONTROL_REFUSED;" + phase + ";" + now + ";parameter_contract");
   return;
  }
  bool applied;
  string property;
  if (phase == 1)
  {
   float color[4];
   color[0] = 1; color[1] = 0; color[2] = 1; color[3] = 1;
   applied = mat.SetParam("FoamColor", color);
   property = "FoamColor_magenta";
  }
  if (phase == 3)
  {
   applied = mat.SetParam("FoamPower", 0.0);
   property = "FoamPower_zero";
  }
  BalticFoamLog("PHASE;" + phase + ";" + now + ";" + property + ";set_return=" + applied);
  if (!applied) BalticFoamRestore(9, now, "set_failed");
 }
'''+t[b:]
# Only reset properties this diagnostic can change.
t=t.replace('   mat.ResetParam("WaterExtinction");\n','').replace('   mat.ResetParam("NormalPower");\n','')
(src/'scripts/5_Mission/BalticPondFoamProbe.c').write_text(t)
t=(old/'baltic_material_binding_probe_v1/config.cpp').read_text().replace('baltic_material_binding_probe_v1','baltic_pond_foam_probe_v1').replace('BalticMaterialBindingProbeV1','BalticPondFoamProbeV1');(src/'config.cpp').write_text(t)
t=(old/'build_probe.py').read_text().replace('baltic_material_binding_probe_v1','baltic_pond_foam_probe_v1').replace('balticmaterialbindingprobe.c','balticpondfoamprobe.c').replace('BalticMaterialBindingProbe.c','BalticPondFoamProbe.c').replace('@BalticMaterialBindingProbeV2','@BalticPondFoamProbeV1').replace("out=B/'packed-v2'","out=B/'packed'");(B/'build_probe.py').write_text(t)
t=(old/'set_phase.py').read_text().replace('baltic_material_binding_probe_v1','baltic_pond_foam_probe_v1').replace('EV34','EV35');(B/'set_phase.py').write_text(t)
(B/'plan.md').write_text('''# EV35 — espuma del consumidor confirmado

Una secuencia intacto / FoamColor magenta / reset / FoamPower0 / reset. Mismo punto residual, hora y viento de EV34. Material pond_moss_1 confirmado por EV34, propiedades leidas en P:/Graphics/materials/water/pond_moss_1.emat. Solo dos propiedades visuales; nada en produccion ni preferencias. Se resuelve el handle al pedir el control, no al aparecer el jugador.

Presupuesto: un run, un control cromatico y una supresion; watchdog90s. No mas parametros en este bloque. PASS del arreglo requiere suprimir el residual en la serie con espuma0 y recuperarlo al restaurar, por encima de variacion temporal, sin desplazar agua/terreno. Si solo cambia espuma legitima y persiste halo, no es arreglo. La marca magenta constituye control positivo de consumo si aparece y desaparece; no inferirlo de SetParamtrue. Fuentes de API: proto.c267-294, ppeffects.c430-443, ya leidasEV34. Mantener hashes, fases, muestras, cierre orderly y estado libre.
''',encoding='utf-8')
print(src)
