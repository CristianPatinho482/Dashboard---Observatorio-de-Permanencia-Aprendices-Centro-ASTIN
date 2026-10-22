# Catálogo DAX

Este catálogo define las medidas del modelo semántico `DashboardAprendicesSENA`. Todas las medidas están en la tabla `_Medidas` y se organizan en carpetas de visualización. Los nombres y el código coinciden con el archivo TMDL del PBIP.

> **Convención:** las medidas se referencian sin tabla (`[Matrículas]`). Las columnas siempre llevan tabla (`FactMatricula[EsPerdida]`). Los porcentajes se guardan como fracción (0,2758) y se formatean como `0.0%`.

---

## 1. Volumen y población

### `Matrículas`
```DAX
Matrículas =
COUNTROWS ( FactMatricula )
```
Formato `#,##0`. Cuenta matrículas, no personas.

### `Aprendices únicos`
```DAX
Aprendices únicos =
DISTINCTCOUNT ( DimAprendiz[AprendizID] )
```
Formato `#,##0`. Un aprendiz con dos fichas cuenta una vez.

### `Fichas`
```DAX
Fichas =
DISTINCTCOUNT ( DimFicha[FichaID] )
```
Formato `#,##0`.

### `Programas`
```DAX
Programas =
DISTINCTCOUNT ( DimPrograma[ProgramaID] )
```
Formato `#,##0`.

### `Pérdidas`
```DAX
Pérdidas =
CALCULATE (
    [Matrículas],
    FactMatricula[EsPerdida] = 1
)
```
Formato `#,##0`. Incluye cancelados y retiros voluntarios.

### `Cancelados`
```DAX
Cancelados =
CALCULATE (
    [Matrículas],
    FactMatricula[EsCancelado] = 1
)
```

### `Retiros voluntarios`
```DAX
Retiros voluntarios =
CALCULATE (
    [Matrículas],
    FactMatricula[EsRetirado] = 1
)
```

### `Activos`
```DAX
Activos =
CALCULATE (
    [Matrículas],
    FactMatricula[EsActivo] = 1
)
```

### `Vinculados`
```DAX
Vinculados =
CALCULATE (
    [Matrículas],
    FactMatricula[EsVinculado] = 1
)
```

### `Trasladados`
```DAX
Trasladados =
CALCULATE (
    [Matrículas],
    FactMatricula[EsTrasladado] = 1
)
```

---

## 2. Tasas

### `Tasa de pérdida`
```DAX
Tasa de pérdida =
DIVIDE ( [Pérdidas], [Matrículas] )
```
Formato `0.0%`.

### `Tasa de cancelación`
```DAX
Tasa de cancelación =
DIVIDE ( [Cancelados], [Matrículas] )
```

### `Tasa de retiro`
```DAX
Tasa de retiro =
DIVIDE ( [Retiros voluntarios], [Matrículas] )
```

### `Tasa de activos`
```DAX
Tasa de activos =
DIVIDE ( [Activos], [Matrículas] )
```

### `Tasa de vinculación`
```DAX
Tasa de vinculación =
DIVIDE ( [Vinculados], [Matrículas] )
```

### `Tasa de pérdida global`
```DAX
Tasa de pérdida global =
CALCULATE (
    [Tasa de pérdida],
    REMOVEFILTERS ()
)
```
Formato `0.0%`. Sirve de referencia para brechas; no cambia con filtros de página.

### `Brecha vs global (pp)`
```DAX
Brecha vs global (pp) =
( [Tasa de pérdida] - [Tasa de pérdida global] ) * 100
```
Formato `+0.0;-0.0;0.0`.

### `Contribución a la pérdida`
```DAX
Contribución a la pérdida =
DIVIDE (
    [Pérdidas],
    CALCULATE ( [Pérdidas], REMOVEFILTERS () )
)
```
Formato `0.0%`. Responde “¿qué porcentaje de todas las pérdidas aporta este grupo?”.

---

## 3. Contacto y calidad

### `Contacto incompleto`
```DAX
Contacto incompleto =
CALCULATE (
    [Matrículas],
    FactMatricula[ContactoCompleto] = 0
)
```

### `% contacto incompleto`
```DAX
% contacto incompleto =
DIVIDE ( [Contacto incompleto], [Matrículas] )
```
Formato `0.0%`.

