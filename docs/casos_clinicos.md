# Casos clínicos sintéticos y reflexión crítica

> Estos casos son datos controlados para evaluar coherencia del prototipo. No representan historias clínicas reales ni deben usarse para tomar decisiones de salud.

## Caso 1 - Influenza con alergia

**Entrada:** tos moderada, fiebre severa; alergia a ibuprofeno; sin antecedentes ni tratamientos actuales.

**Resultado esperado:** Influenza encabeza el resultado con `5/12 = 41.67%`, porque tos aporta 2 y fiebre aporta 3. La urgencia es inmediata por fiebre severa/bandera de alarma. Ibuprofeno se descarta por alergia y paracetamol permanece como candidato sintético seguro.

**Coherencia:** la salida es coherente con la base controlada y demuestra que la severidad modifica la afinidad. La afinidad no se interpreta como probabilidad clínica real.

## Caso 2 - Resfriado con antecedente

**Entrada:** tos leve; antecedente de hipertensión; tratamiento actual warfarina.

**Resultado esperado:** Resfriado común obtiene `1/12 = 8.33%`. La urgencia es posible automanejo orientativo por tratarse solo de un síntoma leve, con la advertencia general del sistema. Ibuprofeno se descarta por la contraindicación configurada para hipertensión; paracetamol y loratadina siguen como candidatos sintéticos.

**Coherencia:** el filtro evita mostrar el candidato conflictivo. El prototipo no determina dosis ni recomienda iniciar un tratamiento.

## Caso 3 - Rinitis alérgica parcial

**Entrada:** estornudos moderados y congestión nasal leve; alergia a paracetamol; sin antecedentes.

**Resultado esperado:** Rinitis alérgica obtiene `3/9 = 33.33%`: estornudos aporta 2 y congestión 1. La urgencia es observación recomendada por el síntoma moderado. Loratadina aparece como candidato porque es el medicamento asociado y no está en la lista de alergias.

**Coherencia:** la enfermedad aparece por coincidencia parcial y el resultado conserva el desglose de puntos.

## Reflexión crítica

El enfoque simbólico de MediLogic ofrece una ventaja clara: cada conclusión puede relacionarse con un hecho y una regla visible. El estudiante puede explicar por qué una coincidencia aportó uno, dos o tres puntos, cuál condición disparó la urgencia y por qué un medicamento fue descartado. Esta trazabilidad es valiosa en un prototipo educativo, pero no convierte el porcentaje calculado en una probabilidad médica. El motor solo conoce las relaciones que fueron escritas en el catálogo; si un paciente expresa un síntoma ambiguo, una combinación no contemplada o una presentación atípica, el resultado puede ser parcial o vacío. Prolog no infiere automáticamente conocimiento clínico que no esté representado.

Un modelo de aprendizaje automático o un modelo probabilístico podría aprender asociaciones a partir de muchos casos reales y producir una distribución de probabilidad condicionada por edad, contexto, evolución y otras variables. Ese enfoque manejaría mejor algunas correlaciones y gradientes de incertidumbre, aunque exigiría datos de calidad, validación clínica, control de sesgos y explicaciones apropiadas. Las reglas fijas de MediLogic son más fáciles de auditar, pero no estiman sensibilidad, especificidad ni riesgo poblacional. La afinidad es una métrica transparente de cobertura de síntomas, no una probabilidad estadística.

La escalabilidad también es distinta. Con pocas enfermedades, una persona puede revisar las relaciones del JSON y regenerar el archivo `.pl`. Con miles de enfermedades, síntomas, tratamientos y excepciones, el número de reglas crece, aparecen conflictos entre expertos y la revisión manual se vuelve costosa. Un sistema moderno puede usar pipelines de datos, embeddings, modelos probabilísticos o agentes que ayuden a buscar y proponer relaciones; aun así, la supervisión humana, la procedencia de los datos y las pruebas seguirían siendo indispensables. Una arquitectura híbrida podría usar reglas para restricciones de seguridad y un modelo validado para priorizar hipótesis, manteniendo una capa de explicación y rechazo de recomendaciones inseguras.

Finalmente, un agente autónomo no debería convertir esta aplicación en una autoridad clínica. Podría automatizar la ingestión de fuentes o detectar relaciones faltantes, pero necesitaría límites de herramientas, registro de decisiones y aprobación experta. La elección de MediLogic es intencional: demostrar inferencia simbólica, reconocer sus límites y dejar claro que un sistema académico de reglas no sustituye un profesional de salud.

