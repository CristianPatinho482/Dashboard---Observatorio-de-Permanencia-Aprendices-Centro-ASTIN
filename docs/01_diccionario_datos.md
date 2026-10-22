# Diccionario de datos — Caracterización de Aprendices Centro ASTIN

**Fuente:** 56 archivos `.xls` de ficha, carpeta `Base de datos aprendices centro`.
**Snapshot:** 19 de octubre de 2026 (todas las fichas reportan la misma fecha).
**Universo:** 1.592 matrículas, 1.583 aprendices únicos, 56 fichas, 15 programas, 2 jornadas.
**Centro:** Centro ASTIN (nombre indicado por el usuario; el código, la regional y la ciudad no vienen en la fuente).

> **Regla de oro:** este diccionario distingue siempre entre *dato observado*, *dato derivado* y *dato no informado*. La fuente no contiene género, edad, municipio, departamento, fecha de matrícula, fecha de egreso ni certificación. Esas dimensiones se crean con la categoría `No informado` y no se usan para inferir comportamientos.

---

## 1. Inventario de la fuente

| Elemento | Valor |
|---|---:|
| Archivos de ficha | 56 |
| Filas de aprendiz | 1.592 |
| Fichas únicas | 56 |
| Programas normalizados | 15 |
| Jornadas | DIURNA (37 fichas, 1.031 matrículas) y NOCTURNA (19 fichas, 561 matrículas) |
| Estado de ficha | `EN EJECUCION` en las 56 fichas |
| Fecha de reporte | `2026-10-19` en las 56 fichas |
| Tamaño de ficha | mínimo 14, máximo 50, mediana 29 |
| Documentos únicos | 1.583 |
| Aprendices en más de una ficha | 9 (18 matrículas) |
| Correos válidos | 1.592 (100%) |
| Celulares válidos | 1.364 (85,7%) |
| Contacto incompleto | 228 matrículas (14,3%) |

Cada archivo tiene una fila de título con ficha, jornada, programa, estado y fecha; la tabla de datos comienza en la fila 5 (índice 4). Los archivos son de solo lectura y no se modifican.

---

## 2. Columnas originales

| Columna original | Tipo | Uso | Observación |
|---|---|---|---|
| `Tipo de Documento` | Texto | Perfil / proxy etario | `CC`, `TI`, `PPT`, `CE`. No es una variable de riesgo validada. |
| `Número de Documento` | Texto | Identificación | Se usa para construir `AprendizID` (hash) y detectar duplicados. **No se publica.** |
| `Nombre` | Texto | Identificación | PII. Se conserva solo en `data/restricted/`. |
| `Apellidos` | Texto | Identificación | PII. Se conserva solo en `data/restricted/`. |
| `Celular` | Texto | Contactabilidad | 208 vacíos; algunos con longitud distinta de 10. |
| `Correo Electrónico` | Texto | Contactabilidad | 0 inválidos; 9 correos repetidos. |
| `Estado` | Texto | Resultado observado | Define pérdida, actividad y suspensión. Ver sección 3. |

---

## 3. Mapeo de estados

La categoría `Pérdida` agrupa `CANCELADO` y `RETIRO VOLUNTARIO`. `TRASLADADO` no es pérdida, pero tampoco se considera activo. `APLAZADO` es una suspensión temporal y permanece vinculado. `CONDICIONADO` es una señal de riesgo académico, no una pérdida.

| Estado | Matrículas | Categoría | ¿Pérdida? | ¿Activo? | ¿Vinculado? | Uso analítico |
|---|---:|---|---:|---:|---:|---|
| `EN FORMACION` | 1.112 | Activo | No | Sí | Sí | Población activa |
| `INDUCCION` | 19 | Activo | No | Sí | Sí | Población activa |
| `CONDICIONADO` | 6 | Activo en riesgo | No | Sí | Sí | Señal de alerta |
| `APLAZADO` | 7 | Suspendido | No | No | Sí | Seguimiento |
| `CANCELADO` | 428 | Desertor | Sí | No | No | Componente principal de la pérdida |
| `RETIRO VOLUNTARIO` | 11 | Desertor | Sí | No | No | Pérdida voluntaria |
| `TRASLADADO` | 9 | Egreso por traslado | No | No | No | Excluido de la tasa de pérdida |

