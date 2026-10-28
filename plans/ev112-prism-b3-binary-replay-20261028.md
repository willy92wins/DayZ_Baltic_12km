# B3B R1: consumir la pareja guardada tras un error de interfaz

Estado: REVISADO_PARA_EJECUTAR. Unidad mecánica nueva y acotada; no segunda compilación.
El control y candidato B3B compilaron en 5.422/4.047s, menos de252MB cada árbol.
El control conserva identidad semántica del histórico y caras/winding de d130.
El primer consumidor terminó con AttributeError antes de abrir el PBO histórico;
no existe veredicto geométrico del candidato. Mantener failure.json y código.

[EXACT] tools/playtest/attach_navmesh.py:20-21 read_pbo(path) llama
path.read_bytes(). El contrato JSON entrega str. Corregir exclusivamente esa
llamada a read_pbo(Path(c['baseline_pbo'])); los otros sitios ya reciben Path.
Regresión SavedEntryPoint recorre verify_saved desde JSON hasta ese lector;
34tests pasan. No cambiar predicados, tolerancias, source,water ni posiciones.

R=E:/DayZ-Baltic-Build/shape-repair-20261025.
Congelados en prism-b3-binary-replay-20261028: failed-consumer/test,
contract-before.json y failure-before.json. Original contratoSHA
45d6bd48e4a03a12cb3adb1c62f6c35ff8fbe81e515281c3f498cc6410d84e56.
Mismos ODOL de prism-b3-binary-pair-20261028:
control0fccfce81ebcdd6b69b32989744ffe7b838b855c67c7dd3e71a0c266606a5525;
candidatob2c8bd4b45b56d139e0f97e14220aef6ed31e965eddc6fdbc040990f05eb5d62.
PBOcontrolcf2f7a48174a213938531d42cee43d100ab1fc53306f4ea9069a57184475bb47;
PBOcandidatob8cfdd52c16a82a77136468030a89de3290fd6197d1b9f25c0d1f2b364c14913.

[DESIGN] R1 sustituye sólo hashes del consumidor/test, añade pines de los cuatro
binarios, del contrato anterior y del replay. Comparar explícitamente que todos
los demás campos y pines permanecen iguales. Verificar antes/después. Consumidor
separado sobre misma pareja y salida nueva; mantener INCONCLUSIVE/REJECTED/PASS
condicional tal como la puerta revisada. No editar ni ocultar la primera salida.
No generar paquete en esta unidad: si pasa, componerlo después con los mismos
límites de la puerta previa y una operación separada. Sin DayZ/despliegue.

Presupuesto: revisión limitada300s, tests120s, un replay180s/2GiB. No más replay,
compilación ni barrido. Si falla geometría, conservar diagnóstico y rediseñar
antes de otra intervención. Una exception de instrumento tampoco es PASS.
Original47FAIL21inciertos, RAM,C1,calidadglobal/council pendientes.

Revisión Fable5.1 nativa133.969s,SOUND,inputs intactos. Notas aceptadas:
contrato R1 nuevo y pines calculados tras última edición; empaquetado futuro
consumirá SHA de R1 y no el contrato anterior. Sin nueva revisión del restoB3B.
