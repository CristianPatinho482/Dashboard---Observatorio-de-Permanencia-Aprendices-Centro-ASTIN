# Publicación web del dashboard

**Pregunta que resuelve:** ¿cómo entregar una dirección electrónica para que el dashboard se abra desde cualquier equipo o dispositivo?

Hay dos caminos distintos, porque el proyecto tiene dos artefactos distintos:

| Artefacto | Qué es | Cómo se publica |
|---|---|---|
| `dashboard/index.html` | Dashboard HTML autocontenido, con Chart.js y los datos embebidos | Se sube a un hosting estático y se comparte la URL |
| `DashboardAprendicesSENA.pbip` | Borrador de proyecto de Power BI (modelo + reporte) | Se completa, se abre en Power BI Desktop y se publica en Power BI Service |

> El archivo `.pbip` **no es un dashboard web**. No se puede enviar por correo ni subir a Power BI Service como si fuera un `.pbix`. Es un formato de desarrollo para editar el reporte con archivos de texto.

---

## 1. Decisión rápida

| Necesidad | Opción recomendada |
|---|---|
| URL inmediata, sin instalar nada, solo consulta | GitHub Pages, Netlify o Azure Static Web Apps con el HTML |
| Audiencia interna del SENA, con control de acceso | Power BI Service (workspace + app) o Azure Static Web Apps con Entra ID |
| Actualización automática de datos y seguridad por usuario | Power BI Service + gateway o fuente en la nube |
| Difusión pública aprobada, sin inicio de sesión | GitHub Pages o Netlify |
| Incrustar en SharePoint, Teams o intranet | Power BI Service o `iframe` del HTML con hosting autenticado |

**Recomendación práctica:** si el objetivo es que el comité vea el dashboard esta semana, publica el HTML en un hosting estático. Si el objetivo es un producto institucional con refresh, permisos y auditoría, hay que completar el PBIP y publicarlo en Power BI Service.

---

## 2. Antes de publicar: tres controles obligatorios

1. **Autorización institucional.** Aunque el dashboard no tenga PII, contiene información académica del SENA. Confirma con la coordinación y con seguridad de la información si puede estar en un sitio público o debe quedar detrás de autenticación.
2. **Solo el HTML público.** No subas `data/restricted/`, la lista nominal, los `.xls` originales, los scripts ni el Excel si no está aprobado. El HTML ya está limpio de nombres, documentos, celulares y correos.
3. **Aviso de alcance.** La página debe seguir mostrando que es un corte del 19/10/2026, que la “generación” es un proxy por prefijo de ficha y que el score prioriza fichas, no personas.

---

## 3. Opción A: publicar el HTML (rápida)

El dashboard es un solo archivo: `dashboard/index.html`. No necesita servidor, base de datos ni internet para funcionar. Al ser estático, cualquier hosting de archivos puede servirlo.

### A.1 GitHub Pages

Ideal si el repositorio puede ser público o si la cuenta tiene planes que permiten Pages en repositorios privados.

1. Crea un repositorio en GitHub.
2. Sube **solo** `dashboard/index.html` con el nombre `index.html` en la raíz del repositorio.
   - Si más adelante insertas un logo, sube también ese archivo de imagen.
3. Entra a **Settings → Pages**.
4. En **Build and deployment**, elige **Deploy from a branch**.
5. Selecciona la rama `main` y la carpeta `/ (root)`. Guarda.
6. Espera uno o dos minutos. La URL será:

```text
https://<usuario>.github.io/<repositorio>/
```

**Ventaja:** URL estable y gratuita. **Límite:** en el plan gratuito el repositorio debe ser público; cualquiera con la URL puede verlo.

### A.2 Netlify Drop

Es la forma más rápida para una revisión o un comité.

1. Abre `https://app.netlify.com/drop`.
2. Arrastra la carpeta `dashboard` completa.
3. Netlify entrega una URL pública inmediata.
4. Si quieres una URL más presentable, cambia el nombre del sitio en la configuración.

**Ventaja:** no requiere repositorio ni configuración. **Límite:** el sitio es público por defecto; la protección con contraseña es de planes pagos.

### A.3 Azure Static Web Apps

Es la opción más adecuada si debe ser **interno y autenticado** sin montar un servidor.

- Permite autenticación con Microsoft Entra ID.
- Tiene capa gratuita para proyectos pequeños.
- Se puede conectar a un repositorio o desplegar con la CLI de Azure.
- Requiere cuenta de Azure y permisos de TI.

No es la opción más rápida, pero sí la más gobernable para una institución.

### A.4 Intranet o SharePoint del SENA

Si el SENA ya tiene una intranet o un sitio institucional:

- Publica el HTML en el hosting autorizado.
- Si se usa SharePoint, no subas el HTML a una biblioteca de documentos esperando que se ejecute: SharePoint suele abrirlo como descarga por seguridad. Lo correcto es usar un sitio o web part autorizado para contenido HTML.
- También se puede incrustar con un `iframe` si la política de la intranet lo permite.

### A.5 Actualizar la versión publicada

Cada vez que cambien los datos:

```powershell
$env:PYTHONIOENCODING='utf-8'
python -X utf8 scripts/06_generar_dashboard.py
```

