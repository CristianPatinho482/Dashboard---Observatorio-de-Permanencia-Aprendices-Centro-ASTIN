# Metodología predictiva y de priorización

**Objetivo:** priorizar fichas y matrículas para gestión académica, no predecir el comportamiento de una persona.
**Datos:** snapshot 2026-10-19; 1.592 matrículas; 439 pérdidas; 56 fichas.
**Validación:** `StratifiedGroupKFold(5)` agrupado por `FichaID`, predicciones out-of-fold.
**Semilla:** `20261019`.

---

## 1. Qué se modela y qué no

| Se modela | No se modela |
|---|---|
| Probabilidad estructural de pérdida por ficha | Trayectoria individual de un aprendiz |
| Score de priorización por matrícula | Diagnóstico, sanción o negación de cupo |
| Proyección de permanencia por escenarios | Pronóstico calendario de nueva matrícula |
| Incertidumbre (IC creíble / bootstrap) | Causalidad de una intervención |

La distinción es central: el modelo aprende **diferencias entre fichas, programas, jornadas y cohortes**, no señales personales. El modelo con variables individuales tiene AUC 0,4666, prácticamente azar.

---

## 2. Datos de entrada

### 2.1 Unidad y etiqueta

- Una fila por matrícula (`FactMatricula`).
- Etiqueta `y = EsPerdida` (1 = cancelado o retiro voluntario; 0 = activo, inducción, condicionado, aplazado o trasladado).
- `TRASLADADO` se trata como no pérdida; es una salida administrativa, no deserción.
- Tasa base: **27,58%** (439/1.592).

### 2.2 Variables

| Grupo | Variable | Tipo | Uso |
|---|---|---|---|
| Estructura | `ProgramaID` | Categórica | Programa normalizado (15) |
| Estructura | `Jornada` | Categórica | DIURNA / NOCTURNA |
| Estructura | `TamanoFicha` | Numérica | Matrículas de la ficha |
| Estructura | `GeneracionOrden` | Numérica | Orden del prefijo (1–17) |
| Estructura | `TasaContactoIncompletoFicha` | Numérica | Proporción de contacto incompleto en la ficha |
| Individuo | `TipoDocumento` | Categórica | CC / TI / PPT / CE |
| Individuo | `DominioGrupo` | Categórica | Gmail / Hotmail-Outlook / Educativo / Otro / Sin correo |
| Individuo | `ContactoCompleto` | 0/1 | Celular y correo válidos |
| Individuo | `TieneMultiplesFichas` | 0/1 | Aparece en más de una ficha |

**Preprocesamiento:** one-hot encoding con `drop="first"` para categóricas; estandarización (z-score) para numéricas; regresión logística `C=1.0`, `max_iter=5000`. No se imputan valores: las variables ausentes se excluyeron del modelo.

**Variable excluida:** `ContactoCompleto` se mantiene en el modelo completo como proxy de contactabilidad/cohorte, pero **no** entra al índice de riesgo de ficha. Su asociación causal no está identificada.

---

## 3. Tres modelos para diagnosticar la señal

| Modelo | Variables | AUC | Brier | Lectura |
|---|---|---:|---:|---|
| Completo | Estructura + individuo | **0,7258** | 0,1776 | Mejor discriminación; usa estructura y algo de individuo |
| Solo individual | Tipo documento, dominio, contacto, múltiples fichas | **0,4666** | 0,2009 | Sin señal personal; ~azar |
| Solo estructural | Programa, jornada, tamaño, generación, contacto de ficha | **0,7158** | 0,1806 | Casi todo el poder está en la estructura |

**Conclusión:** la señal es estructural. El modelo completo no debe presentarse como “predicción personal”; su utilidad es ordenar fichas y matrículas dentro de fichas.

El AUC del modelo completo (0,7258) tiene IC 95% bootstrap por ficha de **0,6694–0,7813** (1.000 réplicas). La ganancia sobre azar es 0,2258.

