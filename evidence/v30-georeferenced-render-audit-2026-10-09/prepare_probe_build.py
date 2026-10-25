from pathlib import Path
B=Path(__file__).parent
s=Path('E:/DayZ-Baltic-Build/v30-native-material-binding-20261009/build_probe.py').read_text()
s=s.replace('baltic_material_binding_probe_v1','baltic_projection_probe_v1').replace('BalticMaterialBindingProbe','BalticProjectionProbe').replace('balticmaterialbindingprobe','balticprojectionprobe').replace('packed-v2','packed').replace('@BalticProjectionProbeV2','@BalticProjectionProbeV1').replace('BUILT_ISOLATED_MATERIAL_BINDING_PROBE','BUILT_CLIENT_READ_ONLY_PROJECTION_PROBE')
s=s.replace("assert not Path('P:/DayZ_MCP_dev/_client/profiles/baltic_projection_probe_v1.phase').exists()\n",'')
(B/'build_probe.py').write_text(s)
print(B/'build_probe.py')
