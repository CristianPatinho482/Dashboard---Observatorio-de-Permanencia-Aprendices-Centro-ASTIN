# Informe estadístico — Permanencia de aprendices

**Snapshot:** 19 de octubre de 2026
**Universo:** 1.592 matrículas · 1.583 aprendices únicos · 56 fichas · 15 programas
**Naturaleza:** estudio transversal descriptivo, con contrastes exploratorios. No es un estudio causal ni longitudinal.

---

## 1. Resumen ejecutivo

| Indicador | Valor | IC 95% |
|---|---:|---:|
| Matrículas | 1.592 | — |
| Pérdidas (cancelado + retiro) | 439 | — |
| **Tasa de pérdida** | **27,58%** | **25,44%–29,82%** |
| Cancelación | 26,88% | — |
| Retiro voluntario | 0,69% | — |
| Activos | 1.137 (71,42%) | — |
| Vinculados (activos + aplazados) | 1.144 (71,86%) | — |
| Trasladados | 9 (0,57%) | — |
| Contacto incompleto | 228 (14,32%) | — |

La pérdida es casi enteramente **cancelación** (428 de 439; 97,5% de las pérdidas). El retiro voluntario es marginal (11 casos). Esto importa para la acción: el fenómeno no se explica por “decisiones voluntarias” declaradas, sino por cancelaciones administrativas/académicas cuyo motivo no está en la fuente.

---

## 2. Métodos

### 2.1 Diseño

- Un solo corte transversal; no hay seguimiento ni fecha de matrícula/egreso.
- Unidad de análisis principal: **matrícula en ficha**. Unidad secundaria: ficha (n=56).
- Los intervalos de confianza de proporciones usan **Wilson** al 95%.
- Los contrastes de independencia usan **chi-cuadrado de Pearson**; cuando hay celdas con frecuencia esperada <5 se reporta **Fisher** o **Monte Carlo** (5.000 simulaciones).
- Tamaño de efecto: **V de Cramér** para tablas de contingencia; **odds ratio (OR)** con IC 95% para tablas 2×2.
- Para controlar confounding por programa en la relación contacto–pérdida se usa **Mantel–Haenszel**.
- Tendencia por generación: **Spearman** y **Cochran–Armitage** (proporciones ordinales).
- El nivel de significancia es 0,05; los p-valores son **exploratorios** y no corrigen por dependencia intra-ficha.

### 2.2 Limitaciones estructurales

1. **Sin fecha de matrícula**: no se puede calcular tiempo en formación, supervivencia ni cohortes calendario.
2. **Sin motivo de retiro**: no se puede distinguir causa académica, económica, laboral o personal.
3. **Sin variables socioeconómicas**: género, edad, municipio y estrato no están en la fuente.
4. **Fichas como clusters**: los aprendices de una misma ficha comparten instructor, horario y programa; los p-valores no corrigen esta dependencia.
5. **Cohortes jóvenes**: las generaciones 345–358 tienen 0% de pérdida porque son recientes, no porque sean exitosas.
6. **Snapshot único**: no hay validación temporal del riesgo ni del modelo.

---

## 3. Resultados globales

### 3.1 Distribución por estado

| Estado | n | % |
|---|---:|---:|
| EN FORMACION | 1.112 | 69,85% |
| CANCELADO | 428 | 26,88% |
| INDUCCION | 19 | 1,19% |
| RETIRO VOLUNTARIO | 11 | 0,69% |
| TRASLADADO | 9 | 0,57% |
| APLAZADO | 7 | 0,44% |
| CONDICIONADO | 6 | 0,38% |

La suma es 1.592. No hay certificados en el snapshot.

### 3.2 Pérdida por jornada

| Jornada | n | Pérdidas | Tasa | IC 95% |
|---|---:|---:|---:|---:|
| DIURNA | 1.031 | 237 | 22,99% | 20,52%–25,65% |
| NOCTURNA | 561 | 202 | 36,01% | 32,14%–40,06% |

- χ²(1) = 30,189; p < 0,001; V de Cramér = 0,138 (efecto pequeño).
- OR diurna vs nocturna = **0,53** (IC 95% 0,423–0,665); Fisher p < 0,001.
- Lectura: la jornada nocturna tiene aproximadamente **1,9 veces** el odds de pérdida de la diurna. Es una asociación robusta en el snapshot, pero **no causal**: la jornada puede estar confundida con programa, cohorte y condiciones laborales.

