# Observatorio de Permanencia Aprendices Centro ASTIN

Abrir `index.html` con doble clic. No requiere internet ni servidor: Chart.js y los datos están embebidos.

- Datos: snapshot 2026-10-19, 56 fichas, 1.592 matrículas.
- Identidad: tipografías Work Sans / Calibri y paleta del Manual de Identidad Corporativa SENA 2024. Los logos no se incluyen; se insertan manualmente.
- Privacidad: el HTML no incluye nombres, documentos, celulares ni correos. Usa `AprendizID` hasheado.
- Lista nominal: `../data/restricted/lista_priorizada.csv` (PII, uso interno; no publicar).
- Actualización: ejecutar `scripts/01` a `04` y luego `06_generar_dashboard.py`.

## Pestañas

1. Resumen ejecutivo
2. Demografía y calidad (con brechas de datos)
3. Programas
4. Fichas
5. Temporal / cohortes (proxy por prefijo de ficha)
6. Riesgos
7. Predictivo y proyección de permanencia
