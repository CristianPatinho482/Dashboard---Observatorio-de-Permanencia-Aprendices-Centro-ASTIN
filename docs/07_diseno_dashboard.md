# Diseño del dashboard — Caracterización de Aprendices Centro ASTIN

## 1. Principio de diseño

El tablero responde una pregunta por página, de lo general a lo específico:

1. **Resumen:** ¿cuál es la situación y qué exige atención hoy?
2. **Demografía y calidad:** ¿qué sabemos y qué no sabemos de la población?
3. **Programas:** ¿dónde se concentra la matrícula y la pérdida?
4. **Fichas:** ¿qué fichas están en riesgo y con qué incertidumbre?
5. **Temporal / cohortes:** ¿cómo cambia la pérdida por generación?
6. **Riesgos:** ¿cómo se valida el semáforo y qué fichas son críticas?
7. **Predictivo:** ¿qué prioriza el modelo y qué no puede predecir?

La narrativa es intencionalmente conservadora: primero el dato observado, luego la incertidumbre, después la priorización. El rojo no se usa para dramatizar; se usa para indicar una banda de riesgo definida.

---

## 2. Páginas y componentes

| Página | KPIs principales | Visuales | Pregunta de decisión |
|---|---|---|---|
| **Resumen** | Matrículas, pérdidas, tasa, fichas críticas, activos, contacto incompleto, alertas altas, prioridad inmediata | Dona por estado; barras por nivel de riesgo; tarjetas de hallazgos; 6 fichas críticas | ¿Dónde pongo la atención esta semana? |
| **Demografía y calidad** | Cobertura de datos; distribución por tipo de documento; dominio de correo; contacto por programa | Barras de tipo de documento; barras de contacto incompleto por programa; tabla de dominios | ¿Qué datos faltan y dónde está la brecha de contacto? |
| **Programas** | n, pérdidas, tasa, IC, tasa ajustada, brecha, participación | Pareto de pérdidas; barras de tasa por programa; tabla ordenable | ¿Qué programas explican la pérdida y cuáles tienen poca evidencia? |
| **Fichas** | n, tasa, IC, probabilidad, prioridad, confiabilidad | Dispersión tamaño vs tasa; histograma de tasas; tabla de 56 fichas | ¿Qué fichas priorizar y cuáles tienen n pequeño? |
| **Temporal / cohortes** | Fichas, matrículas, pérdidas, tasa por generación | Línea de tasa por generación; tabla con proyección base | ¿La pérdida cae por madurez o por cohorte? |
| **Riesgos** | Bandas, fichas, n, pérdidas, tasa; 6 críticas | Barras de validación; tarjetas críticas; tabla completa con ranking | ¿El semáforo es coherente y qué fichas son P1? |
| **Predictivo** | AUC, Brier, ECE, AUC individual; escenarios; alertas | Curva de calibración; histograma de scores; top 15 fichas; proyección; tabla de alertas; coeficientes | ¿Qué prioriza el modelo y qué decisiones no debe tomar? |

---

## 3. Jerarquía visual

- **Barra superior azul oscuro:** identidad SENA, snapshot, número de matrículas, tasa de pérdida, sello “Sin PII · IDs hasheados”.
- **Pestañas sticky:** navegación persistente; la pestaña activa se marca con línea verde.
- **Filtros globales:** programa, jornada, riesgo de ficha y búsqueda por ficha. Se aplican a KPIs, gráficos y tablas de la pestaña activa.
- **Banner amarillo:** declara la brecha de datos (sin género, edad, municipio, fechas, certificación). Es visible en todas las páginas y se puede cerrar.
- **KPIs:** 4 columnas; color solo en el borde izquierdo. El valor grande es el dato; el subtítulo da contexto (n, IC, definición).
- **Tarjetas críticas:** borde rojo suave, probabilidad grande, n/pérdidas, IC, nivel y prioridad.
- **Tablas:** encabezado sticky, números alineados a la derecha, badges de color, scroll interno.
- **Pie:** fuente, snapshot, modelo estrella, nota de PII.

**Paleta oficial (Manual de Identidad Corporativa SENA 2024)**

