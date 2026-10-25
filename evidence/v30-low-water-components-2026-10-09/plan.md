# EV26 — connectivity census and isolated rigid basin translation

Consumer: the next in-game comparison of the reported Narva residual and the final terrain integrator. This is a diagnostic branch, not an accepted level-policy change.

Current candidate EV25 is immutable. `discover_components.py` measures positive-width connectivity on every clipped native triangle. `discover_render_group.py` checks every compiled water instance against the deployed PBO; the local conservative cohort contains six standing bodies, four instances, no engineering vertices, 138 cells. Source and hashes are in discovery/cohort JSON.

[DESIGN] Translate those four instances and all terrain faces under their compiled bounds together by 0.35 m. This is the smallest 25 mm step putting their minimum bed above 1.001 m. Fade terrain displacement to zero over 36 m of surrounding dry terrain, holding all other water support, roads and platforms fixed. Unlike rejected D2, nominal and visible water rise with their bed: preserve depth, area, connectivity and shore crossings. This does not smooth the angular outline yet.

Authority: current request authorizes fixes, whole-map checks and reversible tests; local Narva reprofiling is authorized. Plan `plans/v30-rumbo-agua-1.0.md` records 1 m standing-water beds, but Narva and level exceptions persist. Therefore do not promote this translation or generalize it to the 70 standing-water risks without evidence and a level-policy disposition. Big lakes excluded.

Before runtime: saved float32 terrain, world records and compiled models must prove only four Y translations; every unaffected water depth exact, affected physical/visible depths within 1e-6 m; same active native faces and component labels; projected wet-area symmetric difference <=0.001 m2; bed >=1 m; no new >35-degree face (existing excess must not increase); engineering unchanged, no edit outside the local 36 m apron. Assert fixed/translated support do not conflict. Source/masks/archive entries other than WRP unchanged.

Controls: missing water shift must fail depth conservation; terrain-only low bed must fail floor; displaced protected/outside vertex must fail domain; lost positive-width edge detected by connectivity fixtures. Limits: same-shape translation does not establish root cause, and interpolation/LOD shaders remain opaque.

Budget: one derived translation candidate, no height sweep; one A/B/A runtime sequence with fixed normal sea configuration, same camera, clear noon, strong wind mission. One repair only for a reproducible implementation error, not a failed product gate. Baseline and control must visibly reproduce the targeted symptom or result is INCONCLUSIVE. Capture local basin and R1; use complete local native ground/water readback, plus deployed-byte identities. Do not infer whole-map visual closure from physical checks. The census remains useful independently of the pilot.

## Instrument correction after A/B/A, before B stable replay

The three logs have 784 matching ground samples and 19 matching water planes, but all fail `temporal_timing`: sampling begins during client startup and pauses. Preserve those FAIL results, do not weaken the 550 ms spacing gate. A2's 27-second visual sequence also proves that individual images can miss the intermittent foam/halo. Use the one runtime correction: same B terrain/archive/camera/weather, delay the 64-sample sequence until 60 seconds after the grid census. Replay B once and capture eight frames over at least 25 seconds. This repairs undersampling/launch timing, does not add a height candidate. A1's initial degrees-as-radians FOV call and timed-out correction are invalid views; only `A-basin-correctFOV` participates. Source API uses radians (`MCPClientBridge.c:3459`, vanilla `cameratoolsmenu.c:744`).
