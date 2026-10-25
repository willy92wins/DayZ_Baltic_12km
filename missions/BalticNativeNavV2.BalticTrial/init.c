// Temporary read-only server probe; no CE/actors or network state.
// AIWorld/PGFilter contracts: P:/scripts/3_game/ai/aiworld.c:80,111,137.
void main() { Print("BALTIC_NATIVE_NAV_MAIN_V1"); }
static void BalticNavQuery(string label, vector start, vector finish, PGFilter filter, FileHandle report)
{
    AIWorld ai = GetGame().GetWorld().GetAIWorld();
    start[1] = GetGame().SurfaceRoadY(start[0], start[2]);
    finish[1] = GetGame().SurfaceRoadY(finish[0], finish[2]);
    vector a, b;
    bool sa = ai.SampleNavmeshPosition(start, 2, filter, a);
    bool sb = ai.SampleNavmeshPosition(finish, 2, filter, b);
    TVectorArray points = new TVectorArray;
    bool found = false;
    if (sa && sb) found = ai.FindPath(a, b, filter, points);
    FPrintln(report, "Q;" + label + ";" + start + ";" + finish + ";" + sa + ";" + sb + ";" + a + ";" + b + ";" + found + ";" + points.Count());
    for (int i = 0; i < points.Count(); i++)
        FPrintln(report, "P;" + label + ";" + i + ";" + points.Get(i));
    if (label == "west_east" || label == "east_west")
    {
        for (int step = 0; step <= 120; step++)
        {
            vector requested = start + (finish - start) * (step / 120.0);
            requested[1] = GetGame().SurfaceRoadY(requested[0], requested[2]);
            vector sampled;
            bool success = ai.SampleNavmeshPosition(requested, 0.8, filter, sampled);
            FPrintln(report, "R;" + label + ";" + step + ";" + requested + ";" + success + ";" + sampled);
        }
    }
}


static void BalticNativeDryPoint(FileHandle report, int index, vector requested)
{
    AIWorld ai = GetGame().GetWorld().GetAIWorld();
    PGFilter walk = new PGFilter;
    walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
    requested[1] = GetGame().SurfaceY(requested[0], requested[2]);
    vector sampled;
    bool success = ai.SampleNavmeshPosition(requested, 2, walk, sampled);
    FPrintln(report, "D;" + index + ";" + requested + ";" + success + ";" + sampled);
}

static void BalticNativeDryChunk0(FileHandle report)
{
    BalticNativeDryPoint(report, 0, "192.000000 0 192.000000");
    BalticNativeDryPoint(report, 1, "192.000000 0 4800.000000");
    BalticNativeDryPoint(report, 2, "192.000000 0 5568.000000");
    BalticNativeDryPoint(report, 3, "192.000000 0 5952.000000");
    BalticNativeDryPoint(report, 4, "192.000000 0 6336.000000");
    BalticNativeDryPoint(report, 5, "192.000000 0 6720.000000");
    BalticNativeDryPoint(report, 6, "192.000000 0 7104.000000");
    BalticNativeDryPoint(report, 7, "576.000000 0 576.000000");
    BalticNativeDryPoint(report, 8, "576.000000 0 4800.000000");
    BalticNativeDryPoint(report, 9, "576.000000 0 5184.000000");
    BalticNativeDryPoint(report, 10, "576.000000 0 5568.000000");
    BalticNativeDryPoint(report, 11, "960.000000 0 576.000000");
    BalticNativeDryPoint(report, 12, "960.000000 0 960.000000");
    BalticNativeDryPoint(report, 13, "960.000000 0 1344.000000");
    BalticNativeDryPoint(report, 14, "960.000000 0 4800.000000");
    BalticNativeDryPoint(report, 15, "960.000000 0 5184.000000");
    BalticNativeDryPoint(report, 16, "960.000000 0 5568.000000");
    BalticNativeDryPoint(report, 17, "960.000000 0 6336.000000");
    BalticNativeDryPoint(report, 18, "960.000000 0 6720.000000");
    BalticNativeDryPoint(report, 19, "1284.000000 0 3024.000000");
    BalticNativeDryPoint(report, 20, "1284.000000 0 3144.000000");
    BalticNativeDryPoint(report, 21, "1344.000000 0 960.000000");
    BalticNativeDryPoint(report, 22, "1344.000000 0 2496.000000");
    BalticNativeDryPoint(report, 23, "1344.000000 0 4032.000000");
    BalticNativeDryPoint(report, 24, "1344.000000 0 4416.000000");
    BalticNativeDryPoint(report, 25, "1344.000000 0 4800.000000");
    BalticNativeDryPoint(report, 26, "1344.000000 0 5184.000000");
    BalticNativeDryPoint(report, 27, "1344.000000 0 5952.000000");
    BalticNativeDryPoint(report, 28, "1344.000000 0 6720.000000");
    BalticNativeDryPoint(report, 29, "1344.000000 0 10560.000000");
    BalticNativeDryPoint(report, 30, "1404.000000 0 3024.000000");
    BalticNativeDryPoint(report, 31, "1404.000000 0 3144.000000");
}

static void BalticNativeDryChunk1(FileHandle report)
{
    BalticNativeDryPoint(report, 32, "1404.000000 0 3384.000000");
    BalticNativeDryPoint(report, 33, "1524.000000 0 3024.000000");
    BalticNativeDryPoint(report, 34, "1524.000000 0 3144.000000");
    BalticNativeDryPoint(report, 35, "1524.000000 0 3264.000000");
    BalticNativeDryPoint(report, 36, "1524.000000 0 3384.000000");
    BalticNativeDryPoint(report, 37, "1524.000000 0 3504.000000");
    BalticNativeDryPoint(report, 38, "1728.000000 0 192.000000");
    BalticNativeDryPoint(report, 39, "1728.000000 0 576.000000");
    BalticNativeDryPoint(report, 40, "1728.000000 0 960.000000");
    BalticNativeDryPoint(report, 41, "1728.000000 0 1344.000000");
    BalticNativeDryPoint(report, 42, "1728.000000 0 1728.000000");
    BalticNativeDryPoint(report, 43, "1728.000000 0 2496.000000");
    BalticNativeDryPoint(report, 44, "1728.000000 0 2880.000000");
    BalticNativeDryPoint(report, 45, "1728.000000 0 3264.000000");
    BalticNativeDryPoint(report, 46, "1728.000000 0 3648.000000");
    BalticNativeDryPoint(report, 47, "1728.000000 0 4032.000000");
    BalticNativeDryPoint(report, 48, "1728.000000 0 4416.000000");
    BalticNativeDryPoint(report, 49, "1728.000000 0 4800.000000");
    BalticNativeDryPoint(report, 50, "1728.000000 0 5184.000000");
    BalticNativeDryPoint(report, 51, "1728.000000 0 5568.000000");
    BalticNativeDryPoint(report, 52, "1728.000000 0 5952.000000");
    BalticNativeDryPoint(report, 53, "1728.000000 0 6720.000000");
    BalticNativeDryPoint(report, 54, "1728.000000 0 7104.000000");
    BalticNativeDryPoint(report, 55, "2106.000000 0 6906.000000");
    BalticNativeDryPoint(report, 56, "2106.000000 0 7026.000000");
    BalticNativeDryPoint(report, 57, "2106.000000 0 7146.000000");
    BalticNativeDryPoint(report, 58, "2112.000000 0 192.000000");
    BalticNativeDryPoint(report, 59, "2112.000000 0 576.000000");
    BalticNativeDryPoint(report, 60, "2112.000000 0 1728.000000");
    BalticNativeDryPoint(report, 61, "2112.000000 0 2112.000000");
    BalticNativeDryPoint(report, 62, "2112.000000 0 2496.000000");
    BalticNativeDryPoint(report, 63, "2112.000000 0 2880.000000");
}

