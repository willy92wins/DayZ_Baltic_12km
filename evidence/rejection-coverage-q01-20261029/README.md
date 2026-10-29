# Q01: los rechazos humanos permanecen abiertos y trazables

VERIFIED_OPEN_HUMAN_REJECTIONS significa integridad del registro, no calidad aceptada del mapa.
Nueve casos distintos, cuatro controles de alcance y doce JSON fuente verificados.
Cero casos resueltos; C1 sigue NOT_REVIEWED. El visto bueno de calzada49 no acepta
el río49 y 80de108objetos no demuestran que falte un puente.

Productor real0.234s y consumidor0.234s, ambos<20MB. Contrato26e07a2e… y ledger1a728ab8…
conservados completos. Muse Wonder1.0 implementó; Fable5.1 revisó149.500s.
La corrección separa validación declarativa del consumidor y añade negativos
contra filas prestadas, estados promocionados, hashes, punteros y omisiones.
26pruebas coleccionadas:25pasan y1symlink omitida por permisos Windows; no
se presenta esa cobertura como probada.

Las fuentes públicas anteriores difieren en siete archivos sólo por EOL.
sources/ conserva los bytes exactos de los12JSON sin cambiar archivos históricos
ni el contrato. No abre las imágenes referidas ni publica sus PNG. El directorio
no contiene modelos, WRP, PBO o geometría vanilla.

Reproducción desde la raíz del repo, Python3:
~~~text
python tools/quality/verify_rejection_coverage_ev112.py --root evidence/rejection-coverage-q01-20261029/sources --contract ABS/evidence/rejection-coverage-q01-20261029/contract.json --contract-sha256 26e07a2e86af330bd4591622d937ef527895b73dcb61f6fcca584a5d84a0e9ce --ledger ABS/evidence/rejection-coverage-q01-20261029/ledger.json
~~~
Sustituir ABS por la ruta absoluta del checkout. Tests:test_rejection_coverage_ev112.py.

Q03/Q05/Q17 consumirán los IDs y ámbitos de este registro como regresiones
obligatorias; todavía no existe integración de este ledger con un gate global.
Q02B y escenas compuestas siguen pendientes: aquí no se reparó un contorno,
lecho ni puente. Nav8hist607 y original47FAIL21inciertos no cambian.
