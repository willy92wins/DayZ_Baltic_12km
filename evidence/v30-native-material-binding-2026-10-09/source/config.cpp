class CfgPatches { class baltic_material_binding_probe_v1 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMods { class BalticMaterialBindingProbeV1 { type="mod"; dependencies[]={"Mission"}; class defs { class missionScriptModule { value=""; files[]={"baltic_material_binding_probe_v1/scripts/5_Mission"}; }; }; }; };
