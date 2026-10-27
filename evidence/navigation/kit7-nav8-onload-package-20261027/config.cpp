class CfgPatches
{
	class BalticTrialWorld
	{
		units[]={};
		weapons[]={};
		requiredVersion=0.1;
		requiredAddons[]=
		{
			"DZ_Data",
			"DZ_Surfaces",
			"Baltic_Water_V30",
			"Baltic_Stream_Pilot"
		};
	};
};
class CfgWorlds
{
	class CAWorld;
	class BalticTrial: CAWorld
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
		class Navmesh
		{
			navmeshName="dayz_baltic_12km_dev\tb\narva_trial\navmesh\baltic_trial.nm";
			filterIsolatedIslandsOnLoad=1;
			visualiseOffset=0;
			class GenParams
			{
				tileWidth=8;
				cellSize1=0.25;
				cellSize2=0.1;
				cellSize3=0.1;
				filterIsolatedIslands="true";
				seedPosition[]={6144,0,6144};
				class Agent
				{
					diameter=0.60000002;
					standHeight=1.5;
					crouchHeight=1;
					proneHeight=0.5;
					maxStepHeight=0.44999999;
					maxSlope=60;
				};
				class Links
				{
					class ZedJump387_050
					{
						jumpLength=1.5;
						jumpHeight=0.5;
						minCenterHeight=0.30000001;
						jumpDropdownMin=0.5;
						jumpDropdownMax=-0.5;
						areaType="jump0";
						flags[]=
						{
							"jumpOver"
						};
						color=1727987712;
					};
					class ZedJump388_050
					{
						jumpLength=1.5;
						jumpHeight=0.5;
						minCenterHeight=-0.5;
						jumpDropdownMin=0.5;
						jumpDropdownMax=-0.5;
						areaType="jump0";
						flags[]=
						{
							"jumpOver"
						};
						color=1725781248;
					};
					class ZedJump387_110
					{
						jumpLength=3.9000001;
						jumpHeight=1.1;
						minCenterHeight=0.5;
						jumpDropdownMin=0.5;
						jumpDropdownMax=-0.5;
						areaType="jump0";
						flags[]=
						{
							"jumpOver"
						};
						color=1711308800;
					};
					class ZedJump420_160
					{
						jumpLength=4;
						jumpHeight=1.6;
						minCenterHeight=1.1;
						jumpDropdownMin=0.5;
						jumpDropdownMax=-0.5;
						areaType="jump0";
						flags[]=
						{
							"jumpOver"
						};
						color=1711276287;
					};
					class ZedJump265_210
					{
						jumpLength=2.45;
						jumpHeight=2.5;
						minCenterHeight=1.8;
						jumpDropdownMin=0.5;
						jumpDropdownMax=-0.5;
						areaType="jump0";
						flags[]=
						{
							"climb"
						};
						color=1720975571;
					};
					class Fence50_110deer
					{
						typeId=100;
						jumpLength=8;
						jumpHeight=1.1;
						minCenterHeight=0.5;
						jumpDropdownMin=1;
						jumpDropdownMax=-1;
						areaType="jump2";
						flags[]=
						{
							"jumpOver"
						};
						color=1722460927;
					};
					class Fence110_160deer
					{
						typeId=101;
						jumpLength=8;
						jumpHeight=1.6;
						minCenterHeight=1.1;
						jumpDropdownMin=1;
						jumpDropdownMax=-1;
						areaType="jump3";
						flags[]=
						{
							"jumpOver"
						};
						color=1713700856;
					};
					class Fence50_110hen
					{
						typeId=110;
						jumpLength=4;
						jumpHeight=1.1;
						minCenterHeight=0.5;
						jumpDropdownMin=0.5;
						jumpDropdownMax=-0.5;
						areaType="jump4";
						flags[]=
						{
							"jumpOver"
						};
						color=-22016;
					};
					class Fence110_160hen
					{
						typeId=111;
						jumpLength=4;
						jumpHeight=1.6;
						minCenterHeight=1.1;
						jumpDropdownMin=0.5;
						jumpDropdownMax=-0.5;
						areaType="jump4";
						flags[]=
						{
							"jumpOver"
						};
						color=-22016;
					};
				};
			};
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