static void BalticNativeDryChunk2(FileHandle report)
{
    BalticNativeDryPoint(report, 64, "2112.000000 0 3264.000000");
    BalticNativeDryPoint(report, 65, "2112.000000 0 4032.000000");
    BalticNativeDryPoint(report, 66, "2112.000000 0 4416.000000");
    BalticNativeDryPoint(report, 67, "2112.000000 0 5184.000000");
    BalticNativeDryPoint(report, 68, "2112.000000 0 5952.000000");
    BalticNativeDryPoint(report, 69, "2112.000000 0 7872.000000");
    BalticNativeDryPoint(report, 70, "2112.000000 0 8256.000000");
    BalticNativeDryPoint(report, 71, "2112.000000 0 9024.000000");
    BalticNativeDryPoint(report, 72, "2226.000000 0 6786.000000");
    BalticNativeDryPoint(report, 73, "2346.000000 0 6786.000000");
    BalticNativeDryPoint(report, 74, "2466.000000 0 6666.000000");
    BalticNativeDryPoint(report, 75, "2466.000000 0 6906.000000");
    BalticNativeDryPoint(report, 76, "2466.000000 0 7026.000000");
    BalticNativeDryPoint(report, 77, "2466.000000 0 7146.000000");
    BalticNativeDryPoint(report, 78, "2496.000000 0 192.000000");
    BalticNativeDryPoint(report, 79, "2496.000000 0 960.000000");
    BalticNativeDryPoint(report, 80, "2496.000000 0 1344.000000");
    BalticNativeDryPoint(report, 81, "2496.000000 0 1728.000000");
    BalticNativeDryPoint(report, 82, "2496.000000 0 2112.000000");
    BalticNativeDryPoint(report, 83, "2496.000000 0 2496.000000");
    BalticNativeDryPoint(report, 84, "2496.000000 0 3264.000000");
    BalticNativeDryPoint(report, 85, "2496.000000 0 3648.000000");
    BalticNativeDryPoint(report, 86, "2496.000000 0 4416.000000");
    BalticNativeDryPoint(report, 87, "2496.000000 0 4800.000000");
    BalticNativeDryPoint(report, 88, "2496.000000 0 5184.000000");
    BalticNativeDryPoint(report, 89, "2496.000000 0 5568.000000");
    BalticNativeDryPoint(report, 90, "2496.000000 0 5952.000000");
    BalticNativeDryPoint(report, 91, "2496.000000 0 7104.000000");
    BalticNativeDryPoint(report, 92, "2496.000000 0 7872.000000");
    BalticNativeDryPoint(report, 93, "2496.000000 0 8256.000000");
    BalticNativeDryPoint(report, 94, "2586.000000 0 6666.000000");
    BalticNativeDryPoint(report, 95, "2586.000000 0 6786.000000");
}

static void BalticNativeDryChunk3(FileHandle report)
{
    BalticNativeDryPoint(report, 96, "2586.000000 0 6906.000000");
    BalticNativeDryPoint(report, 97, "2586.000000 0 7026.000000");
    BalticNativeDryPoint(report, 98, "2586.000000 0 7146.000000");
    BalticNativeDryPoint(report, 99, "2880.000000 0 192.000000");
    BalticNativeDryPoint(report, 100, "2880.000000 0 576.000000");
    BalticNativeDryPoint(report, 101, "2880.000000 0 960.000000");
    BalticNativeDryPoint(report, 102, "2880.000000 0 1344.000000");
    BalticNativeDryPoint(report, 103, "2880.000000 0 1728.000000");
    BalticNativeDryPoint(report, 104, "2880.000000 0 2496.000000");
    BalticNativeDryPoint(report, 105, "2880.000000 0 2880.000000");
    BalticNativeDryPoint(report, 106, "2880.000000 0 3264.000000");
    BalticNativeDryPoint(report, 107, "2880.000000 0 3648.000000");
    BalticNativeDryPoint(report, 108, "2880.000000 0 4032.000000");
    BalticNativeDryPoint(report, 109, "2880.000000 0 4800.000000");
    BalticNativeDryPoint(report, 110, "2880.000000 0 5184.000000");
    BalticNativeDryPoint(report, 111, "2880.000000 0 5568.000000");
    BalticNativeDryPoint(report, 112, "2880.000000 0 5952.000000");
    BalticNativeDryPoint(report, 113, "2880.000000 0 6336.000000");
    BalticNativeDryPoint(report, 114, "2880.000000 0 7104.000000");
    BalticNativeDryPoint(report, 115, "2880.000000 0 7872.000000");
    BalticNativeDryPoint(report, 116, "2880.000000 0 8256.000000");
    BalticNativeDryPoint(report, 117, "3264.000000 0 960.000000");
    BalticNativeDryPoint(report, 118, "3264.000000 0 1344.000000");
    BalticNativeDryPoint(report, 119, "3264.000000 0 1728.000000");
    BalticNativeDryPoint(report, 120, "3264.000000 0 2112.000000");
    BalticNativeDryPoint(report, 121, "3264.000000 0 2496.000000");
    BalticNativeDryPoint(report, 122, "3264.000000 0 2880.000000");
    BalticNativeDryPoint(report, 123, "3264.000000 0 3264.000000");
    BalticNativeDryPoint(report, 124, "3264.000000 0 3648.000000");
    BalticNativeDryPoint(report, 125, "3264.000000 0 4032.000000");
    BalticNativeDryPoint(report, 126, "3264.000000 0 4416.000000");
    BalticNativeDryPoint(report, 127, "3264.000000 0 4800.000000");
}

static void BalticNativeDryChunk4(FileHandle report)
{
    BalticNativeDryPoint(report, 128, "3264.000000 0 5184.000000");
    BalticNativeDryPoint(report, 129, "3264.000000 0 5952.000000");
    BalticNativeDryPoint(report, 130, "3264.000000 0 6336.000000");
    BalticNativeDryPoint(report, 131, "3264.000000 0 7104.000000");
    BalticNativeDryPoint(report, 132, "3264.000000 0 7488.000000");
    BalticNativeDryPoint(report, 133, "3264.000000 0 7872.000000");
    BalticNativeDryPoint(report, 134, "3264.000000 0 8640.000000");
    BalticNativeDryPoint(report, 135, "3264.000000 0 9024.000000");
    BalticNativeDryPoint(report, 136, "3264.000000 0 9408.000000");
    BalticNativeDryPoint(report, 137, "3402.000000 0 6672.000000");
    BalticNativeDryPoint(report, 138, "3522.000000 0 6672.000000");
    BalticNativeDryPoint(report, 139, "3522.000000 0 7152.000000");
    BalticNativeDryPoint(report, 140, "3642.000000 0 6912.000000");
    BalticNativeDryPoint(report, 141, "3642.000000 0 7032.000000");
    BalticNativeDryPoint(report, 142, "3642.000000 0 7152.000000");
    BalticNativeDryPoint(report, 143, "3648.000000 0 192.000000");
    BalticNativeDryPoint(report, 144, "3648.000000 0 576.000000");
    BalticNativeDryPoint(report, 145, "3648.000000 0 960.000000");
    BalticNativeDryPoint(report, 146, "3648.000000 0 1344.000000");
    BalticNativeDryPoint(report, 147, "3648.000000 0 1728.000000");
    BalticNativeDryPoint(report, 148, "3648.000000 0 2112.000000");
    BalticNativeDryPoint(report, 149, "3648.000000 0 2496.000000");
    BalticNativeDryPoint(report, 150, "3648.000000 0 2880.000000");
    BalticNativeDryPoint(report, 151, "3648.000000 0 3264.000000");
    BalticNativeDryPoint(report, 152, "3648.000000 0 3648.000000");
    BalticNativeDryPoint(report, 153, "3648.000000 0 4032.000000");
    BalticNativeDryPoint(report, 154, "3648.000000 0 4416.000000");
    BalticNativeDryPoint(report, 155, "3648.000000 0 4800.000000");
    BalticNativeDryPoint(report, 156, "3648.000000 0 5184.000000");
    BalticNativeDryPoint(report, 157, "3648.000000 0 5568.000000");
    BalticNativeDryPoint(report, 158, "3648.000000 0 5952.000000");
    BalticNativeDryPoint(report, 159, "3648.000000 0 6336.000000");
}

static void BalticNativeDryChunk5(FileHandle report)
{
    BalticNativeDryPoint(report, 160, "3648.000000 0 7104.000000");
    BalticNativeDryPoint(report, 161, "3648.000000 0 7488.000000");
    BalticNativeDryPoint(report, 162, "3648.000000 0 7872.000000");
    BalticNativeDryPoint(report, 163, "3648.000000 0 8640.000000");
    BalticNativeDryPoint(report, 164, "3648.000000 0 9024.000000");
    BalticNativeDryPoint(report, 165, "3648.000000 0 9408.000000");
    BalticNativeDryPoint(report, 166, "3762.000000 0 6672.000000");
    BalticNativeDryPoint(report, 167, "3762.000000 0 6792.000000");
    BalticNativeDryPoint(report, 168, "3762.000000 0 6912.000000");
    BalticNativeDryPoint(report, 169, "3762.000000 0 7032.000000");
    BalticNativeDryPoint(report, 170, "3762.000000 0 7152.000000");
    BalticNativeDryPoint(report, 171, "3882.000000 0 6672.000000");
    BalticNativeDryPoint(report, 172, "3882.000000 0 6792.000000");
    BalticNativeDryPoint(report, 173, "3882.000000 0 6912.000000");
    BalticNativeDryPoint(report, 174, "3882.000000 0 7032.000000");
    BalticNativeDryPoint(report, 175, "3882.000000 0 7152.000000");
    BalticNativeDryPoint(report, 176, "4032.000000 0 192.000000");
    BalticNativeDryPoint(report, 177, "4032.000000 0 960.000000");
    BalticNativeDryPoint(report, 178, "4032.000000 0 1344.000000");
    BalticNativeDryPoint(report, 179, "4032.000000 0 1728.000000");
    BalticNativeDryPoint(report, 180, "4032.000000 0 2112.000000");
    BalticNativeDryPoint(report, 181, "4032.000000 0 2496.000000");
    BalticNativeDryPoint(report, 182, "4032.000000 0 3264.000000");
    BalticNativeDryPoint(report, 183, "4032.000000 0 3648.000000");
    BalticNativeDryPoint(report, 184, "4032.000000 0 4800.000000");
    BalticNativeDryPoint(report, 185, "4032.000000 0 5184.000000");
    BalticNativeDryPoint(report, 186, "4032.000000 0 5568.000000");
    BalticNativeDryPoint(report, 187, "4032.000000 0 5952.000000");
    BalticNativeDryPoint(report, 188, "4032.000000 0 6336.000000");
    BalticNativeDryPoint(report, 189, "4032.000000 0 6720.000000");
    BalticNativeDryPoint(report, 190, "4032.000000 0 7104.000000");
    BalticNativeDryPoint(report, 191, "4032.000000 0 7488.000000");
}

