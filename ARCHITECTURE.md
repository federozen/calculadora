# Arquitectura

Este documento describe el flujo técnico y la separación de responsabilidades. La
regla de oro del proyecto: **los números salen siempre de Python determinístico;
el modelo de lenguaje, cuando está activo, sólo interpreta la consulta y redacta.**

## Módulos

| Módulo | Responsabilidad |
| --- | --- |
| `calculadora_futbol_argentino.py` | Aplicación Streamlit: UI, navegación, chat, y orquestación de todo lo demás. Es el punto de entrada. |
| `lpf_models.py` | Objetos de dominio (dataclasses), auditoría y resultados estructurados. No depende de Streamlit. |
| `lpf_data_quality.py` | Normalización y reconciliación de Zonas, Anual, Promedios, fixture y resultados antes de habilitar cuentas. |
| `lpf_loading.py` | Preparación pura de cargas: normaliza resultados de proveedores, reconcilia la foto offline/automática y prepara datos para el estado sin red ni Streamlit. |
| `lpf_http.py` | Transporte HTTP puro de las fuentes públicas. También arma la ventana multi-request de scoreboards ESPN sin parsear eventos. No importa Streamlit; la caché queda en el consumidor. |
| `lpf_provider_adapters.py` | Adaptadores puros de ESPN/FutbolArgentino.com: HTML/JSON ya descargado → tablas, zonas, resultados y metadatos del dominio. |
| `lpf_table_selection.py` | Política pura de prioridad/fallback entre tablas de proveedores, último respaldo y candidatos locales. No lee red, disco ni sesión. |
| `lpf_table_backup.py` | Serialización, persistencia atómica y recuperación del último respaldo válido de zonas + Anual. Conoce JSON/filesystem, pero no Streamlit ni proveedores. |
| `competition_html_adapters.py` | Parsers puros de URLs genéricas del modo avanzado: HTML ya descargado → tabla textual o matriz de jugados/pendientes. |
| `lpf_state.py` | Construcción y revalidación puras del estado canónico LPF: selecciona/deriva Apertura, migra fotos viejas, arma auditoría, Anual autoritativa, pendientes y metadatos sin leer Streamlit. |
| `lpf_scenarios.py` | Optimización exacta (MILP con `scipy.optimize.milp`): escalera de puntajes, rangos y ventanas con postergados; filtra partidos totalmente ajenos a la tabla pero conserva interzonales. |
| `lpf_exact.py` | Núcleo determinístico y garantías conservadoras (línea segura, promedios). Validado por fuerza bruta. |
| `lpf_pisos.py` | **Puntos por objetivo.** Unifica mínimo posible, total seguro y mínimo que asegura para playoffs, copas y descenso. Reutiliza `lpf_scenarios` y `lpf_exact`; Python puro. |
| `lpf_competition_narratives.py` | Relatos de zonas, Libertadores, Sudamericana y descenso. |
| `lpf_competitive_context.py` | Contexto de tabla, cruces internos y proyección del corte; usa el kernel/fuerza canónicos del Monte Carlo. |
| `lpf_conditionals.py` | Condicionales exactos de la próxima fecha: ramas G/E/P, estado final de la pelea, posición al cierre, palancas de otras canchas y condiciones simples; no asigna probabilidades. |
| `lpf_relegation.py` | Foto actual de descensos con desempates reglamentarios y regla de exclusión promedio→Anual; no usa DG para decidir una igualdad de descenso. |
| `lpf_fixture_sources.py` | Parsers y validación de fuentes (FutbolArgentino.com, ESPN) sin inferir partidos por PJ. |
| `lpf_schedule.py` | Agenda y calendario puros: normaliza horarios de proveedor a Argentina, resuelve jornada/postergados, ordena pendientes y define la ventana temporal de la Previa sin Streamlit. |
| `lpf_preview.py` | Previa pura por equipo: recibe ventana/escenarios/contexto ya resueltos y devuelve Markdown + tabla para playoffs, copas o descenso sin leer Streamlit. |
| `lpf_result_updates.py` | Aplicación pura de marcadores pendientes y cálculo de cambios de posiciones; no conoce Streamlit ni persistencia. |
| `lpf_averages.py` | Contrato puro de promedios: normaliza temporadas previas y construye totales acumulados con la Tabla Anual 2026; evita mezclar previas y totales. |
| `lpf_form.py` | Forma reciente, rachas y fuerza regularizada para simulaciones; recibe el Apertura por parámetro y no conoce Streamlit. |
| `lpf_simulation.py` | Monte Carlo puro, kernel único de probabilidades y constructor explícito de contexto: Anual/cupos, zona, suma de puntos y objetivos; recibe todas las fotos por parámetro. |
| `lpf_qualification.py` | Tabla Anual autoritativa, reparto de plazas y contexto puro de copas (clasificados fijos, vivos de Copa Argentina y etiqueta de actualización); no conoce Streamlit. |
| `lpf_display.py` | Nombres periodísticos y edición de texto/tablas para la interfaz. |
| `lpf_text.py` | Utilidades de texto puras y sin dependencias (`_zlow`, `_norm_txt`, `detectar_equipo`, `detectar_equipos`), extraídas del archivo principal para poder probarlas aisladas. |
| `lpf_derive.py` | Derivación e inferencia de datos: reconstruye la foto del Apertura e infiere resultados faltantes fijados por la tabla. Pura. |
| `lpf_reconcile.py` | Reconciliación e integridad de datos entre las fuentes y los cálculos: ajusta resultados a las zonas, repara duplicados, avanza zonas, valida. Pura. |
| `lpf_data_2026.py` | Datos fijos de la temporada: fixture, nóminas de zona, foto del Apertura y el parser del fixture. Fuente autoritativa, módulo puro. |
| `lpf_standings.py` | Motor puro de posiciones y tablas (`_stats`, `_resolver`, `_orden`, `posiciones`, `tabla`, `liga_tabla_df`, `_liga_in_out`). Recibe los criterios de desempate como parámetro; no depende de Streamlit ni de una fuente de datos. |
| `lpf_parsers.py` | Parsers de tablas pegadas (`parse_tabla_anual`, `parse_promedios_tabla`, `parse_tabla_fixture`, ...): texto copiado → datos. Puros. |
| `lpf_clubs.py` | Canonicalización de nombres de clubes (`canon_club`, `canon_base`, `LPF_CLUBES`): traduce cualquier variante al nombre canónico. Capa de dominio pura. |
| `lpf_intents.py` | Ruteo de intención del chat (`_parse_kw`, `_pos_pedida`): traduce una consulta en lenguaje natural a un `{"intent": ...}`. Lógica pura; recibe la lista de equipos como parámetro. |
| `lpf_runtime.py` | Verifica antes del arranque que los módulos críticos desplegados compartan el mismo nivel de compatibilidad interna, sin importarlos. |
| `tests/` | Pruebas unitarias, de invariantes y comparación contra enumeración exhaustiva. |
| `legacy/` | Código archivado que la app ya no importa (p. ej. `calculadora_mundial.py`). |