Luego reemplaza `index.html` en el hosting. La URL se conserva. Como los datos están embebidos, **no hay refresh automático**: la versión publicada es una fotografía del corte.

---

## 4. Opción B: publicar en Power BI Service (producción)

Esta es la vía correcta si se necesita un reporte gobernado, actualizable y con permisos.

### B.1 Requisitos reales

- **Power BI Desktop** instalado en Windows.
- Cuenta de Power BI con acceso a un **workspace**.
- Licencia **Power BI Pro**, **Premium Per User** o un workspace sobre **Fabric/Premium capacity**.
- El reporte debe estar completo. El PBIP actual es un borrador y **no se puede publicar** todavía.
- Una fuente de datos accesible por el servicio para el refresh.

### B.2 Qué falta en este proyecto para publicar en Power BI

El PBIP actual solo tiene el esqueleto del reporte. Le falta:

- modelo semántico TMDL con las 13 dimensiones, 2 tablas de hechos y relaciones;
- medidas DAX;
- páginas PBIR con visuales;
- tema SENA;
- configuración de actualización y credenciales.

Los datos ya están preparados en `data/processed/` y el catálogo de medidas está en `docs/03_catalogo_dax.md`. La publicación en Power BI es un paso posterior a completar ese modelo.

### B.3 Flujo de publicación

1. Abre el proyecto en **Power BI Desktop** (con la vista previa de PBIP habilitada) o construye un `.pbix` equivalente.
2. Verifica que el modelo cargue y que las medidas funcionen.
3. Inicia sesión con la cuenta institucional.
4. Selecciona **Publicar** y elige el workspace destino.
5. En Power BI Service, abre el workspace y revisa el reporte publicado.
6. Crea una **app** para distribuir el reporte a los usuarios finales, en lugar de compartir el workspace de edición.
7. Asigna permisos:
   - edición solo al equipo dueño;
   - lectura a los coordinadores o comité;
   - seguridad por filas (RLS) solo si hace falta y está probada.

La URL tendrá una forma similar a:

```text
https://app.powerbi.com/groups/<workspace>/apps/<app-id>
```

### B.4 Actualización de datos

Hay dos escenarios:

**Datos embebidos (snapshot)**
- El reporte muestra el corte publicado.
- No se actualiza solo.
- Para actualizarlo, se regenera el modelo y se vuelve a publicar.

**Datos actualizables**
- La fuente debe estar en la nube: SharePoint, OneDrive, Azure SQL, Fabric Lakehouse, etc.
- Si la fuente sigue en un disco local, se necesita un **gateway de datos on-premises** instalado y con credenciales.
- Después se configura **Programar actualización** en el dataset.
- Hay que validar que el gateway tenga acceso a la carpeta y que la cuenta tenga permisos.

El proyecto actual usa archivos locales. Para un refresh programado real, lo recomendable es mover `data/processed/` a SharePoint/OneDrive o a una base de datos, y apuntar el modelo allí.

### B.5 “Publicar en la web” vs. publicación interna

Power BI tiene una función llamada **Publish to web** que genera un enlace público sin autenticación. **No la uses para datos institucionales sin autorización expresa.** Cualquiera con el enlace podría verlo.

Para audiencias internas usa:

- app de Power BI en el tenant;
- inserción segura en SharePoint/Teams;
- Embedded Analytics con capacidad de Fabric, si se va a integrar en un portal propio.

---

## 5. Comparación de costos y esfuerzo

| Camino | Esfuerzo | Control de acceso | Refresh | Costo |
|---|---|---|---|---|
| GitHub Pages / Netlify | Bajo | Público, salvo configuración adicional | Manual, regenerando el HTML | Gratis |
| Azure Static Web Apps | Medio | Entra ID / autenticación | Manual o por CI/CD | Capa gratuita limitada |
| Power BI Service con Pro | Medio-alto | Por workspace, app y RLS | Programado con gateway/nube | Licencia por usuario |
| Power BI Service con Fabric/Premium | Alto | Avanzado | Programado | Capacidad |
| SharePoint/intranet | Medio | Según la institución | Según el sitio | Institucional |

---

## 6. Checklist de publicación

- [ ] Autorización de la coordinación y de seguridad de la información.
- [ ] Solo se publica `index.html` (y el logo, si se insertó).
- [ ] No se publica `data/restricted/` ni los `.xls` originales.
- [ ] Se verificó que no haya nombres, documentos, celulares ni correos.
- [ ] La página muestra el corte y las limitaciones.
- [ ] La URL se probó desde otro equipo y desde un celular.
- [ ] Se definió quién actualiza el dashboard y con qué frecuencia.
- [ ] Si es Power BI: workspace, app, licencias, gateway y refresh probados.
- [ ] Si es público: se revisó que la información pueda serlo.

---

## 7. Recomendación final

- **Para esta semana:** publica el HTML en Netlify Drop o GitHub Pages si la información está autorizada para circular. Es la vía más rápida y el dashboard ya está listo.
- **Para producción:** completa el PBIP y publica en Power BI Service con una app, licencias y refresh. Es la única vía que da actualización programada, gobierno y control de acceso real.
- **Para audiencia interna:** no uses un enlace público gratuito. Usa Power BI Service o Azure Static Web Apps con autenticación.