| Uso | Color |
|---|---|
| Verde corporativo | `#39A900` |
| Azul oscuro | `#00304D` |
| Verde oscuro | `#007832` |
| Violeta secundario | `#71277A` |
| Amarillo secundario | `#FDC300` |
| Azul claro secundario | `#50E5F9` |
| Neutro claro | `#F6F6F6` |
| Rojo pérdida (semántico) | `#C62828` |
| Naranja alto (semántico) | `#EF6C00` |
| Fondo | `#F6F6F6` |
| Texto | `#17313F` |

**Tipografía**

- Principal: **Work Sans**, en pesos Regular, Medium, SemiBold y Bold. Se usa en títulos, KPIs y navegación.
- Secundaria: **Calibri**, permitida por el manual para página web y piezas de divulgación. Se usa como respaldo y en tablas.
- No se usan Thin ni ExtraLight.
- El dashboard no incluye logosímbolos ni escudos: el espacio de marca se deja documentado para insertarlos manualmente, respetando el manual.


Los colores de riesgo se refuerzan con texto (`Bajo`, `Medio`, `Alto`, `Crítico`) y no dependen solo del color. Esto mejora accesibilidad para daltonismo.

---

## 4. Interacciones

| Control | Comportamiento |
|---|---|
| Selector de programa | Filtra todas las visuales de la pestaña y recalcula KPIs. |
| Selector de jornada | Filtra por DIURNA/NOCTURNA. |
| Selector de riesgo de ficha | Filtra por Bajo/Medio/Alto/Crítico. |
| Búsqueda de ficha | Filtro de texto por `FichaID`; acepta coincidencia parcial. |
| Limpiar | Restablece todos los filtros. |
| Imprimir / PDF | Abre el diálogo de impresión; el CSS de impresión muestra todas las pestañas y oculta filtros/navegación. |
| Descargar fichas CSV | Exporta la tabla de fichas filtrada, sin PII. |
| Descargar alertas CSV | Exporta hasta 100 alertas visibles, con ID hasheado, sin nombres. |
| Pestañas | Cambian de página sin recargar; cada pestaña se renderiza al activarse (lazy render). |

**Comportamiento esperado:** las tablas de pestañas ocultas están vacías hasta que se activan. No es un error: el render es perezoso para mantener el archivo liviano. Al hacer clic, la tabla se llena.

---

## 5. Arquitectura offline

- Un solo archivo `dashboard/index.html` (≈965 KB) con CSS, JavaScript y **Chart.js 4.4.7 embebido**.
- Los datos están en `dashboard/datos_dashboard.json` y también embebidos en el HTML para que funcione con doble clic, sin servidor.
- No hay llamadas a CDN, fuentes externas, analítica ni APIs. Funciona en intranet/offline.
- `dashboard/chart.umd.min.js` se conserva como fuente; el HTML ya lo incluye.
- Los CSV descargables se generan en el navegador con `Blob`; no se envía nada a un servidor.
- El archivo se probó en Chrome headless: 7 pestañas, 0 errores de JavaScript, 0 `NaN`/`undefined` en el DOM, filtros y tablas funcionando.

---

## 6. Privacidad en el diseño

| Dato | Dashboard | CSV descargable | Lista restringida |
|---|---|---|---|
| Nombre | No | No | Sí (`data/restricted/`) |
| Documento | No | No | Sí |
| Celular / correo | No | No | Sí |
| `AprendizID` hash | Sí | Sí | Sí |
| Ficha / programa / jornada | Sí | Sí | Sí |
| Score / prioridad | Sí | Sí | Sí |

El hash no es reversible con los datos publicados. La lista nominal `data/restricted/lista_priorizada.csv` no debe copiarse al dashboard ni al Excel público. El Excel entregable usa IDs y agregados, no nombres.

---

## 7. Accesibilidad

- Contraste texto/fondo ≥ 4,5:1 en textos principales.
- No se depende solo del color: cada badge tiene texto.
- Navegación por teclado en pestañas, selects, inputs y botones (elementos nativos).
- Etiquetas `label` asociadas a los campos.
- Tablas con encabezados `th` y alineación numérica.
- Texto alternativo implícito en títulos y descripciones; los canvas de Chart.js tienen título y tooltip.
- Impresión en blanco y negro: los badges mantienen texto; las barras pueden perder color, pero las tablas dan el valor.
- Tamaño de fuente base 14 px; KPIs 27 px; tablas 12 px.