### 3.3 Pérdida por programa

El contraste global es significativo: χ²(14) = 65,477; p < 0,001; V de Cramér = 0,203 (efecto moderado). Monte Carlo p = 0,0002. Sin embargo, 2 celdas tienen frecuencia esperada <5 (6,7%), y varios programas tienen una sola ficha.

**Programas con mayor tasa observada**

| Programa | Fichas | n | Pérdidas | Tasa | IC 95% | Brecha vs global |
|---|---:|---:|---:|---:|---:|---:|
| Aplicación de Procedimientos de Laboratorio Químico | 1 | 14 | 7 | 50,00% | 26,8%–73,2% | +22,4 pp |
| Análisis de Materiales para la Industria | 2 | 38 | 14 | 36,84% | 23,4%–52,7% | +9,3 pp |
| Fabricación de Moldes y Troqueles | 2 | 53 | 19 | 35,85% | 24,3%–49,3% | +8,3 pp |
| Química Aplicada a la Industria | 4 | 113 | 40 | 35,40% | 27,2%–44,6% | +7,8 pp |
| Gestión de la Producción Industrial | 6 | 183 | 58 | 31,69% | 25,4%–38,8% | +4,1 pp |
| Coordinación en Sistemas Integrados de Gestión | 15 | 484 | 153 | 31,61% | 27,6%–35,9% | +4,0 pp |

**Programas con menor tasa observada**

| Programa | Fichas | n | Pérdidas | Tasa | IC 95% | Brecha vs global |
|---|---:|---:|---:|---:|---:|---:|
| Monitoreo Ambiental | 4 | 149 | 16 | 10,74% | 6,7%–16,7% | −16,8 pp |
| Modelado de Productos Industriales | 4 | 101 | 23 | 22,77% | 15,7%–31,9% | −4,8 pp |
| Componentes Mecánicos | 3 | 84 | 20 | 23,81% | 16,0%–33,9% | −3,8 pp |
| Procesos de Manufactura (Baxter) | 1 | 26 | 0 | 0,00% | 0,0%–12,9% | −27,6 pp |
| Transformación de Polímeros | 1 | 23 | 0 | 0,00% | 0,0%–14,3% | −27,6 pp |
| Alistamiento de Laboratorios | 1 | 18 | 0 | 0,00% | 0,0%–17,6% | −27,6 pp |

**Lectura correcta:** los programas con 1 ficha y 0% no son “mejores” con evidencia suficiente; su IC superior llega a 12,9%–17,6%, y podrían tener pérdidas ocultas si la cohorte es joven. El ranking por tasa puntual no debe usarse para asignar recursos sin mirar n, IC y generación.

Concentración: HHI = 0,1516; número efectivo de programas = 6,6; top-3 = 56,65% de la matrícula. La cartera está concentrada en Sistemas Integrados de Gestión (30,4%), Gestión de Proyectos (14,8%) y Producción Industrial (11,5%).

### 3.4 Distribución de tasas por ficha

| Estadístico | Valor |
|---|---:|
| Fichas | 56 |
| Media | 27,26% |
| Mediana | 26,80% |
| Desviación estándar | 19,73 pp |
| Mínimo | 0,00% |
| Q1 | 7,44% |
| Q3 | 43,51% |
| Máximo | 62,07% |
| IQR | 36,07 pp |
| Coeficiente de variación | 0,724 |
| Asimetría | −0,067 |
| Curtosis | −1,185 |

No hay outliers según el criterio IQR, pero la dispersión es enorme: la ficha con mayor tasa (62,1%) casi duplica la mediana. Esa heterogeneidad es la principal justificación del enfoque por ficha.

### 3.5 Tamaño de ficha y pérdida

| Tamaño | Fichas | n | Pérdidas | Tasa |
|---|---:|---:|---:|---:|
| < 20 | 5 | 88 | 30 | 34,09% |
| 20–29 | 22 | 548 | 148 | 27,01% |
| 30–39 | 27 | 860 | 220 | 25,58% |
| 40+ | 2 | 96 | 41 | 42,71% |

Correlación tamaño–tasa: Pearson r = 0,070 (p = 0,609); Spearman ρ = 0,036 (p = 0,791). **No hay evidencia de que las fichas más grandes tengan mayor pérdida** en este snapshot; las dos fichas de 40+ son un caso aislado.

