# Video de demostración del RPA

Entregable obligatorio (5 pts): video del funcionamiento completo del RPA con **al menos tres enfermedades cargadas y categorizadas**. Este documento define el guion, la preparación y cómo embeberlo en GitHub.

## 1. Preparación antes de grabar

```bash
# Restaurar el estado base para una toma limpia (4 enfermedades originales)
git checkout -- data/knowledge_base.json prolog/medilogic.pl
rm -f logs/rpa_*.txt

# Backend y frontend en terminales separadas
uvicorn backend.main:app --reload --env-file .env
cd frontend && npm run dev   # http://127.0.0.1:5173
```

Verificar que `rpa/examples/formato_oficial_tutor.txt` contiene las 4 enfermedades del formato oficial del docente, incluido el campo `tratamiento_recomendado`.

## 2. Guion sugerido (3-5 minutos)

1. **Intro (15 s):** nombre del proyecto, integrante y objetivo del RPA: cargar enfermedades desde el archivo oficial del docente sin editar el `.pl` a mano.
2. **Archivo de entrada (30 s):** abrir `rpa/examples/formato_oficial_tutor.txt` y señalar los campos: `nombre_enfermedad`, `sintomas_asociados`, `tratamiento_recomendado`, `medicamentos_contraindicados`, `sistema_cuerpo`.
3. **Estado inicial (30 s):** módulo de paciente → el catálogo aún no incluye Asma bronquial, Diabetes tipo 2 ni Gastroenteritis aguda.
4. **Ejecución visual del RPA (60 s):** Administración → iniciar sesión → sección "Automatización robótica" → seleccionar el TXT → "Ejecutar RPA". Mostrar el resultado JSON: 3 enfermedades creadas, 1 actualizada, síntomas/medicamentos/contraindicaciones creados.
5. **Bitácora (30 s):** abrir `logs/rpa_*.txt` y mostrar el detalle por enfermedad y la validación Prolog.
6. **Verificación del `.pl` (30 s):** en el panel admin, visualizar/descargar `medilogic.pl` y buscar `asma_bronquial`; señalar la clasificación por sistema (`respiratorio`, `endocrino`, `digestivo`, `circulatorio`) y las contraindicaciones generadas.
7. **Comprobación end-to-end (60 s):** módulo de paciente → recargar → Asma bronquial aparece → analizar con `dificultad_respiratoria` severa y `silbido_pecho` moderado, alergia a Salbutamol → el resultado muestra Salbutamol descartado por alergia y Fluticasona como candidato seguro (prueba de que `tratamiento_recomendado` alimenta el motor).
8. **Alternativa CLI (20 s):** `python -m rpa.cli rpa/examples/formato_oficial_tutor.txt` (opcional, demuestra ejecución por terminal).
9. **Cierre (15 s):** advertencia académica y mención de la bitácora como evidencia.

## 3. Grabación en macOS

- **QuickTime Player:** Archivo → Nueva grabación de pantalla; grabar la pantalla completa con el micrófono activo para narrar.
- **OBS Studio** (opción con escenas y mejor control de audio): fuente "Captura de pantalla", 1920x1080, 30 fps.
- Resolver la pantalla en una sola vista (dos mitades: frontend + editor/bitácora) para evitar cortes.

## 4. Publicación y embebido en GitHub

1. Exportar en MP4 (H.264) con nombre `videos/demostracion_rpa.mp4`. Mantener el archivo bajo 50 MB si es posible (GitHub advierte sobre archivos grandes; el límite duro es 100 MB).
2. Opción recomendada para que se reproduzca embebido: crear una **release** (p. ej. `v2.0-entrega-final`), adjuntar el MP4 como binario de la release y copiar la URL de `github.com/user-attachments/...`.
3. En `README.md`, embeber la URL de la release dentro del Markdown; GitHub la muestra con reproductor nativo:

   ```markdown
   ## Video del RPA
   [![Demostración RPA](https://img.youtube.com/vi/XXXX/0.jpg)](URL-DE-LA-RELEASE)
   ```

   o directamente `[Ver video del RPA](URL-DE-LA-RELEASE)`. Si se sube a YouTube (no listado), usar el formato de miniatura anterior.
4. Confirmar también el archivo `videos/demostracion_rpa.mp4` en el repositorio como respaldo descargable.

## 5. Lista de verificación antes de finalizar

- [ ] Se ven cargarse y categorizarse al menos 3 enfermedades.
- [ ] Aparece la bitácora TXT generada.
- [ ] Se muestra el `.pl` actualizado y recargado.
- [ ] Un análisis del paciente usa una enfermedad cargada por el RPA.
- [ ] Audio claro o subtítulos; duración menor a 5 minutos.
- [ ] Video embebido en GitHub y archivo presente en `videos/`.
