# Instrucciones para continuar mejorando el proyecto

Este documento es el traspaso para la IA (o persona) que siga trabajando en la
**Calculadora del Fútbol Argentino · LPF 2026**. Léelo entero antes de tocar código.
Está escrito para que puedas continuar con el mismo criterio y la misma red de
seguridad con que se trabajó hasta acá.

---

## 0. Objetivo (leé esto primero)

Tu tarea tiene tres metas, en este orden de prioridad:

1. **Que funcione.** La app tiene que levantar con `streamlit run` y andar. Antes de
   cualquier mejora, verificá que arranca (sección 2).
2. **Simplificar el código sin cambiar el comportamiento.** El archivo principal es
   un monolito que se está desarmando en módulos chicos y claros. Seguí bajándolo,
   reduciendo duplicación y aclarando lo confuso —pero **los números que devuelve la
   app no pueden cambiar** (sección 4).
3. **Dejarlo listo para mejoras.** Al terminar, el proyecto debe quedar más fácil de
   entender y tocar que como lo encontraste: módulos con una responsabilidad clara,
   pruebas verdes, linter limpio y documentación al día (sección 12).

Regla mental para todo el trabajo: **simplificar es reducir complejidad, no agregar
inteligencia.** No reescribas desde cero, no cambies el stack, no metas frameworks ni
abstracciones "por las dudas". La mejor versión de este trabajo es aburrida, chica y
verificable.

---

## 1. Qué es este proyecto

Aplicación en **Python + Streamlit** que analiza la Liga Profesional 2026: playoffs
por zonas, Tabla Anual, Libertadores, Sudamericana, descenso, promedios, escenarios
de una fecha y puntos por objetivo. El punto de entrada es
`calculadora_futbol_argentino.py`.

**Principio rector, innegociable:** *los números siempre salen de Python
determinístico y validado.* El modelo de lenguaje (cuando está activo) sólo
interpreta la consulta del usuario y redacta; **nunca** calcula. No rompas esto.

**Regla editorial:** no usar **“cota”**, **“piso seguro”**, **“piso ajustado”**, **“garantía exacta”**, **“referencia conservadora”**, **“puntaje que asegura”** ni **“seguro (conservador)”** como etiquetas de cara al usuario. Usar siempre **mínimo posible**, **total seguro** y **mínimo que asegura**. El **total seguro** es suficiente si se alcanza, pero puede pedir puntos de más: todavía no sabemos si es el menor. El **mínimo que asegura** es el menor total comprobado. Distinguí siempre: *corte actual*, *mínimo posible* (desempate a favor), *total seguro*, *mínimo que asegura* (desempate en contra) y *estimación* (siempre rotulada como tal).

---

## 2. Cómo correr y verificar la app

### Instalar y correr
```bash
pip install -r requirements.txt
streamlit run calculadora_futbol_argentino.py
```
La app funciona sin configuración. El asistente de lenguaje es **opcional**: si querés
activarlo, poné una `ANTHROPIC_API_KEY` en `.streamlit/secrets.toml` o desde la UI.
Sin key, la app anda igual (sólo se apaga la redacción asistida; los cálculos no
dependen de eso).

### Verificar que sigue sana (corré esto después de cada cambio)
```bash
pip install pytest ruff --break-system-packages
python -m pytest -q                                   # todas deben pasar
python -m ruff check --select F,E9 *.py tests/*.py    # "All checks passed!"
python -m py_compile calculadora_futbol_argentino.py lpf_*.py
python tools/release.py check
```

### Evitar deploys con archivos mezclados
Desde 3.8.12, los módulos críticos comparten `LPF_RUNTIME_API`. Streamlit ejecuta
`lpf_runtime.runtime_compatibility()` antes de importarlos. Si agregás o cambiás una
interfaz interna incompatible, incrementá el nivel y actualizá juntos los módulos
listados en `lpf_runtime.CRITICAL_COMPONENTS`. No desactives este chequeo para hacer
pasar una actualización parcial.

### Verificar que la app realmente arranca (sin abrir un navegador)
El archivo principal ejecuta UI al importarse, así que se puede hacer un "smoke test"
con Streamlit simulado. Si el import corre **más allá de la carga de datos** (llega a
código de UI), el arranque y la carga de datos están sanos. Guardá un stub mínimo de
Streamlit y hacé `import calculadora_futbol_argentino`; si falla recién en un widget
de UI (no en un `import` ni en la construcción de datos), estás bien. Este chequeo ya
se usó y sirve para confirmar que ninguna extracción rompió la cadena de datos.

---

## 3. Estado actual (punto de partida)

- Versión: `3.8.43` (fuente única en `lpf_version.__version__`; la usan Streamlit,
  `lpf_models.AuditMetadata.calculation_version` y la frontera de servicios).
- Archivo principal: **~10.458 líneas** (arrancó en ~12.780).
- **317 pruebas**, todas verdes en 3.8.43. `ruff` (categorías `F` y `E9`) sigue siendo obligatorio en el entorno de desarrollo.
- Se extrajeron módulos del monolito y se agregó una frontera de servicios JSON-safe;
  las extracciones siguen verificadas por equivalencia exacta contra el original.
- La copia original intacta está en `_original_referencia/` **sólo para probar
  equivalencia** (no se usa en la app, no la importes, no la edites).

---

## 4. Qué significa "simplificar" acá (y qué NO hacer)

### Simplificar es (en orden de valor y seguridad):
- **Seguir sacando capas del monolito** a módulos con una responsabilidad clara,
  usando el patrón seguro de la sección 6. Esto es lo principal.
- **Borrar código muerto** (funciones sin usar, ramas inalcanzables). Ya se archivó
  un fork entero (`calculadora_mundial.py` → `legacy/`) y se limpiaron variables y
  código inalcanzable. Si encontrás más, sacalo (verificá con el linter que nadie lo
  usa).
- **Partir funciones gigantes** en piezas nombradas. El archivo tiene funciones de
  cientos de líneas (p. ej. `cargar_lpf_espn`); separar la lógica pura de la UI las
  hace legibles y testeables.
- **Reducir duplicación**: si ves la misma lógica repetida, unificala en una función
  y reutilizala.
- **Aclarar sin reescribir**: mejores nombres, docstrings breves donde falten,
  comentarios que expliquen el *porqué*.

### Simplificar NO es:
- **Reescribir desde cero.** Prohibido. El valor está en preservar el comportamiento.
- **Cambiar los números.** Si un cálculo da distinto después de tu cambio, es un bug,
  aunque "parezca más correcto". Cambios en la matemática van con una prueba que los
  justifique (sección 9, regla 1).
