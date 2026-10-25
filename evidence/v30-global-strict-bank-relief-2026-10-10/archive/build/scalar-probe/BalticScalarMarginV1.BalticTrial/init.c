// Source-native raster census. SurfaceY and water APIs: 3_game/global/game.c:1162-1188.
// Sea swell probe for views: the server logs the global sea level and the water surface at three points every
// 250 ms, plus one row per real-time second that ties the server clock to the wall clock of the captures.
// No RPC, player movement or terrain edits.
// APIs: world.c SetDate :51; ensystem.c GetHourMinuteSecond :28; game.c SurfaceGetSeaLevelMin/Max/SeaLevel
// :1174-1176, SurfaceGetSeaWaveMax :1178, GetWaterSurfaceHeightNoFakeWave/WithFakeWave :1185-1187;
// weather.c GetActual :38, Set :49, SetLimits :74, GetWindSpeed :243, SetWindSpeed :251,
// SetWindMaximumSpeed :264, SetWindFunctionParams :280, MissionWeather :383.
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    GetGame().GetWorld().SetTimeMultiplier(0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0, 1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 1);
    weather.GetRain().Set(0, 0, 3600);
    weather.GetFog().SetLimits(0, 0);
    weather.GetFog().Set(0, 0, 3600);
    weather.GetSnowfall().SetLimits(0, 0);
    weather.GetSnowfall().Set(0, 0, 3600);
    weather.SetWindMaximumSpeed(20);
    weather.SetWindFunctionParams(1, 1, 1);
    weather.SetWindSpeed(20);
}