---

## 8. Rendimiento

- 1.592 filas y 56 fichas: el filtrado es inmediato en el navegador.
- Render perezoso por pestaña; los gráficos se crean al activar la pestaña.
- Chart.js se destruye/recrea al cambiar filtros para evitar fugas.
- El HTML embebe los datos una sola vez; no hay fetch que pueda fallar en offline.
- Tamaño objetivo < 1,5 MB; actual 965 KB.

---

## 9. Validación realizada

| Prueba | Resultado |
|---|---|
| `node --check` de los scripts embebidos | OK |
| Render en Chrome headless | 7 pestañas visibles |
| KPIs del Resumen | 1.592 / 439 / 27,6% / 6 / 1.137 / 228 / 160 / 65 |
| Tabla de programas | 15 filas, 10 columnas |
| Tabla de fichas | 56 filas, 12 columnas |
| Tabla de generaciones | 17 filas, 6 columnas |
| Tabla de riesgos | 56 filas, 11 columnas |
| Tabla de alertas | 100 filas visibles |
| Filtro NOCTURNA | 561 matrículas; 19 fichas en la tabla de fichas |
| Errores JS | 0 (solo favicon 404, corregido con favicon embebido) |
| `NaN` / `undefined` | 0 |

**Nota:** la validación visual se hizo con capturas full-page de cada pestaña. La última revisión corrigió la alineación de la línea `n/pérdidas` en las tarjetas críticas y agregó un favicon embebido para eliminar el 404.

---

## 10. Cómo usar el tablero en una reunión

1. Abra **Resumen** y lea los 4 primeros KPIs en voz alta: matrículas, pérdidas, tasa, fichas críticas.
2. Revise las 6 tarjetas críticas; anote las fichas y los programas.
3. Vaya a **Riesgos** y valide que el semáforo es monotónico (Bajo 11,0% → Crítico 56,3%).
4. Vaya a **Programas** y pregunte: ¿la pérdida se concentra en los programas grandes? ¿Los programas pequeños tienen IC amplio?
5. Vaya a **Temporal** y explque por qué las cohortes jóvenes tienen 0%: no es éxito, es falta de exposición.
6. Vaya a **Predictivo** y lea la advertencia: el modelo prioriza fichas, no personas.
7. Cierre con **Demografía y calidad**: ¿qué datos faltan para el próximo corte?
8. Descargue la tabla de fichas o alertas si necesita trabajar fuera del tablero.

---

## 11. Mantenimiento

- **Actualización de datos:** reemplazar los CSV de `data/processed/` y volver a ejecutar `06_generar_dashboard.py`. No editar el HTML a mano.
- **Nuevo corte:** cambiar `fecha_reporte` en la fuente y volver a correr 01–06. El banner y el pie se actualizan desde los datos.
- **Nuevos campos:** agregar al ETL, al JSON y al render; no inventar columnas vacías.
- **Nuevo programa:** actualizar el mapa de normalización en `02_etl_modelo_estrella.py` y volver a correr.
- **Cambio de paleta:** editar las variables CSS en `06_generar_dashboard.py` y regenerar.
- **Prueba de regresión:** abrir el HTML, recorrer las 7 pestañas, verificar 0 errores en consola y que los totales sigan siendo 1.592/439/27,6%.

---

## 12. Relación con el PBIP

El dashboard HTML es la versión **inmediata, offline y autocontenida**. El PBIP es la versión **gobernable en Power BI**:

| Aspecto | HTML | PBIP |
|---|---|---|
| Disponibilidad | Inmediata, doble clic | Requiere Power BI Desktop |
| Datos | Embebidos | Modelo semántico + CSV |
| Interactividad | Filtros y pestañas | Segmentaciones, filtros, drillthrough |
| Actualización | Regenerar HTML | Actualizar CSV + refresh |
| Público | Revisión rápida, comité | Operación y publicación |
| PII | Sin PII | Sin PII (modelo usa IDs) |

Ambos consumen la misma verdad: `data/processed/`. Las cifras deben coincidir; si no coinciden, la fuente de verdad es el CSV y se regeneran ambos.
