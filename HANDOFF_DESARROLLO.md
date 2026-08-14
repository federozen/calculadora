# Handoff al equipo de desarrollo · Calculadora LPF 3.8.60
## Fallback exacto de G/E/P para fechas grandes · 3.8.60

`next_round_conditionals` conserva el límite de 8 partidos ajenos porque además de estado necesita enumerar combinaciones, levers, doble entrada y explicaciones por otras canchas. **No aumentar ese límite por fuerza bruta.**

Cuando ese enumerador no está disponible, la UI llama `exact_objective_result_states` sobre el fixture pendiente completo. El solver MILP prueba por cada rama G/E/P: (a) si puede fallar incluso con el mínimo puntaje propio posterior y (b) si puede clasificar incluso con el máximo. De ahí salen únicamente tres estados exactos: asegurado / abierto / eliminado.

El fallback exige que la cantidad de partidos pendientes por club coincida con `rest`. Si la cobertura es incompleta, no publicar cierre exacto. La falta de enumeración detallada tampoco debe bloquear los visuales ESTIMADOS: termómetro, heatmap e impacto de otras canchas siguen disponibles.

## Paridad visual de Copas · 3.8.59

Además del mapa exacto, heatmap y otra cancha, Copas debe preservar los dos visuales base de Playoffs:

1. **G/E/P · EXACTO:** usa `definition` sobre Tabla Anual. Si el club ya está clasificado por vía directa, las tres ramas quedan cerradas a favor; no ocultar la matriz.
2. **¿Cómo viene?**: usa `objective_chances` cuando el objetivo está abierto. Si `objective_chances` devuelve `resolved=true`, mostrar 100% como **estado exacto resuelto**, sin rotularlo como Monte Carlo.

Esta regla aplica tanto a `Visualizaciones → Copas y descenso` como a `Últimas fechas`. El heatmap comparativo sigue siendo ESTIMADO y no reemplaza al termómetro individual.

## Paridad visual de Copas · 3.8.58

Libertadores y Sudamericana deben conservar cuatro capas distintas y no mezclarlas:

1. **Mapa de cupos hoy · EXACTO:** foto actual de la Tabla Anual con vías directas y cupos por tabla; no equivale a clasificación matemática asegurada.
2. **Termómetro del equipo · ESTIMADO:** la cifra destacada sigue pasando por `objective_chances` (6.000 simulaciones).
3. **Heatmap comparativo · ESTIMADO:** reutiliza `lpf_chances_obj`; rojo→amarillo→verde es sólo escala visual y cada celda imprime el porcentaje.
4. **Otra cancha · ESTIMADO:** reutiliza `lpf_conviene_obj`; la barra expresa diferencia de chance entre desenlaces, no probabilidad del partido ni condición exacta.

La asignación de cupos debe seguir viniendo de `allocate_cup_slots`/contexto compartido. No reconstruir campeones, reasignaciones ni cortes dentro de Streamlit.

## Consistencia editorial del Panel por equipo · 3.8.57

La pregunta **Qué necesita para alcanzar el objetivo** tiene una sola narrativa editorial larga compartida con `Últimas fechas`, mediante `_lpf_editorial_need_text`. Mantener esta regla:

1. la salida principal de la UI editorial es el informe completo (`lpf_playoffs_texto`, `lpf_copas_necesita_texto` o `lpf_descenso_texto`);
2. `_lpf_service_need_text` es un resumen JSON-safe para API/auditoría y puede mostrarse sólo como bloque secundario plegado;
3. nunca usar el resumen público como sustituto silencioso del informe largo en Panel por equipo;
4. una mejora narrativa debe entrar por el helper compartido para que Panel por equipo y Últimas fechas no diverjan.

## Restauración editorial 3.8.56

`Últimas fechas` debe conservar dos capas complementarias y visibles en este orden:

1. **Informe editorial del equipo:** reutiliza `lpf_playoffs_texto` o `lpf_copas_necesita_texto` y conserva realidad actual, proyección, referencia histórica, fixture, mínimo que asegura y pendientes.
2. **Lectura visual de la fecha:** grilla G/E/P, mapa de puestos, comparadores, doble entrada, árbol, partidos que más definen, reloj y visual estimada de chances.

La capa visual nunca debe reemplazar ni esconder el informe editorial. Tampoco debe implementarse una segunda versión de sus cálculos dentro de Streamlit.

## Hotfix UI 3.8.55

