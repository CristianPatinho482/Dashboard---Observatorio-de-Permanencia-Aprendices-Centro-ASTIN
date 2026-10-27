# OBservatorio de Aprendices Centro ASTIN

Dashboard de analítica académica construido a partir de **56 reportes de ficha del SENA**, con corte al **19 de octubre de 2026**. El proyecto describe la matrícula, la pérdida, el riesgo por ficha, la permanencia y una capa exploratoria de priorización.

> **Datos del corte:** 1.592 matrículas · 1.583 aprendices únicos · 56 fichas · 15 programas · 2 jornadas · 439 pérdidas (27,58 %).

---

## 1. Qué encontrarás

| Entregable | Archivo | Estado |
|---|---|---|
| Dashboard interactivo offline | `dashboard/index.html` | Funcional. Se abre con doble clic. |
| Lanzador para Windows | `ABRIR_DASHBOARD.bat` | Abre el dashboard en el navegador predeterminado. |
| Libro Excel ejecutivo | `outputs/Dashboard_Aprendices_SENA.xlsx` | Funcional, 9 hojas, sin PII. |
| Documentación y guías | `docs/01_…` a `docs/09_…` | Completa. |
| Modelo estrella procesado | `data/processed/*.csv` | Generado por los scripts 01–04. |
| Lista nominal restringida | `data/restricted/lista_priorizada.csv` | **PII. Uso interno. No publicar.** |
| Guía de publicación web | `docs/09_publicacion_web.md` | Opciones, requisitos y pasos. |
| PBIP de Power BI | `DashboardAprendicesSENA.pbip` | **Borrador incompleto.** Ver sección 11. |

El dashboard HTML es el entregable inmediato: no necesita internet, servidor ni Power BI. Chart.js y los datos están embebidos en el mismo archivo.

---

## 2. Cómo abrirlo

### Forma recomendada

1. Abre la carpeta del proyecto.
2. Haz doble clic en **`ABRIR_DASHBOARD.bat`**.
3. Si Windows pregunta con qué programa abrirlo, elige **Google Chrome** o **Microsoft Edge**.

También puedes abrir directamente:

`dashboard/index.html`

con doble clic o con clic derecho → **Abrir con** → Chrome/Edge.

### Si no abre o se ve en blanco

- Verifica que estés abriendo `dashboard/index.html`, no el archivo `.pbip`.
- Si el navegador descarga el archivo en lugar de mostrarlo, arrástralo a una pestaña de Chrome/Edge.
- Si el equipo tiene restricciones para archivos locales, abre una consola en la carpeta del proyecto y ejecuta:

```powershell
python -m http.server 8765 --directory dashboard
```

Luego abre `http://127.0.0.1:8765/index.html`.

- El dashboard no requiere conexión. Si una visual no aparece, actualiza con `Ctrl + F5`.

---

## 3. Manual rápido del dashboard

### Pestañas

1. **Resumen:** matrículas, pérdidas, tasa, fichas críticas, estados, jornada y hallazgos.
2. **Demografía y calidad:** qué datos existen, qué falta y dónde hay brechas de contacto.
3. **Programas:** ranking por tasa, intervalos de confianza, concentración y pérdidas.
4. **Fichas:** las 56 fichas, su riesgo, probabilidad estructural, intervalo y prioridad.
5. **Temporal / cohortes:** evolución por prefijo de ficha. **No es un año calendario.**
6. **Riesgos:** validación del semáforo, fichas críticas y protocolo de atención.
7. **Predictivo:** modelo, calibración, escenarios de permanencia y priorización individual.

### Filtros

Los filtros de **programa**, **jornada**, **nivel de riesgo** y **búsqueda de ficha** se aplican a la pestaña activa. El botón **Limpiar** restablece la vista.

### Acciones

