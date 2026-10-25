# Extensión del piloto continuo a la red seca

El pilotoV14 pasó geometría independiente y cinco negativos; solo cubre
2.641km en tres corredores. La estimación conservadora de la red seca interior
es88.235km/109071vértices de soporte, con82775conectados en el mayor componente.
No se puede resolver cada carretera por separado ignorando sus intersecciones.

[DESIGN] Preparar un sistema conjunto con el modelo de triángulosV14 sobre
los interiores secos (>18m desde extremos, >48m agua, >480m centroNarva).
Preservar aguas/fairways/bancos/islas y suelo mínimo; soporte lateral12m como
el piloto. Registrar separadamente los cruces de agua/junctions excluidos:
no se declaran vías terminadas ni se rellenan cauces.

Reducir únicamente desigualdades matemáticamente redundantes en el plano
bidimensional de gradientes de cada triángulo. Intersecar todos los semiplanos,
conservar caras activas, y comprobar que el polígono reducido satisface cada
desigualdad original antes de usarlo. No cambiar sus límites ni omitir curvas.

Presupuesto: una preparación; una optimización L1 conjunta<=600s/un hilo con
cota de cambio±2.05m, suelo seco conservado y todas las toleranciasV14. Si el
sistema es inviable o falta memoria, conservar matriz/manifiesto y parar este
candidato sin exportar alturas. Antes del solve, exigir memoria disponible
>=2GiB+4veces el tamaño sparse del sistema ampliado. No cerrar programas ajenos.

Consumidor independiente: red completa a0.37m y anchura0.25m, mismo dominio
seco previo y perfil nativo; amplitud3cm, pendiente6.5%, cuerda6m3cm, talud35°,
protecciones/exterior exactos. No sustituir por residuoLP. No importar hasta
tener ese PASS y negativos. Una importación nativa agrupada y navmesh final
solo después; el mundoV10 permanece intacto durante la preparación.
