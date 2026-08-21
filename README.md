# MediLogic - IA 1

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
- `rpa/`: lector/validador de TXT JSON, importador, CLI y ejemplo con tres enfermedades.
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

La primera versión recibe un archivo `.txt` cuyo contenido es JSON UTF-8. El adaptador está aislado para cambiarlo cuando el docente entregue el formato oficial. El ejemplo carga tres enfermedades:

```bash
python -m rpa.cli rpa/examples/carga_tres_enfermedades.txt
```

El proceso valida referencias, actualiza JSON y `.pl`, recarga Prolog y crea `logs/rpa_*.txt`. La elección entre PyAutoGUI y TagUI queda pendiente de confirmación docente; el flujo requerido sí está implementado del lado del backend en Python.

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

El PDF de la asignación solicita GitHub Pages, pero GitHub Pages no ejecuta FastAPI, SWI-Prolog ni `pyswip`. Por eso este repositorio mantiene una arquitectura local-first y deja pendiente confirmar con el docente si el frontend debe publicarse en Pages y el backend en otro servicio permitido. El repositorio debe permanecer privado durante el desarrollo y hacerse público después de la calificación.

## Entrega académica

La licencia es MIT. El colaborador `ixchop98` y la publicación final del repositorio se configuran en GitHub, fuera del código local. No se incluyen datos médicos reales ni credenciales.
