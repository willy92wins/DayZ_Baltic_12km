class CfgPatches
{
 class BalticWaterClientProbe { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data"}; };
};
class CfgMods
{
 class BalticWaterClientProbe
 {
  dir="baltic_water_client_probe"; name="Baltic water client observer"; type="mod";
  hideName=1; hidePicture=1; dependencies[]={"Mission"};
  class defs { class missionScriptModule { value=""; files[]={"baltic_water_client_probe/scripts/5_Mission"}; }; };
 };
};