---

## 4. Cohortes por prefijo de ficha

| Generación | Fichas | n | Pérdidas | Tasa |
|---|---:|---:|---:|---:|
| GEN-314 | 4 | 121 | 60 | 49,59% |
| GEN-317 | 8 | 230 | 100 | 43,48% |
| GEN-318 | 2 | 50 | 26 | 52,00% |
| GEN-323 | 1 | 24 | 10 | 41,67% |
| GEN-330 | 4 | 146 | 64 | 43,84% |
| GEN-331 | 1 | 26 | 6 | 23,08% |
| GEN-335 | 3 | 74 | 35 | 47,30% |
| GEN-340 | 5 | 100 | 32 | 32,00% |
| GEN-341 | 9 | 275 | 61 | 22,18% |
| GEN-343 | 1 | 21 | 1 | 4,76% |
| GEN-344 | 6 | 191 | 44 | 23,04% |
| GEN-345 | 1 | 23 | 0 | 0,00% |
| GEN-346 | 2 | 69 | 0 | 0,00% |
| GEN-349 | 2 | 60 | 0 | 0,00% |
| GEN-353 | 3 | 85 | 0 | 0,00% |
| GEN-356 | 2 | 49 | 0 | 0,00% |
| GEN-358 | 2 | 48 | 0 | 0,00% |

- Spearman orden–tasa: ρ = **−0,921** (p < 0,001).
- Cochran–Armitage: z = **−14,688** (p < 0,001); pendiente ≈ **−3,52 pp** por prefijo.
- La tendencia es fuerte, pero es **descriptiva**: el prefijo no es un año y las cohortes jóvenes tienen menos tiempo de exposición.

**Lectura de negocio:** la caída del 0% en las generaciones 345–358 no debe celebrarse. Es el resultado esperado de un snapshot temprano. La pregunta correcta es si esas cohortes repetirán el patrón de las maduras cuando acumulen exposición; la proyección base asume que sí (plateau 43,19%).

---

## 5. Contacto y calidad de datos

### 5.1 Contacto vs pérdida

| Contacto | n | Pérdidas | Tasa |
|---|---:|---:|---:|
| Completo | 1.364 | 369 | 27,05% |
| Incompleto | 228 | 70 | 30,70% |

- χ²(1) = 0,812; p = 0,368; V = 0,023.
- OR crudo incompleto vs completo = **1,166** (IC 95% 0,858–1,584).
- OR ajustado por programa (Mantel–Haenszel) = **0,651** (IC 95% 0,463–0,916).

**Conclusión:** el contacto incompleto **no es un factor de riesgo**. La asociación cruda es nula y la ajustada invierte el signo porque el contacto incompleto se concentra en cohortes nuevas con 0% de pérdida y en programas con menor pérdida. Es una **brecha de contactabilidad y actualización de datos**, no una causa de deserción. Se excluyó del índice de riesgo.

Correlación a nivel de ficha: Pearson r = −0,395 (p = 0,003); Spearman ρ = −0,301 (p = 0,024). Negativa, consistente con el confounding por cohorte. No interpretar como “el contacto incompleto protege”.

### 5.2 Tipo de documento

| Tipo | n | Pérdidas | Tasa |
|---|---:|---:|---:|
| CC | 1.296 | 362 | 27,93% |
| TI | 277 | 72 | 25,99% |
| PPT | 18 | 4 | 22,22% |
| CE | 1 | 1 | 100,00% |

χ²(3) = 3,315; p = 0,346; V = 0,046. **Sin asociación significativa.** El caso CE (n=1) no debe interpretarse. El tipo de documento no es un buen predictor individual.

### 5.3 Género, edad, municipio

No informados al 100%. No se imputan. Cualquier tabla que los muestre debe decir `No informado`, no “otro” ni “sin dato” como si fuera una categoría sustantiva.

### 5.4 Duplicados y contactos

- 9 aprendices aparecen en 2 fichas (18 matrículas). No hay duplicados dentro de una ficha.
- 9 correos están repetidos entre personas; 0 correos inválidos.
- 208 celulares vacíos (13,07%); 228 con celular inválido o vacío (14,32%).
- 1.541 nombres abreviados únicos; 9 nombres repetidos. Los nombres no se publican.

---

