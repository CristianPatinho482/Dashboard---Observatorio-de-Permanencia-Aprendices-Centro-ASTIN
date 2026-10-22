# Plan de implementación

**Horizonte:** 90 días para instalar la gestión; 6–12 meses para madurar el modelo con datos longitudinales.
**Alcance:** Centro ASTIN, 56 fichas, 15 programas, 1.592 matrículas.
**Principio:** primero gobernanza y datos, luego automatización. El tablero no reemplaza el juicio del comité.

---

## 1. Objetivos

| Objetivo | Indicador de éxito | Plazo |
|---|---|---|
| Institucionalizar la revisión de fichas críticas | 100% de las 6 fichas con acta y plan | 30 días |
| Cerrar la brecha de contacto | Contacto incompleto ≤ 8% | 60 días |
| Capturar el motivo de cancelación | ≥ 90% de las cancelaciones con motivo | 60 días |
| Reducir la pérdida global | ≤ 25% en el siguiente corte | 90 días |
| Reducir la pérdida nocturna | ≤ 32% | 90 días |
| Operar el tablero con datos actualizados | Corte mensual publicado | 30 días |
| Preparar el modelo longitudinal | Campos mínimos capturados | 90 días |
| Evaluar el piloto de alerta temprana | Protocolo y línea base definidos | 90–180 días |

---

## 2. Fases

### Fase 0 — Validación y acuerdo (semana 1)

**Actividades**

1. Presentar el dashboard y el informe al comité académico.
2. Validar los 15 nombres de programa y el nivel de formación contra SOFIA Plus.
3. Confirmar la definición de pérdida (cancelado + retiro) y la exclusión de trasladado.
4. Acordar que el score no se usa para sancionar ni negar cupo.
5. Designar un **owner** de datos y un **owner** de analítica.
6. Definir el calendario de cortes (mensual o por periodo).

**Entregables**

- Acta de validación metodológica.
- Matriz RACI.
- Calendario de cortes.
- Política de uso responsable (1 página).

**Criterio de salida:** acta firmada y nombres de programa aprobados.

---

### Fase 1 — Intervención inmediata (semanas 2–4)

**Actividades**

1. **Comité por ficha crítica** (6 fichas): revisar asistencia, juicios, novedades, contacto, instructor y conditions de aula.
2. **Plan individual** para las 65 matrículas en prioridad inmediata: llamada, correo, reunión, remisión a bienestar.
3. **Campaña de contacto** para las 228 matrículas con contacto incompleto, priorizando fichas críticas.
4. **Registro de motivo** de cancelación: formulario con categorías y texto libre.
5. **Reunión con instructores** de las fichas críticas para identificar causas operativas.
6. **Revisión de la jornada nocturna**: horarios de atención, transporte, conectividad, tutorías.

**Entregables**

- 6 actas con plan de acción, responsable y fecha.
- Lista de 65 prioridades con estado de contacto.
- Reporte de cobertura de contacto.
- Formulario de motivo de cancelación implementado.

**Criterio de salida:** 100% de fichas críticas con plan; ≥ 50% de prioridades contactadas.

---

### Fase 2 — Gestión por programa y cohorte (semanas 5–8)

**Actividades**

1. **Planes de programa** para Sistemas Integrados de Gestión, Gestión de Proyectos y Producción Industrial (63,1% de las pérdidas).
2. **Análisis de caso** de Monitoreo Ambiental (10,7% de pérdida) para identificar prácticas transferibles.
3. **Monitoreo de cohortes jóvenes** (345–358) con indicadores de proceso: asistencia, entregas, contacto, alertas.
4. **Revisión de admisión y nivelación** en programas con mayor tasa (Laboratorio Químico, Análisis de Materiales, Moldes y Troqueles, Química Aplicada).
5. **Capacitación** a coordinadores en lectura de IC, n y rankings inestables.
6. **Ajuste de metas** con el comité; no prometer reducciones sin recursos.

**Entregables**

- 3 planes de programa con metas y responsables.
- Caso Monitoreo Ambiental.
- Tablero de cohortes jóvenes con indicadores de proceso.
- Acta de capacitación.

**Criterio de salida:** planes aprobados y indicadores de proceso definidos.

---

### Fase 3 — Datos y modelo longitudinal (semanas 9–12)

**Actividades**

1. **Especificación de datos mínimos**: fecha de matrícula, fecha de retiro, motivo, periodo, género, fecha de nacimiento, municipio, departamento, certificación, cupos.
2. **Ajuste del sistema de registro** para capturar esos campos.
3. **Primer corte longitudinal** con al menos dos fechas por aprendiz.
4. **Reemplazo del proxy de generación** por cohortes calendario cuando exista fecha.
5. **Validación temporal** del modelo: entrenar con un corte, evaluar con el siguiente.
6. **Piloto de alerta temprana** con protocolo de contacto y grupo de comparación, si es ético y viable.