## Flujo de datos

1. **Ingreso:** foto offline, actualización desde proveedor, o pegado manual. Para fuentes remotas, `lpf_http` hace sólo transporte; `lpf_provider_adapters` interpreta ESPN/FutbolArgentino.com y `competition_html_adapters` interpreta las URLs HTML genéricas del modo avanzado, sin tocar UI. La prioridad entre tablas candidatas se resuelve en `lpf_table_selection`; la persistencia/recuperación del último respaldo válido vive en `lpf_table_backup`, sin acoplarse a Streamlit.
2. **Preparación (`lpf_loading`):** los resultados se canonicalizan contra las zonas y las distintas fuentes se combinan/reconcilian sin conocer Streamlit ni la red.
3. **Reconciliación y estado (`lpf_state` / `lpf_data_quality`):** se validan Zonas, se reconstruye la
   Tabla Anual desde la foto fija del Apertura más las zonas actuales, y se
   verifican promedios y fixture. Cada partido conserva identidad y estado; un
   postergado no se considera jugado por disputar una fecha posterior.
4. **Auditoría (`lpf_models`):** se emite un `DataQualityReport` con nivel
   (`ok` / `warning` / `blocked`) por dominio (playoffs, copas, promedios,
   descenso). Un problema en un dominio no bloquea los demás.
5. **Cálculo:**
   - Exacto → `lpf_scenarios` (MILP) para ventanas de hasta ocho fechas.
   - Total seguro → `lpf_exact` para horizontes más grandes.
   - Puntos por objetivo → `lpf_pisos`, que elige entre ambos según la ventana.