- **Imprimir / PDF:** usa el botón de impresión del dashboard. El CSS de impresión muestra todas las pestañas y oculta filtros.
- **Descargar fichas CSV:** exporta la tabla filtrada, sin nombres ni documentos.
- **Descargar alertas CSV:** exporta la cola de priorización con ID hasheado, sin PII.
- **Pestañas:** cada una se renderiza al activarse. Es normal que una tabla oculta esté vacía hasta hacer clic.

### Lectura recomendada en comité

1. Abre **Resumen** y revisa los cuatro primeros indicadores.
2. Identifica las fichas críticas y sus programas.
3. Contrasta en **Riesgos** que el semáforo sea coherente: Bajo 11,0 % → Crítico 56,3 %.
4. Revisa **Programas** y **Fichas** con el tamaño de muestra y el intervalo de confianza.
5. Cierra con **Predictivo** y con la advertencia: el score prioriza fichas, no personas.
6. Usa **Demografía y calidad** para definir qué campos faltan capturar en el próximo corte.

---

## 4. Cómo editar el dashboard

### Regla de oro

No edites el HTML generado como fuente principal. Si vuelves a ejecutar el generador, tus cambios se sobrescriben.

El flujo correcto es:

```text
scripts/06_generar_dashboard.py  →  dashboard/index.html
```

### Cambiar el título

En `scripts/06_generar_dashboard.py`, busca:

```html
<h1>Caracterización de Aprendices Centro ASTIN</h1>
```

y también:

```html
<title>Caracterización de Aprendices · Centro ASTIN</title>
```

Modifica ambos y regenera:

```powershell
$env:PYTHONIOENCODING='utf-8'
python -X utf8 scripts/06_generar_dashboard.py
```

### Insertar el logo SENA

El dashboard **no incluye logos recreados**. El manual de identidad indica que el logosímbolo oficial no debe alterarse ni reconstruirse.

1. Guarda el logo oficial en `dashboard/` (por ejemplo, `logo-sena.png`).
2. En `scripts/06_generar_dashboard.py`, busca el comentario:

```html
<!-- LOGO SENA: insertar aquí el logosímbolo oficial. No se recrea en este archivo. -->
```

3. Justo debajo, dentro de `.brand`, inserta:

```html
<img src="logo-sena.png" alt="SENA">
```

4. Regenera con `06_generar_dashboard.py`.

La clase `.brand img` ya deja el logo a 54 px de alto y con proporción automática.

### Cambiar colores

La paleta está en las variables CSS de `scripts/06_generar_dashboard.py`:

```css
--green:#39A900;
--green-dark:#007832;
--dark:#00304D;
--violet:#71277A;
--sky:#50E5F9;
--brand-yellow:#FDC300;
```

Después de cambiarlas, regenera el HTML. Para los gráficos, revisa también el objeto `COLORS` y `RISK_COLOR` dentro del mismo script.

### Cambiar textos, tarjetas o hallazgos

Los textos están en el bloque `TEMPLATE` de `06_generar_dashboard.py`. Los números se calculan desde `data/processed/` y `outputs/*.json`; **no los escribas a mano**.

### Cambiar el Excel

El libro se genera desde `scripts/05_generar_excel.py`. Edita títulos, columnas o formatos allí y vuelve a ejecutar:

```powershell
python -X utf8 scripts/05_generar_excel.py
```

### Cambiar la documentación

Los documentos están en `docs/`. Son Markdown: puedes editarlos con VS Code, Notepad++ o cualquier editor de texto.

---

## 5. Cómo actualizar los datos con nuevas fichas

### Caso 1: nuevas fichas del mismo corte

Sí, el modelo permite agregar nuevas fichas si los reportes conservan la misma estructura.

1. Solicita los nuevos reportes de ficha en `.xls`, con el mismo formato y las mismas columnas:
   - tipo de documento
   - número de documento
   - nombres
   - celular
   - correo
   - estado
   - (la columna de programa/ficha que trae el reporte)
2. Guárdalos en la carpeta fuente:

   `C:\Users\capatino\Desktop\Base de datos aprendices centro`

