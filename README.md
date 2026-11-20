# MediLogic — sistema experto con Prolog, FastAPI y React

> **English summary:** an expert system that ranks possible conditions from a patient's symptoms with SWI-Prolog rules, filters out treatments that clash with allergies, chronic conditions or current medication, and exports the result as a PDF. A FastAPI backend bridges Python and Prolog (`pyswip`); an admin panel edits the knowledge base and regenerates the Prolog file; an RPA importer loads diseases in bulk from JSON. Academic project — not a clinical tool.

Proyecto del laboratorio de *Inteligencia Artificial 1* (Universidad de San Carlos de Guatemala, 2.º semestre 2026). Trabajo individual.

**Lo más interesante del proyecto:**

- La lógica de inferencia vive en Prolog y se genera desde un JSON editable: el CRUD administrativo actualiza el JSON, regenera `medilogic.pl` y recarga el motor con un bloqueo, sin reiniciar el servidor.
- Prolog descarta tratamientos por alergias, condiciones crónicas, contraindicaciones y medicamentos actuales, y la respuesta conserva las opciones descartadas con su motivo.
- Importador RPA que detecta el formato, valida los campos y deja una bitácora por enfermedad.
- Pruebas con `pytest` para la inferencia, la API, el rollback, el RPA y el PDF.


Sistema experto académico de orientación preliminar desarrollado con Python, FastAPI, React/Vite, SWI-Prolog y `pyswip`.

> MediLogic no es una herramienta clínica. Sus resultados son una demostración educativa de inferencia simbólica y no sustituyen la evaluación de un profesional de salud.

## Arquitectura

```text
frontend React/Vite  ->  API FastAPI  ->  PrologEngine (pyswip)  ->  prolog/medilogic.pl
                              |                    ^
                              v                    |
                    data/knowledge_base.json  -- recarga bajo bloqueo
```

- `backend/`: API, modelos, autenticación, persistencia, generación PDF e integración con Prolog.
- `data/`: fuente estructurada para el CRUD administrativo.
- `prolog/`: archivo generado con hechos y reglas; no se edita manualmente.
- `rpa/`: lector/validador de archivos JSON o TXT con JSON, importador, CLI y ejemplo con tres enfermedades.
- `frontend/`: aplicación React independiente.
- `tests/`: pruebas de inferencia, API, rollback, RPA y PDF.
- `docs/`: manuales, decisiones, diagramas y casos clínicos.
- `output/pdf/`: manuales PDF generados.

## Requisitos

- Python 3.11 o superior.
- Node.js 20 o superior.
- SWI-Prolog 10.x (la integración usa `pyswip`; ambas arquitecturas deben coincidir).

## Instalación local

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m backend.auth --hash 'cambia-esta-clave-localmente'
```

Copia el hash impreso en `MEDILOGIC_ADMIN_PASSWORD_HASH` dentro de `.env`. No guardes la contraseña ni el hash real en Git.

Regenera y valida la base Prolog:

```bash
python -m scripts.generate_prolog
```

Inicia el backend:

```bash
uvicorn backend.main:app --reload --env-file .env
```

En otra terminal, instala y ejecuta el frontend:

```bash
cd frontend
npm install
npm run dev
```

Abre `http://127.0.0.1:5173`. El backend queda en `http://127.0.0.1:8000`; su documentación OpenAPI está en `/docs`.

## Afinidad y seguridad

La fórmula única implementada en Prolog es:

```text
puntos_obtenidos = suma de pesos de síntomas coincidentes
puntos_maximos = cantidad de síntomas de la enfermedad * 3
afinidad = puntos_obtenidos / puntos_maximos * 100
```

Los pesos son `leve=1`, `moderado=2` y `severo=3`. El resultado se redondea a dos decimales y se limita a 100%.

Antes de mostrar un candidato, Prolog verifica alergias directas, condiciones crónicas, contraindicaciones con la enfermedad diagnosticada e incompatibilidades con tratamientos actuales. Las opciones descartadas se conservan en la respuesta.

## API principal

Paciente: `GET /api/catalogos`, `POST /api/analisis`, `POST /api/informes/pdf`.

Administración autenticada: `POST /api/auth/login`, CRUD en `/api/admin/sintomas`, `/api/admin/enfermedades`, `/api/admin/medicamentos`, contraindicaciones, `/api/admin/prolog` y `/api/admin/rpa/import`.

## RPA

El RPA recibe un archivo `.json` o `.txt` cuyo contenido es JSON UTF-8 y soporta dos formatos: el **formato oficial del docente** (lista de enfermedades con `nombre_enfermedad`, `descripcion`, `sintomas_asociados`, `tratamiento_recomendado`, `medicamentos_contraindicados` y `sistema_cuerpo`; ver `ejemplos_aux/archivo_rpa.json`) y el formato interno de desarrollo (`rpa/examples/carga_tres_enfermedades.txt`). Ejemplo de ejecución:

```bash
python -m rpa.cli ejemplos_aux/archivo_rpa.json
```

El proceso detecta el formato, valida campos, registra automáticamente síntomas y medicamentos referenciados, crea las contraindicaciones de cada enfermedad, clasifica por sistema y tipo, actualiza JSON y `.pl`, recarga Prolog y genera la bitácora `logs/rpa_*.txt` con el detalle por enfermedad. La elección entre PyAutoGUI y TagUI queda pendiente de confirmación docente; el flujo requerido sí está implementado del lado del backend en Python.

## Pruebas y artefactos

```bash
pytest
cd frontend && npm run build
```

Los manuales PDF se regeneran con:

```bash
python scripts/generate_manual_pdfs.py
```

La bitácora de cambios administrativos está en `logs/changes.txt` durante la ejecución local y no se versiona.

## Decisiones pendientes de despliegue

El PDF de la asignación solicita GitHub Pages, pero GitHub Pages no ejecuta FastAPI, SWI-Prolog ni `pyswip`. Por eso este repositorio mantiene una arquitectura local-first y deja pendiente confirmar con el docente si el frontend debe publicarse en Pages y el backend en otro servicio permitido. El repositorio se mantuvo privado durante el desarrollo y se publicó después de la entrega.

## Entrega académica

La licencia es MIT. El colaborador `ixchop98` y la publicación final del repositorio se configuran en GitHub, fuera del código local. No se incluyen datos médicos reales ni credenciales.
