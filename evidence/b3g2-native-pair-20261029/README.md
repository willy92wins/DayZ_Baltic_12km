# B3G2: pareja nativa completa, aceptación global abierta

Control y candidato:270Q/1080R cadauno,90posiciones en3rondas. Identidad del
motor/paquetes/puntos y cierre oficiales completos. RV alto y bajo de700/723
pasan FAIL→PASS en todaslas rondas con candidato362ef4c2. Persisten RH349/350/1425
y agua723; Bullet sigue sin calibración. Original2658 conserva47FAIL21inciertos.
La comparación mantiene INCONCLUSIVE_PAIRED_DIAGNOSTIC y causaUNPROVEN.

Se corrigió lectura de logs abiertos: FileShareRead|Write|Delete, FileID del
handle NTFS, longitud acotada20MiB y doble snapshot estable paraEND270.
El consumidor vuelve a verificar bytes y diag, no confía en un hash autodeclarado.
El único DumpStack permitido es el golden exacto con timestamp/frames contiguos,
conservado como confusor; desconocidos,duplicados,cola parcial y compileerror
bloquean.40testsPython y11Node PASS; PSparse1archivo. Revisión inicial180.188s
parcial, recuperación109.016s completa y adjudicada. No ampliación de tolerancias.

El primer test de tiempo halló redondeo float de FILETIME a futuro1us. Tres
casos conservados. Corrección compara enteros100ns y retiene esos campos; ISO
sólo representación truncada. Ni tolerancia nueva ni supresión general deE.

Ambos runs retirados orderly_close, release terminal_safe,selfnone,pending0,
heartbeat10s. Preparación,pareja,consumidores,comparación y revisiones CONSUMIDOS.
No relanzarlos ni adoptar sus IDs. Código aprobado para esta unidad en tools;
no se declara cierre físico/visual global ni integración general del piloto seco.

API de lectura comprobada contra documentación Microsoft:
[BY_HANDLE_FILE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information),
[GetFileInformationByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle),
[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).
Sólo NTFS; no afirmar garantía de identidad ReFS con64bits.

Los result-summary son proyecciones explícitas de informes privados de11MB;
su SHA completo queda guardado. Los logs nativos completos, snapshots,
clasificaciones,identidades ycomparison permiten inspección. No recursosvanilla
ni credenciales publicados. La ausencia de pair_snapshot_drift no prueba
animación nula ni espacio libre entre consultas.
