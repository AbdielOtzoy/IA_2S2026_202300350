# Decisiones de diseño

## Persistencia dual

`data/knowledge_base.json` es la fuente estructurada que alimenta el CRUD. `prolog/medilogic.pl` es la representación ejecutable de hechos y reglas. El generador vuelve a construir todo el `.pl`, por lo que no existen ediciones parciales frágiles.

## Recarga segura

Cada mutación valida el modelo, genera JSON y Prolog temporales, compila el Prolog con SWI, reemplaza ambos archivos atómicamente y llama a `load_files/2` con recarga forzada bajo un `RLock`. Si la recarga falla, se restauran los bytes anteriores y se intenta recargar la versión conocida.

## Fórmula fija

Se eligió la fórmula proporcional indicada en el contexto: suma de pesos coincidentes dividida entre el número total de síntomas definidos para la enfermedad multiplicado por 3. Así, una enfermedad con síntomas no marcados no recibe puntos artificiales y el resultado nunca supera 100%.

## Sesión administrativa

La autenticación usa un hash PBKDF2 configurado por entorno y tokens temporales en memoria. No hay credenciales en el repositorio ni persistencia de sesiones.

## Historial clínico

El historial se guarda solamente en `sessionStorage`, limitado a diez entradas y sin enviarse nuevamente al backend. Es una decisión deliberada para no crear un expediente persistente en este prototipo.

## RPA y ambigüedad del formato

La asignación menciona un TXT y también PyAutoGUI/TagUI, pero no fija un formato final en los archivos disponibles. El archivo entregado por el auxiliar (`ejemplos_aux/archivo_rpa.json`) confirma una lista JSON UTF-8 como entrada oficial. Se implementó un adaptador Python que acepta esa extensión `.json` y mantiene compatibilidad con `.txt`, con validación de campos, ejemplo de tres enfermedades y bitácora. La herramienta visual de automatización queda pendiente de confirmación docente.

## Despliegue

GitHub Pages se documenta como pendiente. Pages no ejecuta el backend Python-Prolog; no se inventa un despliegue incompatible con el requisito técnico.
