class CfgPatches
{
	class BalticRoadPivotLab
	{
		units[]={};
		weapons[]={};
		requiredVersion=0.1;
		requiredAddons[]=
		{
			"DZ_Data",
			"DZ_Surfaces"
		};
	};
};
class CfgWorlds
{
	class CAWorld;
	class BalticRoadPivotLab: CAWorld
	{
		description="Baltic 12km - V30";
		MaxTide=1.5;
		MaxWave=0.1;
		class OutsideTerrain
		{
			satellite="DZ\worlds\chernarusplus\data\outside_sat_co.paa";
			enableTerrainSynth=1;
			class Layers
			{
				class Layer0
				{
					nopx="DZ\surfaces\data\terrain\cp_grass_nopx.paa";
					texture="DZ\surfaces\data\terrain\cp_grass_ca.paa";
				};
			};
		};
		worldName="dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp";
		longitude=30;
		latitude=-59;
		startTime="12:00";
		startDate="29/09/2026";
		centerPosition[]={6144,6144,100};
		clutterGrid=1;
		clutterDist=125;
		noDetailDist=65;
		fullDetailDist=10;
		volFogOffset=0;
		midDetailTexture="DZ\worlds\chernarusplus\data\middle_sat_mco.paa";
		class UsedTerrainMaterials
		{
			material1="DZ\surfaces\data\terrain\cp_gravel.rvmat";
			material2="DZ\surfaces\data\terrain\cp_conifer_common1.rvmat";
			material3="DZ\surfaces\data\terrain\cp_grass.rvmat";
			material4="DZ\surfaces\data\terrain\cp_grass_tall.rvmat";
		};
		class Names
		{
		};
		class Sounds
		{
			sounds[]={};
		};
		class Ambient
		{
		};
	};
};
