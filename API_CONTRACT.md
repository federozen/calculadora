# Contrato de cálculos · versión 1

Este documento describe la frontera de aplicación creada para que los mismos motores
puedan ser consumidos desde Streamlit y, más adelante, desde una API HTTP. **No hay
un servidor HTTP en esta versión**: `lpf_services.py` recibe y devuelve estructuras
compatibles con JSON y delega la matemática en los motores existentes.

## Principios

- `contract_version` versiona la forma de los servicios; `calculation_version` identifica
  la versión del motor que produjo la respuesta; `snapshot_schema_version` versiona
  específicamente la forma de la foto canónica de competencia.
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
  "calculation_version": "3.8.41",
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
La distinción entre mínimo posible, clasificación condicionada y mínimo que asegura
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

## 4. Puntos por objetivo de corte

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

Además de los campos internos históricos de `PisoObjetivo`, la salida publica los nombres editoriales `minimum_possible`, `safe_total` y `minimum_guarantee`. `safe_total` es el valor que sabemos que asegura el objetivo; `minimum_guarantee` sólo aparece cuando el motor comprobó que ése es el menor total que asegura. Por compatibilidad con el contrato v1 se conservan `exact_guarantee`, `conservative_reference`, `safe_value` y `floor`. `reading` devuelve la lectura editorial con los mismos términos que Streamlit.


## 5. Foto canónica de competencia

Función: `prepare_competition_snapshot(payload)`. Recibe datos ya normalizados y usa
`lpf_state.build_lpf_state`; no crea una segunda verdad paralela. La salida reúne en
un único objeto `zones`, `annual`, `opening`, `played`, `pending`, `remaining`,
`previous_averages`, `fixture`, `rules` y `audit`. `previous_averages` contiene **sólo temporadas anteriores** (`points/played`); los totales de promedio se reconstruyen con la Tabla Anual vigente dentro del motor.

Entrada conceptual:

```json
{
  "zones": {"A": {"Equipo": {"pts": 10, "pj": 5, "dg": 3, "gf": 8, "ga": 5}}},
  "played": [{"home": "A", "away": "B", "home_goals": 1, "away_goals": 0}],
  "annual": {},
  "opening": {},
  "previous_averages": {"Equipo": {"points": 70, "played": 55}},
  "fixture": [{"f": 7, "l": "A", "v": "B", "tipo": "zone", "zona": "A"}],
  "rules": {"annual_relegations": 1, "average_relegations": 1}
}
```

La foto incluye `snapshot_schema_version = "1"`. La auditoría puede devolver `blocked`;
eso describe la calidad de la foto. El servicio no inventa datos para volverla válida.

`validate_competition_snapshot({"snapshot": ...})` permite validar la foto antes de
calcular. En una foto canónica comprueba que la nómina coincida con las zonas, que
`remaining` tenga enteros no negativos y que su conteo coincida exactamente con los
partidos de `pending`. Un schema de snapshot desconocido se rechaza de forma
explícita antes de entrar a los motores.

## 6. Varias consultas sobre una misma foto

Función: `calculate_competition_batch(payload)`. Es stateless: el cliente manda la
foto y una lista `queries`. Puede mandar tanto el objeto `result` como el sobre
completo devuelto por `prepare_competition_snapshot`. No hay IDs de servidor ni
persistencia en esta versión.

```json
{
  "snapshot": {"...": "resultado de competition_snapshot"},
  "queries": [
    {"id": "playoffs", "type": "objective_points", "scope": "zone", "zone": "A", "team": "River Plate", "cutoff": 8},
    {"id": "escalera", "type": "point_ladder", "scope": "zone", "zone": "A", "team": "River Plate", "cutoff": 8},
    {"id": "rango", "type": "rank_window", "scope": "annual", "team": "River Plate"},
    {"id": "descenso", "type": "descent_points", "team": "River Plate"}
  ]
}
```

Tipos soportados: `objective_points`, `point_ladder`, `rank_window` y
`descent_points`. Los tres primeros pueden seleccionar `scope=zone` (con `zone`) o
`scope=annual`; descenso usa siempre la Anual, los pendientes y los antecedentes de
promedios de la foto. La respuesta conserva el orden de las consultas y devuelve su `id`; además informa
`snapshot_schema_version` y `query_count`.

## 7. Capacidades del servicio

Función: `service_capabilities()`. No recibe datos de competencia y puede exponerse
como un endpoint de metadatos en una futura API. Informa:

- `snapshot_schema_version`;
- operaciones disponibles;
- tipos de consulta aceptados por `competition_batch`;
- cantidad de partidos restantes a partir de la cual se activa la ventana exacta.

Esto permite que un cliente o un futuro adaptador Opta compruebe compatibilidad sin
importar Streamlit ni inspeccionar código interno.

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
