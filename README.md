# Gemelos digitales — prototipo inicial

Ejecutar `pip install -r requirements.txt` y `python app.py`. Abrir http://localhost:8000. En Codespaces abrir el puerto 8000.

El dataset original se incluye. El modelo usa snapshots diarios, calibración de duraciones positivas de 2025 y una fecha de prueba de 2026. El aeropuerto es sintético. No hay conexión en vivo.

## Alcance pendiente
No es una entrega final: faltan reconstrucción completa del estado inicial, eventos ANS durante la jornada, reprogramación, almacén compartido, simulación de escenarios desde la copia sincronizada, optimizador formal (el control actual es una heurística), validación temporal cuantitativa, 5000 réplicas por estrategia y escenario, fichas completas, bitácora histórica y evidencia de sustentación. La simulación actual es una planificación diaria simplificada con reproducción visual. Las distribuciones se ajustan globalmente, no por perfil. El traslado estimado y kits son supuestos. El aeropuerto usa un umbral ilustrativo de 30 minutos y no horarios reales de vuelos.
