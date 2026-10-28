# Adjudicación RoadB0 — 28-10-2026

Fable5.1 nativo SOUND-with-fixes,77.828s; entrada íntegra, sin herramientas.
Codex incorpora los cierres en el plan antes de implementar.

Aceptados: identidad de fuentes, separación config/WRP/consumidor efectivo,
metadatos de pivote/LOD/materiales, campos UNKNOWN, huella completa y límites
del corredor8m, P10 y ausencia de aceptación de conducción.

No se acepta multiplicar el presupuesto de extracción por componente: queda
una extracción120s/2GiB acotada a dos rectas y una curva, con salida parcial.
No se acepta N>=3 como prueba suficiente de convención del pivote ni imponer
segmento-segmento/tolerancia0 sin representación de las superficies. El conteo
no prueba motor y una línea de carretera puede cruzar interior de una superficie
sin que un test de borde aislado baste. Mantener positivos marginales/nodos.

Anclas comprobadas por Codex: road_asset_catalog_ev112.py:15-18 fuente instalada;
model_metadata conserva bbox/centros/LOD/materiales y anchoUNDETERMINED.
P:/DZ/structures/roads/config.cpp contiene clases de piezas y puentes, pero no
tiene identidad instalada demostrada. verify_ftt_pilot.py genera/verifica TXT,
no materializa el consumidor. historical-discriminator.py:36 liga referente
vial por ROAD_SHA;36-52 construyen corredor8m. Inventario de superficies no
resuelve referente independiente de agua, clases ni intención de anchura.

Plan REVISADO_PARA_IMPLEMENTAR. Código/extracción aún pendientes; esta revisión
no certifica consumidor/pivote ni coloca carretera o puente.
