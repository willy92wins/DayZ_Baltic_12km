# Integración de la revisión operativa

SOUND-with-fixes aceptado tras comprobar el sellador y aplicar dos correcciones de captura. La extracción RPT y script se ejecuta antes del lector, incluso si el dato acaba INCONCLUSO. El canal script solo se vincula por creación y UUID; si falta se declara su ausencia. No se infiere la semántica del cargador, RAM ni ausencia de avisos.

El sellador produce frozen/deployment/accepted con misión, código y controles,118paquetesvanilla,4modPBO y ejecutable. El prelaunch comprueba hashes de deployment.inputs: detecta cambios de contenido vanilla. CT_* no necesita excluir-1; ese sentinela solo acompaña exists=false.

Un primer intento de sellado se detuvo por ausencia de adjudication.json antes de escribir frozen/deployment; no hubo lanzamiento. La escritura de adjudicación se completa ahora.