static void BalticNativeDryChunk6(FileHandle report)
{
    BalticNativeDryPoint(report, 192, "4032.000000 0 7872.000000");
    BalticNativeDryPoint(report, 193, "4032.000000 0 8256.000000");
    BalticNativeDryPoint(report, 194, "4032.000000 0 8640.000000");
    BalticNativeDryPoint(report, 195, "4416.000000 0 192.000000");
    BalticNativeDryPoint(report, 196, "4416.000000 0 576.000000");
    BalticNativeDryPoint(report, 197, "4416.000000 0 960.000000");
    BalticNativeDryPoint(report, 198, "4416.000000 0 1344.000000");
    BalticNativeDryPoint(report, 199, "4416.000000 0 1728.000000");
    BalticNativeDryPoint(report, 200, "4416.000000 0 2112.000000");
    BalticNativeDryPoint(report, 201, "4416.000000 0 2496.000000");
    BalticNativeDryPoint(report, 202, "4416.000000 0 2880.000000");
    BalticNativeDryPoint(report, 203, "4416.000000 0 3264.000000");
    BalticNativeDryPoint(report, 204, "4416.000000 0 5184.000000");
    BalticNativeDryPoint(report, 205, "4416.000000 0 5568.000000");
    BalticNativeDryPoint(report, 206, "4416.000000 0 5952.000000");
    BalticNativeDryPoint(report, 207, "4416.000000 0 6336.000000");
    BalticNativeDryPoint(report, 208, "4416.000000 0 6720.000000");
    BalticNativeDryPoint(report, 209, "4416.000000 0 7104.000000");
    BalticNativeDryPoint(report, 210, "4416.000000 0 7488.000000");
    BalticNativeDryPoint(report, 211, "4416.000000 0 7872.000000");
    BalticNativeDryPoint(report, 212, "4416.000000 0 8256.000000");
    BalticNativeDryPoint(report, 213, "4416.000000 0 8640.000000");
    BalticNativeDryPoint(report, 214, "4416.000000 0 9024.000000");
    BalticNativeDryPoint(report, 215, "4800.000000 0 192.000000");
    BalticNativeDryPoint(report, 216, "4800.000000 0 1728.000000");
    BalticNativeDryPoint(report, 217, "4800.000000 0 2112.000000");
    BalticNativeDryPoint(report, 218, "4800.000000 0 2496.000000");
    BalticNativeDryPoint(report, 219, "4800.000000 0 2880.000000");
    BalticNativeDryPoint(report, 220, "4800.000000 0 3264.000000");
    BalticNativeDryPoint(report, 221, "4800.000000 0 4032.000000");
    BalticNativeDryPoint(report, 222, "4800.000000 0 4416.000000");
    BalticNativeDryPoint(report, 223, "4800.000000 0 4800.000000");
}

static void BalticNativeDryChunk7(FileHandle report)
{
    BalticNativeDryPoint(report, 224, "4800.000000 0 5184.000000");
    BalticNativeDryPoint(report, 225, "4800.000000 0 5568.000000");
    BalticNativeDryPoint(report, 226, "4800.000000 0 5952.000000");
    BalticNativeDryPoint(report, 227, "4800.000000 0 6336.000000");
    BalticNativeDryPoint(report, 228, "4800.000000 0 6720.000000");
    BalticNativeDryPoint(report, 229, "4800.000000 0 7104.000000");
    BalticNativeDryPoint(report, 230, "4800.000000 0 7488.000000");
    BalticNativeDryPoint(report, 231, "4800.000000 0 7872.000000");
    BalticNativeDryPoint(report, 232, "4800.000000 0 8256.000000");
    BalticNativeDryPoint(report, 233, "4800.000000 0 8640.000000");
    BalticNativeDryPoint(report, 234, "4800.000000 0 9024.000000");
    BalticNativeDryPoint(report, 235, "4800.000000 0 9408.000000");
    BalticNativeDryPoint(report, 236, "4800.000000 0 12096.000000");
    BalticNativeDryPoint(report, 237, "4896.000000 0 10002.000000");
    BalticNativeDryPoint(report, 238, "5016.000000 0 9522.000000");
    BalticNativeDryPoint(report, 239, "5016.000000 0 9642.000000");
    BalticNativeDryPoint(report, 240, "5016.000000 0 9762.000000");
    BalticNativeDryPoint(report, 241, "5016.000000 0 10002.000000");
    BalticNativeDryPoint(report, 242, "5136.000000 0 9522.000000");
    BalticNativeDryPoint(report, 243, "5136.000000 0 9642.000000");
    BalticNativeDryPoint(report, 244, "5136.000000 0 9882.000000");
    BalticNativeDryPoint(report, 245, "5184.000000 0 192.000000");
    BalticNativeDryPoint(report, 246, "5184.000000 0 576.000000");
    BalticNativeDryPoint(report, 247, "5184.000000 0 960.000000");
    BalticNativeDryPoint(report, 248, "5184.000000 0 1344.000000");
    BalticNativeDryPoint(report, 249, "5184.000000 0 1728.000000");
    BalticNativeDryPoint(report, 250, "5184.000000 0 2112.000000");
    BalticNativeDryPoint(report, 251, "5184.000000 0 2496.000000");
    BalticNativeDryPoint(report, 252, "5184.000000 0 2880.000000");
    BalticNativeDryPoint(report, 253, "5184.000000 0 3264.000000");
    BalticNativeDryPoint(report, 254, "5184.000000 0 4032.000000");
    BalticNativeDryPoint(report, 255, "5184.000000 0 4416.000000");
}

static void BalticNativeDryChunk8(FileHandle report)
{
    BalticNativeDryPoint(report, 256, "5184.000000 0 4800.000000");
    BalticNativeDryPoint(report, 257, "5184.000000 0 5184.000000");
    BalticNativeDryPoint(report, 258, "5184.000000 0 5568.000000");
    BalticNativeDryPoint(report, 259, "5184.000000 0 5952.000000");
    BalticNativeDryPoint(report, 260, "5184.000000 0 6336.000000");
    BalticNativeDryPoint(report, 261, "5184.000000 0 7104.000000");
    BalticNativeDryPoint(report, 262, "5184.000000 0 7488.000000");
    BalticNativeDryPoint(report, 263, "5184.000000 0 7872.000000");
    BalticNativeDryPoint(report, 264, "5184.000000 0 8256.000000");
    BalticNativeDryPoint(report, 265, "5184.000000 0 8640.000000");
    BalticNativeDryPoint(report, 266, "5184.000000 0 9024.000000");
    BalticNativeDryPoint(report, 267, "5184.000000 0 9408.000000");
    BalticNativeDryPoint(report, 268, "5184.000000 0 10176.000000");
    BalticNativeDryPoint(report, 269, "5184.000000 0 11712.000000");
    BalticNativeDryPoint(report, 270, "5256.000000 0 9522.000000");
    BalticNativeDryPoint(report, 271, "5256.000000 0 9642.000000");
    BalticNativeDryPoint(report, 272, "5256.000000 0 10002.000000");
    BalticNativeDryPoint(report, 273, "5568.000000 0 192.000000");
    BalticNativeDryPoint(report, 274, "5568.000000 0 576.000000");
    BalticNativeDryPoint(report, 275, "5568.000000 0 960.000000");
    BalticNativeDryPoint(report, 276, "5568.000000 0 1344.000000");
    BalticNativeDryPoint(report, 277, "5568.000000 0 1728.000000");
    BalticNativeDryPoint(report, 278, "5568.000000 0 2112.000000");
    BalticNativeDryPoint(report, 279, "5568.000000 0 2496.000000");
    BalticNativeDryPoint(report, 280, "5568.000000 0 2880.000000");
    BalticNativeDryPoint(report, 281, "5568.000000 0 3264.000000");
    BalticNativeDryPoint(report, 282, "5568.000000 0 3648.000000");
    BalticNativeDryPoint(report, 283, "5568.000000 0 4032.000000");
    BalticNativeDryPoint(report, 284, "5568.000000 0 4416.000000");
    BalticNativeDryPoint(report, 285, "5568.000000 0 4800.000000");
    BalticNativeDryPoint(report, 286, "5568.000000 0 5184.000000");
    BalticNativeDryPoint(report, 287, "5568.000000 0 5568.000000");
}

