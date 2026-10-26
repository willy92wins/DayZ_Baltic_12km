"""Derive the reviewed C packer for exact kit7 inputs. Does not execute it."""
from pathlib import Path
R=Path(__file__).parent
s=(R/'package_and_deploy_c_nav9_retry.py').read_text()
changes={
'Attach C-generated navmesh':'Attach kit7-generated navmesh',
"navmesh-c-retry-v9-20261026":"navmesh-kit7-v9-20261026",
"nav-c-retry-human-close-20261026":"nav-kit7-preparation-20261026",
"package-midpoint-c-nav-v9":"package-kit7-nav-v9-20261026",
"@DayZ_Baltic_EV112_MidpointCNavV9":"@DayZ_Baltic_EV112_Kit7NavV9",
"@DayZ_Baltic_EV112_MidpointC":"@DayZ_Baltic_EV112_Kit7Overlap",
"nav-c-retry-postprocess-review":"kit7-nav-postprocess-review-20261026",
"e02b1334-4098-4a95-b92d-4346ceff73e9":"57c47974-d29d-4d2c-af5f-65c0a14e1b29",
"0139cd1a7ce360436e474fa6448470dfe93bf34a21229b6cf44f4e839af54126":"0da63d3f258923e784a62bcb59bb1d7f2ab99866816f530bfe73cd4211b23254",
"4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38":"10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc",
"C_NAV9_DEPLOYED_RUNTIME_PENDING":"KIT7_NAV9_DEPLOYED_RUNTIME_PENDING",
" and not (R/'patch-nav-c45/deployment.json').exists()":"",
",R/'orchestrate_c45_retry.js',R/'finish_c45_retry_probe.py'":"",
",read(R/'patch-nav-c45/frozen.json')['inputs']":"",
"assert host['package_hashes']==dep['packages'] and len(host['package_hashes'])==4":"assert {str(Path(p).resolve()).casefold():h for p,h in host['package_hashes'].items()}=={str(Path(p).resolve()).casefold():h for p,h in dep['packages'].items()} and len(host['package_hashes'])==len(dep['packages'])==4",
"navigation45 and patch coverage remain pending.":"navigation607 and patch coverage remain pending.",
"No claim of actor movement or traversal of25Cmodels.":"No graph or actor acceptance before the kit7 consumer."
}
for a,b in changes.items():
    assert a in s,a;s=s.replace(a,b)
start=s.index("frozen=read(R/'patch-nav-c45/frozen.json')")
stop=s.index("write(O/'deployment.json'",start)
s=s[:start]+s[stop:]
s=s.replace("deployed=deployed,generation_run=gen['run_id']","deployed=deployed,packages=packages,inputs=gate['inputs'],generation_run=gen['run_id']")
# The actual four package identities must be present, independent of path spelling.
anchor="assert gen['generator_sha256']=='66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7'"
s=s.replace(anchor,anchor+"\nassert {Path(p).name.casefold():h for p,h in host['package_hashes'].items()}=={'narva_trial.pbo':'10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc','baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6','baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43','dayz_mcp.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'}")
dest=R/'package_and_deploy_kit7_nav9.py';assert not dest.exists();dest.write_text(s)
print(dest)
