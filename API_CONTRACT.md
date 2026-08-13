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

## Superficie pública mínima · service v1

Desde 3.8.47 la frontera recomendada para cualquier consumidor externo es
`lpf_services.calculate(operation, payload)`. `PUBLIC_SERVICE_VERSION = "1"` congela
los nombres de las operaciones públicas; los helpers históricos de este archivo siguen
disponibles para compatibilidad, pero no forman parte de esa superficie estable.

Operaciones públicas:

1. `standings`
2. `preview`
3. `objective_points`
4. `objective_chances`
5. `definition`
6. `relegation`
7. `competition_batch`

`service_capabilities()` es auxiliar y permite descubrir `public_service_version`,
`public_operations`, schema de snapshot y capacidades batch.

El formato preferido de entrada es siempre el **snapshot canónico**. Los modos legacy
que reciben `base`, `remaining` o `cutoff` se conservan para no romper integraciones
existentes, pero una web externa u Opta no debería construir esos parámetros por su
cuenta.

Ejemplo:

```python
from lpf_services import calculate

response = calculate("definition", {
    "snapshot": snapshot,
    "team": "Boca Juniors",
    "objective": "playoffs",
    "zone": "A",
    "round": 14,
})
```

La división semántica es deliberada: `definition` y `objective_points` son salidas
matemáticas exactas/garantías cuando el motor puede probarlas; `objective_chances` es
siempre una **estimación Monte Carlo** y usa 6.000 corridas por defecto. No se mezclan
porcentajes dentro de los condicionales exactos.

### `standings`

Con snapshot acepta `scope=zone|annual` (+ `zone` cuando corresponde) o directamente
`objective=playoffs|libertadores|sudamericana`. Devuelve una tabla con campos estables
en inglés (`position`, `team`, `played`, `points`, `goals_for`, `goals_against`,
`goal_difference`). Para objetivos de Copas usa la Tabla Anual reducida del snapshot.

### `preview`

Entrada preferida: `snapshot`, `team`, `objective`, `scope` y `round` opcional. Los
alcances estables son `next_team_match`, `next_team_day`, `official_round`,
`postponed_only` y `extended_window`. Devuelve `markdown`, `reusable_line` y
`scenarios` como lista de objetos JSON; ningún `DataFrame` cruza la frontera.

### `objective_points`

Entrada preferida: `snapshot`, `team`, `objective` (+ `zone` para Playoffs). Resuelve
automáticamente la base y el corte efectivo. Si la plaza ya está obtenida por una vía
directa, lo informa como objetivo resuelto en lugar de inventar un piso de puntos.

### `objective_chances`

Entrada: `snapshot`, `team`, `objective` (+ `zone` para Playoffs), con `simulations`
y `seed` opcionales. `simulations` vale 6.000 por defecto y debe quedar entre 1.000 y
100.000. La salida publica `estimated=true`, `qualification_probability` (0–1),
`qualification_percentage` y el bloque de proyección auditable. Una vía directa ya
resuelta devuelve 100% sin ejecutar Monte Carlo (`estimated=false`, `simulations=0`).

### `definition`

Es la operación pública de **condicionales exactos**: G/E/P, matriz general, rival
clave, reloj y pruebas de “¿Por qué?”. No asigna probabilidades. Ver la sección 8 para
el detalle del paquete.

### `relegation`

Entrada preferida: `snapshot` y `team` opcional. Devuelve la foto actual de descenso
respetando desempates y reasignación promedio→Anual. Si se informa equipo, agrega su
piso/garantía de permanencia. Cuando faltan antecedentes de promedios la respuesta
marca `complete=false` y no presenta la foto combinada como completa.

### `competition_batch`

Permanece como operación de lote stateless sobre un mismo snapshot. Está orientada a
consultas exactas/reutilizables y conserva sus `type` históricos; no obliga a una capa
HTTP a mantener estado de servidor.

## Sobre de respuesta

Todas las operaciones devuelven:

