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
| `lpf_http.py` | Transporte HTTP puro de las fuentes públicas. No parsea datos ni importa Streamlit; la caché queda en el consumidor. |
| `lpf_provider_adapters.py` | Adaptadores puros de ESPN/FutbolArgentino.com: HTML/JSON ya descargado → tablas, zonas, resultados y metadatos del dominio. |
| `lpf_state.py` | Construcción pura del estado canónico LPF: selecciona/deriva Apertura, arma auditoría, Anual autoritativa, pendientes y metadatos sin leer Streamlit. |
| `lpf_scenarios.py` | Optimización exacta (MILP con `scipy.optimize.milp`): escalera de puntajes, rangos y ventanas con postergados. |
| `lpf_exact.py` | Núcleo determinístico y garantías conservadoras (línea segura, promedios). Validado por fuerza bruta. |
| `lpf_pisos.py` | **Puntos por objetivo.** Unifica el cálculo del mínimo con chances, la garantía exacta y la garantía conservadora para playoffs, copas y descenso. Reutiliza `lpf_scenarios` y `lpf_exact`; Python puro. |
| `lpf_competition_narratives.py` | Relatos de zonas, Libertadores, Sudamericana y descenso. |
| `lpf_competitive_context.py` | Contexto de tabla, cruces internos y proyección del corte. |
| `lpf_fixture_sources.py` | Parsers y validación de fuentes (FutbolArgentino.com, ESPN) sin inferir partidos por PJ. |
| `lpf_display.py` | Nombres periodísticos y edición de texto/tablas para la interfaz. |
| `lpf_text.py` | Utilidades de texto puras y sin dependencias (`_zlow`, `_norm_txt`, `detectar_equipo`, `detectar_equipos`), extraídas del archivo principal para poder probarlas aisladas. |
| `lpf_derive.py` | Derivación e inferencia de datos: reconstruye la foto del Apertura e infiere resultados faltantes fijados por la tabla. Pura. |
| `lpf_reconcile.py` | Reconciliación e integridad de datos entre las fuentes y los cálculos: ajusta resultados a las zonas, repara duplicados, avanza zonas, valida. Pura. |
| `lpf_data_2026.py` | Datos fijos de la temporada: fixture, nóminas de zona, foto del Apertura y el parser del fixture. Fuente autoritativa, módulo puro. |
| `lpf_standings.py` | Motor puro de posiciones y tablas (`_stats`, `_resolver`, `_orden`, `posiciones`, `tabla`, `liga_tabla_df`, `_liga_in_out`). Recibe los criterios de desempate como parámetro; no depende de Streamlit ni de una fuente de datos. |
| `lpf_parsers.py` | Parsers de tablas pegadas (`parse_tabla_anual`, `parse_promedios_tabla`, `parse_tabla_fixture`, ...): texto copiado → datos. Puros. |
| `lpf_clubs.py` | Canonicalización de nombres de clubes (`canon_club`, `canon_base`, `LPF_CLUBES`): traduce cualquier variante al nombre canónico. Capa de dominio pura. |
| `lpf_intents.py` | Ruteo de intención del chat (`_parse_kw`, `_pos_pedida`): traduce una consulta en lenguaje natural a un `{"intent": ...}`. Lógica pura; recibe la lista de equipos como parámetro. |
| `tests/` | Pruebas unitarias, de invariantes y comparación contra enumeración exhaustiva. |
| `legacy/` | Código archivado que la app ya no importa (p. ej. `calculadora_mundial.py`). |

## Flujo de datos

1. **Ingreso:** foto offline, actualización desde proveedor, o pegado manual. Para fuentes remotas, `lpf_http` hace sólo transporte y `lpf_provider_adapters` interpreta la respuesta sin tocar UI.
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
   - Garantía conservadora → `lpf_exact` para horizontes más grandes.
   - Piso por objetivo → `lpf_pisos`, que elige entre ambos según la ventana.
6. **Redacción y UI:** los renderizadores consumen los resultados estructurados.

## Frontera para futura API y proveedores externos

La aplicación debe conservar una frontera simple y estable:

`fuente (actual / Opta) → transporte → adaptador de proveedor → lpf_loading → estado LPF canónico → motores puros → API o Streamlit`

Reglas de esa frontera:

- Los motores de cálculo no importan Streamlit, `requests` ni SDKs de proveedores.
- Streamlit es un consumidor del motor. En el caso de posiciones, sus adaptadores sólo
  inyectan `CRITERIOS()` y delegan en `lpf_standings`.
- El transporte actual vive en `lpf_http` y los parsers/adaptadores de ESPN/FutbolArgentino.com en `lpf_provider_adapters`; ninguno conoce Streamlit. La caché de UI envuelve el transporte desde el archivo principal.
- La preparación previa vive en `lpf_loading`: `normalize_results_for_zones`, `prepare_offline_load` y `prepare_automatic_update` reciben y devuelven estructuras simples. Los fetchers quedan fuera de esa capa.
- El estado de cálculo se construye en `lpf_state.build_lpf_state`: Streamlit sólo aporta
  los valores de sesión y persiste la foto devuelta. Una API puede llamar a la misma función
  con datos ya normalizados, sin importar el archivo principal.
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
dos tablas: la Anual (exacta cuando entra en ventana) y los promedios (referencia conservadora por cocientes).

Para cada objetivo se devuelven tres números con significado distinto:

- **Mínimo posible:** menor puntaje con el que *todavía existe* una combinación
  favorable (desempate a favor).
- **Garantía exacta:** menor puntaje comprobado que asegura el objetivo sin depender de otros resultados ni de desempates (desempate en contra).
- **Referencia conservadora:** total seguro para ventanas grandes; si se alcanza asegura el objetivo, pero puede pedir puntos de más que la garantía exacta.


## Frontera de servicios de cálculo

`lpf_services.py` es una capa de aplicación fina y JSON-safe. No hace red, no conoce
Streamlit ni proveedores y no contiene fórmulas propias: valida/traduce payloads y
delega en `lpf_standings`, `lpf_scenarios` y `lpf_pisos`. Una futura API HTTP debe
llamar esta capa en vez de importar `calculadora_futbol_argentino.py`.

`lpf_version.py` contiene la única versión del motor y puede importarse desde cualquier
interfaz sin disparar UI. El contrato externo se versiona de forma independiente con
`lpf_services.CONTRACT_VERSION`. Ver `API_CONTRACT.md`.

La arquitectura objetivo queda:

`proveedor -> transporte -> adaptador -> loading/state -> motores -> services -> Streamlit/API`

Streamlit puede seguir llamando motores directamente mientras se migra gradualmente;
la existencia de `services` no obliga a reescribir la UI.

## Convenciones

- En interfaz y narrativa no se usa “cota”. La palabra "garantía" se reserva para líneas que no dependen de terceros ni de
  desempates.
- Las estimaciones (Monte Carlo, dificultad, corte probable) se publican siempre
  por separado y rotuladas como tales.
- La Tabla Anual pegada por el usuario es un control, no una segunda fuente viva.
