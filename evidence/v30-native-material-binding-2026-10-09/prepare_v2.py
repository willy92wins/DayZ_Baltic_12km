from pathlib import Path
import shutil
B=Path(__file__).parent
for name in ['reference.json','lint.json','cfgconvert.log','filebank.log']:
 shutil.copyfile(B/name,B/('v1-'+name))
p=B/'build_probe.py';t=p.read_text().replace("out=B/'packed'","out=B/'packed-v2'").replace('@BalticMaterialBindingProbeV1','@BalticMaterialBindingProbeV2');p.write_text(t)
p=B/'prepare_probe.py';t=p.read_text().replace('baltic_material_binding_probe_v1/scripts/5_Mission\"}; }; }; };\\n','baltic_material_binding_probe_v1/scripts/5_Mission\"}; }; }; }; };\\n');p.write_text(t)
with (B/'plan.md').open('a',encoding='utf-8') as f:f.write('\nCorreccion de sonda: el primer run5f62e026 se nego por handle nulo antes de fijar escena; no hubo mutaciones. La revisionV2 resuelve cada handle al pedir la fase tras estabilizar la camara, registra MISSING por separado y permite restauracion sin handle. La presencia de un recurso de reserva no se exige a la referencia. Config inicial tenia una llave de cierre ausente, detectada por CfgConvert y corregida antes de desplegar. Ambos fallos quedan preservados.\n')