3. Respeta el patrón de nombre:

   `Aprendices_<ficha>_<jornada>_<programa>.xls`

4. Ejecuta el pipeline completo:

```powershell
$env:PYTHONIOENCODING='utf-8'
python -X utf8 scripts/01_explorar_datos.py
python -X utf8 scripts/02_etl_modelo_estrella.py
python -X utf8 scripts/03_analisis_estadistico.py
python -X utf8 scripts/04_modelo_predictivo.py
python -X utf8 scripts/05_generar_excel.py
python -X utf8 scripts/06_generar_dashboard.py
```

5. Abre de nuevo `dashboard/index.html` y verifica los totales.

El dashboard, el Excel y los JSON se recalculan. No hay que editar el HTML a mano.

### Caso 2: un corte nuevo

Un corte nuevo **no se suma** al anterior: lo reemplaza. Para publicarlo:

1. Reemplaza los 56 (o más) reportes en la carpeta fuente.
2. Verifica que todos tengan la misma fecha de corte.
3. Cambia `REPORT_DATE` en `scripts/02_etl_modelo_estrella.py` si la fecha es distinta de `2026-10-19`.
4. Vuelve a ejecutar 01 → 06.

### Caso 3: series históricas

El modelo actual es de **un solo snapshot**. No hay una dimensión de periodo ni fechas de matrícula/retiro. Por eso:

- No se puede estimar estacionalidad.
- No se puede entrenar un modelo temporal.
- La “generación” es un proxy por prefijo de ficha, no un año.
- Si pegas cortes de fechas distintas, el modelo los tratará como una sola población y las cifras quedarán mal.

Para análisis longitudinal se deben agregar fechas, periodo y motivo de retiro. La ruta está documentada en `docs/08_plan_implementacion.md`.

### Caso 4: un programa nuevo

Si aparece un programa con un nombre que no esté en el catálogo de 15, revisa el mapa de normalización de `02_etl_modelo_estrella.py` y agrégalo antes de ejecutar el pipeline. Después valida el nombre contra SOFIA Plus.

---

## 6. Identidad visual

Se aplicaron los lineamientos del **Manual de Identidad Corporativa SENA 2024**:

- **Tipografía principal:** Work Sans (Regular, Medium, SemiBold, Bold).
- **Tipografía secundaria:** Calibri, permitida para página web y divulgación.
- **Verde corporativo:** `#39A900`.
- **Azul oscuro:** `#00304D`.
- **Verde oscuro:** `#007832`.
- **Violeta:** `#71277A`.
- **Amarillo:** `#FDC300`.
- **Azul claro:** `#50E5F9`.
- **Neutros:** `#F6F6F6`, `#FFFFFF`.

Los colores rojo, naranja y amarillo se usan además como semáforo de riesgo. Siempre van acompañados de texto (`Bajo`, `Medio`, `Alto`, `Crítico`) para no depender solo del color.

**Logos y elementos gráficos:** no se recrearon. El manual prohíbe alterar el logosímbolo. El lugar de inserción está marcado en el generador del dashboard para que se agregue manualmente el archivo oficial.

---

## 7. Privacidad

- `data/processed/`, el HTML público y el Excel **no contienen** nombres, documentos, celulares ni correos.
- El identificador de aprendiz es un hash no reversible con los datos publicados.
- El correo se reduce a dominio.
- La lista con nombres, documentos y contactos está en `data/restricted/lista_priorizada.csv`. Es de uso interno y **no debe publicarse, enviarse por correo masivo ni adjuntarse al dashboard**.
- La fuente original también es restringida: `data/restricted/aprendices_crudos.json`.
- El score individual es una priorización estructural, no una predicción personal validada. No debe usarse para negar cupos, sancionar ni certificar.

---

## 8. Estructura del proyecto

