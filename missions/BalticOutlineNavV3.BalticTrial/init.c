// Temporary server-only probe, no RPC, economy or actors.
// Verified local contracts: scripts/3_game/ai/aiworld.c:80,111,137;
// global/game.c:930,1162; global/world.c:119; 1_core/proto/ensystem.c:417,443,481.
void main() { Print("BALTIC_OUTLINE_NAV_MAIN_V3"); }
static void BalticOutlinePoint(FileHandle f, int index, vector requested, PGFilter filter)
{
    requested[1] = GetGame().SurfaceY(requested[0], requested[2]);
    vector sampled;
    bool ok = GetGame().GetWorld().GetAIWorld().SampleNavmeshPosition(requested, 2, filter, sampled);
    FPrintln(f, "D;" + index + ";" + requested + ";" + ok + ";" + sampled);
}
static void BalticOutlinePath(FileHandle f, string name, vector start, vector finish, PGFilter filter)
{
    AIWorld ai = GetGame().GetWorld().GetAIWorld();
    start[1] = GetGame().SurfaceY(start[0], start[2]);
    finish[1] = GetGame().SurfaceY(finish[0], finish[2]);
    vector a, b;
    bool sa = ai.SampleNavmeshPosition(start, 2, filter, a);
    bool sb = ai.SampleNavmeshPosition(finish, 2, filter, b);
    TVectorArray path = new TVectorArray;
    bool found = false;
    if (sa && sb) found = ai.FindPath(a, b, filter, path);
    FPrintln(f, "Q;" + name + ";" + sa + ";" + sb + ";" + found + ";" + path.Count());
    for (int i=0; i<path.Count(); i++) FPrintln(f, "P;" + name + ";" + i + ";" + path[i]);
}

static void BalticOutlineChunk0(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 0, "4896 0 11994", filter);
    BalticOutlinePoint(f, 1, "5472 0 11994", filter);
    BalticOutlinePoint(f, 2, "6048 0 11994", filter);
    BalticOutlinePoint(f, 3, "7200 0 11994", filter);
    BalticOutlinePoint(f, 4, "8352 0 11994", filter);
    BalticOutlinePoint(f, 5, "8928 0 11994", filter);
    BalticOutlinePoint(f, 6, "10080 0 11994", filter);
    BalticOutlinePoint(f, 7, "8928 0 11418", filter);
    BalticOutlinePoint(f, 8, "9504 0 11418", filter);
    BalticOutlinePoint(f, 9, "7776 0 10842", filter);
    BalticOutlinePoint(f, 10, "8352 0 10842", filter);
    BalticOutlinePoint(f, 11, "10080 0 10842", filter);
    BalticOutlinePoint(f, 12, "10656 0 10842", filter);
    BalticOutlinePoint(f, 13, "5472 0 10266", filter);
    BalticOutlinePoint(f, 14, "6048 0 10266", filter);
    BalticOutlinePoint(f, 15, "10080 0 10266", filter);
    BalticOutlinePoint(f, 16, "5472 0 9690", filter);
    BalticOutlinePoint(f, 17, "6048 0 9690", filter);
    BalticOutlinePoint(f, 18, "6624 0 9690", filter);
    BalticOutlinePoint(f, 19, "7200 0 9690", filter);
    BalticOutlinePoint(f, 20, "8352 0 9690", filter);
    BalticOutlinePoint(f, 21, "9504 0 9690", filter);
    BalticOutlinePoint(f, 22, "10080 0 9690", filter);
    BalticOutlinePoint(f, 23, "10656 0 9690", filter);
    BalticOutlinePoint(f, 24, "11808 0 9690", filter);
    BalticOutlinePoint(f, 25, "3168 0 9114", filter);
    BalticOutlinePoint(f, 26, "3744 0 9114", filter);
    BalticOutlinePoint(f, 27, "4320 0 9114", filter);
    BalticOutlinePoint(f, 28, "4896 0 9114", filter);
    BalticOutlinePoint(f, 29, "5472 0 9114", filter);
    BalticOutlinePoint(f, 30, "6048 0 9114", filter);
    BalticOutlinePoint(f, 31, "7200 0 9114", filter);
}

