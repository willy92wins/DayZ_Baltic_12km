# EV22 — máscara desplegada frente al agua física actual

Auditoría de toda la superficie a 1 m/px, sin solapar tiles ni basarse en capturas. Se leen las 1.024 máscaras PAA del PBO desplegado EV16 y se convierten con ImageToPAA instalado. Se coteja el suelo triangular actual y el campo de agua congelado, ya validado contra el agua compilada. No se vuelve a inferir agua desde colores del satélite o desde clases nominales.

Contrato: agua nominal visible debe usar la superficie de grava sin vegetación. Se inventarían por separado los píxeles interiores con margen de profundidad y los de borde, para no confundir filtrado de textura con un desalineado grueso. La grava seca no demuestra pintura errónea: también pertenece a caminos y orillas legítimas. El aspecto del satélite y todas las distancias gráficas no se cierran por este gate.

Una pasada completa, hasta cuatro conversiones en paralelo. Máximo una reparación de instrumentación si falla el decodificador. Control positivo de canal mojado, negativo de máscara adulterada y control de muestreo triangular independiente. Sin modificar mapas, materiales o niveles.