```text
Dashboard_Aprendices_SENA/
├── ABRIR_DASHBOARD.bat
├── README.md
├── dashboard/
│   ├── index.html               ← dashboard funcional, autocontenido
│   ├── datos_dashboard.json
│   ├── chart.umd.min.js
│   └── README.md
├── data/
│   ├── processed/               ← modelo estrella sin PII
│   └── restricted/              ← PII, uso interno
├── docs/
│   ├── 01_diccionario_datos.md
│   ├── 02_modelo_estrella.md
│   ├── 03_catalogo_dax.md
│   ├── 04_informe_estadistico.md
│   ├── 05_metodologia_predictiva.md
│   ├── 06_insights_ejecutivos.md
│   ├── 07_diseno_dashboard.md
│   ├── 08_plan_implementacion.md
│   └── 09_publicacion_web.md
├── outputs/
│   ├── 01_exploracion.json
│   ├── 02_etl_resumen.json
│   ├── 03_analisis_estadistico.json
│   ├── 04_modelo_predictivo.json
│   ├── 05_excel_resumen.json
│   └── Dashboard_Aprendices_SENA.xlsx
├── scripts/
│   ├── 01_explorar_datos.py
│   ├── 02_etl_modelo_estrella.py
│   ├── 03_analisis_estadistico.py
│   ├── 04_modelo_predictivo.py
│   ├── 05_generar_excel.py
│   └── 06_generar_dashboard.py
├── powerbi/                     ← espacio para el PBIP final
└── DashboardAprendicesSENA.pbip ← borrador, ver sección 11
```

---

## 9. Requisitos y reproducción

### Requisitos

- Windows 10/11.
- Python 3.12 o superior.
- Dependencias de `requirements.txt`.
- Microsoft Excel solo para abrir el libro; el dashboard no lo necesita.
- Power BI Desktop solo para el PBIP.

Instalación:

```powershell
python -m pip install -r requirements.txt
```

### Reproducción completa

```powershell
$env:PYTHONIOENCODING='utf-8'
python -X utf8 scripts/01_explorar_datos.py
python -X utf8 scripts/02_etl_modelo_estrella.py
python -X utf8 scripts/03_analisis_estadistico.py
python -X utf8 scripts/04_modelo_predictivo.py
python -X utf8 scripts/05_generar_excel.py
python -X utf8 scripts/06_generar_dashboard.py
```

### Validaciones esperadas

| Comprobación | Valor |
|---|---|
| Matrículas | 1.592 |
| Pérdidas | 439 |
| Tasa de pérdida | 27,58 % |
| Fichas | 56 |
| Programas | 15 |
| Aprendices únicos | 1.583 |
| Filas de proyección | 168 (56 × 3 escenarios) |
| PII en dashboard/Excel | 0 |

Si alguno cambia después de una actualización, revisa la fuente antes de publicar.

---

## 10. Cómo poner el dashboard en línea

Hay dos caminos, porque hay dos artefactos distintos. El detalle completo está en **`docs/09_publicacion_web.md`**; aquí va la decisión rápida.

### 10.1 Si quieres una URL ya, con el dashboard actual

El HTML es un archivo autocontenido. Solo necesitas subir `dashboard/index.html` a un hosting estático:

- **Netlify Drop:** arrastra la carpeta `dashboard` a `https://app.netlify.com/drop`. Te da una URL en segundos.
- **GitHub Pages:** sube `index.html` a un repositorio, activa **Settings → Pages → Deploy from a branch → main / root** y usa `https://<usuario>.github.io/<repo>/`.
- **Azure Static Web Apps:** recomendable si debe ser interno y con autenticación de Microsoft Entra ID.
- **Intranet/SharePoint institucional:** úsalo si TI ya tiene un sitio autorizado para contenido HTML.

**Importante:** no subas `data/restricted/`, los `.xls` originales ni la lista nominal. El HTML no contiene PII, pero la información académica institucional igual requiere autorización. GitHub Pages y Netlify son públicos por defecto: si el dashboard es interno, usa una opción con autenticación.