6. **Agenda y alcance (`lpf_schedule`):** la programación ya normalizada se combina con el fixture para decidir próximo partido/día, jornada operativa y postergados sin leer sesión.
7. **Actualización manual (`lpf_result_updates`):** un marcador confirmado actualiza una copia de las zonas y produce los cambios de puestos; Streamlit sólo reconstruye/persiste el estado.
8. **Anual y cupos (`lpf_qualification`):** resuelve la Anual autoritativa y el reparto de plazas internacionales desde datos explícitos, sin leer sesión.
9. **Forma y fuerza (`lpf_form`):** calcula forma, rachas y fuerza regularizada desde tablas/resultados/Apertura explícitos; las simulaciones no necesitan leer sesión para estimar fuerzas.
10. **Monte Carlo (`lpf_simulation`):** construye el contexto estable desde fotos explícitas y recibe fuerza, fixture/contexto y semilla para producir posiciones, puntos y máscaras de objetivo sin conocer Streamlit.
11. **Previa por equipo (`lpf_preview`):** consume ventana/partidos/contexto explícitos y produce relato + tabla de escenarios; Streamlit sólo aporta fallbacks de agenda y sesión.
12. **Condicionales de fecha (`lpf_conditionals`):** enumera la próxima jornada relevante y produce una matriz exacta sin probabilidades.
13. **Descenso actual (`lpf_relegation`):** separa descendidos confirmados de desempates y resuelve la duplicación promedio→Anual.
14. **Redacción y UI:** los renderizadores consumen los resultados estructurados.

## Frontera para futura API y proveedores externos

La aplicación debe conservar una frontera simple y estable:

`fuente (actual / Opta) → transporte → adaptador de proveedor → selección/reconciliación → estado LPF canónico → motores puros → API o Streamlit`

Reglas de esa frontera:

- Los motores de cálculo no importan Streamlit, `requests` ni SDKs de proveedores.
- Streamlit es un consumidor del motor. En el caso de posiciones, sus adaptadores sólo
  inyectan `CRITERIOS()` y delegan en `lpf_standings`.
- El transporte actual vive en `lpf_http` (incluidas la ventana de scoreboards ESPN y la secuencia de páginas de resultados de FutbolArgentino.com); los parsers/adaptadores de ESPN/FutbolArgentino.com viven en `lpf_provider_adapters` y las tablas HTML genéricas en `competition_html_adapters`; ninguno conoce Streamlit. La caché de UI envuelve el transporte desde el archivo principal.
- La prioridad entre zonas/Anual de ESPN, FutbolArgentino.com, respaldo y candidatos locales vive en `lpf_table_selection`. El JSON del último respaldo y su lectura/escritura atómica viven en `lpf_table_backup`; Streamlit sólo conserva opcionalmente una copia de sesión y decide cuándo pedir la persistencia.
- La preparación previa vive en `lpf_loading`: `normalize_results_for_zones`, `prepare_offline_load` y `prepare_automatic_update` reciben y devuelven estructuras simples. Los fetchers quedan fuera de esa capa.
- El estado de cálculo se construye en `lpf_state.build_lpf_state`: Streamlit sólo aporta
  los valores de sesión y persiste la foto devuelta. Una API puede llamar a la misma función
  con datos ya normalizados, sin importar el archivo principal.
- La revalidación defensiva de sesiones existentes vive en `lpf_state.refresh_lpf_quality_state`; recibe candidatos de Apertura/Anual, promedios, fixture, resultados y alertas por parámetro. Streamlit sólo persiste la migración devuelta.
- La agenda real se normaliza en `lpf_schedule`: una fuente futura (incluido Opta) puede aportar fechas/horas y la misma capa decide orden, jornada y postergados sin escribir `session_state`.
- La carga manual de marcadores usa `lpf_result_updates`: la misma regla de actualización PJ/GF/GA/DG/PTS puede reutilizarse desde otra interfaz antes de reconstruir el estado canónico.
- La Tabla Anual, el reparto de plazas y el contexto de copas viven en `lpf_qualification`: una API puede aportar Apertura/Anual/campeones, clasificados fijos, vivos de Copa Argentina y metadatos de actualización explícitos sin leer `session_state`.
- La forma, racha y fuerza regularizada viven en `lpf_form`: una API o simulador puede aportar tabla vigente, resultados y Apertura explícitos sin depender de `session_state`.
- Los antecedentes de promedios se normalizan en `lpf_averages`: `previous_averages` excluye 2026 y `average_totals` suma la Tabla Anual vigente con sus PJ reales.
- El contexto Monte Carlo se arma en `lpf_simulation.build_simulation_context`: Apertura, Anual directa, cupos/reemplazos, antecedentes de promedios y rest entran por parámetro; una API no necesita reproducir fallbacks de sesión.
- Una futura API debe importar `lpf_standings`, `lpf_scenarios`, `lpf_exact` y
  `lpf_pisos` directamente; no debe importar `calculadora_futbol_argentino.py`.