static void BalticNativeDryChunk9(FileHandle report)
{
    BalticNativeDryPoint(report, 288, "5568.000000 0 5952.000000");
    BalticNativeDryPoint(report, 289, "5568.000000 0 6336.000000");
    BalticNativeDryPoint(report, 290, "5568.000000 0 6720.000000");
    BalticNativeDryPoint(report, 291, "5568.000000 0 7104.000000");
    BalticNativeDryPoint(report, 292, "5568.000000 0 7488.000000");
    BalticNativeDryPoint(report, 293, "5568.000000 0 7872.000000");
    BalticNativeDryPoint(report, 294, "5568.000000 0 8256.000000");
    BalticNativeDryPoint(report, 295, "5568.000000 0 8640.000000");
    BalticNativeDryPoint(report, 296, "5568.000000 0 9024.000000");
    BalticNativeDryPoint(report, 297, "5568.000000 0 9792.000000");
    BalticNativeDryPoint(report, 298, "5952.000000 0 192.000000");
    BalticNativeDryPoint(report, 299, "5952.000000 0 960.000000");
    BalticNativeDryPoint(report, 300, "5952.000000 0 1344.000000");
    BalticNativeDryPoint(report, 301, "5952.000000 0 1728.000000");
    BalticNativeDryPoint(report, 302, "5952.000000 0 2112.000000");
    BalticNativeDryPoint(report, 303, "5952.000000 0 2496.000000");
    BalticNativeDryPoint(report, 304, "5952.000000 0 2880.000000");
    BalticNativeDryPoint(report, 305, "5952.000000 0 3264.000000");
    BalticNativeDryPoint(report, 306, "5952.000000 0 3648.000000");
    BalticNativeDryPoint(report, 307, "5952.000000 0 4032.000000");
    BalticNativeDryPoint(report, 308, "5952.000000 0 4416.000000");
    BalticNativeDryPoint(report, 309, "5952.000000 0 4800.000000");
    BalticNativeDryPoint(report, 310, "5952.000000 0 5568.000000");
    BalticNativeDryPoint(report, 311, "5952.000000 0 5952.000000");
    BalticNativeDryPoint(report, 312, "5952.000000 0 6336.000000");
    BalticNativeDryPoint(report, 313, "5952.000000 0 6720.000000");
    BalticNativeDryPoint(report, 314, "5952.000000 0 7104.000000");
    BalticNativeDryPoint(report, 315, "5952.000000 0 7488.000000");
    BalticNativeDryPoint(report, 316, "5952.000000 0 8256.000000");
    BalticNativeDryPoint(report, 317, "5952.000000 0 8640.000000");
    BalticNativeDryPoint(report, 318, "5952.000000 0 9024.000000");
    BalticNativeDryPoint(report, 319, "5952.000000 0 9408.000000");
}

static void BalticNativeDryChunk10(FileHandle report)
{
    BalticNativeDryPoint(report, 320, "5952.000000 0 9792.000000");
    BalticNativeDryPoint(report, 321, "5952.000000 0 10176.000000");
    BalticNativeDryPoint(report, 322, "5952.000000 0 11712.000000");
    BalticNativeDryPoint(report, 323, "5952.000000 0 12096.000000");
    BalticNativeDryPoint(report, 324, "6336.000000 0 192.000000");
    BalticNativeDryPoint(report, 325, "6336.000000 0 576.000000");
    BalticNativeDryPoint(report, 326, "6336.000000 0 960.000000");
    BalticNativeDryPoint(report, 327, "6336.000000 0 1344.000000");
    BalticNativeDryPoint(report, 328, "6336.000000 0 1728.000000");
    BalticNativeDryPoint(report, 329, "6336.000000 0 2112.000000");
    BalticNativeDryPoint(report, 330, "6336.000000 0 2880.000000");
    BalticNativeDryPoint(report, 331, "6336.000000 0 3264.000000");
    BalticNativeDryPoint(report, 332, "6336.000000 0 3648.000000");
    BalticNativeDryPoint(report, 333, "6336.000000 0 4032.000000");
    BalticNativeDryPoint(report, 334, "6336.000000 0 4416.000000");
    BalticNativeDryPoint(report, 335, "6336.000000 0 4800.000000");
    BalticNativeDryPoint(report, 336, "6336.000000 0 5184.000000");
    BalticNativeDryPoint(report, 337, "6336.000000 0 5568.000000");
    BalticNativeDryPoint(report, 338, "6336.000000 0 5952.000000");
    BalticNativeDryPoint(report, 339, "6336.000000 0 7104.000000");
    BalticNativeDryPoint(report, 340, "6336.000000 0 7488.000000");
    BalticNativeDryPoint(report, 341, "6336.000000 0 7872.000000");
    BalticNativeDryPoint(report, 342, "6336.000000 0 8256.000000");
    BalticNativeDryPoint(report, 343, "6336.000000 0 9024.000000");
    BalticNativeDryPoint(report, 344, "6336.000000 0 9408.000000");
    BalticNativeDryPoint(report, 345, "6336.000000 0 9792.000000");
    BalticNativeDryPoint(report, 346, "6336.000000 0 10176.000000");
    BalticNativeDryPoint(report, 347, "6336.000000 0 11712.000000");
    BalticNativeDryPoint(report, 348, "6720.000000 0 192.000000");
    BalticNativeDryPoint(report, 349, "6720.000000 0 960.000000");
    BalticNativeDryPoint(report, 350, "6720.000000 0 1344.000000");
    BalticNativeDryPoint(report, 351, "6720.000000 0 1728.000000");
}

static void BalticNativeDryChunk11(FileHandle report)
{
    BalticNativeDryPoint(report, 352, "6720.000000 0 2112.000000");
    BalticNativeDryPoint(report, 353, "6720.000000 0 2496.000000");
    BalticNativeDryPoint(report, 354, "6720.000000 0 3648.000000");
    BalticNativeDryPoint(report, 355, "6720.000000 0 4032.000000");
    BalticNativeDryPoint(report, 356, "6720.000000 0 4416.000000");
    BalticNativeDryPoint(report, 357, "6720.000000 0 4800.000000");
    BalticNativeDryPoint(report, 358, "6720.000000 0 5184.000000");
    BalticNativeDryPoint(report, 359, "6720.000000 0 5568.000000");
    BalticNativeDryPoint(report, 360, "6720.000000 0 5952.000000");
    BalticNativeDryPoint(report, 361, "6720.000000 0 6336.000000");
    BalticNativeDryPoint(report, 362, "6720.000000 0 6720.000000");
    BalticNativeDryPoint(report, 363, "6720.000000 0 7104.000000");
    BalticNativeDryPoint(report, 364, "6720.000000 0 7488.000000");
    BalticNativeDryPoint(report, 365, "6720.000000 0 7872.000000");
    BalticNativeDryPoint(report, 366, "6720.000000 0 8256.000000");
    BalticNativeDryPoint(report, 367, "6720.000000 0 8640.000000");
    BalticNativeDryPoint(report, 368, "6720.000000 0 9024.000000");
    BalticNativeDryPoint(report, 369, "6720.000000 0 9408.000000");
    BalticNativeDryPoint(report, 370, "6720.000000 0 9792.000000");
    BalticNativeDryPoint(report, 371, "6720.000000 0 11712.000000");
    BalticNativeDryPoint(report, 372, "7026.000000 0 3108.000000");
    BalticNativeDryPoint(report, 373, "7026.000000 0 3348.000000");
    BalticNativeDryPoint(report, 374, "7104.000000 0 192.000000");
    BalticNativeDryPoint(report, 375, "7104.000000 0 960.000000");
    BalticNativeDryPoint(report, 376, "7104.000000 0 1344.000000");
    BalticNativeDryPoint(report, 377, "7104.000000 0 1728.000000");
    BalticNativeDryPoint(report, 378, "7104.000000 0 2112.000000");
    BalticNativeDryPoint(report, 379, "7104.000000 0 2496.000000");
    BalticNativeDryPoint(report, 380, "7104.000000 0 2880.000000");
    BalticNativeDryPoint(report, 381, "7104.000000 0 3264.000000");
    BalticNativeDryPoint(report, 382, "7104.000000 0 3648.000000");
    BalticNativeDryPoint(report, 383, "7104.000000 0 4032.000000");
}

