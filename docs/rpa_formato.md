# Formato RPA

## Formato oficial del docente

El archivo `rpa/examples/formato_oficial_tutor.txt` (igual a `ejemplos_aux/archivo_rpa.json`) representa el formato oficial: un arreglo JSON UTF-8 donde cada elemento es una enfermedad con los campos:

| Campo | Tipo | Uso en la base |
|---|---|---|
| `nombre_enfermedad` | texto | `name` e `id` (minúsculas, sin espacios) |
| `descripcion` | texto | `description` |
| `sintomas_asociados` | lista de textos | síntomas de la enfermedad; se registran automáticamente si no existen |
| `tratamiento_recomendado` | lista de textos | medicamentos que tratan la enfermedad; se registran automáticamente si no existen |
| `medicamentos_contraindicados` | lista de textos | contraindicaciones tipo `disease` contra la enfermedad cargada |
| `sistema_cuerpo` | texto | `system` (clasificación por sistema corporal) |
| `tipo_enfermedad` (opcional) | texto | `type`; si no viene se registra `no_especificado` |

El archivo debe tener extensión `.txt` y contener JSON UTF-8. El flujo completo: lectura, validación de campos, alta automática de síntomas y medicamentos referenciados, creación de contraindicaciones, actualización y recarga de `prolog/medilogic.pl`, y bitácora `logs/rpa_*.txt` con el detalle por enfermedad. Si una enfermedad ya existía, se actualiza conservando su indicador de antecedente (`is_background`), que el formato oficial no incluye.

## Formato interno de desarrollo (retrocompatible)

`rpa/importer.py` también acepta un objeto JSON con `enfermedades` y opcionalmente `sintomas` y `medicamentos`, como `rpa/examples/carga_tres_enfermedades.txt`. El parser detecta el formato por la raíz del JSON (lista = oficial, objeto = interno) y está separado del endpoint y del CLI para adaptarse sin cambiar el motor.