- **Cambiar el stack ni agregar dependencias pesadas.** Nada de reemplazar Streamlit,
  meter una base de datos, un framework nuevo o un ORM.
- **Abstraer de más.** No crees capas genéricas "por si acaso". Simplificá lo que
  hay, no imagines lo que podría venir.
- **Tocar todo a la vez.** Un módulo por vez, verificando entre cada paso.

---

## 5. Mapa de módulos

El monolito se está desarmando en capas. El grafo de dependencias es un DAG (sin
ciclos); respétalo. De más básico a más compuesto:

| Módulo | Responsabilidad | Depende de |
| --- | --- | --- |
| `lpf_text.py` | Normalización de texto, detección de equipos, formateo de números. | — |
| `lpf_clubs.py` | Canonicalización de nombres de clubes (`canon_club`, `canon_base`, `LPF_CLUBES`). | lpf_text |
| `lpf_data_2026.py` | Datos fijos de la temporada: fixture, nóminas de zona, tabla anual, foto del Apertura, parser del fixture. | lpf_clubs |
| `lpf_parsers.py` | Parsers de tablas pegadas (anual, promedios, fixture, lista de equipos). | lpf_text, lpf_clubs |
| `lpf_standings.py` | Motor puro de tabla: estadísticas, desempates, orden, posiciones, tabla y clasificador in/out/pelea. Los criterios entran como parámetro. | — (pandas) |
| `lpf_fixture_sources.py` | Fuentes de fixture y `expected_played_count` (ya existía). | — |
| `lpf_schedule.py` | Agenda/calendario puros para Previa: hora argentina, jornada/postergados, orden real y ventanas temporales. | lpf_clubs |
| `lpf_preview.py` | Previa pura por equipo: Markdown + tabla de escenarios desde ventana/contexto explícitos, sin sesión. | pandas, lpf_display, lpf_scenarios, lpf_standings |
| `lpf_result_updates.py` | Aplicación pura de marcadores confirmados y cambios de posiciones para la carga manual. | lpf_standings |
| `lpf_averages.py` | Contrato puro de promedios: distingue antecedentes previos de totales acumulados y usa la Tabla Anual como fuente de puntos/PJ 2026. | lpf_clubs |
| `lpf_form.py` | Forma reciente, rachas y fuerza regularizada para simulaciones; el Apertura entra por parámetro. | numpy |
| `lpf_simulation.py` | Constructor explícito de contexto y primitivas Monte Carlo: Anual/cupos, promedios, posición/puntos por zona, suma de puntos y máscaras de objetivos. | numpy, lpf_averages, lpf_qualification |
| `lpf_conditionals.py` | Condicionales exactos de la próxima fecha: G/E/P, clasificación asegurada/pelea/eliminación y palancas de otras canchas sin probabilidades. | — |
| `lpf_relegation.py` | Foto actual de descensos respetando desempates y la exclusión promedio→Anual. | — |
| `lpf_qualification.py` | Tabla Anual autoritativa, plazas internacionales y contexto de copas sin sesión. | lpf_clubs, lpf_data_quality, lpf_standings, lpf_text |
| `lpf_data_quality.py` | Reportes de calidad de datos (ya existía). | lpf_models |
| `lpf_state.py` | Constructor y revalidador puros del estado LPF canónico: Apertura, Anual autoritativa, pendientes y auditoría. Todos los valores de sesión entran por parámetro. | lpf_clubs, lpf_data_quality, lpf_models |
| `lpf_loading.py` | Preparación pura de carga: canonicaliza resultados, combina fuentes, avanza standings, reconstruye la Anual e infiere faltantes sin red ni Streamlit. | lpf_clubs, lpf_data_2026, lpf_data_quality, lpf_derive, lpf_fixture_sources, lpf_reconcile, lpf_state |
| `lpf_http.py` | Transporte HTTP de fuentes públicas; no parsea ni conoce Streamlit. | requests |
| `lpf_provider_adapters.py` | Adaptación pura de respuestas ESPN/FutbolArgentino.com a tablas/resultados/metadatos del dominio. | pandas, lpf_clubs, lpf_reconcile, lpf_text |
| `lpf_table_selection.py` | Política pura de prioridad/fallback de zonas y Anual entre proveedores, respaldo y candidatos locales. | lpf_clubs, lpf_reconcile, lpf_text |
| `lpf_table_backup.py` | Construcción, persistencia JSON y recuperación del último respaldo válido de tablas; no conoce Streamlit ni proveedores. | lpf_clubs, lpf_reconcile, lpf_text |
| `competition_html_adapters.py` | Parsing puro de tablas HTML genéricas del modo avanzado (posiciones y matrices equipo × equipo). | pandas, lpf_text |
| `lpf_reconcile.py` | Reconciliación e integridad: ajusta resultados a zonas, repara duplicados, avanza zonas, valida. | lpf_clubs, lpf_data_2026, lpf_fixture_sources, lpf_parsers |
| `lpf_derive.py` | Deriva la foto del Apertura e infiere resultados faltantes. | lpf_text, lpf_clubs, lpf_data_2026, lpf_reconcile |
| `lpf_intents.py` | Ruteo de intención del chat (consulta → `{"intent": ...}`). | lpf_text |
| `lpf_scenarios.py` | Motor exacto MILP (scipy): escalera de puntos, rangos, escenarios. | lpf_models |
| `lpf_exact.py` | Garantías conservadoras (línea segura, promedios). | — |
| `lpf_pisos.py` | Puntos por objetivo y combinación pura de antecedentes/temporada actual para promedios. | lpf_scenarios, lpf_exact |
| `lpf_models.py` | Dataclasses de dominio y auditoría. | — |
| `lpf_version.py` | Única versión del motor compartida por todas las interfaces. | — |
| `lpf_runtime.py` | Chequeo previo al arranque de compatibilidad entre módulos críticos desplegados; lee marcadores sin importar esos módulos. | — |
| `lpf_snapshot.py` | Foto canónica JSON-safe de competencia, `snapshot_schema_version` y selección de alcance por zona/Anual. | lpf_state, lpf_pisos |
| `lpf_services.py` | Contrato JSON-safe para cálculos, validación/capacidades, snapshots y consultas por lote; futura frontera HTTP. | lpf_version, lpf_snapshot, lpf_standings, lpf_scenarios, lpf_pisos |
| `lpf_competition_narratives.py`, `lpf_competitive_context.py`, `lpf_display.py` | Relatos y presentación (ya existían). | varias |