**Definiciones operativas**

- `Pérdida = CANCELADO + RETIRO VOLUNTARIO = 439` (27,58%).
- `Activo = EN FORMACION + INDUCCION + CONDICIONADO = 1.137` (71,42%).
- `Vinculado = Activo + APLAZADO = 1.144` (71,86%).
- La tasa de pérdida se calcula sobre **matrículas**, no sobre personas únicas. Un aprendiz con dos fichas aporta dos matrículas; esto es correcto para gestionar fichas, pero no para contar personas.
- La tasa de cancelación (26,88%) y la de retiro voluntario (0,69%) se reportan por separado para no ocultar la naturaleza de la salida.

---

## 4. Programas normalizados

Los nombres originales venían en mayúsculas, sin tildes y con variaciones. Se normalizaron a 15 nombres canónicos. El nivel de formación se infirió del nombre (`Tecnólogo` o `Técnico`) y se documenta en `NivelFuente`; **debe validarse contra SOFIA Plus** antes de usarlo para decisiones de oferta.

| ID | Programa canónico | Nivel inferido | Fichas | Matrículas |
|---|---|---|---:|---:|
| P01 | Alistamiento de Laboratorios de Análisis y Ensayos para la Industria | Técnico | 1 | 18 |
| P02 | Análisis de Materiales para la Industria | Tecnólogo | 2 | 38 |
| P03 | Aplicación de Procedimientos de Laboratorio Químico | Técnico | 1 | 14 |
| P04 | Coordinación en Sistemas Integrados de Gestión | Tecnólogo | 15 | 484 |
| P05 | Desarrollo de Componentes Mecánicos | Tecnólogo | 3 | 84 |
| P06 | Desarrollo y Modelado de Productos Industriales | Tecnólogo | 4 | 101 |
| P07 | Fabricación de Moldes y Troqueles | Tecnólogo | 2 | 53 |
| P08 | Fabricación de Productos Plásticos por Inyección y Soplado | Tecnólogo | 1 | 19 |
| P09 | Gestión de Proyectos de Desarrollo Económico y Social | Tecnólogo | 9 | 235 |
| P10 | Gestión de la Producción Industrial | Tecnólogo | 6 | 183 |
| P11 | Modelado 3D para la Industria | Tecnólogo | 2 | 52 |
| P12 | Monitoreo Ambiental | Tecnólogo | 4 | 149 |
| P13 | Procesos de Manufactura (Baxter) | Técnico | 1 | 26 |
| P14 | Química Aplicada a la Industria | Tecnólogo | 4 | 113 |
| P15 | Transformación de Polímeros por Inyección | Tecnólogo | 1 | 23 |

La etiqueta `(Baxter)` es un identificador local tomado del nombre del archivo/programa; no implica una relación comercial ni una conclusión sobre el programa.

---

## 5. Generaciones por prefijo de ficha

La fuente no tiene fecha de matrícula ni periodo académico. Para ordenar las fichas en el tiempo se usa el **prefijo de 3 dígitos** del número de ficha (`314`, `317`, …, `358`). Es un **proxy de antigüedad**, no un año calendario.

