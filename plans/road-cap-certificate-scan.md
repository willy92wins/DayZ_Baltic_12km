# Diagnóstico global por certificados, sin editar terreno

Consumidor: decidir una cota de graduación técnicamente factible antes de otro
ASC. V17 con3m fue INFEASIBLE en42s; no produjo candidato. El certificadoV16
demostraba solo una cota local necesaria2.455m, nunca suficiencia global.

[DESIGN] Sobre la matrizV16 exacta, objetivo0 y mismos pisos/máscaras, iniciar
en3m. Si es infactible, obtener un certificado dual y verificarlo contra la
matriz original y cotas. La siguiente cota deriva exclusivamente de la cota
necesaria demostrada por ese certificado, redondeada hacia arriba0.25m.
Cada paso debe aumentar la cota demostrada; si no, parar sin resultado.

VERDE de diagnóstico: un primal finito que cumpla todas las restricciones
originales y cotas, contrastado independientemente. Solo se obtiene un intervalo
de cota global (necesaria/suficiente); no se produce ASC ni se importa nada.
No pretende optimalidad ni modifica criterios de lisura. Los certificados son
combinaciones verificables de desigualdades, no opiniones del solver.

Paradas mecánicas:600s globales/650s proceso; ningún solve>120s; cota explorada
máxima12m; certificado inválido/no progresivo o sin rayo; primer primal válido.
No continuar si el proceso acaba sin resultado. Los12m no se autorizan como
cambio de terreno: cualquier aplicación necesita plan nuevo según la magnitud
y ubicación medidas, con los consumidores de agua/reserva y pendientes vigentes.

Contraejemplos cerrados del certificado: invertir signo, RHSalterado y cotas que
ya eliminan su contradicción deben dejar de demostrar infeasibilidad. Si el
certificado no supera la comprobación algebraica, no guía la siguiente cota.

[EXACT] Highs.changeColsBounds(n,int32indices,float64lower,float64upper) verificado
por docstring instalada01-10. Misma configuración que el diagnóstico anterior;
reutilizar modelo/basis evita reconstruir geométricamente la red en cada paso.