static void BalticOutlineChunk1(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 32, "7776 0 9114", filter);
    BalticOutlinePoint(f, 33, "8352 0 9114", filter);
    BalticOutlinePoint(f, 34, "8928 0 9114", filter);
    BalticOutlinePoint(f, 35, "11808 0 9114", filter);
    BalticOutlinePoint(f, 36, "2016 0 8538", filter);
    BalticOutlinePoint(f, 37, "3168 0 8538", filter);
    BalticOutlinePoint(f, 38, "4320 0 8538", filter);
    BalticOutlinePoint(f, 39, "4896 0 8538", filter);
    BalticOutlinePoint(f, 40, "5472 0 8538", filter);
    BalticOutlinePoint(f, 41, "6048 0 8538", filter);
    BalticOutlinePoint(f, 42, "6624 0 8538", filter);
    BalticOutlinePoint(f, 43, "7776 0 8538", filter);
    BalticOutlinePoint(f, 44, "9504 0 8538", filter);
    BalticOutlinePoint(f, 45, "10656 0 8538", filter);
    BalticOutlinePoint(f, 46, "11808 0 8538", filter);
    BalticOutlinePoint(f, 47, "2592 0 7962", filter);
    BalticOutlinePoint(f, 48, "3744 0 7962", filter);
    BalticOutlinePoint(f, 49, "4320 0 7962", filter);
    BalticOutlinePoint(f, 50, "4896 0 7962", filter);
    BalticOutlinePoint(f, 51, "5472 0 7962", filter);
    BalticOutlinePoint(f, 52, "6048 0 7962", filter);
    BalticOutlinePoint(f, 53, "6624 0 7962", filter);
    BalticOutlinePoint(f, 54, "7200 0 7962", filter);
    BalticOutlinePoint(f, 55, "7776 0 7962", filter);
    BalticOutlinePoint(f, 56, "8928 0 7962", filter);
    BalticOutlinePoint(f, 57, "9504 0 7962", filter);
    BalticOutlinePoint(f, 58, "10080 0 7962", filter);
    BalticOutlinePoint(f, 59, "10656 0 7962", filter);
    BalticOutlinePoint(f, 60, "11232 0 7962", filter);
    BalticOutlinePoint(f, 61, "11808 0 7962", filter);
    BalticOutlinePoint(f, 62, "3744 0 7386", filter);
    BalticOutlinePoint(f, 63, "4320 0 7386", filter);
}

static void BalticOutlineChunk2(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 64, "4896 0 7386", filter);
    BalticOutlinePoint(f, 65, "5472 0 7386", filter);
    BalticOutlinePoint(f, 66, "6048 0 7386", filter);
    BalticOutlinePoint(f, 67, "6624 0 7386", filter);
    BalticOutlinePoint(f, 68, "7776 0 7386", filter);
    BalticOutlinePoint(f, 69, "8352 0 7386", filter);
    BalticOutlinePoint(f, 70, "8928 0 7386", filter);
    BalticOutlinePoint(f, 71, "9504 0 7386", filter);
    BalticOutlinePoint(f, 72, "10080 0 7386", filter);
    BalticOutlinePoint(f, 73, "11232 0 7386", filter);
    BalticOutlinePoint(f, 74, "11808 0 7386", filter);
    BalticOutlinePoint(f, 75, "288 0 6810", filter);
    BalticOutlinePoint(f, 76, "864 0 6810", filter);
    BalticOutlinePoint(f, 77, "1440 0 6810", filter);
    BalticOutlinePoint(f, 78, "2016 0 6810", filter);
    BalticOutlinePoint(f, 79, "2592 0 6810", filter);
    BalticOutlinePoint(f, 80, "3744 0 6810", filter);
    BalticOutlinePoint(f, 81, "4320 0 6810", filter);
    BalticOutlinePoint(f, 82, "4896 0 6810", filter);
    BalticOutlinePoint(f, 83, "5472 0 6810", filter);
    BalticOutlinePoint(f, 84, "6048 0 6810", filter);
    BalticOutlinePoint(f, 85, "6624 0 6810", filter);
    BalticOutlinePoint(f, 86, "7200 0 6810", filter);
    BalticOutlinePoint(f, 87, "7776 0 6810", filter);
    BalticOutlinePoint(f, 88, "8352 0 6810", filter);
    BalticOutlinePoint(f, 89, "8928 0 6810", filter);
    BalticOutlinePoint(f, 90, "9504 0 6810", filter);
    BalticOutlinePoint(f, 91, "10080 0 6810", filter);
    BalticOutlinePoint(f, 92, "10656 0 6810", filter);
    BalticOutlinePoint(f, 93, "11232 0 6810", filter);
    BalticOutlinePoint(f, 94, "11808 0 6810", filter);
    BalticOutlinePoint(f, 95, "288 0 6234", filter);
}

