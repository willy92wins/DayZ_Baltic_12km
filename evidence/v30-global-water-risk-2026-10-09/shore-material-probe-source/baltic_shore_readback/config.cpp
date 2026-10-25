class CfgPatches { class BalticShoreReadback { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMods { class BalticShoreReadback { type="mod"; dependencies[]={"Mission"}; class defs { class missionScriptModule { value=""; files[]={"baltic_shore_readback/scripts/5_Mission"}; }; }; }; };