| Generación | Rango de ficha | Fichas | Matrículas | Pérdidas | Tasa |
|---|---|---:|---:|---:|---:|
| GEN-314 | 3140000–3149999 | 4 | 121 | 60 | 49,59% |
| GEN-317 | 3170000–3179999 | 8 | 230 | 100 | 43,48% |
| GEN-318 | 3180000–3189999 | 2 | 50 | 26 | 52,00% |
| GEN-323 | 3230000–3239999 | 1 | 24 | 10 | 41,67% |
| GEN-330 | 3300000–3309999 | 4 | 146 | 64 | 43,84% |
| GEN-331 | 3310000–3319999 | 1 | 26 | 6 | 23,08% |
| GEN-335 | 3350000–3359999 | 3 | 74 | 35 | 47,30% |
| GEN-340 | 3400000–3409999 | 5 | 100 | 32 | 32,00% |
| GEN-341 | 3410000–3419999 | 9 | 275 | 61 | 22,18% |
| GEN-343 | 3430000–3439999 | 1 | 21 | 1 | 4,76% |
| GEN-344 | 3440000–3449999 | 6 | 191 | 44 | 23,04% |
| GEN-345 | 3450000–3459999 | 1 | 23 | 0 | 0,00% |
| GEN-346 | 3460000–3469999 | 2 | 69 | 0 | 0,00% |
| GEN-349 | 3490000–3499999 | 2 | 60 | 0 | 0,00% |
| GEN-353 | 3530000–3539999 | 3 | 85 | 0 | 0,00% |
| GEN-356 | 3560000–3569999 | 2 | 49 | 0 | 0,00% |
| GEN-358 | 3580000–3589999 | 2 | 48 | 0 | 0,00% |

Las generaciones 314–340 se consideran **maduras** para la proyección (8 prefijos, 771 matrículas, 333 pérdidas, plateau 43,19%). Las generaciones 345–358 son jóvenes y aún no han acumulado pérdidas; su 0% **no significa que sean exitosas**, sino que el snapshot es temprano. Esta es la principal advertencia de lectura temporal.

---

## 6. Diccionario del modelo estrella

### 6.1 `DimAprendiz` (1.583 filas)

| Campo | Tipo | Descripción | Origen |
|---|---|---|---|
| `AprendizID` | Texto | Hash estable del documento (`APR-XXXXXXXXXX`). | Derivado |
| `TipoDocumento` | Texto | `CC`, `TI`, `PPT`, `CE`. | Fuente |
| `Genero` | Texto | Siempre `No informado`. | No disponible |
| `GeneroFuente` | Texto | `No disponible en la fuente`. | Derivado |
| `GrupoEdadProxy` | Texto | Proxy por tipo de documento (`Menor de edad probable`, `Adulto joven/adulto`, `No clasificable`). **No es edad real.** | Derivado |
| `Edad` | Entero | Vacío. No se imputa. | No disponible |
| `MunicipioID` | Texto | `MUN-000` (No informado). | No disponible |
| `DepartamentoID` | Texto | `DEP-000` (No informado). | No disponible |
| `EmailDominio` | Texto | Dominio del correo (sin usuario). | Derivado |
| `TieneCelular` | 0/1 | Celular no vacío. | Derivado |
| `CelularValido` | 0/1 | Celular con 10 dígitos. | Derivado |
| `EmailValido` | 0/1 | Correo con estructura válida. | Derivado |
| `ContactoCompleto` | 0/1 | Celular válido **y** correo válido. | Derivado |
| `TotalMatriculas` | Entero | Veces que aparece el aprendiz. | Derivado |
| `TotalFichas` | Entero | Fichas distintas en las que aparece. | Derivado |
| `PrimeraFicha` / `UltimaFicha` | Texto | Ficha mínima/máxima por orden alfabético; no implica cronología. | Derivado |
| `EstadoActual` | Texto | Peor estado observado entre sus fichas (orden de severidad). | Derivado |
| `TieneMultiplesFichas` | 0/1 | `TotalFichas > 1`. | Derivado |
| `ProbPerdidaMax` | Decimal | Máxima probabilidad estructural entre sus fichas (modelo). | Modelo |
| `NivelAlertaAprendiz` | Texto | `Alto`, `Medio`, `Bajo` según percentiles del score. | Modelo |
| `RequiereIntervencion` | 0/1 | 1 si la prioridad es `Inmediata`. | Modelo |
| `FichasRiesgoAlto` | Texto | Fichas del aprendiz con nivel Alto/Crítico. | Modelo |
| `MotivoPrioridad` | Texto | Señales que explican la prioridad. | Modelo |

