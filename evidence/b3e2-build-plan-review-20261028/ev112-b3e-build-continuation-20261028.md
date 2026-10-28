# B3E2 — completar preflight y ejecutar la pareja pendiente

Estado: BORRADOR_PENDIENTE_DE_REVISION. Codex ejecutor/integrador.
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
