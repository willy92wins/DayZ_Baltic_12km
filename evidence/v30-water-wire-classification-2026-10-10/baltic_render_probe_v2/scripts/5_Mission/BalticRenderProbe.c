// Isolated diagnostic. Engine IDs are read-only verified against native labels by the host.
modded class MissionGameplay
{
 protected bool m_BalticRenderStarted;
 protected bool m_BalticRenderReady;
 protected bool m_BalticRenderRefused;
 protected int m_BalticRenderID;
 protected int m_BalticWaterID;
 protected int m_BalticRenderOriginal;
 protected int m_BalticWaterOriginal;
 protected int m_BalticRenderPhase = -1;
 protected float m_BalticRenderNext;
 protected float m_BalticRenderAge;

 void BalticRenderLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_render_probe_v2.log", FileMode.APPEND);
  if (!file) return;
  FPrintln(file, message);
  CloseFile(file);
 }

 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer()) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  m_BalticRenderAge += timeslice;
  m_BalticRenderNext -= timeslice;
  if (m_BalticRenderNext > 0 || m_BalticRenderRefused) return;
  m_BalticRenderNext = 1;
  if (!m_BalticRenderStarted)
  {
   FileHandle first = OpenFile("$profile:baltic_render_probe_v2.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_RENDER_PROBE_V2_WAITING_VERIFIED_IDS");
   CloseFile(first);
   m_BalticRenderStarted = true;
  }
  if (!m_BalticRenderReady)
  {
   if (!DiagMenu.IsInitialized()) return;
   FileHandle ids = OpenFile("$profile:baltic_render_probe_v2.ids", FileMode.READ);
   if (!ids) return;
   string digest;
   string renderID;
   string waterID;
   FGets(ids, digest);
   FGets(ids, renderID);
   FGets(ids, waterID);
   CloseFile(ids);
   digest = digest.Trim(); renderID = renderID.Trim(); waterID = waterID.Trim();
   m_BalticRenderID = renderID.ToInt();
   m_BalticWaterID = waterID.ToInt();
   if (digest != "34f6377be4fd065d104e67263e0c96ac2cb2e348119a4838eba08d2e61b7a69a" || m_BalticRenderID < 0 || m_BalticWaterID < 0 || m_BalticRenderID == m_BalticWaterID || m_BalticRenderID >= 4096 || m_BalticWaterID >= 4096)
   {
    m_BalticRenderRefused = true; BalticRenderLog("REFUSED;ids"); return;
   }
   m_BalticRenderOriginal = DiagMenu.GetEngineValue(m_BalticRenderID);
   m_BalticWaterOriginal = DiagMenu.GetEngineValue(m_BalticWaterID);
   if (m_BalticRenderOriginal != 0 || m_BalticWaterOriginal != 0)
   {
    m_BalticRenderRefused = true; BalticRenderLog("REFUSED;baseline"); return;
   }
   m_BalticRenderReady = true;
   BalticRenderLog("READY;" + m_BalticRenderID + ";" + m_BalticWaterID + ";" + m_BalticRenderOriginal + ";" + m_BalticWaterOriginal);
  }
  int desired = 0;
  FileHandle command = OpenFile("$profile:baltic_render_probe_v2.phase", FileMode.READ);
  if (command)
  {
   string line; FGets(command, line); CloseFile(command); desired = line.ToInt();
  }
  if (desired < 0 || desired > 4 || m_BalticRenderAge >= 1200) desired = 9;
  if (desired == m_BalticRenderPhase) return;
  // First baseline is untouched; all later transitions restore the exact original values.
  if (m_BalticRenderPhase >= 0)
  {
   DiagMenu.SetEngineValue(m_BalticRenderID, m_BalticRenderOriginal);
   DiagMenu.SetEngineValue(m_BalticWaterID, m_BalticWaterOriginal);
  }
  if (desired == 1) DiagMenu.SetEngineValue(m_BalticRenderID, 1);
  if (desired == 2) DiagMenu.SetEngineValue(m_BalticRenderID, 2);
  if (desired == 3) DiagMenu.SetEngineValue(m_BalticWaterID, 1);
  if (desired == 4)
  {
   DiagMenu.SetEngineValue(m_BalticRenderID, 2);
   DiagMenu.SetEngineValue(m_BalticWaterID, 1);
  }
  m_BalticRenderPhase = desired;
  BalticRenderLog("PHASE;" + desired + ";" + GetGame().GetTime() + ";render;" + DiagMenu.GetEngineValue(m_BalticRenderID) + ";water;" + DiagMenu.GetEngineValue(m_BalticWaterID));
 }
};