> `DimAprendiz` **no contiene nombres, documentos, celulares ni correos**. Esa información vive únicamente en `data/restricted/` y no se publica.

### 6.2 `DimFicha` (56 filas)

| Campo | Tipo | Descripción |
|---|---|---|
| `FichaID` | Texto | Número de ficha (clave de negocio). |
| `FichaNombre` | Texto | Etiqueta legible. |
| `ProgramaID` | Texto | FK a `DimPrograma`. |
| `Jornada` | Texto | `DIURNA` / `NOCTURNA`. |
| `GeneracionID` | Texto | FK a `DimGeneracion`. |
| `CentroID` | Texto | FK a `DimCentroFormacion`. |
| `EstadoFicha` | Texto | `EN EJECUCION` en el snapshot. |
| `FechaReporte` | Fecha | `2026-10-19`. |
| `TotalMatriculas` | Entero | n de la ficha. |
| `AprendicesActivos` | Entero | Activos. |
| `AprendicesVinculados` | Entero | Activos + aplazados. |
| `EnFormacion`, `Induccion`, `Condicionados`, `Aplazados`, `Cancelados`, `Retiros`, `Trasladados`, `Certificados` | Entero | Conteos por estado. |
| `TasaPerdida` | Decimal | Pérdidas / n. |
| `TasaPerdidaAjustada` | Decimal | Tasa suavizada empirical Bayes (prior k=10). |
| `TasaCancelacion`, `TasaRetiro`, `TasaActivos` | Decimal | Componentes. |
| `TasaContactoIncompleto` | Decimal | Proporción con contacto incompleto. **No entra al índice de riesgo.** |
| `IC95Inferior`, `IC95Superior` | Decimal | Intervalo de confianza de la tasa observada. |
| `IndiceRiesgo` | Decimal | Percentil de la tasa ajustada (0–100). |
| `PercentilRiesgo` | Decimal | Percentil empírico. |
| `NivelRiesgo` | Texto | `Bajo`, `Medio`, `Alto`, `Crítico`. |
| `RankingRiesgo` | Entero | 1 = mayor riesgo. |
| `Confiabilidad` | Texto | `Alta`, `Media`, `Baja` según n y intervalo. |
| `AlertaPrincipal`, `AlertaSecundaria` | Texto | Señales descriptivas. |
| `ProbDesercionFicha` | Decimal | Media posterior beta-binomial. |
| `ProbDesercionICInf`, `ProbDesercionICSup` | Decimal | IC creíble 95%. |
| `ProbSupera30`, `ProbSupera40` | Decimal | P(tasa futura > 30% / 40%). |
| `Prioridad` | Texto | `P1`–`P4` para comité académico. |

### 6.3 `DimPrograma` (15 filas)

`ProgramaID`, `ProgramaNombre`, `ProgramaCorto`, `LineaTecnologica`, `NivelFormacion`, `NivelFuente`, `TotalFichas`, `TotalMatriculas`, `Activo`, `NotaNivel`.

### 6.4 `DimJornada` (3 filas)

`JornadaID` (`J00` No informado, `J01` DIURNA, `J02` NOCTURNA), `Jornada`, `Descripcion`.

### 6.5 `DimEstado` (7 filas)

`EstadoID`, `Estado`, `Categoria`, `EsVinculado`, `EsActivo`, `EsPerdida`, `EsCancelado`, `EsRetirado`, `EsTrasladado`, `EsSuspendido`, `EsRiesgo`, `EsCertificado`, `Orden`, `ColorHex`, `Definicion`.