- Un futuro conector Opta debe resolver IDs/nombres, estados de partido y formatos del
  proveedor antes de la capa de cálculo, reutilizando la canonicalización del dominio.
- Las entradas al núcleo deben seguir siendo estructuras Python simples y
  serializables (equipos, partidos, tablas y criterios), para que después puedan
  mapearse a JSON sin reescribir la matemática.
- Si se crea una API, su esquema público se versiona por separado de los payloads del
  proveedor. Cambiar de fuente de datos no debe cambiar el contrato del cálculo.

No se agrega todavía un framework de API ni una interfaz genérica de proveedores:
primero se desacoplan dependencias reales y se prueban; la abstracción se incorpora
cuando exista el primer consumidor concreto.

## Puntos por objetivo (`lpf_pisos`)

Los objetivos "quedar por encima de un corte" comparten estructura: un conjunto de
equipos (`base`) y un corte (`corte`). Por eso una sola función, `piso_por_corte`,
resuelve playoffs (zona, corte 8), Libertadores (tabla reducida, corte de plazas)
y Sudamericana (reducida, corte ampliado). El descenso es el caso espejo y combina
dos tablas: la Anual (exacta cuando entra en ventana) y los promedios (total seguro por cocientes).

Para cada objetivo se devuelven tres números con significado distinto:

- **Mínimo posible:** menor puntaje con el que *todavía existe* una combinación
  favorable (desempate a favor).
- **Total seguro:** total suficiente para ventanas grandes; si se alcanza asegura el objetivo, pero puede pedir puntos de más.
- **Mínimo que asegura:** menor puntaje comprobado que asegura el objetivo sin depender de otros resultados ni de desempates (desempate en contra).



### Composición editorial de la UI (3.8.35)

**Mesa de redacción** concentra también las consultas libres: el explorador y el chat ya no son un workspace paralelo. Esto evita duplicar navegación sin mover el motor de preguntas ni las cuentas determinísticas.

**Visualizaciones → Últimas fechas** es una composición de motores existentes, no un motor nuevo: la tabla de definición usa estados/rangos exactos; G/E/P reutiliza `lpf_preview`; la escalera reutiliza `point_ladder`; y la otra cancha reutiliza el Monte Carlo canónico, rotulado como ESTIMADO. Cualquier cambio matemático debe hacerse en esos módulos fuente y no dentro de la vista.

Desde 3.8.36, `point_ladder` normaliza el fixture contra la tabla que recibe: un partido se conserva si **al menos uno** de sus equipos pertenece a `base`. Esto evita que una zona pague el costo MILP de la otra zona sin perder los interzonales que sí suman puntos.

Desde 3.8.37, los objetivos de copas basados en `piso_por_corte` se definen explícitamente como **vía Tabla Anual**. `reducida` representa a los clubes que todavía compiten por esas plazas; los clubes ausentes de `reducida` porque ya obtuvieron una plaza directa se muestran como clasificados, pero no se les fabrica un piso numérico. Las vías Clausura/Copa Argentina permanecen en el contexto de copas y narrativas, no dentro del solver de puntos.


### Verificación y empaquetado de releases

`tools/release.py` es una herramienta de mantenimiento, no una capa del runtime. Lee por AST `lpf_version.py`, `lpf_runtime.py` y `_REQUIRED_RUNTIME_API` del archivo principal; valida la coherencia del conjunto sin importar Streamlit ni los módulos sensibles. También construye el ZIP completo, el paquete de sincronización del núcleo y el incremental sobre una base explícita. El incremental siempre incluye bootstrap + `CRITICAL_COMPONENTS`, por lo que una mejora sólo de UI no puede dejar un runtime viejo en producción.

Desde 3.8.33, `.github/workflows/ci.yml` ejecuta esa verificación en GitHub junto con la suite y Ruff en cada push/PR. La CI es una barrera de entrega, no una dependencia del runtime: la app sigue pudiendo correr sin GitHub Actions.


## Frontera de servicios de cálculo

`lpf_services.py` es una capa de aplicación fina y JSON-safe. No hace red, no conoce
Streamlit ni proveedores y no contiene fórmulas propias: valida/traduce payloads y
delega en `lpf_standings`, `lpf_scenarios` y `lpf_pisos`. `lpf_snapshot.py` agrega una
foto canónica autocontenida de competencia construida desde `lpf_state`, para que una
misma entrada pueda alimentar varias consultas sin reconstruir datos por fuera. Una
futura API HTTP debe llamar estas capas en vez de importar `calculadora_futbol_argentino.py`.