El motor `_resolver` / `_orden` ya no está en el archivo principal. `posiciones` y
`tabla` permanecen sólo como adaptadores mínimos de Streamlit que inyectan los
criterios de sesión al motor puro de `lpf_standings`.

---

## 6. El patrón de extracción seguro (SEGUÍLO SIEMPRE)

Toda extracción que se hizo respetó estos pasos. No te saltees ninguno.

1. **Elegí un bloque cohesivo** de funciones relacionadas.
2. **Mapeá el cierre de dependencias**: qué funciones y qué globales/constantes usa,
   de forma transitiva. Una función sólo es extraíble si su cierre completo es
   "puro": no toca `st.session_state` ni `requests`. (Ver script sugerido abajo.)
3. **Verificá que no haya ciclos**: el módulo nuevo sólo puede importar de módulos ya
   existentes, nunca del archivo principal.
4. **Creá el módulo nuevo** con las funciones y sus imports (de `lpf_text`,
   `lpf_clubs`, etc.). Poné un docstring que explique la responsabilidad.
5. **Quitá los bloques del archivo principal** y **reimportá con el mismo nombre**
   (`from lpf_nuevo import foo, bar`). Así ningún call-site cambia.
6. **Corré el linter** (`ruff --select F,E9`). Va a atrapar imports faltantes
   (`F821`) e imports sin uso (`F401`). Arreglalos. **Esto ya salvó de dos bugs.**
7. **Probá equivalencia exacta** contra el original (ver sección 7). Es el paso
   más importante: demuestra que el comportamiento no cambió.
8. **Escribí pruebas permanentes** para el módulo nuevo.
9. **Corré toda la suite**, actualizá `CHANGELOG.md`, `ARCHITECTURE.md` y
   `tests/README.md`, y recién ahí das el paso por terminado.

### Cuidado conocido con la extracción por texto
Si extraés bloques buscando "desde `def X` hasta el próximo `def`", vas a arrastrar
cualquier **constante o comentario de módulo que viva suelto entre dos funciones**.
Ya pasó una vez (`_LPF_PROM_HISTORY_VERSION` terminó en el módulo equivocado; lo
atrapó el linter). Revisá el módulo nuevo en busca de asignaciones de módulo que no
correspondan (`grep -nE '^[A-Za-z_][A-Za-z0-9_]* *=' lpf_nuevo.py`).

### Script para mapear el cierre de una función
```python
import re
lines = open('calculadora_futbol_argentino.py').read().split('\n')
defs = {}
for i, l in enumerate(lines):
    m = re.match(r'def ([A-Za-z_][A-Za-z0-9_]*)\(', l)
    if m: defs.setdefault(m.group(1), i)
def block(name):
    s = defs[name]; e = s + 1
    while e < len(lines) and not (lines[e].startswith('def ') or lines[e].startswith('class ')): e += 1
    return '\n'.join(lines[s:e])
# BFS del cierre desde una semilla; marca impuras las que tocan st/requests
```

---

## 7. Cómo probar equivalencia exacta (imprescindible)

La copia intacta original está en `_original_referencia/`. La técnica: cargar la
función **original** en un namespace aislado (dándole sus dependencias ya extraídas)
y compararla contra la nueva sobre muchas entradas reales.

```python
# Cargar la versión original de una función en un namespace controlado
orig_lines = open('_original_referencia/calculadora_futbol_argentino_ORIGINAL.py').read().split('\n')
def block(name, lines):
    s = next(i for i,l in enumerate(lines) if l.startswith(f'def {name}('))
    e = s+1
    while e<len(lines) and not (lines[e].startswith(('def ','class '))): e+=1
    return '\n'.join(lines[s:e])
ns = {'canon_club': canon_club, ...}   # inyectá TODAS las dependencias
exec(block('mi_funcion', orig_lines), ns)
orig_fn = ns['mi_funcion']
# comparar orig_fn(x) contra nueva(x) sobre cientos de entradas reales
```

Compará **capturando también las excepciones** (si el original lanza y el nuevo
lanza lo mismo, son equivalentes). Un ejemplo real: `_lpf_infer_missing_results`
lanza `ValueError` con cierta entrada inválida; original y nuevo lo hacen igual, y
eso es equivalencia correcta.

Usá datos reales de la temporada (`lpf_data_2026`) siempre que puedas, no ejemplos
inventados. Al escribir tests, primero **inspeccioná la forma real de retorno** de la
función (muchas devuelven tuplas con estructura, no lo que uno asume); no adivines.

---

## 8. Qué falta y cómo encararlo (hoja de ruta)

### 8a. Lo que queda es más difícil: pará y cambiá de enfoque
Lo pendiente ya **no** es extracción pura fácil. Es de dos tipos:

- **Tejido de generación de texto editorial** (`lpf_*_texto`, `_copas_bloque_*`,
  `lpf_que_se_juega_fecha`, etc.): son "puras" en el sentido de no tocar `st`, pero
  forman un componente enorme y muy interconectado, y varias leen configuración vía
  accesores (`DIRECTO()`, `CRITERIOS()`, `MEJORES_TERCEROS()`) que sí leen
  `st.session_state`. Extraerlas requiere **inyección de dependencias** (pasar los
  criterios como parámetro), lo que cambia firmas y call-sites. Es un refactor
  mayor: hacelo de a poco y con muchísima prueba de equivalencia, o no lo hagas.

- **Código pegado a la interfaz** (47 funciones con `st.session_state`, 11
  `render_*`, y los cargadores `cargar_lpf_*`, `_lpf_rebuild_state`): acá el objetivo
  no es "mover", es **separar la lógica de la presentación**. Extraé la lógica pura
  que esté enterrada dentro de una función de UI a un helper puro y testeable, y
  dejá en la UI sólo la parte de Streamlit. No muevas Streamlit a otro módulo.

### 8b. Criterios de desempate — resuelto en 3.8.1
El motor de ordenamiento (`_resolver`, `_orden`, `posiciones`, `tabla`) ya vive en
`lpf_standings.py` y recibe `criterios` como parámetro. El módulo no toca Streamlit.
El archivo principal conserva únicamente adaptadores de `posiciones` y `tabla` para
inyectar `CRITERIOS()` sin cambiar los call-sites existentes.

La extracción se comprobó en 1.470 casos aleatorios contra la copia original, con
seis juegos de criterios y equivalencia exacta de orden, posiciones y tabla.