---

## 4. Métricas de validación

### 4.1 Discriminación y calibración

| Métrica | Valor | Interpretación |
|---|---:|---|
| AUC | 0,7258 | Buena discriminación para un modelo estructural |
| Brier | 0,1776 | Mejor que la tasa base (0,1997) |
| Log loss | 0,5320 | — |
| ECE | 0,0478 | Error de calibración bajo (< 0,05) |
| Pendiente de calibración | 0,721 | Predicciones algo extremas; conviene recalibrar si se usan como probabilidad |
| Intercepto de calibración | −0,140 | Ligera sobreestimación global |

### 4.2 Matriz de confusión en el umbral de Youden

Umbral: **0,2022**.

|  | Predicho no pérdida | Predicho pérdida |
|---|---:|---:|
| Real no pérdida | 742 (TN) | 411 (FP) |
| Real pérdida | 114 (FN) | 325 (TP) |

- Sensibilidad: **74,0%**.
- Especificidad: **64,4%**.
- El umbral de Youden maximiza sensibilidad + especificidad; no es un punto de operación operativo. Para priorizar, se usan bandas por percentiles, no este umbral.

### 4.3 Calibración por deciles

| Decil | n | Prob. media | Tasa observada | Brecha |
|---|---:|---:|---:|---:|
| D1 | 160 | 2,71% | 5,63% | +2,91 pp |
| D2 | 160 | 6,45% | 10,62% | +4,18 pp |
| D3 | 159 | 9,85% | 16,35% | +6,51 pp |
| D4 | 159 | 13,71% | 13,84% | +0,13 pp |
| D5 | 159 | 16,19% | 19,50% | +3,30 pp |
| D6 | 159 | 22,12% | 28,30% | +6,18 pp |
| D7 | 159 | 32,68% | 41,51% | +8,83 pp |
| D8 | 159 | 42,85% | 41,51% | −1,34 pp |
| D9 | 159 | 49,87% | 41,51% | −8,36 pp |
| D10 | 159 | 63,30% | 57,23% | −6,07 pp |

El modelo subestima en los deciles bajos y sobreestima en los altos; la pendiente 0,721 confirma que las probabilidades son algo extremas. Para **ordenar** funciona; para **decir “este aprendiz tiene 63% de probabilidad”** no está calibrado con precisión.

---

## 5. Probabilidad por ficha: beta-binomial

Para cada ficha:

\[
p_f \mid y_f \sim \text{Beta}(y_f + \alpha_0,\; n_f - y_f + \beta_0)
\]

con:
- \(\bar{p} = 0.2758\)
- \(k = 10\)
- \(\alpha_0 = \bar{p}k = 2.758\)
- \(\beta_0 = (1-\bar{p})k = 7.242\)

La media posterior es la probabilidad reportada; el IC creíble 95% usa los percentiles 2,5% y 97,5%. También se calcula \(P(p_f > 0.30)\) y \(P(p_f > 0.40)\).

**Por qué:** con fichas de 14–50 aprendices, una tasa observada de 0% o 100% es inestable. El prior la contrae hacia la media global; las fichas pequeñas se mueven más, las grandes menos. No es un “castigo” ni un “beneficio”: es una estimación con incertidumbre.

**Fichas prioritarias**

| Rank | Ficha | Programa | Jornada | n | Tasa | Prob. | IC 95% | Nivel |
|---:|---|---|---|---:|---:|---:|---|---|
| 1 | 3171493 | Producción Industrial | NOCTURNA | 29 | 62,1% | 53,2% | 37,7%–68,4% | Crítico |
| 2 | 3181464 | Sistemas Integrados de Gestión | NOCTURNA | 31 | 61,3% | 53,1% | 37,9%–67,9% | Crítico |
| 3 | 3145899 | Química Aplicada | DIURNA | 30 | 60,0% | 51,9% | 36,6%–67,0% | Crítico |
| 4 | 3302821 | Sistemas Integrados de Gestión | NOCTURNA | 46 | 54,3% | 49,6% | 36,7%–62,5% | Crítico |
| 5 | 3141025 | Sistemas Integrados de Gestión | NOCTURNA | 31 | 54,8% | 48,2% | 33,2%–63,3% | Crítico |
| 6 | 3302143 | Sistemas Integrados de Gestión | DIURNA | 39 | 48,7% | 44,4% | 30,9%–58,3% | Crítico |

