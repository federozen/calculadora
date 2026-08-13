# Handoff al equipo de desarrollo · Calculadora LPF 3.8.51

## Qué se entrega

Esta versión deja separados los cuatro contratos que el equipo debe tratar como fronteras distintas:

| Frontera | Versión | Responsabilidad |
| --- | ---: | --- |
| Public Service | `v1` | 7 operaciones JSON-safe de cálculo. |
| DataProvider | `v2` | Normalizar cualquier fuente a `ProviderData`. |
| Snapshot | `schema 3` | Foto canónica de competencia + objetivos + trazabilidad. |
| Runtime interno | `21` | Evitar despliegues con módulos críticos mezclados. |

No hay FastAPI ni SDK Opta en esta entrega. Esa ausencia es deliberada.

## Arquitectura que debe preservarse

```text
fuente externa
   ↓
transporte / SDK / archivos
   ↓
adaptador del proveedor
   ↓
DataProvider.load() -> ProviderData
   ↓
prepare_competition_snapshot()
   ↓
snapshot schema 3
   ↓
lpf_services.calculate()
   ↓
Streamlit / futura API HTTP / otro consumidor
```

**Regla principal:** ningún proveedor puede contener lógica de Playoffs, Copas, descenso, probabilidades, garantías o “¿Por qué?”. Sólo traduce datos.

## Contrato público de cálculo

`lpf_services.PUBLIC_SERVICE_VERSION == "1"`.

Operaciones estables:

1. `standings`
2. `preview`
3. `objective_points`
4. `objective_chances`
5. `definition`
6. `relegation`
7. `competition_batch`

Entrada recomendada: snapshot canónico. Salida: estructuras serializables a JSON. Los helpers legacy siguen presentes pero no deben usarse para una integración nueva.

`definition` es exacto y no publica probabilidades. `objective_chances` es estimado/Monte Carlo y usa 6.000 simulaciones por defecto.

## DataProvider v2

Interfaz mínima:

```python
class DataProvider(Protocol):
    provider_name: str
    def load(self) -> ProviderData: ...
```

`ProviderData` contiene:

- `zones`
- `played`
- `annual`
- `opening`
- `previous_averages`
- `fixture`
- `qualification`
- `rules`
- `provenance`

`provenance` admite:

```json
{
  "source_name": "Opta",
  "source_updated_at": "2026-08-13T20:00:00+00:00",
  "data_as_of": "2026-08-13T20:00:00+00:00",
  "sources": ["Opta competition feed", "Opta fixtures feed"],
  "warnings": []
}
```

Los timestamps deben ser ISO-8601. Si Opta no informa uno, dejar `null`: no inferirlo por PJ, fecha oficial ni hora de ejecución.

Implementaciones de referencia actuales:

- `CurrentProvider`: estado/fuente actual de Streamlit.
- `CsvProvider`: fuente reproducible para pruebas/importación.

## Snapshot schema 3

Además de zonas, Anual, fixture, pendientes, promedios y contexto de objetivos, todo snapshot canónico nuevo contiene:

```text
traceability
├── traceability_version
├── snapshot_id
├── generated_at
├── provider
├── source
├── coverage
└── quality
```

Semántica importante:

- `snapshot_id`: huella del **contenido competitivo**, no de la fuente. Dos proveedores que entregan la misma foto deben producir el mismo ID.
- `generated_at`: cuándo se construyó el snapshot.
- `source.updated_at` / `source.data_as_of`: cuándo dice la fuente que sus datos son válidos.
- `coverage.last_confirmed_round`: mayor jornada oficial con al menos un resultado explícito que aparece en el fixture. No equivale necesariamente al último partido cronológico si hubo postergados.
- `quality.complete`: falso si la auditoría está bloqueada.

Compatibilidad: schemas 1, 2 y 3 se aceptan. Schema 1 no tiene contexto de objetivos; schema 2 tiene objetivos pero no exige trazabilidad; schema 3 exige `traceability`.

## Checklist para implementar OptaProvider

El futuro `OptaProvider` debe:

1. Resolver IDs Opta a los nombres canónicos de `lpf_clubs`.
2. Entregar zonas con `pts/pj/dg/gf/ga`.
3. Entregar resultados explícitos `(home, away, home_goals, away_goals)`; nunca inferir un resultado por PJ.
4. Entregar fixture con jornada original y, cuando exista, fecha/hora/status.
5. Entregar Tabla Anual y Apertura como tablas, no reglas de clasificación.
6. Entregar antecedentes de promedios sólo de temporadas previas.
7. Separar `qualification`/`rules` del payload de datos del proveedor.
8. Mapear timestamps reales a `provenance`; dejar `null` cuando Opta no los provea.
9. Pasar `provider_payload(OptaProvider(...))` a `prepare_competition_snapshot()`.
10. Verificar que una foto equivalente a Current/CSV genere el mismo `snapshot_id`.

