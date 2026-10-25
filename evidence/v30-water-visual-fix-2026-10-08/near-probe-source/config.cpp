class CfgPatches { class BalticCameraNearProbe { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DayZ_MCP"}; }; };
class CfgMods { class BalticCameraNearProbe { dir="baltic_camera_near_probe"; name="Baltic camera depth diagnostic"; type="mod"; hideName=1; hidePicture=1; dependencies[]={"Mission"}; class defs { class missionScriptModule { value=""; files[]={"baltic_camera_near_probe/scripts/5_Mission"}; }; }; }; };