Las seis comparten: cohortes 314–330, pérdida observada ≥48,7%, y en 4 de 6 la jornada es nocturna. No se debe concluir que la jornada “cause” el resultado; la ficha combina programa, cohorte y condiciones de operación.

---

## 6. Alertas por matrícula

El score out-of-fold se agrupa en bandas:

| Banda | Regla | Matrículas | Prioridad asociada |
|---|---|---:|---|
| Alto | \(p \ge \max(0.40, P90)\) = **0,524** | 160 | Inmediata si ficha crítica; seguimiento si no |
| Medio | \(p \ge \max(0.28, mediana)\) = **0,280** | 439 | Seguimiento |
| Bajo | \(p < 0.280\) | 993 | Rutinaria |

Prioridad operativa:

| Prioridad | Regla | Matrículas |
|---|---|---:|
| Inmediata | Ficha crítica **y** (score alto **o** contacto incompleto) | **65** |
| Seguimiento | Ficha crítica/alto, score alto o contacto incompleto | **562** |
| Rutinaria | Resto | **965** |

**Importante:** la prioridad es una regla de gestión, no una probabilidad. “Inmediata” no significa que la persona vaya a desertar; significa que cumple criterios para revisión humana.

Dentro de cada ficha se calcula `RankingRiesgoFicha` (1 = mayor score) y `PercentilProbabilidad` global. La lista nominal con PII está en `data/restricted/lista_priorizada.csv`; la versión pública usa `AprendizID` hasheado.

---

## 7. Proyección de permanencia

### 7.1 Supuestos

- **Cohortes maduras:** prefijos 314–340 (8 generaciones, 771 matrículas, 333 pérdidas) → plateau global **43,19%**.
- **Plateau por programa:** suavizado hacia el global con \(k=50\):
  \[
  \text{plateau}_p = \frac{y_p + 50 \times 0.4319}{n_p + 50}
  \]
- **Pérdida adicional:** si la ficha tiene tasa observada \(p_{obs}\) y plateau \(P\), la proporción adicional es \((P-p_{obs})/(1-p_{obs})\), aplicada a la población vinculada.
- **Escenarios:** Optimista = plateau − 7 pp; Base = plateau por programa; Pesimista = plateau + 7 pp.

### 7.2 Resultados

| Escenario | Vinculados | Pérdida adicional | Población proyectada | Tasa proyectada |
|---|---:|---:|---:|---:|
| Optimista | 1.144 | 212 | **932** | 40,9% |
| Base | 1.144 | 288 | **856** | 45,6% |
| Pesimista | 1.144 | 375 | **769** | 51,1% |

**Lectura:** aun en el escenario optimista, se proyecta una pérdida acumulada de 40,9%; en el base, 45,6%. La diferencia entre escenarios es de ±7 pp, no un intervalo estadístico.

### 7.3 Lo que la proyección no es

- No es un pronóstico de matrícula nueva: no hay serie temporal ni fecha/periodo de matrícula.
- No es un pronóstico calendario: no hay fecha de inicio/fin de ficha.
- No es una predicción de cada aprendiz: usa la ficha como unidad.
- No incorpora capacidad, cupos, oferta ni política institucional.
- No prueba que una intervención reduzca la pérdida.

Para un pronóstico de nueva matrícula se requiere: fecha/periodo de matrícula, fechas de inicio/fin de ficha, cupos ofertados y matriculados por periodo, meta de admisión, capacidad instalada, y fecha/motivo de retiro.

