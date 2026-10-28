# Sonda completa de lecho y carretera: validadores preparados

Estado: **VALIDADO OFFLINE; CALIBRACIÓN FRESCA Y SONDA COMPLETA SIN EJECUTAR**.
Esta publicación no repara por sí sola el resto del mapa ni acredita aceptación
visual, conducción, RAM o calidad global.

El consumidor mantiene los 2658 puntos originales y separa terreno, Roadway,
agua, RaycastRV y Bullet BUILDING. Conserva las tolerancias: 0,01 m para terreno,
0,03 m para Roadway/RV, 0,05 m para agua y 0,01 m respecto del margen Bullet
calibrado. Los 21 puntos con incertidumbre siguen presentes y no pueden dar
PASS completo mientras no se resuelva su cobertura. Cualquier fallo decisivo
domina el resultado inconcluso.

La revisión independiente de Fable 5.1 produjo dos informes y sus correcciones
están adjudicadas en el plan. Una contraprueba adicional detectó que modificar
el valor de calibración después del gate aún permitía aceptar evidencia.
La corrección vincula los hashes de calibración y sello al recibo de lanzamiento,
los vuelve a comprobar durante la ejecución y exige su identidad al consumir
el resultado. Se conserva el contraejemplo anterior al arreglo.

Validación offline registrada:

- 22 pruebas del consumidor de canales.
- 9 controles de identidad, calibración y cierre (positivo y ocho negativos).
- 8 controles del gate anterior a la cola.
- 7 escenarios simulados del lifecycle.
- 16 mediciones nativas ya registradas y siete mutaciones negativas como
  regresión de código. Su calibración es histórica, no una ejecución nueva.
- 1866 caras triangulares verificadas; el modelo vecino 0012 tiene cobertura
  completa entre Roadway y techo Geometry, con error vertical cero.

Los datos de expectativa usan las caras Roadway con textura water_ext reales.
La lámina Visual llega a separarse 0,25 m y no sirve como sustituto de aquella.
La muestra somera 1769 queda explícitamente inconclusa para profundidad porque
el productor consulta a terreno +0,01 m. No se eleva ninguna tolerancia.

El paquete y las dos misiones están preparados y sellados. La primera admisión
FIFO agotó 200,299 s sin conceder un run; se respetó la prueba ajena. El recibo
público omite la identidad y actividad de ese ocupante. La siguiente ejecución
debe revalidar el sello y usar la cola oficial; calibración nueva antes de sonda.

Los scripts en source son instantáneas con rutas del entorno original, no una
CLI portátil. Preparador, descubrimiento, pruebas y sello ya están consumidos:
no relanzarlos sobre sus salidas existentes. Gate/consumidor/coordinador sólo se
usan siguiendo el estado vivo y con identidad de un run propio. No se publican
PBO, modelos vanilla, credenciales, volcados ni historial privado.

Siguen abiertos C1 sin revisión humana, nueve regresiones visuales, RAM, el
resto de los ríos y costas, y el council ampliado solicitado.