Esta separación es también el primer límite preparado para una futura API: los
consumidores nuevos deben llamar al módulo puro pasando la configuración explícita,
no leer estado de interfaz.

### 8c. Preparación para futura API y Opta
La dirección arquitectónica acordada es:

`proveedor → normalización/reconciliación → motores puros → API o Streamlit`.

No agregues Opta, FastAPI ni otra dependencia sólo "por las dudas". Sí preservá estas
reglas en cada refactor:

- los motores reciben datos y configuración por parámetros;
- ningún motor importa Streamlit ni código de red;
- cualquier proveedor futuro traduce su payload al modelo canónico antes del cálculo;
- la futura API importa módulos puros, nunca el archivo principal Streamlit;
- entradas y salidas del núcleo deben poder representarse en JSON sin depender del
  formato nativo del proveedor.

### 8c bis. Constructor de estado — resuelto en 3.8.2
`_lpf_rebuild_state` ya no contiene las reglas de armado de la foto LPF. Esa lógica vive
en `lpf_state.build_lpf_state`, que recibe explícitamente zonas, resultados, Anual,
Apertura, promedios, fixture y metadatos de Copa Argentina. El wrapper de Streamlit
se limita a leer/escribir sesión.

Esta es la frontera de entrada recomendada para una futura API después de que el
proveedor haya sido normalizado. No hagas que un adaptador Opta escriba directamente
`st.session_state`: debe producir las mismas estructuras que recibe `build_lpf_state`.

### 8c ter. Preparación de cargas — resuelto en 3.8.3
`cargar_lpf_todo` y `cargar_lpf_espn` ya no contienen la mayor parte de la lógica
determinística de preparación. Esa capa vive en `lpf_loading.py` y no toca Streamlit
ni la red. `normalize_results_for_zones` es el contrato mínimo de resultados para
proveedores: canonicaliza clubes, convierte goles a enteros, filtra por la nómina y
deduplica por identidad oficial.

`prepare_offline_load` y `prepare_automatic_update` reciben fotos ya obtenidas y
devuelven zonas/resultados/reconciliación/diagnósticos como estructuras Python
simples. Esto permite que una futura API o un adaptador Opta reutilicen exactamente
la misma preparación. No hagas que Opta escriba sesión ni que los fetchers entren en
los motores.

### 8c quater. Transporte y adaptadores de proveedor — resuelto para LPF en 3.8.4
Los caminos automáticos principales de LPF ya separan transporte de parsing.
`lpf_http.py` hace sólo HTTP; `lpf_provider_adapters.py` recibe HTML/JSON ya descargado
y devuelve estructuras del dominio. El archivo Streamlit conserva la caché y la
persistencia de sesión. Hay fixtures locales de FutbolArgentino.com y ESPN para probar
sin internet.

Un futuro adaptador Opta debe vivir en esta misma frontera conceptual: resolver IDs,
nombres, estados y payloads propios y entregar estructuras simples a `lpf_loading`.
No agregues una interfaz genérica ni un SDK hasta que exista ese consumidor concreto.

### 8c quinquies. Frontera de servicios — resuelto en 3.8.5 y ampliado en 3.8.9
`lpf_services.py` expone cálculos con entrada/salida JSON-safe y errores estables sin
incorporar un framework HTTP. `lpf_snapshot.py` arma una foto completa desde el mismo
constructor de estado de Streamlit; `prepare_competition_snapshot` la expone y
`calculate_competition_batch` permite varias consultas sobre esa misma foto. La futura
API debe ser una capa fina sobre estos servicios; no debe importar el archivo Streamlit
ni volver a implementar cálculos. `API_CONTRACT.md` documenta la versión 1.

La función pura `lpf_pisos.promedio_totales` arma los totales de promedios para UI y
API; no vuelvas a duplicar esa fórmula dentro de Streamlit. No agregues FastAPI/Flask,
persistencia nueva de snapshots canónicos en servidor ni un SDK de Opta hasta que exista el consumidor concreto. El respaldo histórico de tablas sí vive en `lpf_table_backup`.

### 8d. Otros fetchers de red (parcialmente resuelto en 3.8.14–3.8.16)
Los caminos LPF de ESPN/FutbolArgentino.com ya tienen transporte y parsing separados.
Desde 3.8.14, `tabla_desde_url` y `partidos_desde_url` también son wrappers finos: la
descarga histórica vive en `lpf_http.fetch_url_text` y el parsing puro en
`competition_html_adapters.py`, con fixtures locales y equivalencia contra 3.8.13.

Desde 3.8.15, `espn_fixture` tampoco arma dentro de Streamlit la ventana multi-request:
`lpf_http.fetch_espn_scoreboard_window` concentra fecha inicial, bloques de 21 días,
`max_req` y tolerancia a fallos parciales. Recibe `get_json` por parámetro para que la
UI conserve `_espn_get` y su caché. Se comparó contra 3.8.14 en cuatro rutas exactas.

Desde 3.8.16, `futbolargentino_fixture` tampoco arma dentro de Streamlit las dos
consultas de resultados ni sus cache-busters: `lpf_http.fetch_futbolargentino_results_pages`
concentra esa orquestación y recibe `get_html` por parámetro para conservar la caché de UI.
El wrapper sólo parsea/valida respuestas y mantiene exactamente el comportamiento 3.8.15.

Desde 3.8.17, `lpf_tables_with_fallback` tampoco contiene la política de prioridad entre
ESPN, FutbolArgentino.com, última foto y Anual local. Esa decisión vive en
`lpf_table_selection.select_lpf_tables`, módulo puro; Streamlit sólo obtiene candidatos,
delega y persiste si corresponde. La salida se comparó contra 3.8.16 en nueve rutas.

Desde 3.8.18, la persistencia del último respaldo válido tampoco vive en Streamlit.
`lpf_table_backup` construye/valida el JSON, escribe de forma atómica y recupera candidatos
de sesión/disco con la misma prioridad y antigüedad histórica. Streamlit sólo aporta la
copia de sesión y conserva el warning si el filesystem no permite escribir. La recuperación
se comparó contra 3.8.17 en cinco escenarios dirigidos.

Desde 3.8.19, `_lpf_refresh_quality` tampoco reconstruye Apertura/Anual ni arma la auditoría
dentro de Streamlit. `lpf_state.refresh_lpf_quality_state` recibe todos los candidatos y
datos por parámetro y devuelve Apertura seleccionado, Anual autoritativa y reporte; el
wrapper sólo persiste esos valores. Se comparó contra 3.8.18 en siete escenarios con
equivalencia exacta de reporte y efectos de sesión.