static void BalticNativeDryChunk12(FileHandle report)
{
    BalticNativeDryPoint(report, 384, "7104.000000 0 4800.000000");
    BalticNativeDryPoint(report, 385, "7104.000000 0 5184.000000");
    BalticNativeDryPoint(report, 386, "7104.000000 0 5952.000000");
    BalticNativeDryPoint(report, 387, "7104.000000 0 6336.000000");
    BalticNativeDryPoint(report, 388, "7104.000000 0 7104.000000");
    BalticNativeDryPoint(report, 389, "7104.000000 0 7872.000000");
    BalticNativeDryPoint(report, 390, "7104.000000 0 8256.000000");
    BalticNativeDryPoint(report, 391, "7104.000000 0 8640.000000");
    BalticNativeDryPoint(report, 392, "7104.000000 0 9024.000000");
    BalticNativeDryPoint(report, 393, "7104.000000 0 9408.000000");
    BalticNativeDryPoint(report, 394, "7104.000000 0 9792.000000");
    BalticNativeDryPoint(report, 395, "7104.000000 0 11712.000000");
    BalticNativeDryPoint(report, 396, "7104.000000 0 12096.000000");
    BalticNativeDryPoint(report, 397, "7146.000000 0 2988.000000");
    BalticNativeDryPoint(report, 398, "7266.000000 0 3108.000000");
    BalticNativeDryPoint(report, 399, "7266.000000 0 3348.000000");
    BalticNativeDryPoint(report, 400, "7290.000000 0 4560.000000");
    BalticNativeDryPoint(report, 401, "7290.000000 0 4680.000000");
    BalticNativeDryPoint(report, 402, "7290.000000 0 4800.000000");
    BalticNativeDryPoint(report, 403, "7290.000000 0 4920.000000");
    BalticNativeDryPoint(report, 404, "7290.000000 0 5040.000000");
    BalticNativeDryPoint(report, 405, "7386.000000 0 2988.000000");
    BalticNativeDryPoint(report, 406, "7386.000000 0 3108.000000");
    BalticNativeDryPoint(report, 407, "7386.000000 0 3228.000000");
    BalticNativeDryPoint(report, 408, "7386.000000 0 3348.000000");
    BalticNativeDryPoint(report, 409, "7386.000000 0 3468.000000");
    BalticNativeDryPoint(report, 410, "7410.000000 0 4560.000000");
    BalticNativeDryPoint(report, 411, "7410.000000 0 4680.000000");
    BalticNativeDryPoint(report, 412, "7410.000000 0 4800.000000");
    BalticNativeDryPoint(report, 413, "7410.000000 0 5040.000000");
    BalticNativeDryPoint(report, 414, "7488.000000 0 192.000000");
    BalticNativeDryPoint(report, 415, "7488.000000 0 576.000000");
}

static void BalticNativeDryChunk13(FileHandle report)
{
    BalticNativeDryPoint(report, 416, "7488.000000 0 960.000000");
    BalticNativeDryPoint(report, 417, "7488.000000 0 1344.000000");
    BalticNativeDryPoint(report, 418, "7488.000000 0 1728.000000");
    BalticNativeDryPoint(report, 419, "7488.000000 0 2112.000000");
    BalticNativeDryPoint(report, 420, "7488.000000 0 2496.000000");
    BalticNativeDryPoint(report, 421, "7488.000000 0 2880.000000");
    BalticNativeDryPoint(report, 422, "7488.000000 0 3264.000000");
    BalticNativeDryPoint(report, 423, "7488.000000 0 3648.000000");
    BalticNativeDryPoint(report, 424, "7488.000000 0 4416.000000");
    BalticNativeDryPoint(report, 425, "7488.000000 0 4800.000000");
    BalticNativeDryPoint(report, 426, "7488.000000 0 5184.000000");
    BalticNativeDryPoint(report, 427, "7488.000000 0 5568.000000");
    BalticNativeDryPoint(report, 428, "7488.000000 0 5952.000000");
    BalticNativeDryPoint(report, 429, "7488.000000 0 6336.000000");
    BalticNativeDryPoint(report, 430, "7488.000000 0 7104.000000");
    BalticNativeDryPoint(report, 431, "7488.000000 0 7488.000000");
    BalticNativeDryPoint(report, 432, "7488.000000 0 8256.000000");
    BalticNativeDryPoint(report, 433, "7488.000000 0 8640.000000");
    BalticNativeDryPoint(report, 434, "7488.000000 0 9024.000000");
    BalticNativeDryPoint(report, 435, "7488.000000 0 9408.000000");
    BalticNativeDryPoint(report, 436, "7488.000000 0 12096.000000");
    BalticNativeDryPoint(report, 437, "7506.000000 0 3108.000000");
    BalticNativeDryPoint(report, 438, "7506.000000 0 3348.000000");
    BalticNativeDryPoint(report, 439, "7506.000000 0 3468.000000");
    BalticNativeDryPoint(report, 440, "7530.000000 0 4560.000000");
    BalticNativeDryPoint(report, 441, "7530.000000 0 4680.000000");
    BalticNativeDryPoint(report, 442, "7530.000000 0 4920.000000");
    BalticNativeDryPoint(report, 443, "7530.000000 0 5040.000000");
    BalticNativeDryPoint(report, 444, "7650.000000 0 4560.000000");
    BalticNativeDryPoint(report, 445, "7650.000000 0 5040.000000");
    BalticNativeDryPoint(report, 446, "7770.000000 0 4560.000000");
    BalticNativeDryPoint(report, 447, "7770.000000 0 4680.000000");
}

static void BalticNativeDryChunk14(FileHandle report)
{
    BalticNativeDryPoint(report, 448, "7770.000000 0 4800.000000");
    BalticNativeDryPoint(report, 449, "7770.000000 0 5040.000000");
    BalticNativeDryPoint(report, 450, "7866.000000 0 7932.000000");
    BalticNativeDryPoint(report, 451, "7866.000000 0 8052.000000");
    BalticNativeDryPoint(report, 452, "7866.000000 0 8172.000000");
    BalticNativeDryPoint(report, 453, "7872.000000 0 192.000000");
    BalticNativeDryPoint(report, 454, "7872.000000 0 576.000000");
    BalticNativeDryPoint(report, 455, "7872.000000 0 960.000000");
    BalticNativeDryPoint(report, 456, "7872.000000 0 1344.000000");
    BalticNativeDryPoint(report, 457, "7872.000000 0 2112.000000");
    BalticNativeDryPoint(report, 458, "7872.000000 0 2496.000000");
    BalticNativeDryPoint(report, 459, "7872.000000 0 3264.000000");
    BalticNativeDryPoint(report, 460, "7872.000000 0 4032.000000");
    BalticNativeDryPoint(report, 461, "7872.000000 0 4416.000000");
    BalticNativeDryPoint(report, 462, "7872.000000 0 4800.000000");
    BalticNativeDryPoint(report, 463, "7872.000000 0 5184.000000");
    BalticNativeDryPoint(report, 464, "7872.000000 0 5568.000000");
    BalticNativeDryPoint(report, 465, "7872.000000 0 5952.000000");
    BalticNativeDryPoint(report, 466, "7872.000000 0 7104.000000");
    BalticNativeDryPoint(report, 467, "7872.000000 0 7488.000000");
    BalticNativeDryPoint(report, 468, "7872.000000 0 8640.000000");
    BalticNativeDryPoint(report, 469, "7872.000000 0 9024.000000");
    BalticNativeDryPoint(report, 470, "7872.000000 0 9408.000000");
    BalticNativeDryPoint(report, 471, "7872.000000 0 10560.000000");
    BalticNativeDryPoint(report, 472, "7872.000000 0 10944.000000");
    BalticNativeDryPoint(report, 473, "7872.000000 0 11712.000000");
    BalticNativeDryPoint(report, 474, "7872.000000 0 12096.000000");
    BalticNativeDryPoint(report, 475, "7986.000000 0 7932.000000");
    BalticNativeDryPoint(report, 476, "7986.000000 0 8292.000000");
    BalticNativeDryPoint(report, 477, "8106.000000 0 8172.000000");
    BalticNativeDryPoint(report, 478, "8106.000000 0 8292.000000");
    BalticNativeDryPoint(report, 479, "8226.000000 0 7812.000000");
}