Cada actualización requiere regenerar y volver a subir:

```powershell
python -X utf8 scripts/06_generar_dashboard.py
```

La URL se mantiene; lo que cambia es el archivo publicado. No hay refresh automático porque los datos van embebidos.

### 10.2 Si quieres publicar en Power BI Service

El `.pbip` **no se envía ni se sube directamente** a Power BI. Es un formato de desarrollo. Para tener una URL de Power BI hace falta:

1. Completar el modelo semántico y el reporte (el PBIP actual es un borrador).
2. Abrirlo en **Power BI Desktop** y publicarlo en un **workspace**.
3. Crear una **app** de Power BI para distribuirlo.
4. Asignar licencias y permisos a los usuarios.
5. Configurar actualización: si la fuente sigue en archivos locales, se necesita un **gateway**; si está en SharePoint/OneDrive/nube, se puede programar el refresh.

Los viewers necesitan licencia **Power BI Pro/PPU**, o el workspace debe estar en **Fabric/Premium capacity**. La función **“Publish to web”** genera un enlace público sin autenticación: no debe usarse con datos institucionales sin autorización expresa.

### 10.3 Recomendación

- **Para revisión inmediata del comité:** publica el HTML en Netlify Drop o GitHub Pages, con autorización.
- **Para producción, refresh y control de acceso:** completa el PBIP y publica en Power BI Service con workspace + app + gateway.
- **Para audiencia interna:** no uses un enlace público gratuito; usa Power BI Service o Azure Static Web Apps con autenticación.

---

## 11. Por qué no abre el PBIP

El archivo `DashboardAprendicesSENA.pbip` que está en la raíz es un **borrador de reporte**, no el modelo semántico final. Le falta el modelo TMDL con las tablas, relaciones y medidas DAX. Por eso:

- No debe abrirse como si fuera el dashboard terminado.
- Puede abrir una página vacía o mostrar un error.
- Requiere **Power BI Desktop** con la vista previa de PBIP habilitada.
- No existe un `.pbix` compilado.

El dashboard que sí está listo para usar es `dashboard/index.html`. El PBIP queda como línea de trabajo para una versión gobernable en Power BI.

Si necesitas publicar en Power BI, el siguiente paso es completar el modelo semántico y el reporte PBIR, y validarlo en Power BI Desktop. Los datos de origen ya están en `data/processed/` y el catálogo DAX está en `docs/03_catalogo_dax.md`.

---

## 12. Limitaciones que debes comunicar

- Es un **solo corte transversal**. No hay serie histórica ni fechas de matrícula, retiro o certificación.
- No hay género, edad, municipio ni departamento en la fuente. Aparecen como `No informado`; no se imputan.
- El tipo de documento se usa solo como proxy grueso de edad.
- La “generación” es un prefijo de ficha, no un año calendario.
- Los contrastes por programa y jornada son exploratorios y no ajustan clustering intra-ficha.
- El modelo tiene AUC out-of-fold 0,726 (IC 0,669–0,781), pero la calibración es imperfecta (ECE 0,048; pendiente 0,72).
- El AUC con variables individuales es 0,467: no hay señal personal suficiente. **Prioriza fichas, no personas.**
- La proyección es un escenario de permanencia de los 1.144 vinculados, no un pronóstico de nueva matrícula.
- Las fichas pequeñas producen rankings inestables. Siempre lee el tamaño de ficha y el intervalo de confianza.

---

## 13. Créditos y uso

Proyecto de analítica académica para el **Centro ASTIN** del SENA. Construido con Python, pandas, scikit-learn, matplotlib, openpyxl, Chart.js y datos de reportes de ficha.

Uso previsto: comités académicos, coordinación de formación y bienestar al aprendiz. No reemplaza el juicio humano ni las decisiones institucionales. Toda intervención debe tener responsable, registro y revisión.