static void BalticOutlineChunk3(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 96, "864 0 6234", filter);
    BalticOutlinePoint(f, 97, "2592 0 6234", filter);
    BalticOutlinePoint(f, 98, "3168 0 6234", filter);
    BalticOutlinePoint(f, 99, "4896 0 6234", filter);
    BalticOutlinePoint(f, 100, "5472 0 6234", filter);
    BalticOutlinePoint(f, 101, "6048 0 6234", filter);
    BalticOutlinePoint(f, 102, "6624 0 6234", filter);
    BalticOutlinePoint(f, 103, "7200 0 6234", filter);
    BalticOutlinePoint(f, 104, "8352 0 6234", filter);
    BalticOutlinePoint(f, 105, "8928 0 6234", filter);
    BalticOutlinePoint(f, 106, "9504 0 6234", filter);
    BalticOutlinePoint(f, 107, "10080 0 6234", filter);
    BalticOutlinePoint(f, 108, "10656 0 6234", filter);
    BalticOutlinePoint(f, 109, "11232 0 6234", filter);
    BalticOutlinePoint(f, 110, "288 0 5658", filter);
    BalticOutlinePoint(f, 111, "864 0 5658", filter);
    BalticOutlinePoint(f, 112, "2016 0 5658", filter);
    BalticOutlinePoint(f, 113, "2592 0 5658", filter);
    BalticOutlinePoint(f, 114, "3168 0 5658", filter);
    BalticOutlinePoint(f, 115, "3744 0 5658", filter);
    BalticOutlinePoint(f, 116, "4320 0 5658", filter);
    BalticOutlinePoint(f, 117, "6048 0 5658", filter);
    BalticOutlinePoint(f, 118, "6624 0 5658", filter);
    BalticOutlinePoint(f, 119, "7200 0 5658", filter);
    BalticOutlinePoint(f, 120, "7776 0 5658", filter);
    BalticOutlinePoint(f, 121, "8352 0 5658", filter);
    BalticOutlinePoint(f, 122, "9504 0 5658", filter);
    BalticOutlinePoint(f, 123, "10080 0 5658", filter);
    BalticOutlinePoint(f, 124, "10656 0 5658", filter);
    BalticOutlinePoint(f, 125, "11232 0 5658", filter);
    BalticOutlinePoint(f, 126, "11808 0 5658", filter);
    BalticOutlinePoint(f, 127, "288 0 5082", filter);
}

static void BalticOutlineChunk4(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 128, "864 0 5082", filter);
    BalticOutlinePoint(f, 129, "1440 0 5082", filter);
    BalticOutlinePoint(f, 130, "3168 0 5082", filter);
    BalticOutlinePoint(f, 131, "3744 0 5082", filter);
    BalticOutlinePoint(f, 132, "4320 0 5082", filter);
    BalticOutlinePoint(f, 133, "4896 0 5082", filter);
    BalticOutlinePoint(f, 134, "5472 0 5082", filter);
    BalticOutlinePoint(f, 135, "6624 0 5082", filter);
    BalticOutlinePoint(f, 136, "7200 0 5082", filter);
    BalticOutlinePoint(f, 137, "7776 0 5082", filter);
    BalticOutlinePoint(f, 138, "8928 0 5082", filter);
    BalticOutlinePoint(f, 139, "9504 0 5082", filter);
    BalticOutlinePoint(f, 140, "10080 0 5082", filter);
    BalticOutlinePoint(f, 141, "10656 0 5082", filter);
    BalticOutlinePoint(f, 142, "11232 0 5082", filter);
    BalticOutlinePoint(f, 143, "11808 0 5082", filter);
    BalticOutlinePoint(f, 144, "1440 0 4506", filter);
    BalticOutlinePoint(f, 145, "2016 0 4506", filter);
    BalticOutlinePoint(f, 146, "2592 0 4506", filter);
    BalticOutlinePoint(f, 147, "3168 0 4506", filter);
    BalticOutlinePoint(f, 148, "3744 0 4506", filter);
    BalticOutlinePoint(f, 149, "4320 0 4506", filter);
    BalticOutlinePoint(f, 150, "4896 0 4506", filter);
    BalticOutlinePoint(f, 151, "5472 0 4506", filter);
    BalticOutlinePoint(f, 152, "6048 0 4506", filter);
    BalticOutlinePoint(f, 153, "7200 0 4506", filter);
    BalticOutlinePoint(f, 154, "7776 0 4506", filter);
    BalticOutlinePoint(f, 155, "8928 0 4506", filter);
    BalticOutlinePoint(f, 156, "9504 0 4506", filter);
    BalticOutlinePoint(f, 157, "10080 0 4506", filter);
    BalticOutlinePoint(f, 158, "11232 0 4506", filter);
    BalticOutlinePoint(f, 159, "11808 0 4506", filter);
}