static void BalticNativeDryChunk15(FileHandle report)
{
    BalticNativeDryPoint(report, 480, "8226.000000 0 8292.000000");
    BalticNativeDryPoint(report, 481, "8256.000000 0 192.000000");
    BalticNativeDryPoint(report, 482, "8256.000000 0 576.000000");
    BalticNativeDryPoint(report, 483, "8256.000000 0 960.000000");
    BalticNativeDryPoint(report, 484, "8256.000000 0 1344.000000");
    BalticNativeDryPoint(report, 485, "8256.000000 0 1728.000000");
    BalticNativeDryPoint(report, 486, "8256.000000 0 2112.000000");
    BalticNativeDryPoint(report, 487, "8256.000000 0 2496.000000");
    BalticNativeDryPoint(report, 488, "8256.000000 0 3264.000000");
    BalticNativeDryPoint(report, 489, "8256.000000 0 3648.000000");
    BalticNativeDryPoint(report, 490, "8256.000000 0 5952.000000");
    BalticNativeDryPoint(report, 491, "8256.000000 0 6336.000000");
    BalticNativeDryPoint(report, 492, "8256.000000 0 7104.000000");
    BalticNativeDryPoint(report, 493, "8256.000000 0 7872.000000");
    BalticNativeDryPoint(report, 494, "8256.000000 0 8256.000000");
    BalticNativeDryPoint(report, 495, "8256.000000 0 8640.000000");
    BalticNativeDryPoint(report, 496, "8256.000000 0 9024.000000");
    BalticNativeDryPoint(report, 497, "8256.000000 0 11328.000000");
    BalticNativeDryPoint(report, 498, "8256.000000 0 12096.000000");
    BalticNativeDryPoint(report, 499, "8346.000000 0 7932.000000");
    BalticNativeDryPoint(report, 500, "8346.000000 0 8172.000000");
    BalticNativeDryPoint(report, 501, "8640.000000 0 576.000000");
    BalticNativeDryPoint(report, 502, "8640.000000 0 960.000000");
    BalticNativeDryPoint(report, 503, "8640.000000 0 1344.000000");
    BalticNativeDryPoint(report, 504, "8640.000000 0 1728.000000");
    BalticNativeDryPoint(report, 505, "8640.000000 0 2112.000000");
    BalticNativeDryPoint(report, 506, "8640.000000 0 2496.000000");
    BalticNativeDryPoint(report, 507, "8640.000000 0 2880.000000");
    BalticNativeDryPoint(report, 508, "8640.000000 0 3264.000000");
    BalticNativeDryPoint(report, 509, "8640.000000 0 3648.000000");
    BalticNativeDryPoint(report, 510, "8640.000000 0 4032.000000");
    BalticNativeDryPoint(report, 511, "8640.000000 0 4800.000000");
}

static void BalticNativeDryChunk16(FileHandle report)
{
    BalticNativeDryPoint(report, 512, "8640.000000 0 5184.000000");
    BalticNativeDryPoint(report, 513, "8640.000000 0 5568.000000");
    BalticNativeDryPoint(report, 514, "8640.000000 0 5952.000000");
    BalticNativeDryPoint(report, 515, "8640.000000 0 6336.000000");
    BalticNativeDryPoint(report, 516, "8640.000000 0 6720.000000");
    BalticNativeDryPoint(report, 517, "8640.000000 0 7488.000000");
    BalticNativeDryPoint(report, 518, "8640.000000 0 7872.000000");
    BalticNativeDryPoint(report, 519, "8640.000000 0 8256.000000");
    BalticNativeDryPoint(report, 520, "8640.000000 0 8640.000000");
    BalticNativeDryPoint(report, 521, "8640.000000 0 9408.000000");
    BalticNativeDryPoint(report, 522, "8640.000000 0 9792.000000");
    BalticNativeDryPoint(report, 523, "8640.000000 0 10944.000000");
    BalticNativeDryPoint(report, 524, "8640.000000 0 11328.000000");
    BalticNativeDryPoint(report, 525, "8640.000000 0 11712.000000");
    BalticNativeDryPoint(report, 526, "8640.000000 0 12096.000000");
    BalticNativeDryPoint(report, 527, "8658.000000 0 9882.000000");
    BalticNativeDryPoint(report, 528, "8778.000000 0 9882.000000");
    BalticNativeDryPoint(report, 529, "8778.000000 0 10122.000000");
    BalticNativeDryPoint(report, 530, "8778.000000 0 10362.000000");
    BalticNativeDryPoint(report, 531, "8898.000000 0 10362.000000");
    BalticNativeDryPoint(report, 532, "9018.000000 0 10002.000000");
    BalticNativeDryPoint(report, 533, "9018.000000 0 10122.000000");
    BalticNativeDryPoint(report, 534, "9018.000000 0 10242.000000");
    BalticNativeDryPoint(report, 535, "9024.000000 0 192.000000");
    BalticNativeDryPoint(report, 536, "9024.000000 0 576.000000");
    BalticNativeDryPoint(report, 537, "9024.000000 0 960.000000");
    BalticNativeDryPoint(report, 538, "9024.000000 0 1344.000000");
    BalticNativeDryPoint(report, 539, "9024.000000 0 1728.000000");
    BalticNativeDryPoint(report, 540, "9024.000000 0 2112.000000");
    BalticNativeDryPoint(report, 541, "9024.000000 0 2880.000000");
    BalticNativeDryPoint(report, 542, "9024.000000 0 3648.000000");
    BalticNativeDryPoint(report, 543, "9024.000000 0 4032.000000");
}

static void BalticNativeDryChunk17(FileHandle report)
{
    BalticNativeDryPoint(report, 544, "9024.000000 0 4416.000000");
    BalticNativeDryPoint(report, 545, "9024.000000 0 4800.000000");
    BalticNativeDryPoint(report, 546, "9024.000000 0 5568.000000");
    BalticNativeDryPoint(report, 547, "9024.000000 0 6336.000000");
    BalticNativeDryPoint(report, 548, "9024.000000 0 6720.000000");
    BalticNativeDryPoint(report, 549, "9024.000000 0 7488.000000");
    BalticNativeDryPoint(report, 550, "9024.000000 0 7872.000000");
    BalticNativeDryPoint(report, 551, "9024.000000 0 8256.000000");
    BalticNativeDryPoint(report, 552, "9024.000000 0 9024.000000");
    BalticNativeDryPoint(report, 553, "9024.000000 0 10944.000000");
    BalticNativeDryPoint(report, 554, "9024.000000 0 11712.000000");
    BalticNativeDryPoint(report, 555, "9024.000000 0 12096.000000");
    BalticNativeDryPoint(report, 556, "9408.000000 0 192.000000");
    BalticNativeDryPoint(report, 557, "9408.000000 0 576.000000");
    BalticNativeDryPoint(report, 558, "9408.000000 0 960.000000");
    BalticNativeDryPoint(report, 559, "9408.000000 0 1344.000000");
    BalticNativeDryPoint(report, 560, "9408.000000 0 1728.000000");
    BalticNativeDryPoint(report, 561, "9408.000000 0 2112.000000");
    BalticNativeDryPoint(report, 562, "9408.000000 0 2496.000000");
    BalticNativeDryPoint(report, 563, "9408.000000 0 2880.000000");
    BalticNativeDryPoint(report, 564, "9408.000000 0 3264.000000");
    BalticNativeDryPoint(report, 565, "9408.000000 0 3648.000000");
    BalticNativeDryPoint(report, 566, "9408.000000 0 4032.000000");
    BalticNativeDryPoint(report, 567, "9408.000000 0 4800.000000");
    BalticNativeDryPoint(report, 568, "9408.000000 0 5184.000000");
    BalticNativeDryPoint(report, 569, "9408.000000 0 5568.000000");
    BalticNativeDryPoint(report, 570, "9408.000000 0 5952.000000");
    BalticNativeDryPoint(report, 571, "9408.000000 0 6336.000000");
    BalticNativeDryPoint(report, 572, "9408.000000 0 6720.000000");
    BalticNativeDryPoint(report, 573, "9408.000000 0 7104.000000");
    BalticNativeDryPoint(report, 574, "9408.000000 0 7488.000000");
    BalticNativeDryPoint(report, 575, "9408.000000 0 7872.000000");
}

