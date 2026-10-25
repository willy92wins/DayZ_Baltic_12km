class CfgPatches { class baltic_projection_probe_v1 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMods { class BalticProjectionProbeV1 { type="mod"; dependencies[]={"Mission"}; class defs { class missionScriptModule { value=""; files[]={"baltic_projection_probe_v1/scripts/5_Mission"}; }; }; }; };