static void BalticOutlineChunk5(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 160, "1440 0 3930", filter);
    BalticOutlinePoint(f, 161, "2016 0 3930", filter);
    BalticOutlinePoint(f, 162, "2592 0 3930", filter);
    BalticOutlinePoint(f, 163, "3168 0 3930", filter);
    BalticOutlinePoint(f, 164, "3744 0 3930", filter);
    BalticOutlinePoint(f, 165, "4896 0 3930", filter);
    BalticOutlinePoint(f, 166, "5472 0 3930", filter);
    BalticOutlinePoint(f, 167, "6048 0 3930", filter);
    BalticOutlinePoint(f, 168, "6624 0 3930", filter);
    BalticOutlinePoint(f, 169, "7200 0 3930", filter);
    BalticOutlinePoint(f, 170, "7776 0 3930", filter);
    BalticOutlinePoint(f, 171, "8352 0 3930", filter);
    BalticOutlinePoint(f, 172, "9504 0 3930", filter);
    BalticOutlinePoint(f, 173, "10080 0 3930", filter);
    BalticOutlinePoint(f, 174, "10656 0 3930", filter);
    BalticOutlinePoint(f, 175, "11232 0 3930", filter);
    BalticOutlinePoint(f, 176, "11808 0 3930", filter);
    BalticOutlinePoint(f, 177, "1440 0 3354", filter);
    BalticOutlinePoint(f, 178, "2016 0 3354", filter);
    BalticOutlinePoint(f, 179, "2592 0 3354", filter);
    BalticOutlinePoint(f, 180, "3168 0 3354", filter);
    BalticOutlinePoint(f, 181, "3744 0 3354", filter);
    BalticOutlinePoint(f, 182, "4320 0 3354", filter);
    BalticOutlinePoint(f, 183, "4896 0 3354", filter);
    BalticOutlinePoint(f, 184, "5472 0 3354", filter);
    BalticOutlinePoint(f, 185, "6048 0 3354", filter);
    BalticOutlinePoint(f, 186, "6624 0 3354", filter);
    BalticOutlinePoint(f, 187, "7200 0 3354", filter);
    BalticOutlinePoint(f, 188, "7776 0 3354", filter);
    BalticOutlinePoint(f, 189, "8928 0 3354", filter);
    BalticOutlinePoint(f, 190, "9504 0 3354", filter);
    BalticOutlinePoint(f, 191, "10080 0 3354", filter);
}

