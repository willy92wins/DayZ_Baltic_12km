class CfgPatches { class BalticOceanHeightProbeV1 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMods { class BalticOceanHeightProbeV1 { type="mod"; dependencies[]={"Mission"}; class defs { class missionScriptModule { value=""; files[]={"baltic_ocean_height_probe_v1/scripts/5_Mission"}; }; }; }; };
class CfgWorlds { class CAWorld; class BalticTrial: CAWorld { MaxTide=0; }; };
