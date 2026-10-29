# Integración R0, antes de corrección

Suite única privada: 11 métodos, 8 PASS, 2 FAIL, 1 ERROR; 3.500s/73.4MB. No captura histórica. Tres resultados detenidos por el mismo bug: consumer línea132 reutiliza `cat` para una categoría de triángulo y destruye el catálogo dict antes de línea137. Es fallo interno, no corrupción de fuente.

Cobertura declarada incompleta del conjunto cerrado: N01 sólo altera un retorno mock, no cambia bytes entre inspección y carga; N09 no permuta categorías conservando cuentas; el informe literal no compara todavía todos los descriptores/digests contra bytes del fixture. N11 mezcla MEMBER_SCHEMA de helper con SCHEMA de descriptor: probar ambos sin cambiar códigos del helper sellado ni el oráculo original. N13 necesita bool de índice del terminal además del contador de cobertura. Estas deudas se resuelven sólo dentro de la corrección240s tras dictamen, o bloquean captura.

Oráculo adicional literal cap10x2 se fija aparte antes del código de corrección. Triángulos0–15 CAP_START y16–17 BODY; permutar0/17 conserva cuentas y debe rechazar CATEGORY. No expectativas calculadas por productor/consumidor.