---

## 8. Validación y robustez

| Prueba | Resultado | Implicación |
|---|---|---|
| CV agrupada por ficha | AUC 0,7258 | Evita fuga de información entre fichas |
| Bootstrap por ficha | IC 0,6694–0,7813 | Incertidumbre moderada; 56 clusters |
| Modelo individual | AUC 0,4666 | No hay señal personal |
| Modelo estructural | AUC 0,7158 | La estructura explica casi todo |
| Brier vs base | 0,1776 vs 0,1997 | Mejora modesta pero real |
| ECE | 0,0478 | Calibración aceptable en promedio |
| Pendiente de calibración | 0,721 | Probabilidades algo extremas |
| Fichas | 56 | Muestra pequeña para un modelo con 9 variables |

**Riesgos de sobreajuste:** el modelo completo tiene 9 variables y 56 clusters; la regularización L2 y la CV agrupada mitigan, pero no eliminan la inestabilidad. No se reportan coeficientes como efectos causales.

**Coeficientes interpretables (modelo completo, OR):**

| Variable | OR | IC 95% | Lectura |
|---|---:|---|---|
| Generación (por 1 orden) | 0,339 | 0,279–0,411 | A mayor orden (cohorte más reciente), menor odds de pérdida en el snapshot |
| Tamaño de ficha (por 1 DE) | 1,267 | 1,045–1,536 | Fichas más grandes, algo más de odds |
| Jornada nocturna (vs diurna) | 1,286 | 0,912–1,814 | Dirección esperada, IC cruza 1 |
| Tipo documento TI (vs CC) | 1,268 | 0,900–1,786 | Sin evidencia clara |
| Contacto completo | 0,761 | 0,667–0,868 | Asociación, no causalidad; confundido con cohorte |
| Múltiples fichas | 0,571 | 0,243–1,341 | Sin evidencia clara |
| Tasa contacto incompleto ficha (por 1 DE) | 1,025 | 0,800–1,314 | Sin evidencia clara |

Los OR de programa tienen IC muy amplios porque el programa está casi colineal con la ficha; no se interpretan individualmente.

---

## 9. Gobernanza y uso responsable

1. **Uso permitido:** priorizar revisión de fichas, asignar acompañamiento, planificar comité académico, monitorear contactabilidad.
2. **Uso prohibido:** negar cupo, sancionar, etiquetar a una persona como “desertor probable”, decidir beneficios con base en el score.
3. **Explicabilidad:** toda alerta debe mostrar el motivo (`Ficha crítica`, `Probabilidad estructural alta`, `Contacto incompleto`, `Estado condicionado/aplazado`).
4. **Revisión humana:** ninguna acción individual se automatiza; el comité valida.
5. **Privacidad:** la lista nominal es restringida; el dashboard público usa IDs hasheados y no muestra nombres, documentos, celulares ni correos.
6. **Sesgo:** el modelo puede reproducir desigualdades de programa/jornada; no se usa para comparar personas.
7. **Actualización:** reentrenar solo con datos longitudinales y validación temporal; mientras tanto, el modelo es una foto estructural.
8. **Transparencia:** reportar AUC, Brier, calibración y limitaciones junto a cualquier resultado.

---

## 10. Reproducibilidad

```powershell
$env:PYTHONIOENCODING='utf-8'
python -X utf8 scripts/04_modelo_predictivo.py
```

Salidas:
- `data/processed/DimFicha.csv` (probabilidades e IC)
- `data/processed/FactMatricula.csv` (score, alerta, prioridad)
- `data/processed/DimAprendiz.csv` (máximo score, alerta, motivo)
- `data/processed/FactProyeccionMatricula.csv` (168 filas)
- `outputs/04_modelo_predictivo.json`
- `outputs/charts/08_modelo_roc.png` … `12_coeficientes.png`

Todo el proceso es determinista con la semilla indicada, salvo pequeñas variaciones de bibliotecas.