### 6.6 `DimTiempo` (1.095 filas)

Calendario diario 2024-01-01 a 2026-12-31: `FechaID` (yyyyMMdd), `Fecha`, `Anio`, `Trimestre`, `TrimestreNum`, `Mes`, `NombreMes`, `MesCorto`, `AnioMes`, `SemanaISO`, `Dia`, `DiaSemana`, `NombreDia`, `EsFinDeSemana`, `InicioMes`, `FinMes`. En el snapshot solo se usa `2026-10-19`; el calendario queda preparado para futuras series.

### 6.7 `DimCentroFormacion` (1 fila)

`CentroID` (`C001`), `CentroNombre`, `Regional`, `Ciudad`, `CodigoCentro`, `Nota`. El nombre del centro no estaba en la fuente; se usa una etiqueta genérica.

### 6.8 `DimNivelFormacion` (3 filas)

`NivelID`, `NivelFormacion`, `Orden`, `Definicion`. Incluye `No informado`.

### 6.9 `DimMunicipio` y `DimDepartamento` (1 fila cada una)

`MUN-000` / `DEP-000` = `No informado`. No se inventan municipios ni departamentos. Si en el futuro la fuente los incluye, se cargan aquí y se relacionan.

### 6.10 `DimGeneracion` (17 filas)

`GeneracionID`, `GeneracionNombre`, `GeneracionOrden`, `RangoFicha`, `Fichas`, `Matriculas`, `Perdidas`, `TasaPerdida`, `Nota`.

### 6.11 `DimRiesgo` (4 filas)

| Nivel | Orden | Percentil mínimo | Percentil máximo | Acción |
|---|---:|---:|---:|---|
| Bajo | 1 | 0 | 50 | Monitoreo rutinario |
| Medio | 2 | 50 | 75 | Seguimiento mensual |
| Alto | 3 | 75 | 90 | Plan de acción 30 días |
| Crítico | 4 | 90 | 100 | Comité académico en 8 días |

### 6.12 `FactMatricula` (1.592 filas)

Grano: **una fila por matrícula de aprendiz en ficha** (no una persona). Campos:

| Grupo | Campos |
|---|---|
| Claves | `MatriculaID`, `AprendizID`, `FichaID`, `ProgramaID`, `JornadaID`, `EstadoID`, `CentroID`, `NivelID`, `MunicipioID`, `DepartamentoID`, `GeneracionID`, `FechaReporteID` |
| Fecha | `FechaReporte` |
| Flags de estado | `EsVinculado`, `EsActivo`, `EsPerdida`, `EsCancelado`, `EsRetirado`, `EsTrasladado`, `EsSuspendido`, `EsRiesgo`, `EsCertificado` |
| Contacto | `ContactoCompleto`, `TieneCelular`, `CelularValido`, `EmailValido` |
| Riesgo de ficha | `NivelRiesgoFicha`, `IndiceRiesgoFicha` |
| Peso | `Peso` (1 para cada matrícula; reservado para futuras ponderaciones) |
| Modelo | `ProbPerdidaEstimada`, `NivelAlertaAprendiz`, `RankingRiesgoFicha`, `PercentilProbabilidad`, `PrioridadAtencion`, `MotivoPrioridad`, `RequiereIntervencion` |

`MatriculaID` es un consecutivo interno (`MAT-000001`…). No se usa para unir con la fuente.

### 6.13 `FactProyeccionMatricula` (168 filas = 56 fichas × 3 escenarios)

Grano: **ficha × escenario**. Campos: `Escenario`, `FichaID`, `ProgramaID`, `GeneracionID`, `Jornada`, `NivelRiesgo`, `Matriculas`, `PerdidasObservadas`, `TasaObservada`, `PoblacionVinculada`, `TasaFinalSupuesta`, `PerdidaAdicionalEsperada`, `PoblacionProyectada`, `TasaProyectada`, `Nota`.

