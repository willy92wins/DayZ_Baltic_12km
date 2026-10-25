class CfgPatches { class BalticShoreMarker { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMaterials
{
 class Terrain;
 class BalticShoreMagenta: Terrain
 {
  ambient[]={1,0,1,1}; diffuse[]={1,0,1,1}; forcedDiffuse[]={1,0,1,1}; emmisive[]={1,0,1,1}; specular[]={0,0,0,0};
 };
 class BalticShoreWetGreen: Terrain
 {
  ambient[]={0,1,0,1}; diffuse[]={0,1,0,1}; forcedDiffuse[]={0,1,0,1}; emmisive[]={0,1,0,1}; specular[]={0,0,0,0};
 };
};
class CfgWorlds { class CAWorld; class BalticTrial: CAWorld { shoreMaterial="#BalticShoreMagenta"; shoreWetMaterial="#BalticShoreWetGreen"; }; };