static void BalticNativeDryChunk18(FileHandle report)
{
    BalticNativeDryPoint(report, 576, "9408.000000 0 8256.000000");
    BalticNativeDryPoint(report, 577, "9408.000000 0 9024.000000");
    BalticNativeDryPoint(report, 578, "9408.000000 0 9792.000000");
    BalticNativeDryPoint(report, 579, "9408.000000 0 10176.000000");
    BalticNativeDryPoint(report, 580, "9408.000000 0 10944.000000");
    BalticNativeDryPoint(report, 581, "9408.000000 0 11328.000000");
    BalticNativeDryPoint(report, 582, "9408.000000 0 11712.000000");
    BalticNativeDryPoint(report, 583, "9792.000000 0 576.000000");
    BalticNativeDryPoint(report, 584, "9792.000000 0 960.000000");
    BalticNativeDryPoint(report, 585, "9792.000000 0 1344.000000");
    BalticNativeDryPoint(report, 586, "9792.000000 0 1728.000000");
    BalticNativeDryPoint(report, 587, "9792.000000 0 2112.000000");
    BalticNativeDryPoint(report, 588, "9792.000000 0 2496.000000");
    BalticNativeDryPoint(report, 589, "9792.000000 0 2880.000000");
    BalticNativeDryPoint(report, 590, "9792.000000 0 3264.000000");
    BalticNativeDryPoint(report, 591, "9792.000000 0 3648.000000");
    BalticNativeDryPoint(report, 592, "9792.000000 0 4032.000000");
    BalticNativeDryPoint(report, 593, "9792.000000 0 4416.000000");
    BalticNativeDryPoint(report, 594, "9792.000000 0 4800.000000");
    BalticNativeDryPoint(report, 595, "9792.000000 0 5568.000000");
    BalticNativeDryPoint(report, 596, "9792.000000 0 5952.000000");
    BalticNativeDryPoint(report, 597, "9792.000000 0 6336.000000");
    BalticNativeDryPoint(report, 598, "9792.000000 0 6720.000000");
    BalticNativeDryPoint(report, 599, "9792.000000 0 7104.000000");
    BalticNativeDryPoint(report, 600, "9792.000000 0 7488.000000");
    BalticNativeDryPoint(report, 601, "9792.000000 0 8256.000000");
    BalticNativeDryPoint(report, 602, "9792.000000 0 9024.000000");
    BalticNativeDryPoint(report, 603, "9792.000000 0 9408.000000");
    BalticNativeDryPoint(report, 604, "9792.000000 0 9792.000000");
    BalticNativeDryPoint(report, 605, "9792.000000 0 10176.000000");
    BalticNativeDryPoint(report, 606, "9792.000000 0 10560.000000");
    BalticNativeDryPoint(report, 607, "9792.000000 0 10944.000000");
}

static void BalticNativeDryChunk19(FileHandle report)
{
    BalticNativeDryPoint(report, 608, "9792.000000 0 11328.000000");
    BalticNativeDryPoint(report, 609, "9792.000000 0 11712.000000");
    BalticNativeDryPoint(report, 610, "9792.000000 0 12096.000000");
    BalticNativeDryPoint(report, 611, "10062.000000 0 7602.000000");
    BalticNativeDryPoint(report, 612, "10062.000000 0 7722.000000");
    BalticNativeDryPoint(report, 613, "10062.000000 0 7842.000000");
    BalticNativeDryPoint(report, 614, "10062.000000 0 7962.000000");
    BalticNativeDryPoint(report, 615, "10062.000000 0 8082.000000");
    BalticNativeDryPoint(report, 616, "10176.000000 0 192.000000");
    BalticNativeDryPoint(report, 617, "10176.000000 0 576.000000");
    BalticNativeDryPoint(report, 618, "10176.000000 0 1344.000000");
    BalticNativeDryPoint(report, 619, "10176.000000 0 1728.000000");
    BalticNativeDryPoint(report, 620, "10176.000000 0 2112.000000");
    BalticNativeDryPoint(report, 621, "10176.000000 0 2880.000000");
    BalticNativeDryPoint(report, 622, "10176.000000 0 3648.000000");
    BalticNativeDryPoint(report, 623, "10176.000000 0 4032.000000");
    BalticNativeDryPoint(report, 624, "10176.000000 0 4416.000000");
    BalticNativeDryPoint(report, 625, "10176.000000 0 4800.000000");
    BalticNativeDryPoint(report, 626, "10176.000000 0 5184.000000");
    BalticNativeDryPoint(report, 627, "10176.000000 0 5568.000000");
    BalticNativeDryPoint(report, 628, "10176.000000 0 5952.000000");
    BalticNativeDryPoint(report, 629, "10176.000000 0 6336.000000");
    BalticNativeDryPoint(report, 630, "10176.000000 0 6720.000000");
    BalticNativeDryPoint(report, 631, "10176.000000 0 7104.000000");
    BalticNativeDryPoint(report, 632, "10176.000000 0 7488.000000");
    BalticNativeDryPoint(report, 633, "10176.000000 0 7872.000000");
    BalticNativeDryPoint(report, 634, "10176.000000 0 8256.000000");
    BalticNativeDryPoint(report, 635, "10176.000000 0 8640.000000");
    BalticNativeDryPoint(report, 636, "10176.000000 0 9792.000000");
    BalticNativeDryPoint(report, 637, "10176.000000 0 10176.000000");
    BalticNativeDryPoint(report, 638, "10176.000000 0 10560.000000");
    BalticNativeDryPoint(report, 639, "10176.000000 0 11328.000000");
}

static void BalticNativeDryChunk20(FileHandle report)
{
    BalticNativeDryPoint(report, 640, "10182.000000 0 7602.000000");
    BalticNativeDryPoint(report, 641, "10182.000000 0 7722.000000");
    BalticNativeDryPoint(report, 642, "10182.000000 0 7842.000000");
    BalticNativeDryPoint(report, 643, "10182.000000 0 8082.000000");
    BalticNativeDryPoint(report, 644, "10302.000000 0 7602.000000");
    BalticNativeDryPoint(report, 645, "10302.000000 0 7842.000000");
    BalticNativeDryPoint(report, 646, "10302.000000 0 8082.000000");
    BalticNativeDryPoint(report, 647, "10422.000000 0 7602.000000");
    BalticNativeDryPoint(report, 648, "10422.000000 0 7722.000000");
    BalticNativeDryPoint(report, 649, "10422.000000 0 7842.000000");
    BalticNativeDryPoint(report, 650, "10422.000000 0 7962.000000");
    BalticNativeDryPoint(report, 651, "10518.000000 0 9942.000000");
    BalticNativeDryPoint(report, 652, "10518.000000 0 10062.000000");
    BalticNativeDryPoint(report, 653, "10518.000000 0 10182.000000");
    BalticNativeDryPoint(report, 654, "10542.000000 0 7722.000000");
    BalticNativeDryPoint(report, 655, "10542.000000 0 7842.000000");
    BalticNativeDryPoint(report, 656, "10542.000000 0 7962.000000");
    BalticNativeDryPoint(report, 657, "10542.000000 0 8082.000000");
    BalticNativeDryPoint(report, 658, "10560.000000 0 192.000000");
    BalticNativeDryPoint(report, 659, "10560.000000 0 960.000000");
    BalticNativeDryPoint(report, 660, "10560.000000 0 1344.000000");
    BalticNativeDryPoint(report, 661, "10560.000000 0 1728.000000");
    BalticNativeDryPoint(report, 662, "10560.000000 0 2112.000000");
    BalticNativeDryPoint(report, 663, "10560.000000 0 2496.000000");
    BalticNativeDryPoint(report, 664, "10560.000000 0 3264.000000");
    BalticNativeDryPoint(report, 665, "10560.000000 0 4800.000000");
    BalticNativeDryPoint(report, 666, "10560.000000 0 5184.000000");
    BalticNativeDryPoint(report, 667, "10560.000000 0 5568.000000");
    BalticNativeDryPoint(report, 668, "10560.000000 0 5952.000000");
    BalticNativeDryPoint(report, 669, "10560.000000 0 6720.000000");
    BalticNativeDryPoint(report, 670, "10560.000000 0 7104.000000");
    BalticNativeDryPoint(report, 671, "10560.000000 0 7488.000000");
}