No debe:

- importar Streamlit;
- llamar `lpf_pisos`, `lpf_conditionals`, `lpf_simulation` ni otros motores;
- decidir quién clasifica;
- inventar cortes/cupos;
- convertir ausencia de timestamp en “datos frescos”.

## Comandos mínimos de aceptación

Desde la raíz del repositorio:

```bash
pytest -q
python tools/release.py check --root .
```

Si Ruff está instalado en el entorno del equipo:

```bash
ruff check .
```

La CI de GitHub debe correr suite + release guard + Ruff.

## Smoke test de integración

```python
from lpf_data_provider import provider_payload
from lpf_services import prepare_competition_snapshot, calculate

payload = provider_payload(mi_provider)
snapshot = prepare_competition_snapshot(payload)["result"]

assert snapshot["snapshot_schema_version"] == "3"
assert snapshot["traceability"]["snapshot_id"]

respuesta = calculate("definition", {
    "snapshot": snapshot,
    "team": "Boca Juniors",
    "objective": "playoffs",
    "zone": "A",
})
```

El consumidor no debe reconstruir `base`, `cutoff` ni la Tabla Anual reducida.

## Dónde auditarlo en Streamlit

**Datos y auditoría → Contrato público usado por Streamlit** muestra:

- versión del Public Service;
- schema del snapshot y DataProvider;
- snapshot ID;
- fuente;
- timestamp y antigüedad cuando se conoce;
- cobertura de resultados/fixture;
- bloqueos de calidad;
- fallbacks del contrato público registrados en la sesión.

## Excepciones deliberadas que siguen pendientes

- La matriz de **rival clave** conserva un helper exacto directo por rendimiento; no es una segunda lógica matemática.
- Las tablas comparativas completas de probabilidades y la probabilidad de descenso conservan temporalmente el simulador contextual directo; la cifra individual de Playoffs/Copas ya cruza `objective_chances`.
- No existe todavía FastAPI. Cuando se agregue, debe ser una capa fina `HTTP -> calculate() -> JSON`.
- `CurrentProvider` puede tener timestamp desconocido en carga offline/manual. Esto es correcto: no debe reemplazarse por la hora del snapshot.

## Archivos que conviene leer primero

1. `HANDOFF_DESARROLLO.md`
2. `API_CONTRACT.md`
3. `ARCHITECTURE.md`
4. `lpf_data_provider.py`
5. `lpf_snapshot.py`
6. `lpf_services.py`
7. `tests/test_lpf_data_provider.py`
8. `tests/test_lpf_traceability.py`
9. `tests/test_lpf_services.py`

## Política de cambios

Si cambia sólo una implementación de proveedor sin cambiar `ProviderData`, no subir DataProvider version. Si cambia la forma requerida de `ProviderData`, versionar ese contrato. Si cambia la forma del snapshot, subir `snapshot_schema_version` manteniendo lectores anteriores cuando sea razonable. Si cambia la superficie JSON estable de las siete operaciones, versionar Public Service. `LPF_RUNTIME_API` sólo protege compatibilidad interna del despliegue y no reemplaza ninguno de esos contratos.

## Regla de selección en `Últimas fechas` (3.8.51)

La UI debe preservar cuatro roles distintos y no volver a mezclarlos:

1. **Equipo principal:** selección explícita del editor; gobierna todo el tablero. No se elige uno automáticamente en una sesión nueva.
2. **Contexto automático:** equipos cercanos al principal o al corte. Se muestran para ubicar la pelea, pero no son comparadores seleccionados.
3. **Comparadores:** sólo los clubes agregados por el editor en `Comparar también con…`; el principal siempre queda incluido y primero.
4. **Otra cancha clave:** una sugerencia automática basada en sensibilidad exacta; debe rotularse como sugerida/editable y no confundirse con los comparadores.

En la doble entrada usar la convención `equipo principal ↓ / equipo de la otra cancha →`: filas = resultado propio; columnas = resultado de la otra cancha. Si un equipo ya tiene una Copa resuelta por vía directa, debe poder seleccionarse y recibir esa explicación; no reemplazar la selección silenciosamente.

Este cambio no modifica los contratos Public Service/DataProvider/Snapshot.
