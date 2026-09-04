# Casos clínicos sintéticos y reflexión crítica

> Estos casos son datos controlados para evaluar coherencia del prototipo. No representan historias clínicas reales ni deben usarse para tomar decisiones de salud. Las salidas fueron verificadas contra el motor Prolog real del sistema.

## Caso 1 - Influenza con alergia

**Entrada:** tos moderada, fiebre severa; alergia a ibuprofeno; sin antecedentes ni tratamientos actuales.

**Resultado generado por MediLogic:**

- Diagnóstico principal: Influenza con afinidad `5/12 = 41.67%` (tos aporta 2, fiebre aporta 3).
- Urgencia: `inmediata` con acción "Consulta médica inmediata sugerida"; regla determinante: `sintoma_severo_o_alarma` (fiebre severa).
- Medicamentos: ibuprofeno **descartado** por `alergia` (`medication_evaluation/8`, primer criterio de descarte); paracetamol queda como candidato seguro y es el recomendado.
- Reglas activadas (`activated_rule/4`):
  - `coincidencia_de_sintomas`: se sumaron los pesos Prolog leve=1, moderado=2, severo=3.
  - `severidad_ponderada`: la severidad declarada aportó peso a cada coincidencia.
  - `regla_de_urgencia`: urgencia determinada con severidad y banderas de alarma.
  - `medicamento_seguro`: el candidato pasó las comprobaciones de seguridad.

**Coherencia:** la salida es coherente con la base controlada y demuestra que la severidad modifica la afinidad y la urgencia. La afinidad no se interpreta como probabilidad clínica real.

## Caso 2 - Síntoma leve con antecedente de hipertensión y tratamiento actual

**Entrada:** tos leve; antecedente de hipertensión; tratamiento actual warfarina; sin alergias.

**Resultado generado por MediLogic:**

- Diagnóstico principal: Rinitis alérgica con `1/9 = 11.11%` (tos también pertenece a esa enfermedad y su denominador es menor), urgencia `automanejo` con regla `solo_sintomas_leves`; loratadina permanece segura.
- También aparecen Influenza y Resfriado común con `1/12 = 8.33%`; en ambos, ibuprofeno es **descartado** por `chronic_condition`, porque existe la contraindicación `contraindication('ibuprofeno', 'chronic_condition', 'hipertension', ...)`. Esto valida el filtro por antecedente incluso cuando la enfermedad principal no lo necesita.
- Reglas activadas: `coincidencia_de_sintomas`, `severidad_ponderada`, `regla_de_urgencia` y `medicamento_seguro` (ver Caso 1); el descarte proviene de `medication_evaluation/8` con código `chronic_condition`.

**Coherencia:** el ordenamiento por afinidad favorece a la enfermedad con menor denominador ante pesos iguales, comportamiento esperado de la fórmula documentada. El filtro por cronicidad evita mostrar el candidato conflictivo en las enfermedades donde sí es candidato. El prototipo no determina dosis ni recomienda iniciar un tratamiento.

## Caso 3 - Rinitis alérgica parcial

**Entrada:** estornudos moderados y congestión nasal leve; alergia a paracetamol; sin antecedentes.

**Resultado generado por MediLogic:**

- Diagnóstico principal: Rinitis alérgica con `3/9 = 33.33%` (estornudos aporta 2, congestión 1), urgencia `observacion` con regla `sintomas_moderados` y acción "Observación recomendada".
- Medicamentos: loratadina aparece como candidato seguro y recomendado; la alergia a paracetamol no influye porque ese fármaco no es candidato de la enfermedad.
- Reglas activadas: `coincidencia_de_sintomas`, `severidad_ponderada`, `regla_de_urgencia` y `medicamento_seguro`.

**Coherencia:** la enfermedad aparece por coincidencia parcial y el resultado conserva el desglose de puntos que permite explicar el porcentaje.

## Reflexión crítica

El enfoque simbólico de MediLogic ofrece una ventaja clara: cada conclusión puede relacionarse con un hecho y una regla visible. El estudiante puede explicar por qué una coincidencia aportó uno, dos o tres puntos, cuál condición disparó la urgencia y por qué un medicamento fue descartado. Esta trazabilidad es valiosa en un prototipo educativo, pero no convierte el porcentaje calculado en una probabilidad médica. El motor solo conoce las relaciones que fueron escritas en el catálogo; si un paciente expresa un síntoma ambiguo, una combinación no contemplada o una presentación atípica, el resultado puede ser parcial o vacío. Prolog no infiere automáticamente conocimiento clínico que no esté representado.

Un modelo de aprendizaje automático o un modelo probabilístico podría aprender asociaciones a partir de muchos casos reales y producir una distribución de probabilidad condicionada por edad, contexto, evolución y otras variables. Ese enfoque manejaría mejor algunas correlaciones y gradientes de incertidumbre, aunque exigiría datos de calidad, validación clínica, control de sesgos y explicaciones apropiadas. Las reglas fijas de MediLogic son más fáciles de auditar, pero no estiman sensibilidad, especificidad ni riesgo poblacional. La afinidad es una métrica transparente de cobertura de síntomas, no una probabilidad estadística.

La escalabilidad también es distinta. Con pocas enfermedades, una persona puede revisar las relaciones del JSON y regenerar el archivo `.pl`. Con miles de enfermedades, síntomas, tratamientos y excepciones, el número de reglas crece, aparecen conflictos entre expertos y la revisión manual se vuelve costosa. Un sistema moderno puede usar pipelines de datos, embeddings, modelos probabilísticos o agentes que ayuden a buscar y proponer relaciones; aun así, la supervisión humana, la procedencia de los datos y las pruebas seguirían siendo indispensables. Una arquitectura híbrida podría usar reglas para restricciones de seguridad y un modelo validado para priorizar hipótesis, manteniendo una capa de explicación y rechazo de recomendaciones inseguras.

Finalmente, un agente autónomo no debería convertir esta aplicación en una autoridad clínica. Podría automatizar la ingestión de fuentes o detectar relaciones faltantes, pero necesitaría límites de herramientas, registro de decisiones y aprobación experta. La elección de MediLogic es intencional: demostrar inferencia simbólica, reconocer sus límites y dejar claro que un sistema académico de reglas no sustituye un profesional de salud.