El nivel interno fue **2** desde 3.8.16, subió a **3** en 3.8.19 por la nueva función de `lpf_state`, a **4** en 3.8.21 por `lpf_schedule.py`, a **5** en 3.8.22 porque la Mesa de redacción requiere `lpf_result_updates.py` y a **6** en 3.8.23 porque la app importa `lpf_qualification.py` para Anual/cupos, a **7** en 3.8.24 porque también importa sus helpers de contexto de copas y a **8** en 3.8.25 porque la UI importa `lpf_scenarios.can_finish_exact_rank_by_points` y a **9** en 3.8.26 al incorporar `lpf_form.py` como dependencia activa de las simulaciones y a **10** en 3.8.27 al extraer `lpf_simulation.py` como frontera Monte Carlo pura y a **11** en 3.8.28 porque el wrapper importa su constructor explícito de contexto y a **12** en 3.8.29 al unificar `lpf_competitive_context.py` con el kernel y la fuerza canónicos. El archivo principal también comprueba explícitamente que `lpf_runtime.py` tenga el nivel requerido antes de importar módulos sensibles. Los paquetes de actualización deben reemplazar los módulos críticos juntos; no bajes ese nivel sólo para reducir el ZIP.
En 3.8.30 sólo se reordenó la navegación visible de **Accesos principales**; no cambió ningún contrato interno y el runtime siguió en **12**. En 3.8.31 el nivel sube a **13** porque `lpf_averages.py` pasa a ser dependencia crítica de pisos, snapshots y simulación de descenso.

Football-data y Apify siguen definidos por compatibilidad histórica, pero sus ramas
de UI están actualmente deshabilitadas con `and False`. No los extraigas ni reactives
sólo por uniformidad; recién separalos cuando vuelvan a tener un consumidor real y
haya fixtures/requests simulados para ese camino.

### 8d bis. Agenda real y ventana de Previa — resuelto en 3.8.21
`lpf_schedule.py` concentra la interpretación de fecha/hora argentina, la mezcla de agendas, la jornada operativa con postergados, el orden de pendientes y el alcance de la Previa. El módulo recibe fixture y agenda por parámetro y no toca Streamlit ni red. Los wrappers del archivo principal sólo aportan `_ESPN_FECHA_HORA`, `LPF_SCHEDULE` y el respaldo legacy `_ESPN_DIA`.

La extracción se comparó contra 3.8.20 en 120 fotos sintéticas y 720 consultas de alcance con equivalencia exacta. Un futuro proveedor debe aportar programación normalizada a esta capa en lugar de decidir el próximo partido dentro de la UI.

### 8d ter. Aplicación manual de resultados — resuelto en 3.8.22
`lpf_result_updates.py` concentra la mutación estadística de un marcador confirmado y el cálculo de cambios de puestos. Recibe zonas, jugados, pendientes y resultados por parámetro; devuelve copias actualizadas y no toca Streamlit. `_rd_apply_results` conserva únicamente el rebuild del estado y la persistencia de sesión.

La extracción se comparó contra 3.8.21 en 500 casos de marcadores, 300 casos de cambios de puestos y 250 ejecuciones completas del wrapper. Una futura interfaz puede reutilizar esta misma regla antes de llamar al constructor canónico.

### 8d quater. Tabla Anual y plazas internacionales — resuelto en 3.8.23
`lpf_qualification.py` concentra la prioridad Apertura + zonas / Anual directa validada y el reparto reglamentario de plazas de Libertadores/Sudamericana. Recibe todos los candidatos, campeones y reemplazos por parámetro; no lee `session_state` ni red. `lpf_anual_base` y `lpf_plazas_copas` quedan como wrappers de sesión.

La extracción se comparó contra 3.8.22 en 300 casos de Anual y 600 combinaciones de campeones/extras/reemplazos sin diferencias. Una futura API puede reutilizar esta capa para copas sin importar el archivo Streamlit.

### 8d quinquies. Contexto de copas — resuelto en 3.8.24
`lpf_qualification.py` también normaliza los clasificados fijos a Libertadores, los equipos vivos de Copa Argentina y la etiqueta de actualización/fuente. Los wrappers `_lpf_fixed_lib_qualifiers`, `_lpf_copa_arg_alive_for_annual` y `_lpf_copa_snapshot` sólo aportan los fallbacks de sesión.

La extracción se comparó contra 3.8.23 en 600 estados de sesión y 1.800 llamadas de wrapper, con equivalencia exacta. No avanzar todavía sobre el tejido grande de narrativas salvo que haya un corte chico, activo y con dependencias inyectables.

### 8d sexies. Puesto específico: posibilidad vs. probabilidad — corregido en 3.8.25

La pantalla **Escenarios → Puntos y puesto final** ya no debe responder la pregunta práctica con la lista cruda de puntajes matemáticamente posibles. Para el puesto elegido, la vista principal usa 6.000 simulaciones y calcula mediana, 50% central y frecuencia por puntaje **condicionando a las corridas donde el equipo termina exactamente en ese puesto**. Esa mediana sí tiene interpretación probabilística dentro del modelo.

Los extremos matemáticos quedan en una vista separada y rotulada “sin probabilidad”. `lpf_scenarios.can_finish_exact_rank_by_points` exige un escenario en el que haya exactamente `puesto - 1` rivales con más puntos y ninguno empatado con el equipo; como el motor exacto no proyecta marcadores futuros, no publiques un puesto exacto que dependa de un desempate. La prueba por fuerza bruta cubre esta regla.

No vuelvas a calcular una “mediana” sobre la lista de puntajes alcanzables: esos valores no son equiprobables. Si se cambia el modelo probabilístico, rotulalo siempre como estimación y conservá la vista exacta separada.

### 8d septies. Forma y fuerza de simulación — resuelto en 3.8.26

`lpf_form.py` concentra G/E/P, forma reciente, rachas y la fuerza regularizada que usan las simulaciones. Recibe tabla vigente, resultados confirmados y Apertura por parámetro; no importa Streamlit ni red. `_fuerza_lpf` queda como wrapper de sesión para aportar el Apertura.

La extracción se comparó directamente contra 3.8.25 en 1.000 casos de forma/racha, 800 fotos de fuerza y 400 ejecuciones del wrapper, sin diferencias. No cambies pesos del modelo durante una extracción: cualquier cambio probabilístico debe tratarse como una modificación funcional separada y quedar rotulado como estimación.

### 8d octies. Primitivas Monte Carlo — resuelto en 3.8.27