## 6. Validación del índice de riesgo

| Banda | Fichas | n | Pérdidas | Tasa observada | Índice promedio |
|---|---:|---:|---:|---:|---:|
| Bajo | 28 | 789 | 87 | 11,03% | 24,6 |
| Medio | 14 | 389 | 137 | 35,22% | 62,7 |
| Alto | 8 | 208 | 99 | 47,60% | 82,7 |
| Crítico | 6 | 206 | 116 | 56,31% | 95,5 |

La monotonía es perfecta. El índice separa un grupo de 6 fichas con 56,3% de pérdida frente a 28 fichas con 11,0%. **No es una validación predictiva**: el índice se construyó con la misma tasa que luego se compara. Es una comprobación de coherencia, no una prueba de acierto futuro.

---

## 7. Poder estadístico

- Tasa base 27,58%; n = 1.592.
- Diferencia mínima detectable entre dos grupos iguales: **6,28 pp** (α = 0,05 bilateral; poder 80%; aproximación normal).
- Para fichas pequeñas (n=14–30), el IC de una tasa puede abarcar 25–30 pp. Por eso se reportan IC y no solo el ranking.
- Los contrastes por ficha y por generación tienen baja potencia y dependencia intra-cluster; son exploratorios.

---

## 8. Hallazgos que resisten el escrutinio

1. **La pérdida global es alta y consistente:** 27,6% (IC 25,4–29,8), con 97,5% de cancelaciones.
2. **La jornada nocturna tiene mayor pérdida:** 36,0% vs 23,0%, OR 0,53, p < 0,001. Asociación robusta, no causal.
3. **Hay heterogeneidad real entre fichas:** tasas de 0% a 62,1%, con IC amplios en fichas pequeñas.
4. **Los programas difieren:** χ² p < 0,001, V = 0,203; pero el ranking puntual es inestable por tamaños de 1 ficha.
5. **La pérdida cae con el prefijo de ficha:** ρ = −0,921; es un proxy de madurez, no un año.
6. **El contacto incompleto no predice pérdida:** OR crudo 1,17 (p = 0,368); ajustado 0,65. Es un tema de datos, no de riesgo.
7. **El tipo de documento no discrimina:** p = 0,346; V = 0,046.
8. **Las fichas críticas concentran 206 matrículas y 116 pérdidas:** 26,4% de las pérdidas del centro en 10,7% de la matrícula.

---

## 9. Lo que NO se puede concluir

- Que la jornada nocturna **cause** la deserción. Puede haber confusión con programa, edad, empleo o cohorte.
- Que un programa sea “mejor” que otro por su tasa puntual. Varios tienen 1 ficha y IC muy amplios.
- Que las cohortes jóvenes sean exitosas por tener 0% de pérdida. No han acumulado exposición.
- Que el contacto incompleto cause deserción. La evidencia apunta a lo contrario/confounding.
- Que el índice de riesgo prediga el futuro. Es un ranking de la tasa observada suavizada.
- Que el modelo individual sirva para señalar personas. AUC individual = 0,467.

---

## 10. Recomendaciones metodológicas

1. Reportar siempre `n` e IC junto a las tasas; no publicar rankings sin denominador.
2. No comparar programas como si hubiera asignación aleatoria; hay autoselección y clustering por ficha.
3. Validar el nivel de formación y los nombres de programa contra SOFIA Plus.
4. Solicitar a la fuente: fecha de matrícula, fecha de retiro, motivo, periodo académico, género, edad, municipio y certificación.
5. Con datos longitudinales, reemplazar el proxy de generación por cohortes calendario y ajustar modelos de supervivencia.
6. Mantener el contacto incompleto como indicador de calidad, separado del riesgo.
7. Revisar las 6 fichas críticas con el comité académico antes de tomar decisiones de cierre o reasignación.
8. No usar este informe para sancionar aprendices ni para negar cupos.

---

## 11. Reproducibilidad

Resultados generados por `scripts/03_analisis_estadistico.py` y `scripts/04_modelo_predictivo.py`. Salidas verificables:

- `outputs/03_analisis_estadistico.json`
- `outputs/04_modelo_predictivo.json`
- `outputs/charts/01–12*.png`

Semilla: `20261019`. Versiones: Python 3.14, pandas 3.0.3, SciPy 1.18.1, scikit-learn 1.9.1.