**Entregables**

- Diccionario de datos v2.
- Primer dataset longitudinal.
- Protocolo de evaluación del piloto.
- Informe de validación temporal (o plan si aún no hay datos).

**Criterio de salida:** datos mínimos capturados en ≥ 80% de los nuevos registros.

---

## 3. Roles y responsabilidades (RACI)

| Actividad | Dirección | Coordinación académica | Registro / sistemas | Bienestar | Analítica | Instructores |
|---|---|---|---|---|---|---|
| Validar metodología | A | R | C | I | C | I |
| Comité fichas críticas | A | R | I | C | C | C |
| Contacto prioridades | I | A | C | R | I | C |
| Motivo de cancelación | I | A | R | C | C | I |
| Actualización del tablero | I | C | C | I | R | I |
| Planes de programa | A | R | I | C | C | C |
| Datos demográficos | A | C | R | I | C | I |
| Política de uso | A | R | C | C | C | I |
| Evaluación de impacto | A | C | C | C | R | I |

`R` = responsable de ejecutar; `A` = aprueba; `C` = consultado; `I` = informado.

---

## 4. Datos requeridos para la siguiente versión

| Campo | Tipo | Uso | Prioridad |
|---|---|---|---|
| Fecha de matrícula | Fecha | Cohortes, tiempo de exposición, supervivencia | Crítica |
| Fecha de retiro/cancelación | Fecha | Tiempo hasta el evento, causa temporal | Crítica |
| Motivo de retiro | Categórica + texto | Causa, planes de acción | Crítica |
| Periodo académico | Texto/fecha | Comparación entre cortes | Crítica |
| Fecha de inicio/fin de ficha | Fecha | Proyección calendario | Alta |
| Cupos ofertados / matriculados | Entero | Pronóstico de nueva matrícula | Alta |
| Género | Categórica | Equidad | Alta |
| Fecha de nacimiento / edad | Fecha/entero | Equidad, riesgo etario | Alta |
| Municipio / departamento | Categórica | Equidad territorial, movilidad | Alta |
| Certificación | Fecha/booleano | Tasa de éxito, tiempo a certificación | Alta |
| Estrato / condición socioeconómica | Categórica | Vulnerabilidad | Media |
| Discapacidad / apoyos | Categórica | Inclusión | Media |
| Asistencia | Porcentaje | Alerta temprana | Media |
| Juicios evaluativos | Categórica/numérica | Alerta temprana | Media |

**Regla:** si un campo no está, se reporta `No informado`; no se imputa ni se inventa.

---

## 5. Gobernanza

### 5.1 Propiedad del dato

- **Owner de datos:** registro académico; responsable de la calidad, completitud y oportunidad.
- **Steward de analítica:** analítica institucional; responsable del modelo, tablero y definiciones.
- **Comité académico:** decide acciones sobre fichas y aprendices.
- **Bienestar:** ejecuta contacto y acompañamiento.
- **Dirección:** aprueba metas y recursos.

### 5.2 Calidad

| Dimensión | Regla | Frecuencia |
|---|---|---|
| Completitud | ≥ 98% en campos críticos | Mensual |
| Unicidad | 0 duplicados dentro de ficha | Mensual |
| Validez | Correo y celular válidos | Mensual |
| Consistencia | Suma de estados = total | Cada corte |
| Oportunidad | Corte publicado ≤ 5 días hábiles | Mensual |
| Trazabilidad | Versión de fuente y script | Cada corte |

### 5.3 Privacidad

- El dashboard público usa IDs hasheados y agregados.
- La lista nominal vive en `data/restricted/` con acceso restringido.
- No se envía PII por correo ni se publica en Power BI Service sin roles.
- El hash no se comparte con terceros.
- Toda extracción nominal requiere autorización y registro.

### 5.4 Uso responsable

- Prohibido usar el score para negar cupo, sancionar o etiquetar.
- Toda alerta debe tener motivo y revisión humana.
- Las decisiones de cierre de ficha o programa requieren análisis adicional, no solo tasa.
- Se debe reportar la incertidumbre (IC, n) junto con cualquier ranking.

---