`lpf_simulation.py` concentra la simulación de posición/puntos por zona, la matriz de puntos sumados en los pendientes y la máscara booleana de objetivos (playoffs, copas y descenso). Recibe fuerza y contexto por parámetro; no conoce Streamlit, sesión ni red.

`_sim_zone_rank_points` y `_sim_zone_pos` permanecen como wrappers para conservar firmas/call-sites y aportar la fuerza histórica desde `_fuerza_lpf`; `_sim_lpf_add` y `_obj_bool` se importan directamente del módulo puro. La extracción se comparó contra 3.8.26 en 500 casos de zona, 500 wrappers, 800 matrices globales y 900 máscaras de objetivos sin diferencias. No cambies `pdraw`, localía ni la semilla durante una extracción: cualquier ajuste probabilístico es un cambio funcional separado.

### 8d nonies. Contexto de simulación explícito — resuelto en 3.8.28

`lpf_simulation.build_simulation_context` concentra el armado estable que antes hacía `_lpf_ctx`: resuelve la Anual con fotos explícitas, reparte cupos con un reemplazo de Copa Argentina explícito y prepara `zona_de`, puntos/DG base, promedios y restantes. No lee sesión ni red.

`_lpf_ctx` conserva la firma histórica porque muchos call-sites de UI la usan, pero su único trabajo es resolver los fallbacks de Apertura, Anual directa y reemplazo de Copa Argentina desde la sesión y pasarlos al constructor puro. La equivalencia se verificó contra 3.8.27 en 500 estados dirigidos/aleatorios sin diferencias. Una futura API debe llamar al constructor puro con datos del snapshot, no emular `session_state`.

### 8d decies. Auditoría probabilística — corregido en 3.8.29

La app debe tener **un solo modelo probabilístico activo**. `lpf_simulation.match_outcome_probabilities` es el kernel canónico: 26% de empate y factor local 1,22. La fuerza canónica sale de `lpf_form.estimate_team_strength`. `lpf_competitive_context` puede conservar su regularización vieja sólo como fallback de compatibilidad si se lo llama aislado; los caminos activos de Streamlit deben pasarle la fuerza canónica explícita.

La auditoría de Fecha 4 encontró además que la simulación de una zona ignoraba el rival real en los interzonales y luego completaba ese partido contra un “rival promedio”. Desde 3.8.29, `simulate_zone_rank_points` procesa cualquier pendiente que afecte a la zona y usa la fuerza/localía del rival externo cuando está disponible. No reviertas esto para recuperar equivalencia con 3.8.28: es una corrección funcional respaldada por pruebas.

Se congeló una foto real del 11/08/2026 20:28 ART con 59 partidos completados. El backtest secuencial dio log-loss 1,037 para el modelo canónico y 1,057 para el camino editorial anterior. **No calibres parámetros con esa muestra**: cuatro fechas son insuficientes. El próximo ajuste de 26%/1,22 requiere un backtest histórico amplio y separado de cualquier refactor.

La mediana condicionada a un puesto debe publicar el tamaño de muestra. `lpf_simulation.summarize_rank_condition` marca como inestable una muestra menor a 100 corridas; la UI debe advertirlo. No ocultes ese aviso aunque la mediana “parezca razonable”.

### 8e. Promedios: contrato explícito — corregido en 3.8.31
`lpf_averages.py` separa dos conceptos que antes compartían el nombre ambiguo `prom`: `previous_averages` contiene sólo temporadas anteriores y `average_totals` contiene esos antecedentes más la Tabla Anual 2026 vigente. La Tabla Anual aporta tanto puntos como PJ de 2026; las zonas sólo sirven de respaldo si una foto legacy no trae PJ.

La corrección se auditó contra las fotos internas sincronizadas: **30/30 equipos** reproducen exactamente los totales Pts/PJ publicados. La fórmula anterior usaba PJ del Clausura junto con puntos de Apertura+Clausura y fallaba 30/30 denominadores. `lpf_pisos.promedio_totales` queda como wrapper de compatibilidad y `lpf_simulation` construye `average_totals` antes de evaluar descenso. No vuelvas a pasar temporadas previas directamente a un consumidor que espere totales.


### 8f. Releases verificables — resuelto en 3.8.32

`tools/release.py` elimina el armado manual de paquetes. `check` valida que la versión canónica, `pyproject.toml`, el runtime requerido por Streamlit y todos los componentes críticos estén sincronizados; también compila estáticamente los `.py` y exige que README/CHANGELOG publiquen la versión vigente.

Para construir artefactos:

```bash
python tools/release.py check
python tools/release.py build --output-dir /mnt/data --base-dir /ruta/a/la/version/anterior
```

El comando `build` genera siempre el ZIP completo y `sincronizacion-nucleo-X.Y.Z.zip`. Si recibe `--base-dir`, genera además el incremental y **fuerza** dentro de ese ZIP `calculadora_futbol_argentino.py`, `lpf_version.py`, `lpf_runtime.py` y todos los `CRITICAL_COMPONENTS`, aunque no hayan cambiado. Si detecta un archivo eliminado, no arma un incremental engañoso: obliga a usar el ZIP completo.

No vuelvas a armar estos ZIP con listas manuales. `LPF_RUNTIME_API` permanece en 13 en 3.8.32 porque esta mejora no cambia contratos de la app.

### 8g. CI automática — resuelto en 3.8.33

`.github/workflows/ci.yml` ejecuta en cada push/PR tres barreras obligatorias: suite completa, Ruff (`F,E9`) y `tools/release.py check`. No uses `continue-on-error` en esos pasos ni los conviertas en avisos opcionales: el objetivo es impedir que un commit con runtime/versión mezclados o una regresión llegue al deploy.

La CI instala `.[dev]` desde `pyproject.toml`, usa Python 3.11 y permisos de sólo lectura. No agrega dependencias al runtime de Streamlit. `LPF_RUNTIME_API` sigue en **13** porque este cambio es exclusivamente de entrega. Suite: **264 pruebas**.

### 8h. Previa por equipo pura — resuelto en 3.8.34

`lpf_preview.py` concentra el texto y la tabla exacta de la Previa por equipo. Recibe la ventana de `lpf_schedule`, los partidos que quedan abiertos, la Tabla Anual, `n_anual` y el contexto de copas ya resuelto; no importa Streamlit ni red. `lpf_previa_equipo_texto` queda como adaptador de sesión/agenda.