static void BalticNativeDryChunk21(FileHandle report)
{
    BalticNativeDryPoint(report, 672, "10560.000000 0 7872.000000");
    BalticNativeDryPoint(report, 673, "10560.000000 0 8256.000000");
    BalticNativeDryPoint(report, 674, "10560.000000 0 8640.000000");
    BalticNativeDryPoint(report, 675, "10560.000000 0 9024.000000");
    BalticNativeDryPoint(report, 676, "10560.000000 0 9408.000000");
    BalticNativeDryPoint(report, 677, "10560.000000 0 10560.000000");
    BalticNativeDryPoint(report, 678, "10560.000000 0 10944.000000");
    BalticNativeDryPoint(report, 679, "10758.000000 0 10062.000000");
    BalticNativeDryPoint(report, 680, "10944.000000 0 1344.000000");
    BalticNativeDryPoint(report, 681, "10944.000000 0 1728.000000");
    BalticNativeDryPoint(report, 682, "10944.000000 0 2112.000000");
    BalticNativeDryPoint(report, 683, "10944.000000 0 2496.000000");
    BalticNativeDryPoint(report, 684, "10944.000000 0 2880.000000");
    BalticNativeDryPoint(report, 685, "10944.000000 0 3264.000000");
    BalticNativeDryPoint(report, 686, "10944.000000 0 3648.000000");
    BalticNativeDryPoint(report, 687, "10944.000000 0 4032.000000");
    BalticNativeDryPoint(report, 688, "10944.000000 0 4416.000000");
    BalticNativeDryPoint(report, 689, "10944.000000 0 5184.000000");
    BalticNativeDryPoint(report, 690, "10944.000000 0 5568.000000");
    BalticNativeDryPoint(report, 691, "10944.000000 0 5952.000000");
    BalticNativeDryPoint(report, 692, "10944.000000 0 6336.000000");
    BalticNativeDryPoint(report, 693, "10944.000000 0 6720.000000");
    BalticNativeDryPoint(report, 694, "10944.000000 0 7104.000000");
    BalticNativeDryPoint(report, 695, "10944.000000 0 7488.000000");
    BalticNativeDryPoint(report, 696, "10944.000000 0 8256.000000");
    BalticNativeDryPoint(report, 697, "10944.000000 0 8640.000000");
    BalticNativeDryPoint(report, 698, "10944.000000 0 9024.000000");
    BalticNativeDryPoint(report, 699, "10944.000000 0 9408.000000");
    BalticNativeDryPoint(report, 700, "10944.000000 0 9792.000000");
    BalticNativeDryPoint(report, 701, "11328.000000 0 1728.000000");
    BalticNativeDryPoint(report, 702, "11328.000000 0 2112.000000");
    BalticNativeDryPoint(report, 703, "11328.000000 0 2880.000000");
}

static void BalticNativeDryChunk22(FileHandle report)
{
    BalticNativeDryPoint(report, 704, "11328.000000 0 3264.000000");
    BalticNativeDryPoint(report, 705, "11328.000000 0 3648.000000");
    BalticNativeDryPoint(report, 706, "11328.000000 0 4032.000000");
    BalticNativeDryPoint(report, 707, "11328.000000 0 4416.000000");
    BalticNativeDryPoint(report, 708, "11328.000000 0 4800.000000");
    BalticNativeDryPoint(report, 709, "11328.000000 0 5184.000000");
    BalticNativeDryPoint(report, 710, "11328.000000 0 5952.000000");
    BalticNativeDryPoint(report, 711, "11328.000000 0 6336.000000");
    BalticNativeDryPoint(report, 712, "11328.000000 0 7104.000000");
    BalticNativeDryPoint(report, 713, "11328.000000 0 7872.000000");
    BalticNativeDryPoint(report, 714, "11328.000000 0 9024.000000");
    BalticNativeDryPoint(report, 715, "11712.000000 0 1728.000000");
    BalticNativeDryPoint(report, 716, "11712.000000 0 2496.000000");
    BalticNativeDryPoint(report, 717, "11712.000000 0 2880.000000");
    BalticNativeDryPoint(report, 718, "11712.000000 0 3648.000000");
    BalticNativeDryPoint(report, 719, "11712.000000 0 4032.000000");
    BalticNativeDryPoint(report, 720, "11712.000000 0 4416.000000");
    BalticNativeDryPoint(report, 721, "11712.000000 0 4800.000000");
    BalticNativeDryPoint(report, 722, "11712.000000 0 5184.000000");
    BalticNativeDryPoint(report, 723, "11712.000000 0 5568.000000");
    BalticNativeDryPoint(report, 724, "11712.000000 0 5952.000000");
    BalticNativeDryPoint(report, 725, "11712.000000 0 6336.000000");
    BalticNativeDryPoint(report, 726, "11712.000000 0 6720.000000");
    BalticNativeDryPoint(report, 727, "11712.000000 0 7104.000000");
    BalticNativeDryPoint(report, 728, "11712.000000 0 7488.000000");
    BalticNativeDryPoint(report, 729, "11712.000000 0 7872.000000");
    BalticNativeDryPoint(report, 730, "11712.000000 0 8256.000000");
    BalticNativeDryPoint(report, 731, "11712.000000 0 9024.000000");
    BalticNativeDryPoint(report, 732, "11712.000000 0 9408.000000");
    BalticNativeDryPoint(report, 733, "12096.000000 0 2112.000000");
    BalticNativeDryPoint(report, 734, "12096.000000 0 2496.000000");
    BalticNativeDryPoint(report, 735, "12096.000000 0 3264.000000");
}

static void BalticNativeDryChunk23(FileHandle report)
{
    BalticNativeDryPoint(report, 736, "12096.000000 0 3648.000000");
    BalticNativeDryPoint(report, 737, "12096.000000 0 4032.000000");
    BalticNativeDryPoint(report, 738, "12096.000000 0 4416.000000");
    BalticNativeDryPoint(report, 739, "12096.000000 0 4800.000000");
    BalticNativeDryPoint(report, 740, "12096.000000 0 5184.000000");
    BalticNativeDryPoint(report, 741, "12096.000000 0 5568.000000");
    BalticNativeDryPoint(report, 742, "12096.000000 0 5952.000000");
    BalticNativeDryPoint(report, 743, "12096.000000 0 6336.000000");
    BalticNativeDryPoint(report, 744, "12096.000000 0 6720.000000");
    BalticNativeDryPoint(report, 745, "12096.000000 0 7104.000000");
    BalticNativeDryPoint(report, 746, "12096.000000 0 7488.000000");
    BalticNativeDryPoint(report, 747, "12096.000000 0 8256.000000");
    BalticNativeDryPoint(report, 748, "12096.000000 0 8640.000000");
    BalticNativeDryPoint(report, 749, "12096.000000 0 9024.000000");
    BalticNativeDryPoint(report, 750, "12096.000000 0 9408.000000");
}

static void BalticNativeNav()
{
    if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
    FileHandle report = OpenFile("$profile:baltic_native_nav_v1.log", FileMode.WRITE);
    if (!report) return;
    FPrintln(report, "BALTIC_NATIVE_NAV_V1");
    FPrintln(report, "world=" + GetGame().GetWorldName());
    PGFilter walk = new PGFilter;
    walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
    FPrintln(report, "flags=" + walk.GetIncludeFlags() + ";" + walk.GetExcludeFlags());
    BalticNavQuery("west_local", "2357.841205 0 6899.011058", "2367.724848 0 6897.490009", walk, report);
    BalticNavQuery("east_local", "2466.561284 0 6882.279522", "2476.444928 0 6880.758474", walk, report);
    BalticNavQuery("west_east", "2357.841205 0 6899.011058", "2476.444928 0 6880.758474", walk, report);
    BalticNavQuery("east_west", "2476.444928 0 6880.758474", "2357.841205 0 6899.011058", walk, report);
    PGFilter none = new PGFilter;
    none.SetFlags(PGPolyFlags.NONE, PGPolyFlags.ALL, PGPolyFlags.NONE);
    BalticNavQuery("negative_no_polygons", "2357.841205 0 6899.011058", "2476.444928 0 6880.758474", none, report);
    BalticNativeDryChunk0(report);
    BalticNativeDryChunk1(report);
    BalticNativeDryChunk2(report);
    BalticNativeDryChunk3(report);
    BalticNativeDryChunk4(report);
    BalticNativeDryChunk5(report);
    BalticNativeDryChunk6(report);
    BalticNativeDryChunk7(report);
    BalticNativeDryChunk8(report);
    BalticNativeDryChunk9(report);
    BalticNativeDryChunk10(report);
    BalticNativeDryChunk11(report);
    BalticNativeDryChunk12(report);
    BalticNativeDryChunk13(report);
    BalticNativeDryChunk14(report);
    BalticNativeDryChunk15(report);
    BalticNativeDryChunk16(report);
    BalticNativeDryChunk17(report);
    BalticNativeDryChunk18(report);
    BalticNativeDryChunk19(report);
    BalticNativeDryChunk20(report);
    BalticNativeDryChunk21(report);
    BalticNativeDryChunk22(report);
    BalticNativeDryChunk23(report);
    FPrintln(report, "BALTIC_NATIVE_NAV_COMPLETE");
    CloseFile(report);
    Print("BALTIC_NATIVE_NAV_COMPLETE_V1");
}
class BalticNativeNavMission: MissionServer
{
    override void OnInit()
    {
        super.OnInit();
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BalticNativeNav, 15000, false);
    }
    void ~BalticNativeNavMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BalticNativeNav);
    }
}
Mission CreateCustomMission(string path) { return new BalticNativeNavMission(); }