### `Aprendices con celular válido`
```DAX
Aprendices con celular válido =
CALCULATE (
    DISTINCTCOUNT ( DimAprendiz[AprendizID] ),
    DimAprendiz[CelularValido] = 1
)
```

> **Advertencia:** el contacto incompleto es una bandera operativa, no un factor de riesgo. Se concentra en cohortes nuevas con 0% de pérdida; su asociación ajustada es espuria.

---

## 4. Riesgo de ficha

### `Fichas críticas`
```DAX
Fichas críticas =
CALCULATE (
    DISTINCTCOUNT ( DimFicha[FichaID] ),
    DimFicha[NivelRiesgo] = "Crítico"
)
```

### `Fichas altas o críticas`
```DAX
Fichas altas o críticas =
CALCULATE (
    DISTINCTCOUNT ( DimFicha[FichaID] ),
    DimFicha[NivelRiesgo] IN { "Alto", "Crítico" }
)
```

### `Matrículas en fichas críticas`
```DAX
Matrículas en fichas críticas =
CALCULATE (
    [Matrículas],
    DimFicha[NivelRiesgo] = "Crítico"
)
```

### `Pérdidas en fichas críticas`
```DAX
Pérdidas en fichas críticas =
CALCULATE (
    [Pérdidas],
    DimFicha[NivelRiesgo] = "Crítico"
)
```

### `Tasa de pérdida en fichas críticas`
```DAX
Tasa de pérdida en fichas críticas =
DIVIDE ( [Pérdidas en fichas críticas], [Matrículas en fichas críticas] )
```

### `% de pérdidas en fichas críticas`
```DAX
% de pérdidas en fichas críticas =
DIVIDE ( [Pérdidas en fichas críticas], [Pérdidas] )
```

### `Probabilidad media de pérdida (ficha)`
```DAX
Probabilidad media de pérdida (ficha) =
AVERAGE ( DimFicha[ProbDesercionFicha] )
```
Formato `0.0%`. Es la media posterior beta-binomial de las fichas en contexto.

### `Fichas con probabilidad > 30%`
```DAX
Fichas con probabilidad > 30% =
COUNTROWS (
    FILTER (
        VALUES ( DimFicha[FichaID] ),
        CALCULATE ( AVERAGE ( DimFicha[ProbDesercionFicha] ) ) > 0.30
    )
)
```

### `Índice de riesgo promedio`
```DAX
Índice de riesgo promedio =
AVERAGE ( DimFicha[IndiceRiesgo] )
```
Formato `0.0`.

---

## 5. Alertas individuales

### `Alertas altas`
```DAX
Alertas altas =
CALCULATE (
    [Matrículas],
    FactMatricula[NivelAlertaAprendiz] = "Alto"
)
```

### `Aprendices con alerta alta`
```DAX
Aprendices con alerta alta =
CALCULATE (
    DISTINCTCOUNT ( DimAprendiz[AprendizID] ),
    FactMatricula[NivelAlertaAprendiz] = "Alto"
)
```

### `Prioridad inmediata`
```DAX
Prioridad inmediata =
CALCULATE (
    [Matrículas],
    FactMatricula[PrioridadAtencion] = "Inmediata"
)
```

### `Aprendices en prioridad inmediata`
```DAX
Aprendices en prioridad inmediata =
CALCULATE (
    DISTINCTCOUNT ( DimAprendiz[AprendizID] ),
    FactMatricula[PrioridadAtencion] = "Inmediata"
)
```

### `Cobertura de alertas`
```DAX
Cobertura de alertas =
DIVIDE (
    [Aprendices con alerta alta],
    [Aprendices únicos]
)
```
Formato `0.0%`. Mide cuántos aprendices quedan en la banda alta; no es una tasa de éxito.

---

## 6. Modelo predictivo (constantes documentadas)

Estas medidas son **constantes de documentación** tomadas de `outputs/04_modelo_predictivo.json`. No se recalculan dentro del modelo; sirven para mostrar la ficha técnica en el reporte.

### `AUC del modelo`
```DAX
AUC del modelo = 0.7258
```
Formato `0.000`. AUC out-of-fold con validación agrupada por ficha (5 folds).

### `Brier del modelo`
```DAX
Brier del modelo = 0.1776
```
Formato `0.000`.

### `ECE del modelo`
```DAX
ECE del modelo = 0.0478
```
Formato `0.000`.

