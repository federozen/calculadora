# Contrato de cálculos · versión 1

Este documento describe la frontera de aplicación creada para que los mismos motores
puedan ser consumidos desde Streamlit y, más adelante, desde una API HTTP. **No hay
un servidor HTTP en esta versión**: `lpf_services.py` recibe y devuelve estructuras
compatibles con JSON y delega la matemática en los motores existentes.

## Principios

- `contract_version` versiona la forma del payload; `calculation_version` identifica
  la versión del motor que produjo la respuesta.
- Las funciones de servicio no importan Streamlit, `requests` ni proveedores.
- ESPN, FutbolArgentino.com y un futuro Opta quedan antes de esta frontera: sus datos
  deben normalizarse al modelo LPF antes de pedir cálculos.
- Los servicios no reimplementan fórmulas. Sólo validan/traducen JSON y llaman a
  `lpf_standings`, `lpf_scenarios` o `lpf_pisos`.
- Los errores de entrada usan `ContractError(code, message, field)` para que una
  futura API pueda mapearlos a HTTP sin depender de un framework hoy.

## Sobre de respuesta

Todas las operaciones devuelven:

```json
{
  "contract_version": "1",
  "calculation_version": "3.8.6",
  "calculation": "standings",
  "result": {}
}
```

No se agrega una hora de generación al sobre para que el resultado de una misma
entrada siga siendo determinístico.

## 1. Tabla y posiciones

Función: `calculate_standings(payload)`.

Entrada mínima:

```json
{
  "teams": ["A", "B"],
  "matches": [
    {"home": "A", "away": "B", "home_goals": 1, "away_goals": 0}
  ]
}
```

Opcionales: `tiebreakers`, `fair_play`, `ranking`. Si `tiebreakers` no se informa se
usan los criterios LPF del motor; una lista vacía se respeta como lista vacía.

La salida contiene `positions`, `table` y los `tiebreakers` aplicados. Las filas de
`table` usan nombres estables de campo: `position`, `team`, `played`, `points`,
`goals_for`, `goals_against`, `goal_difference`.

## 2. Escalera exacta de puntos

Función: `calculate_point_ladder(payload)`.

```json
{
  "base": {"A": {"pts": 10}, "B": {"pts": 9}},
  "matches": [{"home": "A", "away": "B"}],
  "team": "A",
  "cutoff": 1
}
```

Devuelve exactamente la salida de `lpf_scenarios.point_ladder`, convertida a JSON.
La distinción entre mínimo posible, clasificación condicionada y garantía matemática
sigue siendo responsabilidad del motor, no del contrato.

## 3. Rango de puesto en una ventana

Función: `calculate_rank_window(payload)`.

Los resultados fijados se expresan como lista porque JSON no permite tuplas como
claves de objeto:

```json
{
  "base": {"A": 10, "B": 9, "C": 8},
  "matches": [{"home": "A", "away": "B"}, {"home": "A", "away": "C"}],
  "team": "A",
  "fixed": [{"home": "A", "away": "B", "result": "E"}]
}
```

`result` usa `L` (gana local), `E` (empate) o `V` (gana visitante), igual que el
motor interno.

## 4. Piso por objetivo de corte

Función: `calculate_objective_floor(payload)`.

```json
{
  "base": {"A": 10, "B": 9, "C": 8},
  "remaining": {"A": 2, "B": 2, "C": 2},
  "matches": [{"home": "A", "away": "B"}],
  "team": "A",
  "cutoff": 2,
  "objective_key": "playoffs",
  "objective_name": "los playoffs"
}
```

Además de los campos de `PisoObjetivo`, la salida publica `floor` (mejor piso
existente: exacto o conservador) y `reading` como lectura breve ya existente en el
dominio.

## Futuro adaptador HTTP

Cuando exista una API real, su trabajo debería ser delgado:

1. autenticar/limitar requests si corresponde;
2. parsear JSON;
3. llamar a una función de `lpf_services`;
4. mapear `ContractError` a un error HTTP;
5. devolver el sobre sin recalcular nada.

Un proveedor como Opta pertenece a otra entrada del sistema:

`Opta -> adaptador Opta -> lpf_loading/lpf_state -> lpf_services/motores -> HTTP o Streamlit`

No debe importarse un SDK de Opta dentro de los motores ni de `lpf_services.py`.