La extracción se comparó directamente contra 3.8.33 en Playoffs, Descenso y Copas, incluyendo Markdown, DataFrame y `attrs`, sin diferencias. No vuelvas a mover fallbacks de sesión al módulo puro: cualquier dato nuevo de UI debe resolverse antes y entrar por parámetro. `LPF_RUNTIME_API` sube a **14** y el módulo pasa a ser crítico. Suite: **269 pruebas**.

### 8i. Últimas fechas y chat editorial — resuelto en 3.8.35

El chat deja de ser un workspace principal y se embebe dentro de **Mesa de redacción → Consultas y chat**. No dupliques esa UI ni vuelvas a agregar un segundo botón de Chat libre: el objetivo es que las consultas libres sean una herramienta editorial, no una navegación paralela.

`render_definition_radar` pasa a ser el tablero de **Últimas fechas**. Reutiliza los motores existentes: Previa exacta para G/E/P, `point_ladder` para la escalera por puntaje y `lpf_otros_resultados_sim` para el impacto estimado de la otra cancha. No agregues fórmulas nuevas a esta vista; si cambia un cálculo, debe cambiar primero en su motor fuente. `LPF_RUNTIME_API` sigue en **14** porque sólo cambió la composición de UI. Suite: **272 pruebas**.

### 8j. Solver exacto filtra partidos ajenos — resuelto en 3.8.36

`point_ladder` recibe a menudo el fixture global aunque calcule una sola zona. Antes, partidos entre dos equipos de la otra zona inflaban `len(matches)` y podían apagar el MILP por límite aun cuando no movían ningún punto de la tabla. El motor ahora elimina sólo esos partidos totalmente ajenos y conserva cualquier interzonal que toque un equipo de `base`.

No vuelvas a filtrar por "ambos equipos dentro" porque eso borraría interzonales reales. La regla correcta es: **conservar el partido si al menos uno de sus equipos pertenece a la tabla calculada**. Esto alinea Puntos por objetivo, Escenarios, servicios y Radar sin cambiar firmas. `LPF_RUNTIME_API` sigue en **14**. Suite: **274 pruebas**.

### 8k. Copas: pisos sólo por Tabla Anual — resuelto en 3.8.37

Los pisos numéricos de Libertadores/Sudamericana responden únicamente a la ruta que depende de la **Tabla Anual**. No vuelvas a rotularlos como si agotaran todas las formas de clasificar: Clausura y Copa Argentina otorgan plazas por vías independientes que no se pueden expresar honestamente como un mínimo de puntos de la Anual.

Los equipos que ya tienen una plaza directa quedan fuera de `reducida`; eso **no significa que deban desaparecer** de Puntos por objetivo. Deben mostrarse como ya clasificados, sin mínimo de puntos y con una explicación de la vía directa. `LPF_RUNTIME_API` sigue en **14**. Suite: **279 pruebas**.

### 8l. Qué tiene que pasar + desempates de descenso — resuelto en 3.8.38

`lpf_conditionals.py` enumera **sólo la próxima fecha oficial relevante para una zona**. Para cada rama propia G/E/P cuenta exactamente los desenlaces de las otras canchas y separa: clasificación asegurada, pelea abierta, eliminación y posición al cierre de la fecha. Sus porcentajes son **frecuencia combinatoria**, nunca probabilidad. Si encuentra una condición suficiente de una o dos canchas, puede narrarla como “X no gana y Y pierde”; si no existe una regla corta, debe decirlo en vez de simplificar de más.

La UI vive en **Visualizaciones → Últimas fechas → Condicionales de un equipo**. Está disponible dentro de la ventana exacta de **8 partidos o menos** y con **4 o menos** se marca como **Modo definición**. El Monte Carlo de “qué otra cancha pesa más” sigue separado y rotulado ESTIMADO.

`lpf_relegation.py` es la fuente común para la foto “si terminara hoy”: una igualdad en una posición de descenso **no se rompe por DG**. Se informa partido desempate. Si el empate está en promedios, la plaza de la Anual puede quedar condicionada por quién termine bajando por esa primera vía. `LPF_RUNTIME_API` sube a **15** y ambos módulos pasan a críticos. Suite: **290 pruebas**.

---

## 9. Reglas de oro (no las rompas)

1. **Nunca cambies el resultado de un cálculo sin una prueba que lo justifique.** El
   valor del proyecto es su honestidad numérica.
2. **Toda extracción se prueba por equivalencia exacta contra el original** antes de
   darla por buena.
3. **Corré `ruff --select F,E9` y `pytest` después de cada cambio.** Ambos deben
   quedar limpios. El linter atrapa imports faltantes/sobrantes que el `py_compile`
   no ve.
4. **No metas Streamlit en los módulos puros.** Si una función necesita
   `st.session_state`, o se queda en el archivo principal, o recibe el dato como
   parámetro.
5. **Una sola fuente de verdad para la versión** (`lpf_version.__version__`). Si la subís,
   actualizá el CHANGELOG.
6. **No inventes datos.** Si falta una tabla, la app debe decirlo, no rellenar. Las
   estimaciones van siempre rotuladas y separadas de los hechos exactos.
7. **Mantené el DAG de módulos.** Un módulo nuevo importa de los existentes, nunca
   del archivo principal (evita ciclos).

---

## 10. Convenio de desempates (para no equivocarte en los cálculos)

- **Mínimo posible / mejor puesto / "puede clasificar"** → desempate **a favor**:
  sólo cuentan los rivales estrictamente por encima.
- **Garantía / peor puesto / "puede quedar afuera"** → desempate **en contra**:
  cuentan los rivales iguales o por encima.

Esto está verificado por fuerza bruta en `tests/test_lpf_scenarios.py` y
`tests/test_lpf_exact.py`. Si tocás el motor, esas pruebas te protegen.

---

## 11. Verificación de integridad de datos

`tests/test_data_pipeline.py` comprueba que el fixture calza con las nóminas (30
equipos, 16 partidos c/u, sin fantasmas) y que los datos llegan bien a la tabla y a
los pisos, incluido el camino real de carga (`cargar_lpf_todo`) a través de los
módulos extraídos y el constructor puro `lpf_state.build_lpf_state`. Si cambiás datos de la temporada o la reconciliación, estas
pruebas son tu control.

---

## 12. Definición de "listo para mejoras" (cuándo terminaste)

El trabajo está bien entregado cuando **todo** esto es cierto:

- [ ] `streamlit run calculadora_futbol_argentino.py` **levanta y anda**.
- [ ] `python -m pytest -q` pasa **todas** las pruebas.
- [ ] `ruff --select F,E9 *.py tests/*.py` dice **"All checks passed!"**.
- [ ] Cada módulo nuevo tiene **una responsabilidad clara**, un docstring, y **prueba
      de equivalencia** documentada contra el original.
