# B3E2 — completar preflight y ejecutar la pareja pendiente

Estado: REVISADO_PARA_IMPLEMENTAR. Codex ejecutor/integrador.
Nuevo intento acotado; no relanzar el CLI ni la carpeta B3E consumidos.

La sonda de lectura nueva confirmó9lecturas/7archivos con hashes externos,
0.641s de hijo,16tests finales. No demuestra causa del timeout previo60.047s
ni sustituye las comprobaciones oficiales. B3E anterior no llegó a compilar.

## Alcance y trazabilidad

Mismo producto P2/P8/P9/P11 y contrato geométrico B3E revisado. Control d130,
candidato B3D f2b7, proof ae5e, contrato b445, cadena5df; no autoría nueva.
Preservar Visual/Memory/Roadway,201modelos,poses,controles700dry/723wet,
4560pares exactos MLOD, plano1e-6, overlay±.02/.01, bits mundiales incluso
signedzero y censo1520completo. No exigir grosor local exacto no aprobado.
Resultado sólo COMPILED_B3E_CONDITIONAL o rechazo/inconcluso; no motor/paquete201.

## Implementación propuesta

[EXACT] build_prism_b3e_ev112.py sha914bef55add8016bec4e82996863a647520d1aa016a67bf7529b5fca94861eaa
contiene run_tree,preflight,sequence y execute. El CLI/execute original quedan
consumidos. prism_b3e_compiled_ev112.py sha36bce0d822621e5879179243591d028ed9ae9c09f40c624d6b755db768b9a5eb
es consumidor publicado; sus41fixtures ya pasaron y no necesitan repetirse por rutina.

[DESIGN] Preparador nuevo, con aprobación/plan y carpeta exclusivos. Importar sólo
primitivas publicadas; no modificar fuentes selladas. Separar los pasos oficiales
del preflight y sellado de hashes mediante eventos flush+fsync; todo el preflight
mantiene60s/2GiB. Verificar hash externo de recibos ANTES de confiar en sus campos.
Reusar la copia local con arreglo literal archivado5fb69872, comprobando el diff
con el original9f8786a5; no tocar la skill gobernada. No bootstrap/montaje/reparación
de entorno. Diag ausente no es permiso nativo; requisito de build ausente bloquea.

Fijar nueva aprobación con postimágenes de preparador, consumidor, tests nuevos,
este plan y recibos de revisión/suite. Copiar contrato de parentesco, no reemplazar
pins históricos por lo que se observe. Crear una pareja de fuentes nuevas con
config idéntica; primero compilar control, releer PBO/ODOL y pasar gate_control;
únicamente entonces compilar candidato y consumirlo con gate B3E sin cambios.
No invocar solver, editor ni preparadores antiguos. No repetir la sonda diagnóstica.

El preparador nuevo debe conservar orden de fases, devolución de fallos geométricos,
pinning transitivo y outputs antes/después. Observar únicamente procesos propios
por PID/create_time; evidenciar cierre y distinguir hashes instalados de procesos
realmente observados. Cualquier fallo conserva recibos; nada de reintentos internos.

## Validación y presupuesto

Una revisión de este plan180s; código180s y suite120s para los cambios nuevos.
Fixtures contra consumidores: aprobación ajena/ausente, recibo de preflight cambiado,
control fallido impide candidato, deadline pese a retorno0 tardío, fuentes/config
mutadas entre pasos, propagación de rechazo e INCONCLUSIVE sin falso PASS.
No basta un mock que repita la implementación: comparar contrato/manifest contra
pins publicados y hacer prueba positiva/negativa del consumidor real sobre fixture.

Una ejecución: preflight60s/2GiB; control150s/2GiB; gatecontrol180s/2GiB;
candidato150s/2GiB; consumidor180s/2GiB. Límites de pared comprobados incluso
si la espera devuelve éxito tardío. Si preflight vuelve a agotar60s, parar,
conservar fase y reevaluar ruta; no aumentar presupuesto para obtener PASS.
Si control rechaza, no compilar candidato. Si geometría rechaza, no barrer parámetros.

No DayZ/lease/201/despliegue. Original2658 sigue47FAIL/21inciertos; RAM,nueve
regresiones,C1sinrevisar y calidadglobal abiertas. Carreteras siguen como preparación
independiente: catálogo A y planes de corredores, nunca puente por proximidad.

## Adjudicación de revisión — 28-10

Fable5.1 nativo85.109s, SOUND-with-fixes; entrega íntegra, fuentes intactas.
Recibos R/b3e2-build-plan-review-20261028. Se concretan los requisitos:

1. Antes de parsear recibos: SHA literal354fbb2e5edea80e88521f02cd135ac2f6a7608a14085af5cc088395a542e68e
   para preflight histórico;5df50091 para contrato previo, b445 y ae5e completos
   desde los pins publicados. No confiar en el hash que se declara a sí mismo.
2. Comprobaciones oficiales en hijo aislado (misma imagen PythonGIS), con PID real,
   fases flush+fsync y deadline60s que incluye sellado. No llamada opaca dentro
   del orquestador sin recibo. No atribuir causa: F2 del dictamen especula dónde
   agotó; el log anterior ya terminó comprobaciones oficiales antes de hashes.
3. Verificar pins transitivos antes de cada fase. F3 parcialmente refutado: contrato
   B3D YA fija packer526159a7, model_config8b340a2a y los tres lectores. No duplicar
   ni sustituir esos pins por actuales. Añadir lzo/lzss y comprobar módulos cargados
   contra las rutas fijadas, como en el catálogo vial. Hash no prueba ejecución.
4. Esquema de aprobación B3E2_EXECUTION_V1 y ruta de salida nueva fijada; exigir plan
   B3E2 y preparador nuevo. Rechazar aprobación/entrypoint B3E antiguo, sin prohibir
   que se pine el helper antiguo si sólo se importan sus primitivas autorizadas.
5. Tras fallo de un gate, leer sólo su reporte NUEVO si existe y enlazar estado/hash
   sin reinterpretación. No leer un reporte preexistente antes de lanzar, como
   podría entenderse en F5. Fixture demuestra que no se crea carpeta candidata.
6. Hijo trivial real para prueba de orquestador y PBO fixture aceptado por lector,
   además de prueba de consumidor real independiente. Retorno0 fuera de deadline
   rechaza; descendiente observado vivo impide cierre y se retira por identidad.
   Se mantiene limitación de muestreo, sin promesa de detectar hijos no observados.

No implementación ni pareja ejecutadas aún. Suite/code review nuevos antes de
ejecución. No repetir diagnóstico, catálogo, preparador antiguo ni sus revisiones.
