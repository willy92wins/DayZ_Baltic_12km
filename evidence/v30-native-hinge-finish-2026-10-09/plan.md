# EV25 — taludes secos mediante uniones de caras nativas

Consumidor: candidato de terreno y su paquete de prueba. Petición viva de terminar toda la superficie, P12/P14 y pasos 4/7 del rumbo. No sustituye la decisión reservada de lagos ni el cierre gráfico de BALTIC-016.

## Descubrimiento y cambio de mecanismo

EV24 enumera las 12.566.533 aristas internas reales. En x11319,z3747 dos caras opuestas cumplen individualmente 35 grados pero difieren 69,99986 grados. Las alturas de sus cuatro vértices son 5,130199, 8,105896, 8,105896 y 5,140146 m. El control de pendiente no es un control de continuidad entre caras. Los casos fuertes se concentran en taludes. Esta unidad minimiza directamente el salto de gradiente entre caras; no repite un barrido de sigma ni el ajuste de contorno retirado.

## Autoría [DESIGN]

Una pasada de descenso por coordenadas sobre las uniones triangulares nativas, con intervalos de pendiente resueltos antes de cada cambio. Coloreado de 5x5 para que dos coordenadas simultáneas no compartan ni cara ni término del objetivo. Energía cuadrática de diferencias de gradiente entre caras, más fidelidad 1/16 a la fuente; máximo de 2 m. Solo tierra natural a <=36 m de quiebros >=10 grados. Umbral de localización, no aceptación artística.

Conservar todos los vértices de toda celda que tenga plano de agua congelado, mar/playa, reserva vial, plataformas, corredores, cumbres, Narva y controles anteriores. Así el contorno físico/visible y cada cara que sostiene agua permanecen exactos. Conservar banda exterior de 66 m y bancos de los dos lagos grandes dentro de 72 m. Tierra baja no se rebaja por debajo de su valor previo; resto conserva mínimo 1,80 m. Metadatos intactos.

Presupuesto: un candidato, <=60 barridos o 10 minutos; parar si movimiento máximo <0,0001 m. Una corrección solo por defecto de implementación reproducible, nunca un cambio de pesos/radios/umbrales. No integrar sectores rechazados por el consumidor sin un recibo explícito de composición y nueva verificación.

## Verde definido antes de calcular

- Límites/metadata/regiones fijas exactos; ningún nuevo triángulo >max(fuente,35 grados), tolerancia de serialización 0,0001 grados. Consumidor vial actual PASS.
- Toda celda con plano físico y sus cuatro alturas exactas, por lo que contornos, profundidad, cuerpos, juntas y máscara de agua permanecen iguales. El mar y los modelos/objetos de agua no cambian.
- Consumidor independiente de normales por producto vectorial, sin usar energía del autor: energía angular media en aristas incidentes a zona editable baja >=10%; p99 y número >30 grados no aumentan en banco e interior natural. Inventario por 384 m y máximos conservado; no esconder empeoramientos con promedio. No se convierte una métrica en aceptación visual.
- Negativos cerrados: plano inclinado, pliegue de 45 grados, error en soporte acuático, carretera, cara sobrependiente y vértice fuera de dominio. Derivada/descenso comprobados contra suma explícita de términos en una malla pequeña; no se usa como prueba de acabado.
- Si pasa, WRP/paquete identificado, lectura nativa del cambio y vistas diurnas de taludes actuales. No TB/base final mientras sigan decisiones o defectos bloqueantes.

APIs verificadas: v30_common.py:26 (triángulos NW-SE), EV13/optimize_native_turns.py:41 (norma de gradiente por cara), EV24/audit_native_surface.py (producto vectorial independiente). Solo NumPy/SciPy del Python GIS. No cambios vanilla.