- Streamlit no permite mutar `st.session_state[key]` de un widget después de instanciarlo en el mismo rerun. Los botones **Agregar sugeridos** y **Quitar comparadores** usan callbacks (`on_click`) para modificar el multiselect antes del rerun. Mantener este patrón en futuras acciones sobre widgets.
- `Últimas fechas` deja visibles los visuales tipo Mundial adaptados a LPF: grilla G/E/P, mapa exacto de puestos tras la fecha, cara a cara, doble entrada, árbol, partido bisagra visual, chances estimadas y reloj.
- La semántica sigue separada: mapa/grillas/árbol/bisagra son **EXACTOS**; el termómetro de chances es **ESTIMADO** y pasa por `objective_chances`.


## Bootstrap de producción · 3.8.54

Leer también `PRODUCTION_BOOTSTRAP.md`. Se entregan:

- `api/`: FastAPI con health/readiness/capabilities + siete endpoints.
- `providers/opta.py`: `OptaTransport + OptaNormalizer -> OptaProvider`.
- `Dockerfile.api`, `.env.example` y `Makefile`.
- `tools/build_snapshot.py`, `tools/smoke_api.py`, `tools/production_acceptance.py` y `tools/build_runtime_bundle.py`.
- siete casos dorados en `tests/fixtures/production/`.
- bundle mínimo de runtime/API regenerable para despliegues, separado del repo completo.
- empaquetado Setuptools explícito: API sin dependencia obligatoria de Streamlit.

El objetivo es que el primer sprint empiece por payloads reales de Opta e infraestructura, no por descubrir cómo invocar los motores.


## Qué se entrega

Esta versión deja separados los cuatro contratos que el equipo debe tratar como fronteras distintas:

| Frontera | Versión | Responsabilidad |
| --- | ---: | --- |
| Public Service | `v1` | 7 operaciones JSON-safe de cálculo. |
| DataProvider | `v2` | Normalizar cualquier fuente a `ProviderData`. |
| Snapshot | `schema 3` | Foto canónica de competencia + objetivos + trazabilidad. |
| Runtime interno | `21` | Evitar despliegues con módulos críticos mezclados. |

Desde 3.8.54 hay un **bootstrap FastAPI** y una **plantilla Opta**, pero no hay credenciales, endpoints ni schema inventado del producto Opta contratado. Ver `PRODUCTION_BOOTSTRAP.md`.

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
- `api/` ya implementa la capa fina `HTTP -> calculate() -> JSON`; Desarrollo debe agregar autenticación/infraestructura según el entorno y conectar el snapshot server-side a Opta/cache.
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
## Regla visual de `Últimas fechas` (3.8.52)

Sobre la regla de selección de 3.8.51 se suma una convención obligatoria para futuras interfaces:

1. **Un solo equipo seleccionado:** el `equipo principal` es el único protagonista. Los comparadores sólo agregan filas a G/E/P.
2. **La otra cancha se selecciona como partido, no como equipo.** Mostrar `Partido de la otra cancha (sugerido, editable)` y cruzar filas del principal con columnas `gana local / empate / gana visitante`.
3. **Convención de doble entrada:** `equipo principal ↓ / partido ajeno →`. No volver a una orientación dependiente de qué club del partido se tomó como referencia interna.
4. **Semántica de color:** verde/amarillo/rojo representan estados matemáticos; siempre acompañar con texto. Nunca convertir la frecuencia de combinaciones en probabilidad.
5. **Partidos que más definen:** puede ordenarse usando los `levers` exactos de `next_round_conditionals`; publicar el cambio como conteo de caminos exactos entre mejor/peor desenlace. No rotular ese conteo como chance.
6. La grilla visual es lectura principal; las tablas extensas y exportaciones pueden quedar como detalle secundario.

Este cambio no modifica Public Service v1, DataProvider v2, snapshot schema 3 ni Runtime API 21.


## Regla de configuración visible en `Últimas fechas` (3.8.53)

La interfaz no debe volver al flujo wizard donde elegir el equipo principal oculta las decisiones siguientes. El orden obligatorio es:

1. **Configuración visible completa:** objetivo, zona si corresponde, equipo principal, comparadores y partido de la otra cancha.
2. Antes de elegir equipo, comparadores y otra cancha pueden estar deshabilitados, pero deben seguir visibles para que el editor entienda el alcance del tablero.
3. El equipo principal sólo fija el protagonista; no representa una acción final ni abre una vista distinta.
4. Después de todos los controles debe existir un corte explícito **Resultado del análisis**. Recién debajo van contexto automático, G/E/P, doble entrada, árbol, partidos que más definen y reloj.
5. `Partido de la otra cancha` ofrece modo automático o selección manual; el resultado no debe volver a crear un segundo selector del mismo concepto.
6. Existe un test de arquitectura/UI que comprueba que esos controles aparecen en el código antes de la sección de resultados.

Este cambio no modifica Public Service v1, DataProvider v2, snapshot schema 3 ni Runtime API 21.
