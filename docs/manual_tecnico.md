# Manual técnico

## Propósito

MediLogic es un prototipo académico de sistema experto. La aplicación recibe un perfil clínico sintético, consulta reglas Prolog y devuelve coincidencias explicables. No realiza diagnóstico definitivo.

## Componentes

1. React/Vite muestra formularios y resultados.
2. FastAPI valida el contrato HTTP y aplica autenticación.
3. `KnowledgeRepository` conserva el JSON, genera el `.pl` y registra cambios.
4. `PrologEngine` ejecuta consultas con `pyswip`, fuerza `load_files/2` al recargar y protege el estado compartido con un bloqueo.
5. ReportLab genera el informe PDF.
6. El módulo RPA procesa TXT JSON en el backend y escribe una bitácora.

## Contrato Prolog

El archivo exporta hechos para `symptom/4`, `disease/6`, `medication/3`, relaciones de síntomas/medicamentos y contraindicaciones. Las reglas públicas principales son:

- `severity_weight/2`: `leve=1`, `moderado=2`, `severo=3`.
- `diagnosis_metrics/6`: suma pesos, calcula máximo y afinidad.
- `matched_symptom/5`: devuelve el detalle de cada coincidencia.
- `urgency/4`: prioridad para síntomas severos o de alarma.
- `medication_evaluation/8`: descarta alergias, antecedentes, enfermedad y tratamientos incompatibles.
- `activated_rule/4`: aporta trazabilidad legible para el informe.

## Seguridad de medicamentos

El orden de evaluación evita que un candidato alérgico o contraindicado se presente como recomendado. Si todos los candidatos son descartados, la API devuelve una advertencia y `recommended_medication=null`.

## CRUD y rollback

El administrador no edita el `.pl` directamente. Los endpoints convierten el modelo validado a JSON, reconstruyen Prolog y comprueban su sintaxis antes de reemplazar archivos. Las relaciones inválidas se rechazan; por ejemplo, no se puede borrar un síntoma todavía usado por una enfermedad.

## Pruebas

Las pruebas cubren afinidad, severidad, urgencia, alergias, cronicidad, tratamientos, login, protección de rutas, CRUD, rollback, carga RPA y PDF. Ejecutar `pytest` desde la raíz y `npm run build` dentro de `frontend`.
