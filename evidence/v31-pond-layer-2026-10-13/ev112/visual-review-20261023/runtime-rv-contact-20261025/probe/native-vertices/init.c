// Diagnostic only: WRP loading versus explicit ECE_CREATEPHYSICS.
// APIs: game.c:691-703, enphysics.c:57-60, centraleconomy.c:17,28-33.
// Controls: identical masks for vanilla stream, custom stream and empty space.
// No acceptance of walking, visuals or WRP collision follows from spawned objects.
void main() {}
class BalticCollisionProbeMission: MissionServer
{
    protected ref array<Object> m_Objects = new array<Object>;
    protected ref array<CargoBase> m_Proxies = new array<CargoBase>;
    protected ref set<Object> m_Hits = new set<Object>;
    protected Object m_Pilot;
    protected Object m_Native;
    protected int m_After;
    protected int m_Index;
    protected bool m_Done;
    void Log(string row)
    {
        FileHandle file = OpenFile("$profile:baltic_collision_probe_v1.log", FileMode.APPEND);
        if (!file) { m_Done = true; return; }
        FPrintln(file, row);
        CloseFile(file);
    }
    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer()) return;
        FileHandle file = OpenFile("$profile:baltic_collision_probe_v1.log", FileMode.WRITE);
        FPrintln(file, "BALTIC_COLLISION_DIAGNOSTIC_V3");
        CloseFile(file);
        int flags = ECE_CREATEPHYSICS | ECE_KEEPHEIGHT | ECE_NOSURFACEALIGN | ECE_NOPERSISTENCY_WORLD;
        m_Pilot = GetGame().CreateObjectEx("Land_cs_kit_118_0000", "1000 100 1000", flags);
        m_Native = GetGame().CreateObjectEx("Land_streambed_leaf_long_straight", "1100 100 1000", flags);
        GetGame().GetObjectsAtPosition("8262 0 8934", 40, m_Objects, m_Proxies);
        m_After = GetGame().GetTime() + 10000;
    }
    void Inspect(string label, Object obj)
    {
        string row = "OBJECT;" + label;
        if (!obj) { Log(row + ";NULL"); return; }
        string type = obj.GetType();
        string shape = obj.GetShapeName();
        vector pos = obj.GetPosition();
        bool body = dBodyIsSet(obj);
        int layer;
        if (body) layer = dBodyGetInteractionLayer(obj);
        row = row + ";" + type + ";" + shape + ";" + pos + ";" + body + ";" + layer;
        Log(row);
    }
    void Probe(string label, float x, float z, float top, float bottom)
    {
        vector above = Vector(x, top, z);
        vector below = Vector(x, bottom, z);
        vector contact;
        vector normal;
        int component;
        Object obj;
        float fraction;
        m_Hits.Clear();
        bool rv = DayZPhysics.RaycastRV(above, below, contact, normal, component, m_Hits, null, null, true, false, ObjIntersectGeom, 0, CollisionFlags.NEARESTCONTACT);
        string shapes;
        for (int k = 0; k < m_Hits.Count(); k++)
        {
            obj = m_Hits.Get(k);
            if (obj) shapes = shapes + obj.GetShapeName() + "|";
        }
        vector bc;
        vector bn;
        Object hit;
        bool bullet = DayZPhysics.RayCastBullet(above, below, PhxInteractionLayers.BUILDING, null, hit, bc, bn, fraction);
        string bs;
        if (hit) bs = hit.GetShapeName();
        string row = "RAY;" + label + ";" + x + ";" + z + ";" + rv + ";" + contact + ";" + shapes;
        row = row + ";" + bullet + ";" + bc + ";" + bs;
        row = row + ";" + normal + ";" + bn;
        Log(row);
    }
    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || m_Done || GetGame().GetTime() < m_After) return;
        if (m_Index == 0)
        {
            Inspect("spawn_pilot", m_Pilot);
            Inspect("spawn_native", m_Native);
            for (int k = 0; k < m_Objects.Count(); k++) Inspect("wrp", m_Objects[k]);
            Probe("wrp_pilot", 8262, 8934, 30, 0);
            m_Objects.Clear();
            m_Proxies.Clear();
            GetGame().GetObjectsAtPosition("8262 0 8934", 40, m_Objects, m_Proxies);
            for (int j = 0; j < m_Objects.Count(); j++) Inspect("wrp_refreshed", m_Objects[j]);
            Probe("wrp_refreshed", 8262, 8934, 30, 0);
        }
        int col = m_Index % 17;
        int line = m_Index / 17;
        float dx = col * 2 - 16;
        float dz = line * 2 - 16;
        Probe("spawn_pilot", 1000 + dx, 1000 + dz, 150, 50);
        Probe("spawn_native", 1100 + dx, 1000 + dz, 150, 50);
        Probe("empty", 1200 + dx, 1000 + dz, 150, 50);
        m_Index++;
        if (m_Index == 289)
        {
            FileHandle vertexInput = OpenFile("$mission:vertex-points.csv", FileMode.READ);
            string vertexRow;
            ref array<string> fields = new array<string>;
            if (!vertexInput) { Log("FAIL;NO_VERTEX_POINTS"); m_Done = true; return; }
            while (FGets(vertexInput, vertexRow) >= 0)
            {
                fields.Clear(); vertexRow.Split(";", fields);
                if (fields.Count() != 2) { Log("FAIL;VERTEX_SCHEMA"); break; }
                vector q = fields[1].ToVector();
                Probe("vertex_native_" + fields[0], q[0], q[2], 150, 50);
            }
            CloseFile(vertexInput);
            Log("END;289"); m_Done = true;
        }
    }
}
Mission CreateCustomMission(string path) { return new BalticCollisionProbeMission(); }
