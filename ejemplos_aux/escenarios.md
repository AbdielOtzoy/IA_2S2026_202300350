MediLogic (Sistema Experto Médico)
│
├── 1. MÓDULO PACIENTE (Diagnóstico y Consulta)
│ ├── 1.1. Ingreso de Datos Básicos
│ │ ├── Paso 1: Seleccionar síntomas principales mediante checkboxes.
│ │ ├── Paso 2: Indicar nivel de severidad por cada síntoma seleccionado (Leve /
Moderado / Severo).
│ │ ├── Paso 3: Registrar alergias a medicamentos
│ │ └── Paso 4: Registrar enfermedades crónicas preexistentes
│ │
│ ├── 1.2. Proceso de Inferencia Lógica (Motor Prolog)
│ │ ├── Paso 1: Python envía los datos clínicos al archivo .pl mediante pyswip.
│ │ ├── Paso 2: Prolog evalúa hechos, reglas y contraindicaciones.
│ │ ├── Paso 3: Se calcula el porcentaje de afinidad ponderando la severidad (Leve=1,
Moderado=2, Severo=3).
│ │ └── Escenarios posibles:
│ │ ├── Escenario A: Coincidencia alta con una enfermedad y sin contraindicaciones
(Diagnóstico directo + Medicamento seguro).
│ │ ├── Escenario B: Conflicto detectado (El medicamento ideal está contraindicado
por alergia/crónica -> Prolog descarta y busca alternativa segura).
│ │ └── Escenario C: Síntomas insuficientes o no concluyentes (Sin coincidencias
directas o afinidad baja).
│ │
│ ├── 1.3. Generación de Resultados e Informes
│ │ ├── Paso 1: Despliegue visual de enfermedades ordenadas por porcentaje de
afinidad.
│ │ ├── Paso 2: Visualización del nivel de urgencia sugerido ("Consulta inmediata",
"Observación", etc.).
│ │ ├── Paso 3: Historial local temporal de sesión activa en la interfaz.
│ │ └── Paso 4: Opción de descarga del informe en PDF (incluye resumen,
advertencias, medicamentos y reglas activadas).
│ │
├── 2. MÓDULO ADMINISTRADOR (Gestión de Base de Conocimiento Manual)
│ ├── 2.1. Autenticación
│ │ └── Paso 1: Ingreso de credenciales válidas de administrador.
│ │
│ ├── 2.2. Gestión de Entidades
│ │ ├── Paso 1: Crear, editar o eliminar enfermedades, síntomas o medicamentos.
│ │ └── Paso 2: Definir relaciones de contraindicación y clasificación por sistema
corporal.
│ │
│ └── 2.3. Sincronización del Archivo Lógico
│ ├── Paso 1: El backend procesa los cambios hechos en la interfaz.
│ ├── Paso 2: Sobrescribe físicamente el archivo `.pl` en el disco.
│ └── Paso 3: Ejecuta la recarga dinámica en el motor Prolog (`consult/1`) para
actualizar la memoria sin reiniciar el sistema.
│
└── 3. MÓDULO RPA Y AUTOMATIZACIÓN (Carga Masiva)
├── 3.1. Recepción y Estructura del Archivo de Entrada (.txt)
│ ├── *Definición obligatoria para pruebas:* El archivo debe tener una estructura
tabular o delimitada clara (JSON plano con campos: `Nombre, Descripcion,
SintomasAsociados, MedicamentosContraindicados, SistemaCuerpo`).
│ └── Paso 1: El administrador selecciona el archivo `.txt` estructurado desde la
interfaz.
│
├── 3.2. Ejecución del Robot (Python + PyAutoGUI / TagUI)
│ ├── Paso 1: El RPA lee iterativamente el archivo plano.
│ ├── Paso 2: Simula el llenado automatizado de los formularios del panel de
administrador o inyecta directamente los datos en la base lógica.
│ └── Escenarios posibles en pruebas:
│ ├── Escenario A (Éxito): El archivo cumple con el formato exacto, el robot
completa la carga masiva y actualiza el `.pl`.
│ └── Escenario B (Fallo de Formato): El archivo tiene campos faltantes o estructura
incorrecta, el robot se detiene o lanza una excepción controlada.
│
└── 3.3. Generación de Bitácora (Archivo Plano)
├── Paso 1: El robot genera un archivo de salida (ej. `bitacora_rpa.txt`) detallando qué
elementos fueron agregados con éxito y la fecha/hora.
└── Paso 2: El administrador valida el archivo de salida como comprobante de la
ejecución.
Flujo Completo del Sistema MediLogic (Desde el Sistema Vacío hasta la Calificación)
│
├── ESTADO INICIAL DEL SISTEMA
│ └── Base de datos lógica en Prolog (.pl) y paneles vacíos (sin enfermedades, síntomas
ni contraindicaciones registradas).
│
├── 1. MÓDULO ADMINISTRADOR - CARGA MASIVA (RPA)
│ ├── 1.1. Preparación del Archivo de Entrada
│ │ ├── Qué revisar: Que los estudiantes utilicen la estructura JSON/plana
estandarizada (con campos: nombre, descripción, síntomas, contraindicaciones, sistema
corporal).
│ │ └── Escenarios:
│ │ ├── Éxito: El archivo está bien estructurado.
│ │ └── Fallo: Archivo con formato incorrecto o campos vacíos.
│ ├── 1.2. Ejecución del Robot (Python + PyAutoGUI / TagUI)
│ │ ├── Qué revisar: Que el RPA lea el archivo y simule la inserción o actualización de la
base de conocimiento de forma automatizada desde el backend.
│ │ └── Escenarios:
│ │ ├── Éxito: El robot procesa todas las líneas y actualiza el archivo `.pl`.
│ │ └── Fallo: El robot se detiene por errores de interfaz o sintaxis.
│ └── 1.3. Generación de Bitácora y Sincronización
│ ├── Qué revisar: Que se genere el archivo plano de bitácora con el registro de la
carga y que el motor Prolog recargue los hechos (`consult/1`)[cite: 2].
│ └── Escenarios:
│ ├── Éxito: Bitácora generada y archivo `.pl` actualizado con las enfermedades del
JSON.
│ └── Fallo: El `.pl` no refleja los cambios y requiere reinicio manual.
│
├── 2. MÓDULO ADMINISTRADOR - GESTIÓN MANUAL (Opcional / Ajustes)
│ ├── 2.1. Panel de Control Protegido por Credenciales
│ │ └── Qué revisar: Que el acceso esté bloqueado para usuarios sin credenciales[cite:
2].
│ ├── 2.2. ABM (CRUD) de Enfermedades, Síntomas y Medicamentos
│ │ ├── Qué revisar: Crear, editar o eliminar registros manualmente[cite: 2].
│ │ └── Escenario: Los cambios se escriben y guardan correctamente en el disco y
memoria lógica[cite: 2].
│ └── 2.3. Gestión de Contraindicaciones (Doble Nivel)
│ ├── Qué revisar: Que se puedan configurar contraindicaciones tanto entre fármacos y
patologías como con alergias/enfermedades crónicas.
│ └── Escenario: Configuración correcta de restricciones de seguridad farmacológica.
│
├── 3. MÓDULO PACIENTE - FLUJO ANÓNIMO Y DIAGNÓSTICO
│ ├── 3.1. Pantalla de Bienvenida
│ │ └── Qué revisar: Acceso libre sin necesidad de login[cite: 2], mostrando la
advertencia de que es una herramienta de apoyo preliminar.
│ ├── 3.2. Ingreso de Perfil Clínico
│ │ ├── Paso 1: Selección de síntomas mediante checkboxes[cite: 2].
│ │ ├── Paso 2: Asignación del nivel de severidad por síntoma (*Leve=1, Moderado=2,
Severo=3*).
│ │ ├── Paso 3: Registro opcional de alergias a medicamentos[cite: 2].
│ │ └── Paso 4: Registro opcional de enfermedades crónicas preexistentes (diabetes,
hipertensión, etc.)[cite: 2].
│ ├── 3.3. Inferencia Lógica (Motor Prolog)
│ │ ├── Qué revisar: Que Python envíe los datos a Prolog y este ejecute las reglas de
afinidad y seguridad[cite: 2].
│ │ └── Escenarios de Evaluación durante la Calificación:
│ │ ├── Escenario A (Diagnóstico Estándar): Síntomas coinciden con una enfermedad
cargada; el sistema calcula el porcentaje de afinidad ponderando la severidad y ordena los
resultados de mayor a menor probabilidad[cite: 2].
│ │ ├── Escenario B (Conflicto por Alergia / Crónica): El medicamento ideal para una
enfermedad está contraindicado con las alergias o padecimientos crónicos del usuario;
Prolog debe detectarlo, descartar el fármaco de riesgo y sugerir una alternativa segura[cite:
2].
│ │ └── Escenario C (Sin Coincidencias): Síntomas insuficientes o no concluyentes; el
sistema maneja la respuesta sin colapsar.
│ └── 3.4. Emisión de Resultados e Informes
│ ├── Qué revisar:
│ │ ├── Visualización de gráficos de barras de afinidad o tablas[cite: 2].
│ │ ├── Despliegue del nivel de urgencia (*"Consulta médica inmediata sugerida",
"Posible automanejo", "Observación recomendada"*)[cite: 2].
│ │ ├── Historial local temporal de sesión activa[cite: 2].
│ │ └── Opción de descarga del informe en PDF con fecha, advertencias,
medicamentos y reglas activadas[cite: 2].
│ └── Escenario: El PDF se genera correctamente con toda la estructura solicitada.
│
└── 4. EVALUACIÓN Y REFLEXIÓN CRÍTICA
└── 4.1. Revisión del Documento de Casos Clínicos y Análisis Crítico
├── Qué revisar: Que se presenten los 3 casos clínicos requeridos y la sección de
reflexión teórica (IA simbólica vs. IA moderna, manejo de incertidumbre y escalabilidad)[cite:
2].
└── Escenario: Profundidad y coherencia en el análisis crítico presentado por el
estudiante.
Flujo de Pruebas con Datos Reales para la Calificación
│
├── ESTADO 0: SISTEMA VACÍO
│ └── Verificación inicial: El archivo `.pl` está vacío, no hay enfermedades ni síntomas
registrados y la interfaz muestra ceros o listas vacías[cite: 2].
│
├── PASO 1: CARGA MASIVA AUTOMATIZADA (MÓDULO RPA)
│ ├── Acción de Prueba:
│ │ * El administrador carga el archivo JSON con los datos de "Hipertensión" y "Asma
Bronquial".
│ │ * El robot (RPA) ejecuta la lectura e inyección de datos[cite: 2].
│ ├── Qué se valida:
│ │ * El robot procesa el archivo de forma completamente automatizada[cite: 2].
│ │ * Se genera el archivo plano de bitácora con el reporte de carga.
│ │ * El archivo `.pl` se actualiza en el disco y Prolog recarga los hechos (`consult/1`) en
caliente[cite: 2].
│ └── Resultado esperado: El sistema ya cuenta con las reglas y hechos de Hipertensión
y Asma en memoria[cite: 2].
│
├── PASO 2: PRUEBA DE CONSULTA Y DIAGNÓSTICO (MÓDULO PACIENTE -
ANÓNIMO)
│ ├── Acceso: El usuario ingresa a la pantalla principal sin necesidad de iniciar
sesión[cite: 2].
│ │
│ ├── CASO DE PRUEBA A: Diagnóstico Estándar y Ponderación por Severidad
│ │ ├── Datos de entrada ingresados por el usuario:
│ │ │ * Síntoma 1: dolor_cabeza (Severidad: Severo = 3 pts)[cite: 2]
│ │ │ * Síntoma 2: mareo (Severidad: Moderado = 2 pts)[cite: 2]
│ │ │ * Alergias: Ninguna[cite: 2]
│ │ │ * Enfermedades crónicas: Ninguna[cite: 2]
│ │ ├── Proceso en Prolog: Cruza los síntomas, aplica la ponderación por severidad y
calcula el porcentaje de afinidad[cite: 2].
│ │ └── Comportamiento esperado al consultar:
│ │ * El sistema muestra los resultados ordenados de mayor a menor probabilidad[cite:
2].
│ │ * **Hipertensión** aparece en primer lugar con un porcentaje de afinidad alto
(debido a que los síntomas coinciden y son severos)[cite: 2].
│ │ * Se sugiere el medicamento estándar (ej. un antihipertensivo seguro)[cite: 2].
│ │ * Se emite el nivel de urgencia correspondiente (ej. "Consulta médica inmediata
sugerida")[cite: 2].
│ │ * Se despliegan las reglas Prolog activadas que justifican el diagnóstico[cite: 2].
│ │
│ └── CASO DE PRUEBA B: Detección de Conflictos y Restricción de Contraindicaciones
│ ├── Datos de entrada ingresados por el usuario:
│ │ * Síntoma 1: dolor_cabeza (Severidad: Moderado)[cite: 2]
│ │ * Síntoma 2: mareo (Severidad: Leve)[cite: 2]
│ │ * Alergias: Ninguna[cite: 2]
│ │ * Enfermedades crónicas / Antecedentes: **Hipertensión** (Registrada
previamente en su perfil o detectada)[cite: 2].
│ ├── Proceso en Prolog: El motor evalúa las contraindicaciones configuradas para la
Hipertensión[cite: 2].
│ └── Comportamiento esperado al consultar:
│ │ * El sistema detecta que el medicamento ideal inicial (ej. *Ibuprofeno* según la
base de datos de ejemplo) está contraindicado para pacientes hipertensos[cite: 2].
│ │ * **Acción clave de Prolog:** Descarta automáticamente el fármaco de riesgo para
evitar complicaciones[cite: 2].
│ │ * Sugiere un medicamento alternativo seguro que cumpla la misma función pero
sin repercusiones para su condición crónica[cite: 2].
│ │ * El informe detalla la regla de contraindicación que se activó para hacer la
exclusión[cite: 2].
│
├── PASO 3: VALIDACIÓN DE REPORTES E HISTORIAL (PACIENTE)
│ ├── Comportamiento esperado:
│ │ * El usuario visualiza los resultados mediante gráficos de barras de afinidad o tablas
limpias[cite: 2].
│ │ * El historial local temporal de la sesión permite alternar y ver las consultas hechas
durante la navegación[cite: 2].
│ │ * Al hacer clic en descargar PDF, se genera un documento formal que incluye la
fecha, resumen del diagnóstico, advertencias, medicamentos seguros y las reglas Prolog
activadas[cite: 2].
│
└── PASO 4: REVISIÓN DE LA EVALUACIÓN CRÍTICA (HABILIDADES)
└── Qué verificar en el documento adjunto:
* Los 3 casos clínicos documentados con sus datos de entrada y salidas reales[cite: 2].
* La profundidad de la reflexión crítica comparando las limitaciones del sistema basado
en reglas en Prolog frente a los modelos probabilísticos de Machine Learning y Agentes de
IA[cite: 2].