## 6. Riesgos y mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Datos incompletos o tardíos | Alta | Alto | Acuerdo de nivel de servicio con registro; validaciones automáticas |
| Interpretación causal errónea | Alta | Alto | Comunicar limitaciones; capacitación; notas en el tablero |
| Estigmatización de aprendices | Media | Alto | Política de uso; prohibición de sanciones; revisión humana |
| Fichas pequeñas generan rankings inestables | Alta | Medio | Mostrar IC y n; no ordenar solo por tasa |
| Cambio de nombres de programa | Media | Medio | Catálogo maestro y validación contra SOFIA |
| Falta de mantenimiento del tablero | Media | Alto | Owner designado; calendario; documentación |
| Dependencia de una sola persona | Alta | Alto | Repositorio, scripts, README, transferencia de conocimiento |
| El modelo no se valida temporalmente | Alta | Medio | No usarlo para decisiones individuales; plan de validación |
| Expectativas irreales de reducción | Media | Medio | Metas de gestión, no promesas; evaluar con línea base |
| Duplicados de aprendices entre fichas | Media | Bajo | `AprendizID` y regla de conteo documentada |

---

## 7. Criterios de aceptación

### 7.1 Dashboard HTML

- [x] 7 pestañas funcionales, sin errores JS.
- [x] KPIs coherentes con `outputs/03` y `outputs/04`.
- [x] Filtros de programa, jornada, riesgo y búsqueda.
- [x] Descargas CSV sin PII.
- [x] Sin llamadas externas; funciona offline.
- [x] Banner de brecha de datos visible.
- [x] Tablas con n, tasa, IC y prioridad.
- [x] Validado en Chrome headless (0 `NaN`, 0 `undefined`).

### 7.2 Excel

- [ ] Portada, Resumen, Programas, Fichas, Cohortes, Riesgos, Predictivo, Diccionario, Notas.
- [ ] Cifras coincidentes con el HTML.
- [ ] Gráficos nativos y filtros.
- [ ] Sin PII.
- [ ] Formato condicional en tasas y niveles.

### 7.3 PBIP

- [ ] Modelo TMDL con 13 dimensiones + 2 hechos + tabla de medidas.
- [ ] Relaciones 1:* sin ambigüedad.
- [ ] Medidas DAX del catálogo.
- [ ] 7 páginas con visuales equivalentes al HTML.
- [ ] `pbir validate` sin errores críticos.
- [ ] Documentación de actualización de la ruta de datos.

### 7.4 Reproducibilidad

- [ ] Pipeline 01 → 06 ejecutable desde cero.
- [ ] Semilla fija.
- [ ] README con instrucciones.
- [ ] Source en solo lectura.
- [ ] Salidas versionadas.

---

## 8. Calendario resumido

| Semana | Hito | Entregable |
|---|---|---|
| 1 | Validación metodológica | Acta, RACI, calendario |
| 2 | Comité fichas críticas | 6 actas |
| 3 | Contacto prioridades | Reporte de cobertura |
| 4 | Motivo de cancelación | Formulario y primeras cifras |
| 5 | Planes de programa | 3 planes |
| 6 | Caso Monitoreo Ambiental | Informe |
| 7 | Cohortes jóvenes | Tablero de proceso |
| 8 | Capacitación | Acta |
| 9 | Datos mínimos v2 | Diccionario |
| 10 | Ajuste de sistemas | Campos capturados |
| 11 | Primer corte longitudinal | Dataset |
| 12 | Validación y cierre | Informe y plan 2027 |

---

## 9. Presupuesto y recursos (orden de magnitud)

| Rubro | Supuesto | Prioridad |
|---|---|---|
| Analista de datos | 0,5 FTE durante 3 meses | Alta |
| Coordinación académica | 0,2 FTE | Alta |
| Bienestar | 1 profesional para contacto | Alta |
| Desarrollo de formulario | 2–3 semanas de TI | Alta |
| Capacitación | 2 talleres de 2 horas | Media |
| Licencias Power BI | Pro para publicación | Media |
| Evaluación externa | Opcional, 1 consultoría | Baja |

No se incluye costo de intervenciones (tutorías, transporte, apoyos), que debe presupuestar bienestar.

---

## 10. Después de los 90 días

1. **Corte longitudinal** con al menos dos observaciones por aprendiz.
2. **Modelo de supervivencia** (Kaplan–Meier / Cox) para tiempo hasta el retiro.
3. **Pronóstico de matrícula** con series temporales y estacionalidad.
4. **Evaluación de impacto** de las intervenciones (diferencias en diferencias o ensayo escalonado).
5. **Publicación en Power BI Service** con roles y actualización programada.
6. **Catálogo de indicadores** institucional, con definiciones únicas.
7. **Auditoría de equidad** por género, edad y territorio cuando existan datos.
8. **Revisión anual** del modelo y de las metas.

---

## 11. Mensaje de cierre

El tablero ya muestra lo que se puede mostrar con la fuente actual: 439 pérdidas, 6 fichas críticas, una brecha de contacto y un modelo que prioriza fichas, no personas. Lo que falta no es “más dashboard”: son **fechas, motivos y datos demográficos**. La institución que capture esos campos podrá pasar de describir la deserción a prevenirla con evidencia.