static void BalticOutlineChunk6(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 192, "10656 0 3354", filter);
    BalticOutlinePoint(f, 193, "11232 0 3354", filter);
    BalticOutlinePoint(f, 194, "11808 0 3354", filter);
    BalticOutlinePoint(f, 195, "2016 0 2778", filter);
    BalticOutlinePoint(f, 196, "2592 0 2778", filter);
    BalticOutlinePoint(f, 197, "3744 0 2778", filter);
    BalticOutlinePoint(f, 198, "4320 0 2778", filter);
    BalticOutlinePoint(f, 199, "5472 0 2778", filter);
    BalticOutlinePoint(f, 200, "6048 0 2778", filter);
    BalticOutlinePoint(f, 201, "6624 0 2778", filter);
    BalticOutlinePoint(f, 202, "7776 0 2778", filter);
    BalticOutlinePoint(f, 203, "8352 0 2778", filter);
    BalticOutlinePoint(f, 204, "8928 0 2778", filter);
    BalticOutlinePoint(f, 205, "9504 0 2778", filter);
    BalticOutlinePoint(f, 206, "10080 0 2778", filter);
    BalticOutlinePoint(f, 207, "10656 0 2778", filter);
    BalticOutlinePoint(f, 208, "11232 0 2778", filter);
    BalticOutlinePoint(f, 209, "1440 0 2202", filter);
    BalticOutlinePoint(f, 210, "2016 0 2202", filter);
    BalticOutlinePoint(f, 211, "2592 0 2202", filter);
    BalticOutlinePoint(f, 212, "3744 0 2202", filter);
    BalticOutlinePoint(f, 213, "4320 0 2202", filter);
    BalticOutlinePoint(f, 214, "4896 0 2202", filter);
    BalticOutlinePoint(f, 215, "5472 0 2202", filter);
    BalticOutlinePoint(f, 216, "6048 0 2202", filter);
    BalticOutlinePoint(f, 217, "7200 0 2202", filter);
    BalticOutlinePoint(f, 218, "7776 0 2202", filter);
    BalticOutlinePoint(f, 219, "8352 0 2202", filter);
    BalticOutlinePoint(f, 220, "8928 0 2202", filter);
    BalticOutlinePoint(f, 221, "9504 0 2202", filter);
    BalticOutlinePoint(f, 222, "10080 0 2202", filter);
    BalticOutlinePoint(f, 223, "10656 0 2202", filter);
}

static void BalticOutlineChunk7(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 224, "11232 0 2202", filter);
    BalticOutlinePoint(f, 225, "1440 0 1626", filter);
    BalticOutlinePoint(f, 226, "2592 0 1626", filter);
    BalticOutlinePoint(f, 227, "3168 0 1626", filter);
    BalticOutlinePoint(f, 228, "3744 0 1626", filter);
    BalticOutlinePoint(f, 229, "4896 0 1626", filter);
    BalticOutlinePoint(f, 230, "5472 0 1626", filter);
    BalticOutlinePoint(f, 231, "6048 0 1626", filter);
    BalticOutlinePoint(f, 232, "6624 0 1626", filter);
    BalticOutlinePoint(f, 233, "7200 0 1626", filter);
    BalticOutlinePoint(f, 234, "7776 0 1626", filter);
    BalticOutlinePoint(f, 235, "8352 0 1626", filter);
    BalticOutlinePoint(f, 236, "8928 0 1626", filter);
    BalticOutlinePoint(f, 237, "9504 0 1626", filter);
    BalticOutlinePoint(f, 238, "10080 0 1626", filter);
    BalticOutlinePoint(f, 239, "10656 0 1626", filter);
    BalticOutlinePoint(f, 240, "864 0 1050", filter);
    BalticOutlinePoint(f, 241, "1440 0 1050", filter);
    BalticOutlinePoint(f, 242, "2016 0 1050", filter);
    BalticOutlinePoint(f, 243, "2592 0 1050", filter);
    BalticOutlinePoint(f, 244, "3168 0 1050", filter);
    BalticOutlinePoint(f, 245, "4320 0 1050", filter);
    BalticOutlinePoint(f, 246, "5472 0 1050", filter);
    BalticOutlinePoint(f, 247, "6048 0 1050", filter);
    BalticOutlinePoint(f, 248, "6624 0 1050", filter);
    BalticOutlinePoint(f, 249, "7200 0 1050", filter);
    BalticOutlinePoint(f, 250, "7776 0 1050", filter);
    BalticOutlinePoint(f, 251, "8352 0 1050", filter);
    BalticOutlinePoint(f, 252, "8928 0 1050", filter);
    BalticOutlinePoint(f, 253, "9504 0 1050", filter);
    BalticOutlinePoint(f, 254, "10080 0 1050", filter);
    BalticOutlinePoint(f, 255, "10656 0 1050", filter);
}

