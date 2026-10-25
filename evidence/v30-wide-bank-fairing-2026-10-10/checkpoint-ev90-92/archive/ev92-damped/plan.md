# EV92 — una amortiguación calculada, aprobada por integrador

Codex/root aprueba esta unidad offline el2026-10-10 dentro de la petición viva
de seguir autónomamente con taludes y fallos. No autoriza despliegue ni cambia
criterios. La propuesta independiente permanece en plan-proposal.md.

EV91 queda rechazado: su única resolución produjo una meseta nueva36m².
El fullEV91 attempt-02 informa únicamente shape_contract=false y otras26puertas
PASS. Se conserva íntegro y se usa solo como dirección geométrica congelada.
B es f9fb23de…61f0; H91 es865901ab…e702. Crear una sola salida EV92, sin solver,
con D=H91−B. Ni otro alpha ni reparación posterior si falla.

[DESIGN] Derivar energía sobre las350stencils existentes: para cada stencil,
b_s es su combinación lineal enB y d_s enD. Pesos1 paraDxx/Dzz y2 paraDxz.
Sumar con Fraction exacto sobre los float32 binarios:
k0=sum(w*b_s²), k1=sum(2*w*b_s*d_s), k2=sum(w*d_s²).
No incluir fidelidad del optimizador ni ajustar el polinomio con muestras.
Exigir k0>0,k2>0,k1<0,E(1)<=0.75E(0), discriminantepositivo.
Convertir los momentos a float64 para raíz cuadrada. Raíz inferior estable:
a_energy=(k0/2)/(-k1+sqrt(k1²−k2*k0)).

Para foco840,370, la prominencia=max(0,min(hc−hvecino1,hc−hvecino2)).
El objetivo es0.75*promB en cada eje. Derivar las raíces de ambas diferencias
afines decrecientes; mínimo de raíces[0,1] por eje. Si no hay, rechazar.
a_lo=max(a_energy,a_EW,a_NS,0); exigir0<a_lo<1.
Regla única alpha=(a_lo+1)/2. Este intervalo expresa materialidad de energía
yprominencia; NO es prueba de factibilidadglobal, ni incluye noflat/agua/ángulos.

[EXACT] Derivación independiente rational4664c3e7 produce momentos
[221.2263916770154,-186.20880690454646,84.52271160360701]. El cálculoestable
produce a_energy0.35384751023735095, alpha0.6769237551186755. La fórmula de
raíz directa independiente difiere1ULP; se conserva como contraste, no se
eligealpha por ese desvío. El margen a ambos extremos es material, no unULP.

Mantener85variables/350stencils originales,43pins de collarB y42gradoslibres,
las cotas físicas/inward y testigosD8. H92=float32(B+alpha*(float64(H91)−B))
conB promovido a float64 y un único cast final. Metadatos y todoslos demás
vértices exactosB. Verificar cotas y testigos exactos antes de escribir.
Una marca exclusiva impide una segunda autoría. Hashes de fuentes antes/después,
prepared por identidad, archivo nuevo y recibo con calls=0/parent91 declarado.

Revisión del autor/prepared y fixtures cerradas antes de escribir. Después,
el consumidor independiente verifica fórmula completa2048², procedencia y
las27puertas EV91 sin modificar tolerancias, poblaciones o criterios. La
representación de recibo adaptada para reutilizarEV91 debe ser explícita;
H92 no se atribuye a SLSQP. Conservar diagnósticos heredados y wet-support.
Si cualquier puerta falla, EV92 se rechaza sinotraautoría bajoesteplan.
PASSoffline no acepta agua dinámica/render ni BASE1.0; gráficos pendientes.