`lpf_version.py` contiene la única versión del motor y puede importarse desde cualquier
interfaz sin disparar UI. El contrato externo se versiona de forma independiente con
`lpf_services.CONTRACT_VERSION`. Ver `API_CONTRACT.md`.

La arquitectura objetivo queda:

`proveedor -> transporte -> adaptador -> loading/state -> snapshot -> motores/services -> Streamlit/API`

Streamlit puede seguir llamando motores directamente mientras se migra gradualmente;
la existencia de `services` no obliga a reescribir la UI.

## Compatibilidad de despliegue

Los módulos cuyo contrato cruza capas publican `LPF_RUNTIME_API`; desde 3.8.15 también `lpf_http.py`, porque Streamlit importa sus orquestadores de transporte. En 3.8.16 el nivel subió a **2** al agregarse la secuencia requerida de resultados de FutbolArgentino.com, en 3.8.19 subió a **3** por `lpf_state.refresh_lpf_quality_state` y en 3.8.21 subió a **4** al incorporar `lpf_schedule.py` como dependencia activa de la Previa, en 3.8.22 subió a **5** al incorporar `lpf_result_updates.py` para la carga manual de resultados y en 3.8.23 subió a **6** al incorporar `lpf_qualification.py` para Anual/cupos, en 3.8.24 subió a **7** porque Streamlit importa también sus helpers de contexto de copas y en 3.8.25 subió a **8** porque la UI requiere `lpf_scenarios.can_finish_exact_rank_by_points` y en 3.8.26 sube a **9** al incorporar `lpf_form.py` como dependencia activa del modelo de simulación; en 3.8.27 sube a **10** al incorporar `lpf_simulation.py` como frontera Monte Carlo pura y en 3.8.28 sube a **11** porque Streamlit importa también su constructor explícito de contexto de simulación y en 3.8.29 sube a **12** al unificar `lpf_competitive_context.py` con el kernel/fuerza canónicos del Monte Carlo; en 3.8.31 sube a **13** al incorporar `lpf_averages.py` y separar previas de totales de promedios; en 3.8.34 sube a **14** al incorporar `lpf_preview.py` como dependencia activa de la Previa por equipo; en 3.8.38 sube a **15** al incorporar `lpf_conditionals.py` y `lpf_relegation.py` como dependencias activas de Últimas fechas y descenso; en 3.8.41 sube a **16** al incorporar `lpf_editorial_definition.py` y la matriz/proof exacta consumida por la UI de definición. `lpf_runtime.py`
lee esos marcadores directamente desde los archivos, antes de que Streamlit importe
el motor. Si un deploy manual mezcla módulos viejos y nuevos, la app se detiene con
un diagnóstico de archivos desincronizados. El nivel de runtime no reemplaza
`lpf_version.__version__`: la versión identifica la entrega; el nivel sólo cambia si
se rompe compatibilidad entre módulos.

## Convenciones

- En interfaz y narrativa no se usa “cota”. La palabra "garantía" se reserva para líneas que no dependen de terceros ni de
  desempates.
- Las estimaciones (Monte Carlo, dificultad, corte probable) se publican siempre
  por separado y rotuladas como tales.
- La Tabla Anual pegada por el usuario es un control, no una segunda fuente viva.


## Contrato de snapshot y futura API

Desde 3.8.13 la foto canónica declara `snapshot_schema_version` de manera independiente
de `contract_version` y de `calculation_version`. `lpf_services` valida las invariantes
estructurales antes de ejecutar consultas batch y publica `service_capabilities()` para
que una futura capa HTTP u Opta pueda negociar el formato soportado sin acoplarse a
Streamlit. El batch sigue siendo stateless y no persiste snapshots en servidor.


### Lectura de puntos condicionada al puesto (3.8.25)

En **Escenarios → Puntos y puesto final**, la pregunta práctica “con cuántos puntos suele terminar N.º” se responde con la misma simulación de zona, pero conservando también los puntos finales de cada corrida. La estadística se condiciona a `puesto == objetivo`: mediana y cuantiles se calculan sólo sobre esas corridas. Los extremos de factibilidad matemática se consultan aparte mediante `can_finish_exact_rank_by_points`, que no modela marcadores futuros y por eso exige ausencia de empate en puntos para afirmar un puesto exacto.

