# Formato RPA provisional

Hasta recibir el ejemplo oficial del docente, `rpa/importer.py` acepta `.txt` UTF-8 con JSON. La raíz contiene `enfermedades` y opcionalmente `sintomas` y `medicamentos`. Cada enfermedad usa los mismos campos que `data/knowledge_base.json`.

El archivo `rpa/examples/carga_tres_enfermedades.txt` demuestra tres altas, una creación de síntoma, clasificación por sistema/tipo, validación de relaciones, recarga de Prolog y bitácora. El parser está separado del endpoint y del CLI para poder adaptar el formato sin cambiar el motor.