- [ ] `CHANGELOG.md`, `ARCHITECTURE.md`, `tests/README.md` y este documento están
      **al día** con lo que hiciste.
- [ ] No quedó **código muerto** nuevo ni imports sin uso.
- [ ] Los **números de la app no cambiaron** (lo garantizan las pruebas de
      equivalencia y la suite).

"Listo para mejoras" significa que la próxima persona pueda agregar una función nueva
(por ejemplo, un objetivo o una vista) tocando **un módulo chico y testeable**, sin
tener que leer 11.000 líneas. Cada extracción que hagas acerca ese objetivo.

---

## 13. Resumen de un vistazo

- Meta: **que funcione**, **simplificar sin cambiar los números**, **dejarlo listo
  para mejoras**. En ese orden.
- Trabajá **de a un módulo por vez**, con calma.
- **Extraé → reimportá con el mismo nombre → linteá → probá equivalencia → testeá →
  documentá.**
- Lo fácil ya se hizo; lo que queda pide inyección de dependencias o separar lógica
  de presentación. El motor de ordenamiento, el constructor del estado LPF y la preparación determinística
  de cargas ya están extraídos. Las URLs HTML genéricas también quedaron separadas en
  3.8.14, la ventana ESPN quedó fuera de Streamlit en 3.8.15 y la secuencia de resultados de FutbolArgentino.com en 3.8.16, la agenda/alcance de la Previa en 3.8.21, la aplicación manual de resultados en 3.8.22, la Anual/cupos en 3.8.23, el contexto de copas en 3.8.24, la forma/fuerza de simulación en 3.8.26, las primitivas Monte Carlo en 3.8.27, el contexto explícito de simulación en 3.8.28 y la auditoría/unificación probabilística en 3.8.29 y el contrato explícito de promedios en 3.8.31. Desde 3.8.32 los releases se validan y empaquetan con `tools/release.py`, evitando listas manuales de núcleo; desde 3.8.33 GitHub ejecuta además tests, Ruff y ese guard automáticamente en cada push/PR; en 3.8.34 la Previa por equipo se extrae a `lpf_preview.py`, dejando en Streamlit sólo agenda y sesión. Football-data y Apify
  están confirmados como ramas deshabilitadas: no invertir trabajo ahí hasta que se
  reactiven. El próximo paso debe salir de una dependencia activa y comprobable; no
  crear una API ni un adaptador Opta hasta tener un consumidor real.
- No reescribas, no cambies el stack, no abstraigas de más.
- Ante la duda, la respuesta segura es **hacer menos y verificar más**.

### 8m. Previa y simulación visibles — corregido en 3.8.39

Las probabilidades publicables generales usan 6.000 simulaciones; la Previa expone próximo partido real, fecha oficial y fecha + postergados, y la simulación de playoffs conserva interzonales contra rivales reales. La narrativa diferencia PJ, partidos por jugar y puntos totales. Runtime **15**.

### 8n. Objetivo compartido y fecha específica — corregido en 3.8.40

El último objetivo consultado deja de ser una memoria exclusiva del chat: los selectores de Panel por equipo, Mesa de redacción, Visualizaciones y el explorador se sincronizan antes de crear sus widgets y actualizan `LPF_LAST_OBJECTIVE` por callback. Los atajos genéricos del chat respetan ese estado. Previa y “La otra cancha” pasan una fecha oficial explícita al resolvedor de `lpf_schedule`; no se reimplementa agenda en Streamlit. La herramienta de otra cancha tampoco publica recomendaciones si el objetivo internacional ya está cumplido por vía directa o si el club queda fuera del área de riesgo de descenso usada para ese análisis. Runtime **15**; suite **301 pruebas**.


### 8p. Explicación negativa y parcial — 3.8.42

`branch_explanation` debe explicar también por qué una rama no alcanza: si no asegura, distingue entre seguir abierto, terminar la fecha dentro del corte y quedar matemáticamente afuera. `lpf_conditionals` publica condiciones simples de eliminación suficientes/necesarias además de las favorables. La matriz general tiene explicación a demanda por equipo y G/E/P. Nunca llamar “clasificado” a quien sólo termina una jornada dentro del corte; nunca interpretar conteos de combinaciones como probabilidad. Runtime **16**; suite **312 pruebas**.

### 8o. Definición visual exacta — 3.8.41

`Visualizaciones → Últimas fechas` comparte el objetivo activo y construye una tabla de trabajo común para Playoffs, Libertadores por Tabla Anual o al menos Sudamericana por Tabla Anual. La vista muestra zona de pelea aun con el torneo abierto; para la fecha pendiente agrega matriz G/E/P multiseleccionable, semáforo compacto y doble entrada contra un rival elegido. `lpf_conditionals.key_rival_matrix` mantiene abiertas las demás canchas y enumera sus combinaciones; `branch_explanation` produce la capa “¿Por qué?” con una prueba auditable y no probabilística. El árbol reducido sólo abre ramas que cambian el estado y el reloj informa hitos demostrables; un total que asegura sólo se muestra cuando `point_ladder` lo comprobó exactamente. `lpf_editorial_definition.py` es puro y queda preparado para API/Opta. Runtime **16**; suite **309 pruebas**.

### 8q. Definición fuera de Streamlit — 3.8.43

- `lpf_editorial_definition.objective_context` arma el universo Playoffs/Copas con entradas explícitas; no leer sesión desde ese módulo.
- `definition_guarantee` y `guarantee_round_label` concentran la garantía y su primera fecha alcanzable.
- `definition_snapshot` es la salida JSON-safe común para otra interfaz. `lpf_services.calculate_definition` la expone sin red ni proveedores.
- Si una futura API usa Copas, debe alimentar el contexto de vías directas antes de pedir la definición; no recrear esa regla en HTTP.


### 8r. Selección explícita en Últimas fechas — 3.8.51

En `render_definition_radar` no mezclar los roles de equipos. El **equipo principal** se elige explícitamente; el **contexto automático** sólo ubica la pelea; los **comparadores** se agregan manualmente y nunca sustituyen al principal; la **otra cancha clave** es una sugerencia exacta editable. La matriz G/E/P debe conservar al principal como primera fila. En Copas, los clasificados por vía directa siguen disponibles en el selector para explicar que el objetivo ya está resuelto. Runtime **21**; suite **352 pruebas**.