### `AUC individual`
```DAX
AUC individual = 0.4666
```
Formato `0.000`. Modelo solo con variables individuales; ~azar.

### `AUC estructural`
```DAX
AUC estructural = 0.7158
```
Formato `0.000`. Modelo sin variables individuales.

---

## 7. Proyección de permanencia

### `Población vinculada (Base)`
```DAX
Población vinculada (Base) =
CALCULATE (
    SUM ( FactProyeccionMatricula[PoblacionVinculada] ),
    FactProyeccionMatricula[Escenario] = "Base"
)
```

### `Pérdida adicional esperada (Base)`
```DAX
Pérdida adicional esperada (Base) =
CALCULATE (
    SUM ( FactProyeccionMatricula[PerdidaAdicionalEsperada] ),
    FactProyeccionMatricula[Escenario] = "Base"
)
```
Formato `#,##0.0`.

### `Población proyectada (Base)`
```DAX
Población proyectada (Base) =
CALCULATE (
    SUM ( FactProyeccionMatricula[PoblacionProyectada] ),
    FactProyeccionMatricula[Escenario] = "Base"
)
```

### `Tasa proyectada (Base)`
```DAX
Tasa proyectada (Base) =
DIVIDE (
    [Pérdida adicional esperada (Base)],
    [Población vinculada (Base)]
)
```
Formato `0.0%`.

### `Población proyectada (escenario)`
```DAX
Población proyectada (escenario) =
SUM ( FactProyeccionMatricula[PoblacionProyectada] )
```
Se usa en el gráfico por escenario, donde `FactProyeccionMatricula[Escenario]` está en el eje.

### `Tasa proyectada (escenario)`
```DAX
Tasa proyectada (escenario) =
DIVIDE (
    SUM ( FactProyeccionMatricula[PerdidaAdicionalEsperada] ),
    SUM ( FactProyeccionMatricula[PoblacionVinculada] )
)
```

---

## 8. Medidas auxiliares para tablas

### `Ranking de riesgo`
```DAX
Ranking de riesgo =
MIN ( DimFicha[RankingRiesgo] )
```
En una tabla por ficha devuelve el ranking; en un total no tiene sentido.

### `Probabilidad de pérdida`
```DAX
Probabilidad de pérdida =
AVERAGE ( DimFicha[ProbDesercionFicha] )
```

### `Límite inferior IC`
```DAX
Límite inferior IC =
AVERAGE ( DimFicha[ProbDesercionICInf] )
```

### `Límite superior IC`
```DAX
Límite superior IC =
AVERAGE ( DimFicha[ProbDesercionICSup] )
```

### `Tasa de pérdida ajustada`
```DAX
Tasa de pérdida ajustada =
AVERAGE ( DimFicha[TasaPerdidaAjustada] )
```

---

## 9. Formato condicional

| Medida / columna | Regla | Color |
|---|---|---|
| `NivelRiesgo` | Texto exacto | Bajo `#39A900`, Medio `#FDC300`, Alto `#EF6C00`, Crítico `#C62828` |
| `PrioridadAtencion` | Texto exacto | Inmediata `#C62828`, Seguimiento `#FDC300`, Rutinaria `#607D8B` |
| `Tasa de pérdida` | > 40% | Rojo; 30–40% naranja; < 30% verde |
| `Brecha vs global (pp)` | > 0 | Rojo; < 0 verde |
| `Probabilidad de pérdida` | > 0.50 | Rojo; 0.30–0.50 naranja; < 0.30 verde |

En el PBIP se implementan con formato condicional por reglas sobre las columnas de texto y escalas de color sobre las medidas. En el HTML se implementan con clases CSS y umbrales equivalentes.

---

## 10. Buenas prácticas

1. **No usar suma de tasas**: las tasas se recalculan con `DIVIDE` en cada contexto; nunca se promedian tasas de fichas.
2. **No ocultar el denominador**: toda tabla de tasas debe mostrar `n` o `Matrículas`.
3. **No interpretar el índice como probabilidad**: el índice es un percentil; la probabilidad es `ProbDesercionFicha`.
4. **No comparar programas sin IC**: con 1 ficha y n=14, el IC es muy amplio.
5. **No usar el score individual para sancionar**: el AUC individual es 0,467; el modelo prioriza fichas, no personas.
6. **No usar la proyección como presupuesto**: es un escenario de permanencia, no una proyección calendario.
