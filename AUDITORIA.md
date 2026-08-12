# Auditoría: reglas, alcance de exactitud y controles

Este documento explica qué garantiza la aplicación, qué no, y cómo se controla.

## Cuatro referencias que no se confunden

La aplicación evita llamar "piso" a números distintos:

- **Corte actual:** puntos que tiene hoy el último clasificado.
- **Mínimo posible:** menor puntaje con el que existe una combinación favorable (incluye ganar un desempate).
- **Mínimo que asegura:** menor puntaje comprobado con el que un equipo entra sin depender de otros resultados ni de desempates.
- **Total seguro:** total que asegura el objetivo pero puede pedir puntos de más cuando todavía no se calcula el mínimo exacto.
- **Corte estimado:** rango probable de la simulación; nunca se presenta como
  certeza.

## Niveles de certeza

| Nivel | Qué significa | De dónde sale |
| --- | --- | --- |
| **Exacto** | Puntos, PJ, techo, rango por resultados, escenarios factibles y escalera por optimización. | `lpf_scenarios` (MILP) y `lpf_pisos` en ventanas de hasta ocho fechas. |
| **Total seguro** | Total que asegura cuando el cálculo exacto completo no se activa. Puede pedir algún punto de más; nunca declara una clasificación falsa. | `lpf_exact` (`safe_guarantee_line`, `safe_average_guarantee_points`). |
| **Estimado** | Monte Carlo, dificultad, corte probable, impacto de otras canchas. | Simulación con semilla fija, siempre rotulada. |

## Reglas de datos

1. Resultados explícitos para identificar partidos jugados.
2. Foto fija del Apertura más las zonas vigentes para reconstruir la Tabla Anual.
3. Tabla Anual directa sólo si pasa los controles (queda como control, no como
   fuente viva).
4. Inferencia por PJ únicamente como respaldo, siempre rotulada.

Los partidos tienen identidad propia: un encuentro postergado no se considera
jugado sólo porque el equipo haya disputado una fecha posterior.

## Bloqueos por dominio

El semáforo de calidad (`ok` / `warning` / `blocked`) se evalúa por dominio:
playoffs, copas, promedios y descenso. Un problema exclusivo de un dominio no
invalida los cálculos de los demás.


## Auditoría probabilística · 3.8.29

La estimación tiene **un solo modelo activo** para Previa, chances, escenarios y “Realidad y proyección”:

- fuerza: `lpf_form.estimate_team_strength` (Apertura como antecedente, Clausura vigente y forma reciente cuando hay resultados);
- empate fijo: **26%**;
- factor de localía: **1,22** sobre la fuerza del local;
- kernel único: `lpf_simulation.match_outcome_probabilities`;
- el fixture real se respeta, incluidos los interzonales. Si un rival no está disponible en la fuerza, recién ahí se usa 1,0 como respaldo.

Antes de 3.8.29, `lpf_competitive_context` usaba 27% de empate, factor local 1,08 y otra regularización, y la simulación de una zona podía convertir un interzonal en un partido contra “rival promedio”. Esas dos divergencias quedaron eliminadas.

### Control con la Fecha 4 real

Se congeló `tests/fixtures/lpf_2026_fecha4_probability_audit.json` con la foto del **11/08/2026 20:28 ART**, cuando había 59 partidos terminados y Talleres–Lanús todavía estaba pendiente. Fuentes de control: FutbolArgentino.com (tabla del Clausura), TyC Sports (Fecha 4) y Nuevo Mundo (cierre de la Fecha 4).

En esos 59 partidos hubo 33 triunfos locales, 9 empates y 17 triunfos visitantes. Un backtest secuencial —sin mirar el resultado futuro para construir la fuerza— dio:

| Modelo | Log-loss medio | Brier multiclase |
| --- | ---: | ---: |
| Canónico (26% / 1,22 + `lpf_form`) | **1,037** | **0,624** |
| Camino editorial anterior (27% / 1,08 + fuerza paralela) | 1,057 | 0,640 |

**Decisión:** no se ajustan 26% ni 1,22 a partir de sólo cuatro fechas. La tasa observada de empates de esta muestra es mucho menor, pero 59 partidos son insuficientes para reemplazar una parametrización estable sin un backtest histórico más largo. El cambio 3.8.29 corrige **consistencia interna**, no entrena un modelo nuevo.

### Puesto específico y tamaño de muestra

La distribución “si termina 8º” es condicional. La app informa cuántas de las 6.000 corridas terminaron exactamente en ese puesto y marca la lectura como **muestra condicionada chica** cuando hay menos de 100 casos. Una mediana con 80 casos no debe leerse con la misma estabilidad que una basada en 500. Los extremos matemáticos siguen separados y sin probabilidad.

## Controles automatizados

Las pruebas viven en `tests/` y cubren, entre otras cosas:

- **Puntos por objetivo** (`test_lpf_pisos.py`): en ligas chicas se enumeran todos
  los resultados posibles y se verifica que el mínimo posible es realmente
  alcanzable y que la garantía es el menor puntaje que asegura el objetivo en
  todos los desenlaces (con desempate adverso). También chequea invariantes
  (`puntos_hoy ≤ mínimo ≤ techo`, `garantía ≥ mínimo`) y que el total seguro nunca sea menor que el mínimo que asegura real.
- Comparación del optimizador contra enumeración exhaustiva en casos pequeños.
- Postergados, Tabla Anual derivada, escalera exacta y ventanas dobles.

Ejecución:

```bash
python -m pytest -q
```