No es un pronóstico calendario ni de nueva matrícula: es una **proyección de permanencia** de la población ya vinculada bajo supuestos explícitos.

---

## 7. Datos faltantes y decisiones

| Dimensión | Situación | Decisión |
|---|---|---|
| Género | 100% ausente | `No informado`; no se imputa. |
| Edad | 100% ausente | `Edad` vacía; solo proxy por tipo de documento, marcado como proxy. |
| Municipio / departamento | 100% ausente | `MUN-000` / `DEP-000`; no se inventan. |
| Fecha de matrícula | Ausente | No se calculan cohortes calendario; se usa prefijo de ficha. |
| Fecha de egreso / certificación | Ausente | No se calcula tiempo a certificación ni supervivencia. |
| Certificados | 0 registros | `Certificados = 0`; no se reporta tasa de certificación. |
| Motivo de retiro | Ausente | No se descompone la pérdida por causa. |
| Celular | 208 vacíos (13,1%) | Se marca `TieneCelular=0`; no se imputa. |
| Correo | 0 inválidos, 9 repetidos | Se conserva; dominio como variable descriptiva. |

**No se debe** usar `Edad` ni `Género` en el dashboard como si fueran datos observados. Aparecen como `No informado` y así se reportan.

---

## 8. Privacidad y acceso

| Archivo | Contenido | Acceso |
|---|---|---|
| `dashboard/index.html` | Dashboard agregado, IDs hasheados, sin PII | Público interno |
| `dashboard/datos_dashboard.json` | Datos agregados + IDs hasheados | Público interno |
| `data/processed/*.csv` | Modelo estrella sin nombres ni documentos | Uso analítico |
| `data/restricted/aprendices_crudos.json` | Filas originales con nombres, documentos, celular, correo | Restringido |
| `data/restricted/lista_priorizada.csv` | Lista nominal priorizada | Restringido |

El hash se construye con SHA-256 sobre el documento y un prefijo `APR-`; no se puede revertir con la información publicada. Los correos se reducen a dominio; los celulares solo a flags de validez. Cualquier extracción nominal debe hacerse desde `data/restricted/` con autorización y registro de acceso.

---

## 9. Reglas de calidad aplicadas

1. **Una fila por matrícula**: se conservan las 9 personas con dos fichas; no se deduplican para el análisis de fichas.
2. **Sin duplicados dentro de una ficha**: 0 casos.
3. **Documento vacío**: 0 casos.
4. **Correo**: 0 inválidos; 9 correos compartidos entre personas (posible correo familiar o error de digitación). No se usa como identificador.
5. **Celular**: se marca inválido si no tiene 10 dígitos; 228 registros con celular inválido o vacío.
6. **Fechas**: todas las fichas reportan `2026-10-19`; no se imputan fechas.
7. **Nombres de programa**: normalización manual documentada; 15 categorías.
8. **Nivel de formación**: inferido del nombre; `NivelFuente` lo declara.
9. **Estados**: mapeo explícito; `TRASLADADO` fuera de la tasa de pérdida.
10. **Riesgo**: el índice es un percentil de la tasa ajustada, no un score multifactorial; no incluye contacto incompleto.

---

## 10. Reproducibilidad

```powershell
$env:PYTHONIOENCODING='utf-8'
python -X utf8 scripts/01_explorar_datos.py
python -X utf8 scripts/02_etl_modelo_estrella.py
python -X utf8 scripts/03_analisis_estadistico.py
python -X utf8 scripts/04_modelo_predictivo.py
python -X utf8 scripts/05_generar_excel.py
python -X utf8 scripts/06_generar_dashboard.py
python -X utf8 scripts/07_generar_pbip.py
```

Los scripts 01–04 leen la carpeta fuente en modo solo lectura. Los scripts 05–07 consumen `data/processed/` y `outputs/`. La semilla de los modelos y remuestreos es `20261019`.