static void BalticOutlineChunk8(FileHandle f, PGFilter filter)
{
    BalticOutlinePoint(f, 256, "864 0 474", filter);
    BalticOutlinePoint(f, 257, "1440 0 474", filter);
    BalticOutlinePoint(f, 258, "2016 0 474", filter);
    BalticOutlinePoint(f, 259, "2592 0 474", filter);
    BalticOutlinePoint(f, 260, "3168 0 474", filter);
    BalticOutlinePoint(f, 261, "3744 0 474", filter);
    BalticOutlinePoint(f, 262, "4320 0 474", filter);
    BalticOutlinePoint(f, 263, "4896 0 474", filter);
    BalticOutlinePoint(f, 264, "5472 0 474", filter);
    BalticOutlinePoint(f, 265, "6048 0 474", filter);
    BalticOutlinePoint(f, 266, "6624 0 474", filter);
    BalticOutlinePoint(f, 267, "7200 0 474", filter);
    BalticOutlinePoint(f, 268, "7776 0 474", filter);
    BalticOutlinePoint(f, 269, "8352 0 474", filter);
    BalticOutlinePoint(f, 270, "8928 0 474", filter);
    BalticOutlinePoint(f, 271, "9504 0 474", filter);
    BalticOutlinePoint(f, 272, "10080 0 474", filter);
    BalticOutlinePoint(f, 273, "5184 0 7644", filter);
    BalticOutlinePoint(f, 274, "5460 0 7392", filter);
    BalticOutlinePoint(f, 275, "5766 0 522", filter);
    BalticOutlinePoint(f, 276, "5094 0 1440", filter);
    BalticOutlinePoint(f, 277, "8400 0 6882", filter);
    BalticOutlinePoint(f, 278, "8712 0 6684", filter);
}

static void BalticOutlineProbe()
{
    if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
    FileHandle f = OpenFile("$profile:baltic_outline_nav_v3.log", FileMode.WRITE);
    if (!f) return;
    FPrintln(f, "BALTIC_OUTLINE_NAV_V3");
    FPrintln(f, "world=" + GetGame().GetWorldName());
    PGFilter walk = new PGFilter;
    walk.SetFlags(PGPolyFlags.WALK, PGPolyFlags.SWIM | PGPolyFlags.SWIM_SEA | PGPolyFlags.DISABLED, PGPolyFlags.NONE);
    FPrintln(f, "flags=" + walk.GetIncludeFlags() + ";" + walk.GetExcludeFlags());
    BalticOutlineChunk0(f, walk);
    BalticOutlineChunk1(f, walk);
    BalticOutlineChunk2(f, walk);
    BalticOutlineChunk3(f, walk);
    BalticOutlineChunk4(f, walk);
    BalticOutlineChunk5(f, walk);
    BalticOutlineChunk6(f, walk);
    BalticOutlineChunk7(f, walk);
    BalticOutlineChunk8(f, walk);
    BalticOutlinePath(f, "summit_0_0", "5184 0 7644", "5244 0 7644", walk);
    BalticOutlinePath(f, "summit_0_1", "5460 0 7392", "5520 0 7392", walk);
    BalticOutlinePath(f, "summit_1_0", "5766 0 522", "5826 0 522", walk);
    BalticOutlinePath(f, "summit_1_1", "5094 0 1440", "5154 0 1440", walk);
    BalticOutlinePath(f, "summit_2_0", "8400 0 6882", "8460 0 6882", walk);
    BalticOutlinePath(f, "summit_2_1", "8712 0 6684", "8772 0 6684", walk);
    PGFilter none = new PGFilter;
    none.SetFlags(PGPolyFlags.NONE, PGPolyFlags.ALL, PGPolyFlags.NONE);
    BalticOutlinePath(f, "negative", "6000 0 6000", "6060 0 6000", none);
    FPrintln(f, "BALTIC_OUTLINE_NAV_COMPLETE");
    CloseFile(f);
    Print("BALTIC_OUTLINE_NAV_COMPLETE_V3");
}
class BalticOutlineNavMission: MissionServer
{
    override void OnInit()
    {
        super.OnInit();
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).CallLater(BalticOutlineProbe, 15000, false);
    }
    void ~BalticOutlineNavMission()
    {
        GetGame().GetCallQueue(CALL_CATEGORY_GAMEPLAY).Remove(BalticOutlineProbe);
    }
}
Mission CreateCustomMission(string path) { return new BalticOutlineNavMission(); }
