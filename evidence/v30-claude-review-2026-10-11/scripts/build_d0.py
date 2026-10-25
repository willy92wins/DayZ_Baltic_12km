import runpy
ns = runpy.run_path("build_bisect.py", run_name="lib")
props, b = ns["read_pbo"](ns["B_PBO"])
assert ns["sha"](ns["B_PBO"]) == ns["EXPECT"][ns["B_PBO"]]
ns["build"]("D0", b, props, {})