class BalticScalarMarginMission : MissionServer
{
 protected ref array<vector> m_Points = new array<vector>;
 protected ref array<float> m_B = new array<float>;
 protected FileHandle m_Log;
 protected int m_Next;
 protected int m_Sample;
 protected bool m_Done;
 override void OnInit()
 {
  super.OnInit();
  if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") { m_Done=true;return; }
  m_Log=OpenFile("$profile:baltic_scalar_margin_v1.log",FileMode.WRITE);
  if (!m_Log) { m_Done=true;return; }
  FPrintln(m_Log,"BALTIC_SCALAR_MARGIN_V1;8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b");
  m_Points.Insert(Vector(8274, 2.97510028, 11664)); m_B.Insert(3.00010037);
  m_Points.Insert(Vector(8274, 3.044734, 11652)); m_B.Insert(3.08936691);
  m_Points.Insert(Vector(9378, 4.4288969, 11472)); m_B.Insert(4.4576931);
  m_Points.Insert(Vector(9390, 4.46690798, 11472)); m_B.Insert(4.48317051);
  m_Points.Insert(Vector(9402, 4.45338678, 11466)); m_B.Insert(4.4726882);
  m_Points.Insert(Vector(5286, 1.94482136, 10350)); m_B.Insert(1.95009995);
  m_Points.Insert(Vector(8208, 1.83839667, 9252)); m_B.Insert(1.87132597);
  m_Points.Insert(Vector(11526, 3.1513226, 9234)); m_B.Insert(3.17884755);
  m_Points.Insert(Vector(9498, 1.82274508, 8952)); m_B.Insert(1.84549022);
  m_Points.Insert(Vector(9402, 1.83437181, 8460)); m_B.Insert(1.85291994);
  m_Points.Insert(Vector(5004, 7.05768299, 8046)); m_B.Insert(7.11565256);
  m_Points.Insert(Vector(11496, 2.56031179, 8046)); m_B.Insert(2.64439297);
  m_Points.Insert(Vector(11550, 2.5795126, 7884)); m_B.Insert(2.6763432);
  m_Points.Insert(Vector(11460, 4.15006351, 7854)); m_B.Insert(4.21290159);
  m_Points.Insert(Vector(11454, 4.19250202, 7842)); m_B.Insert(4.27230787);
  m_Points.Insert(Vector(7620, 6.78757334, 7560)); m_B.Insert(6.81561089);
  m_Points.Insert(Vector(3990, 2.211061, 7434)); m_B.Insert(2.2592485);
  m_Points.Insert(Vector(4002, 2.27694607, 7428)); m_B.Insert(2.33797193);
  m_Points.Insert(Vector(3984, 2.09351015, 7422)); m_B.Insert(2.16026115);
  m_Points.Insert(Vector(7068, 7.05663538, 7176)); m_B.Insert(7.06979036);
  m_Points.Insert(Vector(11418, 1.88986194, 6918)); m_B.Insert(1.9469223);
  m_Points.Insert(Vector(11424, 1.88160479, 6900)); m_B.Insert(1.94345617);
  m_Points.Insert(Vector(8076, 4.13837433, 6762)); m_B.Insert(4.15641785);
  m_Points.Insert(Vector(8076, 4.11143875, 6750)); m_B.Insert(4.15742588);
  m_Points.Insert(Vector(11310, 1.87816548, 6642)); m_B.Insert(1.89454782);
  m_Points.Insert(Vector(6534, 5.34357929, 6624)); m_B.Insert(5.43754864);
  m_Points.Insert(Vector(11316, 1.8427285, 6624)); m_B.Insert(1.88545692);
  m_Points.Insert(Vector(7308, 4.90141582, 6552)); m_B.Insert(4.99781513);
  m_Points.Insert(Vector(5574, 5.21681356, 6432)); m_B.Insert(5.26319742);
  m_Points.Insert(Vector(1902, 2.58280277, 6426)); m_B.Insert(2.62634516);
  m_Points.Insert(Vector(3234, 2.69227862, 6378)); m_B.Insert(2.72492528);
  m_Points.Insert(Vector(1830, 2.5040586, 6312)); m_B.Insert(2.52589583);
  m_Points.Insert(Vector(1818, 2.57753563, 6300)); m_B.Insert(2.70497084);
  m_Points.Insert(Vector(1842, 2.51753664, 6300)); m_B.Insert(2.55138969);
  m_Points.Insert(Vector(2328, 2.49535608, 6168)); m_B.Insert(2.52542567);
  m_Points.Insert(Vector(5862, 3.82588434, 6054)); m_B.Insert(3.88822532);
  m_Points.Insert(Vector(600, 3.44136572, 6036)); m_B.Insert(3.48263097);
  m_Points.Insert(Vector(6066, 4.07725143, 6036)); m_B.Insert(4.11130619);
  m_Points.Insert(Vector(6090, 4.09323645, 6036)); m_B.Insert(4.11107302);
  m_Points.Insert(Vector(11460, 2.46735263, 6012)); m_B.Insert(2.54314375);
  m_Points.Insert(Vector(5292, 3.82264137, 5928)); m_B.Insert(3.8436718);
  m_Points.Insert(Vector(7212, 20.4001884, 5844)); m_B.Insert(20.4252777);
  m_Points.Insert(Vector(6030, 3.63420534, 5826)); m_B.Insert(3.69812799);
  m_Points.Insert(Vector(2148, 2.60307407, 5646)); m_B.Insert(2.65063167);
  m_Points.Insert(Vector(4716, 1.8034451, 5622)); m_B.Insert(1.80689013);
  m_Points.Insert(Vector(6300, 3.56481957, 5556)); m_B.Insert(3.61017132);
  m_Points.Insert(Vector(10152, 5.17663097, 5496)); m_B.Insert(5.22816229);
  m_Points.Insert(Vector(3222, 4.00216198, 5454)); m_B.Insert(4.05604076);
  m_Points.Insert(Vector(4794, 1.8113842, 5412)); m_B.Insert(1.82276833);
  m_Points.Insert(Vector(1290, 2.60978889, 5382)); m_B.Insert(2.62510014);
  m_Points.Insert(Vector(1230, 2.73447585, 5256)); m_B.Insert(2.81590319);
  m_Points.Insert(Vector(1242, 2.60010028, 5238)); m_B.Insert(2.62510037);
  m_Points.Insert(Vector(5982, 2.10157061, 5178)); m_B.Insert(2.14595914);
  m_Points.Insert(Vector(2022, 2.64433098, 5142)); m_B.Insert(2.70649838);
  m_Points.Insert(Vector(1248, 2.8288281, 5106)); m_B.Insert(2.90328908);
  m_Points.Insert(Vector(1116, 2.64444423, 5082)); m_B.Insert(2.68659353);
  m_Points.Insert(Vector(1128, 2.62510014, 5064)); m_B.Insert(2.65010023);
  m_Points.Insert(Vector(4974, 1.81934214, 5040)); m_B.Insert(1.83868372);
  m_Points.Insert(Vector(4980, 1.82989693, 5034)); m_B.Insert(1.85979319);
  m_Points.Insert(Vector(2190, 2.23536372, 4908)); m_B.Insert(2.2900846);
  m_Points.Insert(Vector(11760, 1.80769324, 4884)); m_B.Insert(1.81538641);
  m_Points.Insert(Vector(1944, 2.63611984, 4746)); m_B.Insert(2.69776487);
  m_Points.Insert(Vector(3588, 4.1112957, 4734)); m_B.Insert(4.14615154);
  m_Points.Insert(Vector(4212, 4.66005039, 4662)); m_B.Insert(4.74499989);
  m_Points.Insert(Vector(7098, 2.37510014, 4464)); m_B.Insert(2.40009999);
  m_Points.Insert(Vector(7830, 3.77987981, 4422)); m_B.Insert(3.83492661);
  m_Points.Insert(Vector(7836, 3.79711366, 4410)); m_B.Insert(3.87745476);
  m_Points.Insert(Vector(4986, 2.38613367, 4392)); m_B.Insert(2.42264628);
  m_Points.Insert(Vector(6636, 4.56231022, 4392)); m_B.Insert(4.69951963);
  m_Points.Insert(Vector(1848, 2.47510004, 4368)); m_B.Insert(2.50010014);
  m_Points.Insert(Vector(6270, 3.21379566, 4362)); m_B.Insert(3.26890826);
  m_Points.Insert(Vector(6276, 3.22822523, 4362)); m_B.Insert(3.27221608);
  m_Points.Insert(Vector(6288, 3.18998575, 4356)); m_B.Insert(3.24204993);
  m_Points.Insert(Vector(6294, 3.23386002, 4356)); m_B.Insert(3.32979846);
  m_Points.Insert(Vector(3732, 4.6114316, 4212)); m_B.Insert(4.62255383);
  m_Points.Insert(Vector(4278, 4.40009975, 3966)); m_B.Insert(4.42509985);
  m_Points.Insert(Vector(10596, 2.79268694, 3948)); m_B.Insert(2.817173);
  m_Points.Insert(Vector(10602, 2.70969057, 3936)); m_B.Insert(2.7195189);
  m_Points.Insert(Vector(10206, 3.23697758, 3774)); m_B.Insert(3.23697782);
  m_Points.Insert(Vector(9102, 4.68338776, 3666)); m_B.Insert(4.73073101);
  m_Points.Insert(Vector(7638, 2.79440117, 3594)); m_B.Insert(2.91370201);
  m_Points.Insert(Vector(7662, 2.85408497, 3582)); m_B.Insert(2.93501592);
  m_Points.Insert(Vector(2880, 3.53134966, 3570)); m_B.Insert(3.59656262);
  m_Points.Insert(Vector(2898, 3.37896252, 3564)); m_B.Insert(3.41568255);
  m_Points.Insert(Vector(7746, 2.8739953, 3552)); m_B.Insert(3.04980087);
  m_Points.Insert(Vector(7758, 2.79637885, 3546)); m_B.Insert(2.91115165);
  m_Points.Insert(Vector(7764, 2.67510009, 3528)); m_B.Insert(2.70009995);
  m_Points.Insert(Vector(11208, 5.27840614, 3366)); m_B.Insert(5.32723761);
  m_Points.Insert(Vector(7266, 2.96781874, 3150)); m_B.Insert(3.04924631);
  m_Points.Insert(Vector(3558, 3.17202711, 3132)); m_B.Insert(3.22365212);
  m_Points.Insert(Vector(7440, 2.90010023, 3054)); m_B.Insert(2.92510009);
  m_Points.Insert(Vector(3384, 2.76886415, 3012)); m_B.Insert(2.78954506);
  m_Points.Insert(Vector(7494, 2.92510009, 3000)); m_B.Insert(2.95009995);
  m_Points.Insert(Vector(4056, 5.93694973, 2994)); m_B.Insert(6.01425982);
  m_Points.Insert(Vector(4062, 5.74279261, 2982)); m_B.Insert(5.76365948);
  m_Points.Insert(Vector(7488, 2.99174118, 2928)); m_B.Insert(3.08338189);
  m_Points.Insert(Vector(7494, 3.06714702, 2922)); m_B.Insert(3.2341938);
  m_Points.Insert(Vector(7506, 2.92510033, 2916)); m_B.Insert(2.95010018);
  m_Points.Insert(Vector(3366, 2.77436781, 2868)); m_B.Insert(2.82353449);
  m_Points.Insert(Vector(4626, 2.16023731, 2580)); m_B.Insert(2.18259883);
  m_Points.Insert(Vector(2520, 3.32923365, 2304)); m_B.Insert(3.40853071);
  m_Points.Insert(Vector(2520, 3.25768065, 2286)); m_B.Insert(3.30351353);
  m_Points.Insert(Vector(3948, 2.26236534, 2208)); m_B.Insert(2.30627227);
  m_Points.Insert(Vector(3192, 4.42472649, 2196)); m_B.Insert(4.48577213);
  m_Points.Insert(Vector(3186, 4.27509975, 2190)); m_B.Insert(4.30009985);
  m_Points.Insert(Vector(2730, 3.40787363, 2112)); m_B.Insert(3.47208548);
  m_Points.Insert(Vector(5406, 2.86706805, 2004)); m_B.Insert(2.90903592);
  m_Points.Insert(Vector(2688, 3.37838411, 1992)); m_B.Insert(3.42934632);
  m_Points.Insert(Vector(5892, 2.52929139, 1968)); m_B.Insert(2.55010033);
  m_Points.Insert(Vector(4854, 5.97272873, 1962)); m_B.Insert(6.01264429);
  m_Points.Insert(Vector(7470, 4.1037035, 1920)); m_B.Insert(4.15264845);
  m_Points.Insert(Vector(8448, 3.29513717, 1914)); m_B.Insert(3.32230663);
  m_Points.Insert(Vector(8454, 3.19505024, 1914)); m_B.Insert(3.24000001);
  m_Points.Insert(Vector(8664, 3.17510009, 1836)); m_B.Insert(3.20009995);
  m_Points.Insert(Vector(8676, 3.31479311, 1836)); m_B.Insert(3.37115574);
  m_Points.Insert(Vector(8676, 3.35426116, 1830)); m_B.Insert(3.45009184);
  m_Points.Insert(Vector(8682, 3.17510009, 1824)); m_B.Insert(3.20009995);
  m_Points.Insert(Vector(6480, 6.08444977, 1800)); m_B.Insert(6.1379385);
  m_Points.Insert(Vector(4812, 5.48356915, 1776)); m_B.Insert(5.5625205);
  m_Points.Insert(Vector(11244, 2.1843431, 1662)); m_B.Insert(2.21392226);
  m_Points.Insert(Vector(5862, 2.57843781, 1632)); m_B.Insert(2.60626316);
  m_Points.Insert(Vector(12036, 2.4086616, 1620)); m_B.Insert(2.49420381);
  m_Points.Insert(Vector(12042, 2.39265776, 1620)); m_B.Insert(2.48534322);
  m_Points.Insert(Vector(2886, 2.94086409, 1608)); m_B.Insert(2.98785281);
  m_Points.Insert(Vector(1836, 2.96419764, 1542)); m_B.Insert(3.02048182);
  m_Points.Insert(Vector(12120, 2.29961157, 1506)); m_B.Insert(2.36698532);
  m_Points.Insert(Vector(1734, 2.79815388, 1452)); m_B.Insert(2.84620786);
  m_Points.Insert(Vector(2652, 3.39247131, 1344)); m_B.Insert(3.45038772);
  m_Points.Insert(Vector(1488, 2.72205067, 1314)); m_B.Insert(2.75888205);
  m_Points.Insert(Vector(1488, 2.81431198, 1308)); m_B.Insert(2.9200592);
  m_Points.Insert(Vector(4710, 6.08167744, 1308)); m_B.Insert(6.11325455);
  m_Points.Insert(Vector(2094, 1.94066072, 1206)); m_B.Insert(1.9540478);
  m_Points.Insert(Vector(5898, 3.01367426, 1176)); m_B.Insert(3.07556295);
  m_Points.Insert(Vector(4074, 4.35939932, 1116)); m_B.Insert(4.41701984);
  m_Points.Insert(Vector(1230, 2.87852621, 1068)); m_B.Insert(2.87852645);
  m_Points.Insert(Vector(1218, 2.83869648, 1056)); m_B.Insert(2.8391552);
  m_Points.Insert(Vector(1140, 2.80201387, 984)); m_B.Insert(2.85072803);
  m_Points.Insert(Vector(8916, 1.94702792, 966)); m_B.Insert(1.95586646);
  m_Points.Insert(Vector(8892, 1.89199805, 960)); m_B.Insert(1.9313978);
  m_Points.Insert(Vector(996, 2.85798073, 882)); m_B.Insert(2.8659234);
  m_Points.Insert(Vector(6504, 3.01581359, 846)); m_B.Insert(3.13456821);
  m_Points.Insert(Vector(4236, 5.01341057, 786)); m_B.Insert(5.04255295);
  m_Points.Insert(Vector(4248, 5.0049963, 786)); m_B.Insert(5.0311532);
  m_Points.Insert(Vector(3684, 8.05127144, 666)); m_B.Insert(8.09624863);
  m_Points.Insert(Vector(7716, 9.15354347, 654)); m_B.Insert(9.20636177);
  m_Points.Insert(Vector(3696, 7.99576092, 648)); m_B.Insert(8.02487755);
  m_Points.Insert(Vector(7704, 9.14443302, 648)); m_B.Insert(9.16376591);
  m_Points.Insert(Vector(2130, 2.77843761, 600)); m_B.Insert(2.83131075);
  m_Points.Insert(Vector(3294, 8.50391674, 600)); m_B.Insert(8.55773258);
  m_Points.Insert(Vector(3144, 7.67555952, 516)); m_B.Insert(7.74258661);
  m_Points.Insert(Vector(1758, 2.67601418, 492)); m_B.Insert(2.70009995);
  m_Points.Insert(Vector(1734, 2.73199034, 480)); m_B.Insert(2.77975345);
  m_Points.Insert(Vector(1884, 1.80618167, 474)); m_B.Insert(1.81236327);
  m_Points.Insert(Vector(1668, 2.7652483, 438)); m_B.Insert(2.80606818);
  m_Points.Insert(Vector(1632, 2.72467709, 378)); m_B.Insert(2.75805688);
  m_Points.Insert(Vector(1620, 2.85095644, 366)); m_B.Insert(2.92079687);
  m_Points.Insert(Vector(1488, 2.83089876, 324)); m_B.Insert(2.90613627);
  m_Points.Insert(Vector(1482, 2.71814442, 318)); m_B.Insert(2.78606057);
  m_Points.Insert(Vector(10260, 2.16070676, 306)); m_B.Insert(2.19201136);
  m_Points.Insert(Vector(10260, 2.35835361, 300)); m_B.Insert(2.44625401);
  m_Points.Insert(Vector(10248, 2.20471907, 294)); m_B.Insert(2.24450111);
  m_Points.Insert(Vector(10242, 2.36209393, 288)); m_B.Insert(2.38188434);
  m_Points.Insert(Vector(8280, 3.78828764, 11664)); m_B.Insert(3.79431343);
  m_Points.Insert(Vector(8274, 1.00915539, 11658)); m_B.Insert(1.00915539);
  m_Points.Insert(Vector(8280, 1.78838789, 11652)); m_B.Insert(1.78838789);
  m_Points.Insert(Vector(8274, 3.70706201, 11646)); m_B.Insert(3.70706201);
  m_Points.Insert(Vector(9384, 4.71635342, 11472)); m_B.Insert(4.83697271);
  m_Points.Insert(Vector(9378, 5.75080967, 11466)); m_B.Insert(6.0107913);
  m_Points.Insert(Vector(9396, 2.29891753, 11472)); m_B.Insert(2.29891753);
  m_Points.Insert(Vector(9390, 6.57848644, 11466)); m_B.Insert(7.1925211);
  m_Points.Insert(Vector(9408, 4.16114378, 11466)); m_B.Insert(4.16114378);
  m_Points.Insert(Vector(9402, 6.18708372, 11460)); m_B.Insert(6.40971661);
  m_Points.Insert(Vector(5292, 1.61954486, 10350)); m_B.Insert(1.61954486);
  m_Points.Insert(Vector(5286, 2.62077022, 10344)); m_B.Insert(2.62077022);
  m_Points.Insert(Vector(8214, 1, 9252)); m_B.Insert(1);
  m_Points.Insert(Vector(8208, 1.15120018, 9246)); m_B.Insert(1.15120018);
  m_Points.Insert(Vector(11532, 6.03605366, 9234)); m_B.Insert(6.55051708);
  m_Points.Insert(Vector(11526, 3.33135033, 9228)); m_B.Insert(3.33135033);

  m_Next=GetGame().GetTime()+5000;
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  GetGame().GetWeather().SetWindSpeed(20);
  if (m_Done || GetGame().GetTime()<m_Next) return;
  m_Next=GetGame().GetTime()+250;
  int now=GetGame().GetTime();
  FPrintln(m_Log,"T;"+m_Sample+";"+now+";"+GetGame().GetWeather().GetWindSpeed()+";"+GetGame().SurfaceGetSeaLevel()+";"+GetGame().SurfaceGetSeaWaveMax());
  for (int i=0;i<m_Points.Count();i++)
  {
   vector point=m_Points[i];float ground=GetGame().SurfaceY(point[0],point[2]);
   vector above=Vector(point[0],ground+100,point[2]);
   bool sea=GetGame().SurfaceIsSea(point[0],point[2]);bool pond=GetGame().SurfaceIsPond(point[0],point[2]);
   float nominal=GetGame().GetWaterSurfaceHeightNoFakeWave(above);
   float fake=GetGame().GetWaterSurfaceHeightWithFakeWave(above);
   float depthH=GetGame().GetWaterDepth(Vector(point[0],ground+0.01,point[2]));
   float depthB=GetGame().GetWaterDepth(Vector(point[0],m_B[i]+0.01,point[2]));
   FPrintln(m_Log,"P;"+m_Sample+";"+i+";"+ground+";"+sea+";"+pond+";"+nominal+";"+fake+";"+depthH+";"+depthB);
  }
  m_Sample++;
  if (m_Sample==241)
  {
   FPrintln(m_Log,"END;"+m_Sample+";"+m_Points.Count());CloseFile(m_Log);m_Log=null;m_Done=true;
  }
 }
}
Mission CreateCustomMission(string path) { return new BalticScalarMarginMission(); }
