# Manual de usuario

## Iniciar un análisis

1. Abra la pantalla de inicio y seleccione **Iniciar análisis**.
2. Marque uno o más síntomas. Para cada síntoma seleccione leve, moderado o severo.
3. Marque alergias a medicamentos si aplica.
4. Marque enfermedades crónicas o antecedentes. El catálogo proviene de Prolog y solo muestra registros configurados como antecedentes.
5. Opcionalmente marque tratamientos actuales.
6. Pulse **Ejecutar análisis**.

## Interpretar el resultado

Cada tarjeta muestra afinidad, puntos obtenidos, puntos máximos, coincidencias, peso por severidad y la regla de urgencia. Las opciones seguras aparecen separadas de los medicamentos descartados y cada descarte explica su causa.

Una alerta inmediata significa que se detectó un síntoma severo o de alarma. Observación indica que hay síntomas moderados. Posible automanejo es solo una orientación del prototipo para perfiles leves; no reemplaza una valoración profesional.

## Historial y PDF

Los resúmenes recientes quedan únicamente en el navegador durante la sesión activa. **Descargar PDF** genera un informe con fecha, fórmula, coincidencias, urgencia, medicamentos y reglas activadas.

## Panel administrativo

1. Seleccione **Administración** e inicie sesión con credenciales definidas por `MEDILOGIC_ADMIN_USERNAME` y `MEDILOGIC_ADMIN_PASSWORD_HASH`.
2. Cree síntomas, medicamentos o enfermedades con identificadores en minúsculas y guiones bajos.
3. En una enfermedad, use ids existentes en los campos de síntomas y medicamentos.
4. Revise los registros y descargue `medilogic.pl` si necesita inspeccionar la base generada.
5. Seleccione un TXT RPA para cargar nuevos registros. El sistema valida, recarga y registra la bitácora.

## Errores comunes

- **No se pudo cargar el catálogo:** revise que FastAPI y SWI-Prolog estén instalados y que el backend esté activo.
- **Referencia inexistente:** cree primero el síntoma o medicamento usado por la enfermedad.
- **No se puede eliminar:** la entidad aún está relacionada; quite la relación desde la enfermedad o contraindicación.
- **Credenciales inválidas:** regenere el hash con `python -m backend.auth --hash ...` y actualice el `.env`.

