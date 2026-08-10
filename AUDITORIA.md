# Auditoría: reglas, alcance de exactitud y controles

Este documento explica qué garantiza la aplicación, qué no, y cómo se controla.

## Cuatro referencias que no se confunden

La aplicación evita llamar "piso" a números distintos:

- **Corte actual:** puntos que tiene hoy el último clasificado.
- **Mínimo todavía posible:** menor puntaje con el que existe una combinación
  favorable (incluye ganar un desempate).
- **Garantía matemática:** puntaje con el que un equipo entra sin depender de otros
  resultados ni de desempates.
- **Corte estimado:** rango probable de la simulación; nunca se presenta como
  certeza.

## Niveles de certeza

| Nivel | Qué significa | De dónde sale |
| --- | --- | --- |
| **Exacto** | Puntos, PJ, techo, rango por resultados, escenarios factibles y escalera por optimización. | `lpf_scenarios` (MILP) y `lpf_pisos` en ventanas de hasta ocho fechas. |
| **Garantía conservadora** | Línea segura cuando el cálculo exacto completo no se activa. Puede pedir algún punto de más; nunca declara una garantía falsa. | `lpf_exact` (`safe_guarantee_line`, `safe_average_guarantee_points`). |
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

## Controles automatizados

Las pruebas viven en `tests/` y cubren, entre otras cosas:

- **Piso por objetivo** (`test_lpf_pisos.py`): en ligas chicas se enumeran todos
  los resultados posibles y se verifica que el mínimo posible es realmente
  alcanzable y que la garantía es el menor puntaje que asegura el objetivo en
  todos los desenlaces (con desempate adverso). También chequea invariantes
  (`puntos_hoy ≤ mínimo ≤ techo`, `garantía ≥ mínimo`) y que la cota conservadora
  nunca sea menor que la garantía exacta real.
- Comparación del optimizador contra enumeración exhaustiva en casos pequeños.
- Postergados, Tabla Anual derivada, escalera exacta y ventanas dobles.

Ejecución:

```bash
python -m pytest -q
```