```json
{
  "contract_version": "1",
  "calculation_version": "3.8.48",
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
`previous_averages`, `fixture`, `rules`, `format`, `qualification_inputs`, `qualification` y `audit`. `previous_averages` contiene **sólo temporadas anteriores** (`points/played`); los totales de promedio se reconstruyen con la Tabla Anual vigente dentro del motor. `qualification` conserva el universo elegible y el corte efectivo de Playoffs/Libertadores/Sudamericana, de modo que otro cliente no tenga que reconstruir la Tabla Anual reducida.

Entrada conceptual:

```json
{
  "zones": {"A": {"Equipo": {"pts": 10, "pj": 5, "dg": 3, "gf": 8, "ga": 5}}},
  "played": [{"home": "A", "away": "B", "home_goals": 1, "away_goals": 0}],
  "annual": {},
  "opening": {},
  "previous_averages": {"Equipo": {"points": 70, "played": 55}},
  "fixture": [{"f": 7, "l": "A", "v": "B", "tipo": "zone", "zona": "A"}],
  "rules": {
    "annual_relegations": 1,
    "average_relegations": 1,
    "opening_rounds": 16,
    "playoff_cutoff": 8,
    "sudamericana_slots": 6
  },
  "qualification": {
    "champions": {"apertura": "", "clausura": "", "copa_argentina": ""},
    "international_champions": {"libertadores": "", "sudamericana": ""},
    "copa_argentina_replacement": ""
  }
}
```

La foto vigente incluye `snapshot_schema_version = "2"`. Schema 1 sigue admitido para
consultas legacy, pero no contiene `qualification` y por eso no puede resolver objetivos
por nombre. La auditoría puede devolver `blocked`; eso describe la calidad de la foto.
El servicio no inventa datos para volverla válida.

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
    {"id": "playoffs", "type": "objective_status", "objective": "playoffs", "zone": "A", "team": "River Plate"},
    {"id": "lib", "type": "objective_points", "objective": "libertadores", "team": "River Plate"},
    {"id": "sud", "type": "point_ladder", "objective": "sudamericana", "team": "River Plate"},
    {"id": "rango", "type": "rank_window", "scope": "annual", "team": "River Plate"},
    {"id": "descenso", "type": "descent_points", "team": "River Plate"}
  ]
}
```

Tipos soportados: `objective_points`, `objective_status`, `point_ladder`, `rank_window`,
`definition` y `descent_points`. `objective_points`, `point_ladder` y `rank_window` conservan el
modo legacy `scope=zone|annual` con `cutoff` cuando corresponde. Con un snapshot schema
2 también pueden recibir `objective=playoffs|libertadores|sudamericana`: el servicio
toma automáticamente la base y el corte del snapshot (para Playoffs sólo se agrega
`zone`). `objective_status` exige ese modo nuevo y, si el club ya tiene Libertadores
por otra vía, devuelve el objetivo como resuelto con su motivo. Descenso usa siempre
la Anual, pendientes y antecedentes de promedios. La respuesta conserva el orden, el
`id`, `snapshot_schema_version` y `query_count`.

## 7. Capacidades del servicio

Función: `service_capabilities()`. No recibe datos de competencia y puede exponerse
como un endpoint de metadatos en una futura API. Informa:

- `snapshot_schema_version` vigente y versiones de snapshot aceptadas;
- objetivos resolubles desde el snapshot (`playoffs`, `libertadores`, `sudamericana`);
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

## 8. Paquete exacto de definición

Función: `calculate_definition(payload)`. Expone el mismo paquete matemático que alimenta
**Últimas fechas** sin importar Streamlit. No asigna probabilidades ni usa Monte Carlo.

Entrada conceptual:

```json
{
  "base": {"A": {"pts": 10}, "B": {"pts": 9}, "C": {"pts": 8}},
  "remaining": {"A": 2, "B": 2, "C": 2},
  "round_matches": [{"home": "A", "away": "C"}],
  "pending_matches": [{"home": "A", "away": "C"}, {"home": "A", "away": "B"}],
  "fixture": [{"f": 13, "l": "A", "v": "C"}, {"f": 14, "l": "A", "v": "B"}],
  "team": "A",
  "cutoff": 2,
  "selected_teams": ["A", "B"],
  "key_team": "B"
}
```

La salida incluye `fight_zone`, `matrix`, `report`, `key_rival`, `guarantee`,
`guarantee_round_label` y `clock`. Para Playoffs, `base` es la zona correspondiente.
El modo explícito `base + cutoff` se conserva por compatibilidad. Con un snapshot schema 2,
la misma operación puede pedirse sin preparar esa base:

```json
{
  "snapshot": {"...": "resultado de competition_snapshot"},
  "team": "River Plate",
  "objective": "libertadores",
  "round": 13,
  "selected_teams": ["River Plate", "Boca Juniors"],
  "key_team": "Boca Juniors"
}
```

Para Playoffs se agrega `zone`; para Copas el servicio toma del snapshot la Tabla Anual
reducida, el corte efectivo y las vías directas. `round` es el nombre estable del campo y
`fecha` se acepta como alias. Si ambos se omiten se usa la jornada operativa vigente.
`competition_batch` acepta el mismo cálculo con `type: "definition"`. Si el equipo ya
tiene el objetivo resuelto por una vía directa, la respuesta lo marca como `resolved` y
no enumera ramas innecesarias.

La operación es aditiva y no cambia la forma de las operaciones existentes, por lo que
`CONTRACT_VERSION` permanece en `1`.
