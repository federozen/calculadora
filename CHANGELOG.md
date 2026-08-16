## 3.8.62 · 2026-08-16

- Corrige el caso real posterior a 3.8.61: una base validada de 49 resultados frente a una tabla que implica 67 partidos requiere conciliar 18 faltantes, por lo que el antiguo límite fijo de 16 bloqueaba antes de intentar una solución.
- `_lpf_infer_missing_results` deja de usar un tope fijo de partidos y pasa a un presupuesto determinístico de **250.000 estados de búsqueda**. Se mantienen las guardas de máximo 2 PJ nuevos por club, fechas oficiales consecutivas y validación final exacta de PJ/puntos/GF/GC/DG.
- Si la búsqueda supera el presupuesto, no infiere; si aparecen dos soluciones compatibles, tampoco infiere y devuelve un diagnóstico explícito de ambigüedad.
- Nueva regresión `49 → 67`: completa Fecha 4 + siete partidos de Fecha 5 y reconstruye exactamente 18 marcadores cuando la solución es única. El caso de dos fechas completamente ambiguas sigue fallando cerrado.
- Mejora el diagnóstico de fuentes en Streamlit: errores de ESPN/FutbolArgentino y filas recibidas pero descartadas por normalización se muestran en el error principal, en vez de quedar resumidos sólo como `aportó 0`.
- Public Service v1, DataProvider v2, Snapshot schema 3 y Runtime API 21 siguen estables.

## 3.8.61 · 2026-08-15

- Corrige la actualización transaccional cuando el standings se adelanta a los feeds de resultados: la conciliación determinística ahora puede completar una base validada con varios partidos nuevos, incluso si abarcan dos fechas consecutivas.
- `_lpf_infer_missing_results` compara la tabla nueva contra la base validada y busca una **única** combinación de fixture + marcadores que reproduzca exactamente PJ, puntos, GF, GC y DG de todos los clubes.
- Guardas conservadores: como máximo 16 partidos por actualización, como máximo 2 PJ nuevos por club, sólo una ventana de fechas oficiales consecutivas desde la primera fecha pendiente y rechazo inmediato ante una segunda solución compatible.
- Agrega regresión del caso `49 → 61`: cuatro partidos de Fecha 4 ya estaban en la base, se completan los otros once y además Racing-Banfield de Fecha 5; con feeds vacíos se reconstruyen exactamente los 12 faltantes si la tabla los fija de forma unívoca.
- El diagnóstico de cobertura deduplica candidatos idénticos: si FutbolArgentino.com y ESPN aportan la misma foto vacía/incompleta, no imprime dos veces las mismas diferencias.
- Sigue siendo transaccional: si la reconstrucción no es exacta o única, `played` queda vacío para esa actualización y la base válida anterior no se reemplaza.
- Public Service v1, DataProvider v2, Snapshot schema 3 y Runtime API 21 siguen estables.

## 3.8.60 · 2026-08-14

- Corrige el caso real de Copas con muchas otras canchas: la matriz G/E/P ya no queda en `—` cuando `next_round_conditionals` supera el límite corto de 8 partidos ajenos.
- Nuevo fallback exacto `exact_objective_result_states`: usa MILP sobre el fixture pendiente completo y resuelve seis pruebas de factibilidad (garantía/eliminación para G/E/P) sin enumerar `3^N` combinaciones.
- El fallback exige cobertura completa del fixture para la tabla analizada; si `rest` y los partidos pendientes no coinciden, no publica un cierre matemático.
- `Últimas fechas` deja de cortar el flujo cuando la enumeración detallada no está disponible: termómetro, heatmap de Copas e impacto estimado de otras canchas siguen visibles.
- La doble entrada, árbol y ranking exacto de otras canchas siguen usando enumeración corta porque necesitan descomponer combinaciones; no se reemplazan por probabilidades.
- `Visualizaciones → Copas y descenso` reutiliza el mismo fallback MILP, evitando que una entrada muestre G/E/P y la otra vuelva a dejar guiones.
- Public Service v1, DataProvider v2, Snapshot schema 3 y Runtime API 21 siguen estables.

## 3.8.59 · 2026-08-14

- Corrige la paridad visual de Copas: `Visualizaciones → Copas y descenso` muestra ahora **Qué pasa si gana, empata o pierde · EXACTO** para Libertadores/Sudamericana.
- La matriz G/E/P reutiliza el contrato `definition` y la misma especificación visual que Playoffs; no crea una segunda lógica de clasificación.
- Para clubes con objetivo ya resuelto por vía directa, la matriz conserva las tres ramas y las marca como **YA CLASIFICADO / OBJETIVO CUMPLIDO**, porque G/E/P ya no modifica el cupo.
- El termómetro individual se muestra también cuando el objetivo está resuelto: usa una marca exacta al 100% y texto `OBJETIVO RESUELTO`, no una falsa simulación de 6.000 casos.
- `Últimas fechas` ya no corta sin visuales ante una vía directa: conserva G/E/P, medidor de estado y acceso al heatmap comparativo de Copas.
- Heatmap y otra cancha estimada de 3.8.58 permanecen sin cambios. Public Service v1, DataProvider v2, Snapshot schema 3 y Runtime API 21 siguen estables.

## 3.8.58 · 2026-08-14

- Da paridad visual a **Libertadores/Sudamericana**: `Visualizaciones → Copas y descenso` deja de ser casi sólo narrativa y suma tablero de Tabla Anual.
- Nuevo **Mapa de cupos si la temporada terminara hoy · EXACTO**: distingue Libertadores por vía directa, Libertadores por Tabla Anual, Sudamericana por Tabla Anual y fuera de cupos hoy, sin presentar esa foto como clasificación matemática definitiva.
- Nuevo **Mapa de probabilidades de Copas · ESTIMADO** con escala continua rojo→amarillo→verde y porcentaje explícito por celda para Libertadores, Sudamericana específica y al menos una copa.
- El equipo seleccionado conserva su termómetro estimado; la cifra destacada sigue pasando por `objective_chances` y la tabla comparativa conserva el simulador contextual ya documentado.
- `Últimas fechas` muestra el mismo heatmap de Copas al calcular chances y deja de mandar la **otra cancha de Copas** a otra pestaña: ahora incluye barras de impacto y cruces futuros en la misma pantalla.
- Los visuales de Copas reutilizan `lpf_chances_obj`, `lpf_conviene_obj` y la asignación canónica de cupos; no duplican reglas de clasificación.
- Public Service v1, DataProvider v2, Snapshot schema 3 y Runtime API 21 sin cambios.

## 3.8.57 · 2026-08-14

- Corrige `Panel por equipo → Qué necesita para alcanzar el objetivo`: el informe editorial largo vuelve a ser la salida principal.
- Centraliza la narrativa en `_lpf_editorial_need_text`, compartida por Panel por equipo y Últimas fechas.
- Mantiene `_lpf_service_need_text` como resumen operativo secundario, plegado, para API/auditoría.
- `Resumen completo` reutiliza la misma narrativa larga y deja de depender del resumen público salvo para auditoría secundaria.
- Agrega regresiones estáticas que fijan la precedencia del informe largo y la fuente editorial única.
- Public Service v1, DataProvider v2, Snapshot schema 3 y Runtime API 21 sin cambios. Suite final: **367 pruebas**.

## 3.8.56 · 2026-08-14

- Restaura en `Últimas fechas` el informe editorial largo por equipo que había quedado desconectado al priorizar el nuevo tablero visual.
- El informe queda visible antes de las visualizaciones, no dentro de un expander.
- Reutiliza los generadores editoriales existentes para Playoffs y Copas, preservando una sola fuente de verdad.
- Mantiene íntegros grilla G/E/P, mapa de puestos, cara a cara, doble entrada, árbol, partidos bisagra, reloj y chances estimadas.
- Agrega una regresión de UI para impedir que futuras reorganizaciones vuelvan a eliminar el informe del flujo de `Últimas fechas`.

## 3.8.55 · 2026-08-13

### Hotfix de Session State y visuales tipo Mundial

- Corrige `StreamlitAPIException` en `Últimas fechas`: los botones de comparadores ya no escriben el key del `multiselect` después de que el widget fue instanciado; usan callbacks seguros antes del rerun.
- Añade **Mapa de puestos después de esta fecha · EXACTO** para principal y comparadores.
- Añade **Cara a cara** visual usando el mismo motor G/E/P exacto.
- `Partidos que más definen` suma una barra visual de sensibilidad exacta, inspirada en el partido bisagra del Mundial.
- El termómetro de chances del Mundial queda visible como bloque separado **ESTIMADO**, alimentado por `objective_chances` con 6.000 simulaciones.
- 364 tests. Runtime API 21, Public Service v1, DataProvider v2 y Snapshot schema 3 sin cambios.

## 3.8.54 · 2026-08-13

### Developer / Production Bootstrap

- Se agrega `api/` con una capa FastAPI delgada para las siete operaciones públicas, `/health`, `/ready` y `/v1/capabilities`. `ContractError` se traduce a HTTP 422 y no se replica matemática.
- Staging puede usar `LPF_SNAPSHOT_FILE`; producción puede construir `create_app(snapshot_loader=...)` con un loader Opta/cache sin cambiar endpoints.
- Nuevo `providers/opta.py` con fronteras `OptaTransport` y `OptaNormalizer`; `OptaProvider` termina obligatoriamente en `ProviderData`.
- Se corrige el empaquetado Python: Setuptools recibe módulos/paquetes explícitos y deja de confundir `legacy`/`data` con runtime. Streamlit pasa al extra `ui`; FastAPI al extra `api`.
- Se suman `Dockerfile.api`, `.dockerignore`, `.env.example`, `Makefile`, `tools/build_snapshot.py`, `tools/smoke_api.py`, `tools/production_acceptance.py` y `tools/build_runtime_bundle.py`.
- Acceptance kit con **7 casos dorados**, uno por operación pública, y prueba de equivalencia OptaProvider/CurrentProvider por `snapshot_id`.
- No cambian Public Service v1, DataProvider v2, snapshot schema 3 ni Runtime API 21. Suite final: **361 pruebas**; acceptance kit y build de wheel OK.

## 3.8.53 · 2026-08-13

### Configuración completa antes del análisis

- `Visualizaciones -> Últimas fechas` deja de ocultar decisiones detrás de la selección del equipo principal. Objetivo, zona, principal, comparadores y otra cancha aparecen en un único bloque de configuración.
- Comparadores y otra cancha permanecen visibles desde el inicio en estado deshabilitado; se activan al elegir un equipo con el objetivo abierto.
- La UI separa explícitamente **Configurá el tablero** de **Resultado del análisis**. Contexto automático, G/E/P, doble entrada, árbol, ranking exacto y reloj quedan sólo en la segunda sección.
- La otra cancha se configura arriba como `Automática` o como partido manual; la sugerencia automática conserva el criterio de sensibilidad exacta.
- Se agrega una regresión de orden visual que impide volver al flujo wizard progresivo.
- Cambio de UI/composición: Public Service v1, DataProvider v2, snapshot schema 3 y Runtime API **21** permanecen sin cambios.
- Suite: **353 pruebas**.

## 3.8.52 · 2026-08-13

### Cierre visual de Últimas fechas con doble entrada por partido

- La matriz general G/E/P pasa a una grilla visual tipo Mundial con estados exactos coloreados y el equipo principal marcado; el detalle completo/exportable queda en un expander.
- La segunda dimensión de la doble entrada cambia de **equipo rival** a **partido de la otra cancha**. Las columnas se leen como `gana local / empate / gana visitante`, evitando seleccionar dos veces protagonistas distintos.
- Se conserva la sugerencia automática, pero ahora ordena partidos completos por sensibilidad exacta; el editor puede elegir cualquier otra cancha de la fecha.
- Nuevo bloque `Partidos que más definen`: ranking exacto derivado de los `levers` ya enumerados, expresado como cantidad de caminos favorables que cambian, no como probabilidad.
- `¿Por qué?` sigue disponible para la matriz general, cada celda de la doble entrada y el resumen G/E/P; árbol reducido, Zona de pelea y Reloj se mantienen.
- Cambio de UI/composición: Public Service v1, DataProvider v2, snapshot schema 3 y Runtime API **21** permanecen sin cambios.
- Suite: **352 pruebas**.

## 3.8.51 · 2026-08-13

### Selección explícita de equipo y roles claros en Últimas fechas

- `Visualizaciones → Últimas fechas` empieza sin equipo principal implícito: el editor debe elegirlo explícitamente.
- Se distinguen cuatro fuentes de clubes visibles: principal manual, contexto automático alrededor del corte, comparadores manuales y otra cancha clave sugerida/editable.
- La matriz G/E/P mantiene siempre al principal como primera fila y el multiselect sólo contiene otros equipos (`Comparar también con…`). Los sugeridos no se agregan solos.
- La doble entrada muestra orientación explícita `principal ↓ / otra cancha →` y rotula filas/columnas.
- Los clasificados por vía directa a Copas pueden seleccionarse y se muestran como objetivo resuelto; la UI ya no los reemplaza silenciosamente por otro club.
- Cambio sólo de UI/composición: Public Service v1, DataProvider v2, snapshot schema 3 y Runtime API **21** permanecen sin cambios.
- Suite: **352 pruebas**.

## 3.8.50 · 2026-08-13

### Trazabilidad/frescura del snapshot y paquete de handoff

- `lpf_snapshot.py` publica **snapshot schema 3** con `traceability_version = 1`: `snapshot_id`, hora de construcción, proveedor, procedencia, cobertura y resumen de calidad. El ID se calcula sólo sobre contenido competitivo para comparar fotos entre fuentes.
- `lpf_data_provider.py` sube a **DataProvider v2** y suma `ProviderData.provenance`; v1 sigue declarado como soportado. `CsvProvider` completa procedencia desde nombres/mtime de archivos si el caller no informa metadata.
- `prepare_competition_snapshot()` propaga la procedencia al snapshot y `validate_competition_snapshot()` exige trazabilidad sólo en schema 3. Snapshots schema 1/2 siguen aceptados dentro de sus capacidades históricas.
- **Datos y auditoría** muestra snapshot ID, fuente, timestamp/edad si se conoce, cobertura del fixture/resultados y bloqueos; una fuente sin timestamp queda explícitamente como antigüedad desconocida.
- La carga automática registra procedencia y hora de consulta; la carga offline/manual no inventa un timestamp de origen.
- Nuevo `HANDOFF_DESARROLLO.md` para entregar el repositorio: superficie pública v1, DataProvider v2, snapshot schema 3, checklist Opta, comandos de CI/release y excepciones todavía deliberadas.
- `LPF_RUNTIME_API` sube a **21** porque proveedor, snapshot, servicios y Streamlit comparten el nuevo contrato de trazabilidad. Public Service permanece en **v1**.
- Suite: **351 pruebas**. `tools/release.py check` OK; Ruff no está instalado en el entorno de construcción local.

## 3.8.49 · 2026-08-13

### DataProvider común para desacoplar definitivamente la fuente de datos

- Nuevo `lpf_data_provider.py` con contrato `DataProvider` v1 y objeto `ProviderData` JSON-safe. La salida canónica cubre zonas, jugados, Tabla Anual, Apertura, antecedentes de promedios, fixture, vías de clasificación y reglas.
- `CurrentProvider` adapta el estado/fuente actual de Streamlit; `_lpf_service_snapshot_payload` pasa obligatoriamente por esta capa antes de `prepare_competition_snapshot`.
- `CsvProvider` agrega una fuente reproducible de referencia con validación de columnas, canonicalización de clubes, resultados, fixture e inferencia de interzonales. Una misma foto Current/CSV se prueba por equivalencia de snapshot.
- `service_capabilities()` publica `data_provider_contract_version = 1` y `current/csv` como implementaciones de referencia. Public Service permanece en v1.
- Un futuro Opta sólo debe implementar `load() -> ProviderData`; no incorpora SDK ni reglas de torneo en motores/servicios. `LPF_RUNTIME_API` sube a **20** y `lpf_data_provider.py` entra al núcleo crítico. Suite: **346 pruebas**.

## 3.8.48 · 2026-08-13

### Streamlit consume la frontera pública v1

- La **Previa** usa `lpf_services.calculate("preview")` como ruta principal; el adaptador legacy queda sólo como fallback explícito.
- **Visualizaciones → Últimas fechas** obtiene zona de pelea, matriz general, G/E/P, garantía, escalera y reloj desde `calculate("definition")`. La matriz de rival clave conserva por ahora su helper exacto directo para no recalcular el paquete completo.
- **Puntos por objetivo** y la foto/pisos de **Descenso** consumen `objective_points`, `relegation`, `standings` y `competition_batch`; `Qué necesita para alcanzar el objetivo` usa la misma lectura JSON del contrato público.
- En la Mesa de redacción, la cifra destacada de chances de **Playoffs/Copas** sale de `objective_chances` con 6.000 simulaciones. Las tablas comparativas completas y la probabilidad de descenso conservan temporalmente el simulador contextual directo.
- **Datos y auditoría** incorpora un bloque que muestra la versión del contrato/snapshot, las rutas migradas y cualquier fallback de compatibilidad registrado en la sesión.
- Se agregan guardas de arquitectura para impedir que Previa/definición/puntos regresen silenciosamente a llamadas directas. `PUBLIC_SERVICE_VERSION` permanece en **1** y `LPF_RUNTIME_API` en **19**. Suite: **340 pruebas**.

## 3.8.47 · 2026-08-13

### Superficie pública mínima para una futura API

- Se congela `PUBLIC_SERVICE_VERSION = 1` con siete operaciones estables en `lpf_services.calculate()`: `standings`, `preview`, `objective_points`, `objective_chances`, `definition`, `relegation` y `competition_batch`.
- Las integraciones nuevas usan snapshot como entrada preferida. Los helpers legacy (`objective_floor`, `point_ladder`, `rank_window`, etc.) siguen disponibles por compatibilidad pero dejan de ser el contrato recomendado para HTTP/Opta.
- `preview` reutiliza `lpf_preview` y `lpf_schedule` y convierte la tabla de escenarios a objetos JSON; no filtra pandas fuera de la frontera.
- `objective_chances` reutiliza `lpf_competitive_context` + fuerza canónica, usa **6.000 simulaciones por defecto** y separa explícitamente `estimated=true` de `definition`, que permanece exacto. Las plazas directas se resuelven en 100% sin simular.
- `relegation` reúne foto actual + piso/garantía opcional por equipo; si faltan antecedentes de promedios publica `complete=false` en vez de presentar una conclusión combinada incompleta.
- `service_capabilities()` agrega `public_service_version` y `public_operations`. `LPF_RUNTIME_API` permanece en **19** porque no cambia el contrato que consume Streamlit entre módulos críticos. Suite: **335 pruebas**.

## 3.8.46 · 2026-08-13

### Comparaciones editoriales sin selecciones heredadas

- La **Matriz de la fecha** deja de precargar automáticamente varios clubes: al abrirla sólo selecciona el **equipo bajo la lupa**. Los equipos cercanos al club y al corte aparecen como sugerencias visibles, pero no se marcan solos.
- La clave de estado del multiselect incorpora el equipo bajo la lupa, de modo que cambiar de club no arrastra una selección de comparadores hecha para otro equipo.
- El selector de **Matriz de rival clave** se rotula como `Rival sugerido (editable)` y aclara que la propuesta automática surge de sensibilidad exacta de la fecha, no de azar.
- `LPF_RUNTIME_API` permanece en **19**: es una corrección de interfaz y estado, sin cambios en el contrato entre módulos críticos. Suite: **328 pruebas**.

## 3.8.45 · 2026-08-13

### Definición por objetivo directamente desde el snapshot

- `lpf_services.calculate_definition()` suma modo snapshot: con `snapshot`, `team`, `objective` y `round`/`fecha` resuelve automáticamente base, corte, pendientes y fixture; Playoffs sólo requiere `zone`. El modo legacy `base + cutoff` se conserva.
- `competition_batch` incorpora `type=definition`, reutilizando exactamente el mismo resolvedor de objetivo/fecha y sin duplicar reglas de Copas.
- La fecha explícita se valida contra los pendientes del snapshot; si se omite, se usa la jornada operativa vigente. Un objetivo ya resuelto por vía directa se devuelve antes de correr la enumeración exacta.
- **Últimas fechas** agrega una guía visible que indica dónde abrir `🔍 ¿Por qué?`: matriz general, matriz de rival clave y explicación G/E/P del equipo bajo la lupa.
- `LPF_RUNTIME_API` sube a **19** porque la fachada de servicios y el resolvedor de calendario comparten ahora el contrato de definición desde snapshot. Suite: **328 pruebas**.

## 3.8.44 · 2026-08-13

### Snapshot schema 2 con objetivos de Playoffs y Copas

- `lpf_snapshot.py` incorpora `qualification` con el universo y corte efectivo de **Playoffs, Libertadores y al menos Sudamericana**. Para Copas guarda la Anual elegible después de retirar vías directas ya resueltas, sus motivos y los avisos de plazas todavía abiertas.
- Las reglas de formato (`opening_rounds`, `playoff_cutoff`, `sudamericana_slots`) quedan separadas de las reglas de descenso dentro del snapshot. Los campeones y reemplazos que determinan vías directas quedan en `qualification_inputs`.
- `lpf_services.competition_batch` agrega `objective_status` y acepta `objective` en consultas de objetivo, escalera o rango. El consumidor ya no necesita fabricar una tabla reducida ni repetir el `cutoff`; para Playoffs sólo debe indicar la zona.
- Si el equipo ya obtuvo Libertadores por una vía directa, la consulta devuelve un estado resuelto y el motivo. En el objetivo de al menos Sudamericana, una plaza de Libertadores se reconoce como objetivo superior ya cumplido.
- `snapshot_schema_version` sube a **2**, pero schema 1 sigue admitido para las consultas legacy. `service_capabilities()` publica las versiones de snapshot aceptadas y los objetivos disponibles.
- `LPF_RUNTIME_API` sube a **18** porque `lpf_snapshot` y `lpf_services` comparten el nuevo contrato de objetivos. Suite: **323 pruebas**.

## 3.8.43 · 2026-08-13

### Definición desacoplada de Streamlit y lista para otra interfaz

- `lpf_editorial_definition.py` incorpora un **contexto puro de objetivo** para Playoffs, Libertadores y al menos Sudamericana: recibe zonas, Apertura/Anual y vías directas por parámetro, y devuelve la tabla efectiva + corte sin leer sesión.
- La garantía exacta y la **primera fecha oficial en que puede alcanzarse** también salen de helpers puros; Streamlit queda como adaptador de sesión/calendario en vez de contener esa lógica.
- Nuevo `definition_snapshot`: empaqueta zona de pelea, matriz G/E/P seleccionable, informe del equipo, rival clave opcional, mínimo que asegura y reloj de definición en una estructura JSON-safe y sin probabilidades.
- `lpf_services.calculate_definition()` expone ese paquete a una futura API sin importar Streamlit ni proveedores. Para Copas, el consumidor entrega la Tabla Anual reducida por las vías directas vigentes; el contrato sigue siendo aditivo y mantiene `CONTRACT_VERSION = 1`.
- `LPF_RUNTIME_API` sube a **17** porque Streamlit y la fachada de servicios requieren nuevas funciones de `lpf_editorial_definition.py`; el núcleo debe desplegarse completo. Suite: **317 pruebas**.

## 3.8.42 · 2026-08-13

### “¿Por qué?” también explica lo que no alcanza

- La capa exacta **“¿Por qué?”** deja de explicar sólo garantías o eliminaciones totales: ahora también cuenta por qué un G/E/P **no asegura por sí solo**, aunque todavía mantenga vivo el objetivo.
- Los condicionales calculan también condiciones simples **suficientes/ necesarias para quedar afuera**. Si existe una combinación adversa que vuelve inalcanzable el objetivo, la explicación la muestra sin convertirla en probabilidad.
- Se corrige una distinción didáctica importante: **terminar la fecha dentro del corte por puntos no equivale a haber asegurado Playoffs o Copas**. La explicación lo dice explícitamente cuando el campeonato sigue abierto.
- La **matriz general de equipos** suma su propio expander “¿Por qué?”, seleccionando equipo y G/E/P; la doble entrada de rival clave y el equipo bajo la lupa conservan la misma prueba auditable.
- `LPF_RUNTIME_API` permanece en **16**: se amplía de manera retrocompatible la prueba de `lpf_conditionals.py`, sin agregar una nueva dependencia crítica. Suite: **312 pruebas**.

## 3.8.41 · 2026-08-13

### Definición visual exacta y explicación auditable

- **Zona de pelea** queda visible también con el torneo abierto: recorta la tabla alrededor del equipo y del corte, con puntos, partidos por jugar y techo matemático.
- Nueva **matriz general G/E/P** con multiselección de equipos y vista alternativa de **semáforo compacto**. Los colores resumen estado matemático; el texto conserva la condición exacta y nunca representa probabilidad.
- Nueva **matriz de rival clave**: cruza G/E/P del equipo con G/E/P de otra cancha elegida. Los demás partidos quedan abiertos y se enumeran exactamente; el rival sugerido surge de sensibilidad combinatoria, pero puede cambiarse manualmente.
- Nuevo **árbol reducido**: corta ramas terminales y sólo abre condiciones que cambian el estado. Nuevo **reloj de definición**: muestra qué puede resolverse en la próxima fecha y cuándo puede alcanzarse un mínimo que asegura ya probado por el solver.
- Nuevo **“¿Por qué?”** opcional: explica por qué una rama asegura o elimina con puntos tras la fecha, combinaciones verificadas y rivales todavía capaces de igualar/superar. Una condición necesaria no se presenta como suficiente.
- El paquete visual comparte el objetivo global para **Playoffs, Libertadores y al menos Sudamericana**. En copas usa la Tabla Anual reducida y separa clasificados por vías directas. Descenso conserva su tratamiento específico Anual+Promedios para no simplificarlo de forma engañosa.
- Nuevo `lpf_editorial_definition.py` puro, reutilizable por Streamlit/API. `lpf_conditionals.py` amplía su contrato con prueba estructurada y doble entrada de rival clave. `LPF_RUNTIME_API` sube a **16** y el nuevo módulo entra al núcleo crítico. Suite: **309 pruebas**.

## 3.8.40 · 2026-08-13

### Objetivo compartido y ventanas coherentes entre chat y paneles

- **Objetivo activo único:** Playoffs, Libertadores, al menos Sudamericana o Descenso se conserva entre el chat, Panel por equipo, Mesa de redacción y Visualizaciones. Entrar a una vista ya no vuelve silenciosamente a Playoffs ni pisa el último objetivo consultado.
- El explorador del chat incorpora un selector visible de **Objetivo activo**. Sus atajos genéricos “Qué necesita” y “Qué le conviene” generan la consulta para ese objetivo, en vez de forzar Playoffs.
- **Previa** y **La otra cancha** aceptan fecha oficial específica también en Panel por equipo y Visualizaciones; el chat reconoce consultas como “Fecha 8” y entrega esa fecha al mismo resolvedor de agenda. La opción “Fecha + postergados” conserva la ampliación con atrasados anteriores.
- “La otra cancha” evita recomendaciones engañosas: si el club ya tiene una plaza directa de Libertadores, el objetivo no depende de resultados ajenos; para descenso no publica una recomendación cuando el club queda fuera de la zona de riesgo editorial (últimos seis de Promedios o Tabla Anual).
- `LPF_RUNTIME_API` permanece en **15**: no cambia el contrato entre módulos críticos. Suite: **301 pruebas**.

## 3.8.39 · 2026-08-13

### Previa y simulación: criterios visibles y coherentes

- **Previa por equipo** expone tres alcances claros: próximo partido real por agenda, fecha oficial específica y fecha + postergados. Un atrasado programado antes que la próxima jornada puede tener su propia previa sin confundir fecha de juego con número de fecha.
- Las probabilidades publicables generales quedan unificadas en **6.000 simulaciones** y la interfaz deja de rotular 8.000 cuando el cálculo usaba otra cantidad. Las simulaciones de impacto de “otra cancha” conservan muestras mayores porque comparan diferencias pequeñas y controlan ruido.
- La simulación visible de playoffs deja de convertir los interzonales en un rival promedio: cada interzonal pendiente se resuelve una sola vez contra su rival real, usando su fuerza cuando está disponible.
- El informe de playoffs usa **puntos totales**, distingue **PJ** de **partidos por jugar** y enumera cada partido restante en una línea propia. Las salidas condicionadas se describen como **frecuencias del modelo**, no como una probabilidad general del equipo.
- `LPF_RUNTIME_API` permanece en **15**: no cambia el contrato entre módulos críticos.
- Suite: **296 pruebas**.

## 3.8.38 · 2026-08-12

### Últimas fechas: condicionales exactos y descenso coherente

- Nuevo `lpf_conditionals.py`: enumera exactamente la próxima fecha relevante de una zona para las ramas gana/empata/pierde, sin asignar probabilidades.
- **Visualizaciones → Últimas fechas → Condicionales de un equipo** muestra matriz, dos gráficos y narrativa exacta; busca condiciones simples suficientes de una o dos canchas cuando existen.
- Las frecuencias de los gráficos quedan rotuladas como **combinatorias, no probabilidades**. El Monte Carlo de impacto ajeno permanece separado como ESTIMADO.
- La vista está disponible dentro de la ventana exacta (8 partidos o menos) y marca **Modo definición** con 4 o menos.
- Nuevo `lpf_relegation.py`: resuelve la foto actual de descensos respetando el partido desempate y la exclusión de quien ya baja por promedios. Los relatos ya no rompen empates de descenso por DG.
- `LPF_RUNTIME_API` sube a **15**; `lpf_conditionals.py` y `lpf_relegation.py` entran al núcleo crítico. Suite: **290 pruebas**.

## 3.8.37 · 2026-08-12

### Copas: distinguir la Tabla Anual de las vías directas

- **Puntos por objetivo** renombra las metas de copas basadas en puntos como **Libertadores por Tabla Anual** y **Al menos Sudamericana por Tabla Anual**.
- Corrige una contradicción editorial: un club podía figurar “sin chances” por el corte de la Anual aunque todavía tuviera una vía independiente por Clausura/Copa Argentina. El estado “sin chances” queda ahora explícitamente limitado a la ruta de Tabla Anual.
- Los clubes ya clasificados por una vía directa dejan de desaparecer del resumen por equipo; se muestran como clasificados sin inventar un mínimo de puntos.
- La vista “Todos los equipos, un objetivo” incluye también esos clasificados directos y los separa con `Tipo de dato = Vía directa`.
- Regresión con la foto real incluida: Belgrano, campeón del Apertura, permanece visible como clasificado a Libertadores. Suite: **279 pruebas**. `LPF_RUNTIME_API` permanece en **14**.

## 3.8.36 · 2026-08-12

### Consistencia del solver exacto en las últimas fechas

- `lpf_scenarios.point_ladder` descarta antes del límite/solver los partidos donde ninguno de los dos equipos pertenece a la tabla calculada.
- Los cruces interzonales se mantienen cuando tocan a un club de la tabla; sólo se eliminan partidos matemáticamente irrelevantes.
- Corrige la contradicción potencial entre **Puntos por objetivo** y **Radar/Escenarios**: con las últimas ocho fechas, el fixture global suma 120 partidos pero una zona sólo depende de 64; el solver ya no se desactiva por los 56 partidos de la otra zona.
- Se agregan regresiones para el límite del MILP y para preservar interzonales. Suite: **274 pruebas**. `LPF_RUNTIME_API` permanece en **14**.

## 3.8.35 · 2026-08-12

### Últimas fechas: tablero de definición y navegación más simple

- Se elimina **Chat libre** de `Accesos principales`; el chat guiado/libre, su explorador y el simulador rápido quedan integrados en **Mesa de redacción → Consultas y chat**.
- Se conserva compatibilidad de sesión: si `workspace_nav` todavía apunta a `💬 Chat libre`, se migra automáticamente a `🗞️ Mesa de redacción`.
- **Visualizaciones → Últimas fechas** agrega una foto matemática de la zona, gráfico de puntos actuales + margen disponible, calendario comparado y un bloque de condicionales por equipo.
- El condicional del próximo partido reutiliza la Previa exacta; la escalera por puntaje reutiliza `point_ladder`; el impacto de la otra cancha reutiliza el Monte Carlo canónico y queda rotulado como **ESTIMADO**.
- No se modifica la matemática ni el contrato interno. Suite: **272 pruebas**. `LPF_RUNTIME_API` permanece en **14**.

## 3.8.34 · 2026-08-12

### Previa por equipo: cálculo y narrativa fuera de Streamlit

- Se agrega `lpf_preview.py`, módulo puro que recibe ventana de calendario, partidos abiertos, Tabla Anual, número de descensos y contexto de copas ya resueltos, y devuelve el Markdown y DataFrame de escenarios.
- `lpf_previa_equipo_texto` queda reducido a un adaptador de UI: aporta agenda/sesión y delega; ya no contiene `exact_result_scenarios` ni construcción de DataFrames.
- Equivalencia directa contra 3.8.33 en tres rutas activas (Playoffs, Descenso y Copas): texto completo, filas y atributos de exportación idénticos.
- Se agregan regresiones de pureza, objetivos visibles, descenso y frontera del wrapper.
- Suite: **269 pruebas**. `LPF_RUNTIME_API` sube de 13 a **14** y `lpf_preview.py` entra al núcleo crítico.

## 3.8.33 · 2026-08-12

### CI automática: tests, linter y release guard antes del deploy

- Se agrega `.github/workflows/ci.yml`, ejecutado en cada `push` y `pull_request`.
- El workflow instala `.[dev]` y corre `python -m pytest -q`, `python -m ruff check --select F,E9 *.py tests/*.py tools/*.py` y `python tools/release.py check`.
- La CI usa permisos `contents: read`, timeout de 15 minutos y `concurrency` con cancelación de corridas anteriores de la misma referencia.
- Se agregan regresiones que fijan esos comandos y prohíben `continue-on-error`, para que una falla de tests/linter/release bloquee efectivamente el check.
- Suite: **264 pruebas**. `LPF_RUNTIME_API` permanece en **13** porque no cambia ningún contrato interno de ejecución.

## 3.8.32 · 2026-08-12

### Releases verificables y empaquetado seguro

- Se agrega `tools/release.py`, un guard estático que comprueba `lpf_version.py`, el runtime requerido por el archivo principal, todos los `CRITICAL_COMPONENTS`, la metadata de `pyproject.toml`, README/CHANGELOG y la sintaxis Python.
- El mismo comando construye el ZIP completo, el paquete de sincronización de núcleo y un incremental opcional. El incremental incluye siempre bootstrap + núcleo crítico completos aunque esos archivos no hayan cambiado respecto de la base.
- Se corrige la metadata histórica de `pyproject.toml`, que todavía declaraba 3.8.1; desde ahora debe coincidir con la versión canónica.
- Se agregan regresiones que demuestran que un paquete incremental no puede omitir `lpf_runtime.py`, `lpf_version.py`, el archivo principal ni un componente crítico.
- Suite: **261 pruebas**. `LPF_RUNTIME_API` permanece en **13** porque no cambia ningún contrato interno de ejecución.

## 3.8.31 · 2026-08-12

### Promedios: previas y totales dejan de mezclarse

- Se agrega `lpf_averages.py`, contrato puro que distingue **temporadas previas** (`previous_averages`) de **totales acumulados de promedio** (`average_totals`).
- Se corrige `promedio_totales`: los puntos y PJ de 2026 salen de la Tabla Anual autoritativa. Las zonas quedan sólo como respaldo para fotos legacy sin PJ; ya no se combinan puntos de Apertura+Clausura con un denominador que cuente únicamente el Clausura.
- Auditoría contra las dos fotos internas sincronizadas (Tabla Anual + Promedios): la nueva combinación reproduce **30/30** totales Pts/PJ de la fuente; la fórmula anterior fallaba el denominador en **30/30**. Ejemplos: Boca 159/90 (antes 159/74), River 152/90 (antes 152/74), Aldosivi 42/49 (antes 42/33).
- `lpf_simulation.build_simulation_context` recibe explícitamente antecedentes previos y construye los totales antes de evaluar descenso. `objective_mask` usa `average_totals`; `ctx["prom"]` queda sólo como alias legacy de esos totales.
- Los snapshots reutilizan el mismo normalizador JSON-safe, con nombres de clubes canonicalizados.
- Suite: **255 pruebas**. `LPF_RUNTIME_API` sube de 12 a **13** y `lpf_averages.py` entra al núcleo crítico.

## 3.8.30 · 2026-08-11

### Accesos principales: Puntos por objetivo al final

- Se reordena únicamente la navegación superior de **Accesos principales**: **Puntos por objetivo** pasa al último lugar y **Panel por equipo** queda primero.
- No cambian cálculos, destinos, claves de navegación ni el contrato interno; `LPF_RUNTIME_API` permanece en **12**.
- Se agrega una regresión estática para fijar el orden solicitado. Suite: **247 pruebas**.

## 3.8.29 · 2026-08-11

### Auditoría probabilística y unificación del modelo

- Se auditaron los caminos probabilísticos activos con una foto real de Fecha 4 (59 partidos completados antes de Talleres–Lanús) y se confirmó que convivían dos modelos distintos dentro de la app.
- `lpf_simulation.match_outcome_probabilities` pasa a ser el kernel canónico: 26% de empate y factor local 1,22. Previa, Monte Carlo y `lpf_competitive_context` comparten la misma fórmula.
- `lpf_competitive_context` acepta una fuerza explícita y la UI le pasa la fuerza de `lpf_form` (Apertura + Clausura + forma reciente), en vez de usar una regularización paralela.
- `simulate_zone_rank_points` simula ahora los interzonales contra el rival real —incluida su fuerza y localía— cuando está disponible, en lugar de convertirlos en un partido contra rival promedio.
- En la foto auditada, el backtest secuencial del modelo canónico dio log-loss **1,037** frente a **1,057** del modelo editorial anterior. No se recalibraron parámetros con sólo cuatro fechas: la muestra queda como control, no como entrenamiento.
- **Puntos y puesto final** informa el número de corridas condicionadas y advierte cuando son menos de 100; así una mediana basada en pocos casos no se presenta con la misma estabilidad que una muestra amplia.
- Se agrega `tests/fixtures/lpf_2026_fecha4_probability_audit.json` y pruebas de normalización/sensibilidad, backtest, cupos de playoffs, interzonales y consistencia entre los dos caminos de simulación.
- La suite sube de 237 a **246 pruebas**. `LPF_RUNTIME_API` sube de 11 a **12** y `lpf_competitive_context.py` entra al conjunto crítico.

## 3.8.28 · 2026-08-11

### Contexto de simulación sin dependencias ocultas de sesión

- `lpf_simulation.build_simulation_context` arma ahora el contexto estable de Monte Carlo (Anual, tabla reducida, cupos, puntos base, zonas y promedios) a partir de datos explícitos.
- `_lpf_ctx` queda como wrapper de UI: resuelve desde sesión únicamente los fallbacks históricos de Apertura, Anual directa y reemplazo de Copa Argentina, y los pasa al módulo puro.
- Se elimina así una dependencia implícita importante para una futura API/snapshot: el motor ya no necesita que `lpf_anual_base`/`lpf_plazas_copas` consulten sesión mientras se arma el contexto de objetivos.
- Equivalencia exacta contra 3.8.27: **500/500** ejecuciones del wrapper con Apertura explícito/parcial, fallbacks de `ESTADO`/sesión, Anual directa y reemplazo de Copa Argentina.
- La suite sube de 234 a **237 pruebas**. `LPF_RUNTIME_API` sube de 10 a **11** porque el archivo principal requiere la nueva función de `lpf_simulation`.

## 3.8.27 · 2026-08-11

- Nuevo `lpf_simulation.py` con las primitivas Monte Carlo puras usadas por la LPF: simulación de posición/puntos por zona, suma de puntos sobre pendientes y máscara de cumplimiento de objetivos.
- `_sim_zone_rank_points` / `_sim_zone_pos` quedan como wrappers de compatibilidad que sólo aportan la fuerza calculada por `lpf_form`; `_sim_lpf_add` y `_obj_bool` pasan a ser aliases del módulo puro.
- Equivalencia exacta contra 3.8.26: 500/500 casos del núcleo de zona, 500/500 del wrapper, 800/800 matrices de puntos y 900/900 máscaras de objetivos.
- La suite sube de 229 a **234 pruebas**. `LPF_RUNTIME_API` sube de 9 a **10** y `lpf_simulation.py` entra al conjunto crítico para detectar deploys parciales.

## 3.8.26 · 2026-08-11

### Forma y fuerza de simulación fuera de Streamlit

- Se agrega `lpf_form.py`, módulo puro para resultado G/E/P, forma reciente, rachas y la fuerza regularizada que alimenta las simulaciones LPF.
- `_res_letra`, `forma_equipo`, `racha_equipo` y `_fuerza_lpf` quedan como wrappers de compatibilidad; sólo `_fuerza_lpf` lee la foto de Apertura desde sesión y la pasa explícitamente al modelo puro.
- No cambian los pesos históricos del modelo: seis partidos equivalentes de antecedente, peso creciente del Clausura, hasta 25% de forma reciente, normalización por mediana y límites 0.55–1.75.
- La equivalencia directa contra 3.8.25 se verificó en **1.000 casos** de forma/racha, **800 fotos** de fuerza y **400 ejecuciones** del wrapper con fallbacks de sesión.
- La suite sube de 224 a **229 pruebas**. `LPF_RUNTIME_API` sube de 8 a **9** y `lpf_form.py` entra en el conjunto crítico para impedir despliegues parciales.

## 3.8.25 · 2026-08-11

### Escenarios: el puesto específico deja de tratar extremos como si fueran típicos

- Se corrige la lectura de **“Puntos y puesto final”**: la vista principal ya no enumera todos los puntajes matemáticamente compatibles con un puesto como si pesaran igual.
- Para un puesto elegido (por ejemplo, 8º), la app corre **6.000 simulaciones** y calcula la distribución de puntos **sólo entre las corridas en las que el equipo termina en ese puesto**. Muestra mediana estimada, 50% central, frecuencia por puntaje y la chance estimada de terminar allí.
- La mediana queda correctamente ponderada por la frecuencia del modelo; no se calcula sobre la lista de puntajes alcanzables. Los extremos poco frecuentes quedan fuera del resumen central.
- Los extremos matemáticos siguen disponibles en una vista separada y explícitamente rotulada **“sin probabilidad”**. Se agregó `lpf_scenarios.can_finish_exact_rank_by_points`, que exige un escenario con el puesto exacto por puntos y no publica como exacto un caso que dependa de un desempate futuro no modelado.
- El nuevo solver se validó por fuerza bruta en ligas chicas y la simulación refactorizada conserva exactamente las posiciones del algoritmo histórico con la misma semilla. Suite: **224 pruebas**.
- El archivo principal importa una función nueva de `lpf_scenarios`; `LPF_RUNTIME_API` sube de 7 a **8** para detectar deploys parciales antes del import.

## 3.8.24 · 2026-08-11

### Contexto de copas fuera de Streamlit

- `lpf_qualification.py` también concentra la normalización de clasificados fijos a Libertadores, los equipos todavía vivos en Copa Argentina y la etiqueta de actualización/fuente usada por las narrativas de copas.
- `_lpf_fixed_lib_qualifiers`, `_lpf_copa_arg_alive_for_annual` y `_lpf_copa_snapshot` quedan como wrappers finos: sólo aportan los fallbacks guardados en `session_state` y delegan la lógica pura.
- La equivalencia se verificó contra 3.8.23 en **600 estados de sesión**, con **1.800 comparaciones** de los tres wrappers, además de **800 casos** permanentes de normalización de clasificados/vivos.
- La suite sube de 213 a **217 pruebas**. No cambia ningún cupo, orden de clasificación ni narrativa resultante.
- El archivo principal requiere nuevas funciones de `lpf_qualification`, por lo que `LPF_RUNTIME_API` sube de 6 a **7** para detectar un deploy parcial antes del import.

## 3.8.23 · 2026-08-11

### Tabla Anual y reparto de plazas fuera de Streamlit

- Se agregó `lpf_qualification.py`, módulo puro que resuelve la Tabla Anual autoritativa (Apertura + zonas actuales, con fallback validado a Anual directa) y reparte las plazas de Libertadores/Sudamericana con los mismos reordenamientos históricos.
- `lpf_anual_base` queda como adaptador de sesión: sólo reúne candidatos de Apertura/Anual y delega en `lpf_qualification.annual_base`. `lpf_plazas_copas` sólo aporta el reemplazo de Copa Argentina guardado en sesión y delega en `allocate_cup_slots`.
- La equivalencia se verificó contra 3.8.22 en **300 casos** de construcción de Anual y **600 combinaciones** de campeones/extras/reemplazos de Copa Argentina, sin diferencias.
- La suite sube de 206 a **213 pruebas**. No cambia ninguna fórmula, prioridad reglamentaria ni resultado de clasificación a copas.
- `lpf_qualification.py` entra en el chequeo de compatibilidad y `LPF_RUNTIME_API` sube de 5 a **6** para detectar un núcleo incompleto antes de importar el módulo nuevo.

## 3.8.22 · 2026-08-11

### Aplicación manual de resultados fuera de Streamlit

- Se agregó `lpf_result_updates.py`, módulo puro que aplica marcadores pendientes sobre una copia de las zonas y calcula los cambios de posiciones en zonas y Tabla Anual.
- `_rd_apply_results` queda como adaptador: aporta el estado actual, delega la mutación estadística, reconstruye la foto LPF con el constructor existente y sólo persiste `ESTADO`, `RD_LAST_CHANGES` y `RD_LAST_RESULTS`.
- La extracción se comparó contra 3.8.21 en **500 casos** de aplicación de marcadores, **300 casos** de cambios de puestos y **250 ejecuciones** del wrapper completo con estado de sesión simulado; todas fueron equivalentes.
- La suite sube de 200 a **206 pruebas**. No cambia ninguna fórmula, criterio de desempate ni resultado matemático.
- `lpf_result_updates.py` entra en el chequeo de compatibilidad y `LPF_RUNTIME_API` sube de 4 a **5** para detectar despliegues parciales antes del import.

## 3.8.21 · 2026-08-11

### Agenda real y alcance de la Previa fuera de Streamlit

- Se agregó `lpf_schedule.py`, módulo puro que normaliza fecha/hora en Argentina, combina agendas, ordena pendientes por programación real, distingue jornada operativa de postergados y resuelve el alcance de la Previa.
- `_lpf_schedule_map`, `lpf_jornada_actual`, `lpf_partidos_equipo_ordenados`, `lpf_proximo_partido_equipo` y `_lpf_scope_games` quedan como adaptadores finos: Streamlit sólo aporta la agenda de ESPN/sesión y el fixture oficial.
- La lógica nueva se comparó contra 3.8.20 en **120 fotos sintéticas** con **720 comparaciones de alcance** (próximo partido, próximo día, postergados, ventana ampliada y fecha oficial), con equivalencia exacta.
- Se agregaron pruebas permanentes de prioridad entre agendas, compatibilidad legacy, postergados, orden por calendario real, agrupación por día y conversión horaria argentina. La suite sube de 194 a **200 pruebas**.
- `lpf_schedule.py` entra en el chequeo de compatibilidad y `LPF_RUNTIME_API` sube de 3 a **4**. El archivo principal también verifica explícitamente el nivel de `lpf_runtime.py` antes de importar el resto del motor para diagnosticar mejor un deploy parcial.
- No cambia ninguna fórmula, resultado matemático ni regla de clasificación.

## 3.8.20 · 2026-08-11

### Escenarios: Puntos y puesto final más claro

- La herramienta visible **“Puntaje y puesto”** pasa a llamarse **“Puntos y puesto final”**, usando el vocabulario habitual del fútbol argentino.
- La pantalla separa explícitamente dos preguntas: **“¿Con cuántos puntos puede clasificar?”** y **“¿Con cuántos puntos puede terminar en un puesto específico?”**.
- El selector **“Puesto puntual a buscar”** se reemplaza por **“¿Qué puesto querés analizar?”** y el botón nombra directamente el puesto elegido.
- La tabla deja de repetir una columna de “Sí” y muestra sólo **Puntos finales**, **Mejor puesto con esos puntos** y **Peor puesto con esos puntos**.
- Se aclara que un mismo total de puntos puede llevar a posiciones distintas por los resultados de los demás equipos y los desempates.
- Se migra automáticamente una sesión que todavía conserve la selección interna `Puntaje y puesto`.
- No cambia ninguna fórmula ni resultado matemático. La suite sube de 192 a **194 pruebas**.

## 3.8.19 · 2026-08-11

### Revalidación/migración de sesiones fuera de Streamlit

- Se agregó `lpf_state.refresh_lpf_quality_state`, función pura que elige el primer Apertura válido entre candidatos explícitos, reconstruye la Anual viva cuando corresponde y vuelve a emitir el `DataQualityReport` con alertas de procedencia.
- `_lpf_refresh_quality` queda como adaptador: lee los candidatos de sesión/estado, delega toda la lógica y sólo persiste `LPF_APERTURA`, `LPF_ANUAL` y `LPF_DATA_QUALITY`.
- La función nueva no intenta derivar un Apertura nuevo para migrar una sesión; conserva la semántica histórica exacta de 3.8.18.
- Se comparó contra `_lpf_refresh_quality` de 3.8.18 en **7 escenarios dirigidos**, incluidos fallback a sesión/incorporado, ausencia de Apertura válido, Anual importada y alertas warning/bloqueo. Coincidieron reporte y efectos laterales.
- `LPF_RUNTIME_API` sube de 2 a **3** porque el archivo principal requiere la nueva función de `lpf_state`; los módulos críticos deben actualizarse juntos.
- No cambia ninguna fórmula, fuente ni resultado. La suite sube de 189 a **192 pruebas**.

## 3.8.18 · 2026-08-11

### Último respaldo válido fuera de Streamlit

- Se agregó `lpf_table_backup.py`, responsable de construir, escribir y recuperar el respaldo JSON de zonas + Tabla Anual sin importar Streamlit ni conocer proveedores.
- `_save_lpf_snapshot` queda como adaptador de sesión: construye el payload con el módulo nuevo, conserva una copia en `st.session_state` y delega la escritura atómica a disco. `_load_lpf_snapshot` sólo aporta el candidato de sesión y delega la recuperación.
- Se conserva exactamente la prioridad histórica **sesión → disco**, el límite de antigüedad de una semana, la compatibilidad con respaldos legacy (`A/B`, `Zona A/B`, `tabla_anual`) y los mismos diagnósticos editoriales.
- La función de recuperación se comparó directamente contra la implementación 3.8.17 en 5 escenarios: sesión válida, sesión vencida con disco válido, formato legacy, respaldo inválido y ausencia total. Las salidas fueron equivalentes.
- `lpf_table_backup.py` entra en `lpf_runtime.CRITICAL_COMPONENTS`, por lo que una actualización parcial que omita el módulo se detecta antes de cargar el motor.
- No cambia selección de fuentes, datos ni matemática. La suite sube de 180 a **189 pruebas**.

## 3.8.17 · 2026-08-10

### Política de prioridad/fallback de tablas fuera de Streamlit

- Se agregó `lpf_table_selection.py`, módulo puro que decide la combinación de zonas y Tabla Anual entre ESPN, FutbolArgentino.com, último respaldo y candidatos locales.
- `lpf_tables_with_fallback` queda reducido a obtener candidatos, delegar la selección y persistir el respaldo si la política lo habilita. No valida ni decide prioridades dentro de la UI.
- La prioridad se conserva: zonas ESPN → FutbolArgentino.com → última foto; con zonas frescas, Anual FutbolArgentino.com → Anual de la última foto → sesión/incluida.
- El selector no importa Streamlit, `requests`, no lee disco y no escribe sesión; una futura fuente Opta puede entregar candidatos a la misma política.
- Se comparó la salida exacta con 3.8.16 en 9 escenarios dirigidos, incluidos fallos parciales, tablas inválidas y error de persistencia.
- `lpf_table_selection.py` entra en `lpf_runtime.CRITICAL_COMPONENTS` para detectar actualizaciones parciales antes del import.
- No cambia ninguna fórmula ni dato. La suite sube de 172 a **180 pruebas**.

## 3.8.16 · 2026-08-10

### Fixture FutbolArgentino.com sin orquestación HTTP en Streamlit

- `futbolargentino_fixture` deja de construir dentro del archivo principal las dos URLs de resultados, el cache-buster y la tolerancia a fallos parciales.
- Esa orquestación de transporte vive ahora en `lpf_http.fetch_futbolargentino_results_pages`, que recibe `get_html` por parámetro para conservar la caché de Streamlit o reutilizar `fetch_html` desde otra interfaz.
- El parsing, canonicalización y validación de partidos siguen fuera del transporte y no cambia ninguna prioridad de fuentes ni cálculo LPF.
- La implementación nueva se comparó contra 3.8.15 en cuatro escenarios dirigidos: éxito total, error de parsing + fallo de red, primer origen caído y una página vacía. Salidas, errores y URLs consultadas fueron equivalentes.
- Como el archivo principal ahora importa una función nueva de `lpf_http`, el nivel `LPF_RUNTIME_API` sube a **2** en todos los módulos críticos; así una actualización parcial se detecta antes de cargar el motor.
- La suite sube de 170 a **172 pruebas**.

## 3.8.15 · 2026-08-10

### Ventana de scoreboards ESPN fuera de Streamlit

- `espn_fixture` deja de construir dentro del archivo principal la ventana temporal y los bloques de scoreboards. Esa orquestación de transporte vive ahora en `lpf_http.fetch_espn_scoreboard_window`.
- La función nueva no parsea eventos ni toca Streamlit. Acepta un `get_json` inyectable: la UI conserva `_espn_get` y su caché, mientras una futura API puede usar `fetch_espn_json` directamente.
- Se preservan el inicio especial de LPF (`2026-07-01`), bloques de 21 días, límite `max_req`, tolerancia a bloques fallidos y metadatos de cobertura.
- La nueva ruta se comparó de forma exacta contra `espn_fixture` de 3.8.14 en cuatro escenarios: normal, consulta limitada, bloque fallido y fallo inicial. Coincidieron salida, secuencia de requests simulados y efectos de sesión.
- `lpf_http.py` entra en el chequeo de compatibilidad de deploy, porque la 3.8.15 agrega una función que el archivo principal importa; una actualización parcial con un `lpf_http.py` viejo se detecta antes del import.
- Se confirmó que las ramas de football-data y Apify del modo avanzado están actualmente deshabilitadas (`and False`); no se refactorizan mientras no vuelvan a ser consumidoras reales.
- No cambia parsing, datos ni matemática LPF. La suite sube de 166 a **170 pruebas**.

## 3.8.14 · 2026-08-10

### Parsing HTML genérico separado del transporte

- Las cargas avanzadas por URL (`tabla_desde_url` y `partidos_desde_url`) dejan de mezclar descarga y parsing dentro del archivo Streamlit. Los wrappers sólo descargan y delegan.
- Se agregó `competition_html_adapters.py`, módulo puro que interpreta tablas de posiciones y matrices equipo × equipo desde HTML ya obtenido. No importa `requests` ni Streamlit.
- `lpf_http.fetch_url_text` conserva el transporte histórico de esas URLs genéricas (User-Agent simple, timeout y sin reinterpretar el status), para no cambiar mensajes ni comportamiento mientras se separan responsabilidades.
- Se agregaron fixtures locales de tabla, una rueda e ida/vuelta. Las salidas se compararon de forma exacta contra las funciones anteriores de 3.8.13: jugados, pendientes, notas y texto de tabla coinciden.
- `competition_html_adapters.py` entra en el chequeo previo de compatibilidad de deploy para que una actualización parcial no termine en `ModuleNotFoundError`.
- No cambia ninguna fórmula ni cálculo LPF. La suite sube de 160 a **166 pruebas**.

## 3.8.13 · 2026-08-10

### Contrato de snapshot validado para futura API/Opta

- La foto canónica declara ahora `snapshot_schema_version = "1"`, separada de `contract_version` y de la versión del motor. Esto permite evolucionar el formato de datos sin confundirlo con cambios matemáticos.
- `lpf_services.validate_competition_snapshot` valida una foto completa antes de usarla: nómina y zonas, enteros no negativos de `remaining`, equipos conocidos en pendientes, coherencia exacta entre pendientes y partidos restantes, y reglas de descenso. No ejecuta ni modifica fórmulas.
- `calculate_competition_batch` acepta tanto el objeto `result` de un snapshot como el sobre completo devuelto por `prepare_competition_snapshot`; también rechaza explícitamente schemas de snapshot no soportados antes de entrar a los optimizadores.
- Se agregó `service_capabilities()`: informa versión de contrato, versión de snapshot, operaciones, tipos de consulta batch y la ventana exacta vigente (8 partidos). Una futura API puede exponerlo como endpoint de metadatos sin importar Streamlit.
- El batch devuelve además `snapshot_schema_version` y `query_count`. Los snapshots parciales del contrato v1 siguen siendo aceptados para compatibilidad; la validación estricta se aplica a las fotos canónicas.
- No se agregó FastAPI, persistencia, base de datos ni SDK de Opta. La suite sube de 154 a **160 pruebas** y no cambia ninguna fórmula ni resultado matemático.

## 3.8.12 · 2026-08-10

### Protección contra despliegues con archivos mezclados

- Se agregó `lpf_runtime.py`, un chequeo de compatibilidad que lee marcadores de los módulos críticos **sin importarlos**. Si un deploy combina archivos de distintas generaciones, Streamlit lo detecta antes de cargar el motor y muestra qué archivos deben sincronizarse.
- Los módulos sensibles al contrato entre capas comparten `LPF_RUNTIME_API = 1`. Este nivel sólo se incrementa cuando cambia una interfaz interna incompatible; no depende del número de versión comercial.
- El sidebar muestra siempre `Motor de cálculo · vX.Y.Z`, para poder comprobar visualmente qué versión tomó Streamlit Cloud.
- Se cerró el barrido editorial residual de la escalera exacta: sus estados visibles usan **Mínimo que asegura** y ya no reaparecen “garantía exacta” ni “mínimo que garantiza” en esa ruta.
- Se agregaron pruebas del caso sano, de un `lpf_pisos.py` viejo/sin marcador y del orden de arranque: el chequeo ocurre antes de importar los módulos sensibles.
- No cambia ninguna fórmula, dato, umbral ni narrativa de cálculo. La suite sube de 151 a **154 pruebas**.

## 3.8.11 · 2026-08-10

### Narrativa: Total seguro y Mínimo que asegura

- Se reemplazan en toda la interfaz y las narraciones las etiquetas visibles **“referencia conservadora”** y **“garantía exacta”** por conceptos más directos: **total seguro** y **mínimo que asegura**.
- **Total seguro**: sabemos que alcanza si se llega a esa marca, pero todavía no sabemos si es el menor total que asegura.
- **Mínimo que asegura**: el motor exacto comprobó que ningún total alcanzable menor garantiza el objetivo.
- El bloque de rivales deja de concatenar máximos individuales en un párrafo: los lista uno por línea y explica que esos máximos no pueden darse todos simultáneamente por los cruces entre rivales.
- La API agrega `minimum_guarantee` y `safe_total` como alias editoriales, sin romper las claves técnicas existentes del contrato v1.
- No cambia ninguna fórmula, umbral ni resultado matemático.

## 3.8.10 · 2026-08-10

### Compatibilidad de despliegues parciales en Puntos por objetivo

- Se blinda la interfaz frente a repositorios con archivos mezclados: si `calculadora_futbol_argentino.py` nuevo recibe un `PisoObjetivo` de 3.8.7 o anterior, deriva **garantía exacta** desde `piso_exacto/exacto` y **referencia conservadora** desde `piso_conservador` en vez de lanzar `AttributeError`.
- La misma compatibilidad se aplica a `lpf_services`, para que una futura API tampoco falle ante objetos internos del contrato anterior.
- No cambia ninguna fórmula, umbral ni resultado matemático. La corrección es exclusivamente de integración/compatibilidad.

## 3.8.9 · 2026-08-10

### Foto canónica de competencia y consultas por lote

- Se agregó `lpf_snapshot.py`: construye una foto autocontenida de la competencia a partir del mismo `lpf_state.build_lpf_state` que usa Streamlit. Incluye zonas, Tabla Anual, Apertura, jugados, pendientes, partidos restantes, antecedentes de promedios, fixture, reglas y auditoría. No hace red ni importa Streamlit.
- `lpf_state` conserva ahora los antecedentes de promedios dentro del estado canónico; esto evita que una futura API tenga que reconstruir una parte de la competencia por fuera del estado.
- La combinación de puntos/PJ actuales con antecedentes para promedios salió de Streamlit y vive en `lpf_pisos.promedio_totales`. El wrapper de la UI sólo aporta `st.session_state.PROMEDIOS`. Se verificó equivalencia exacta en 1.500 casos aleatorios contra la fórmula 3.8.8.
- `lpf_services.prepare_competition_snapshot` expone esa foto con entrada/salida JSON-safe y auditoría incluida. Una foto puede enviarse luego a `calculate_competition_batch` para resolver varias consultas sin repetir la carga o reconciliación.
- El batch admite `objective_points`, `point_ladder`, `rank_window` y `descent_points`, con alcance por zona o Tabla Anual cuando corresponde. Descenso reutiliza la misma combinación Anual + promedios que Streamlit.
- No se agregó persistencia de snapshots, IDs de sesión, FastAPI, base de datos ni SDK de Opta: la frontera sigue siendo stateless y verificable.
- La suite sube de 140 a **147 pruebas**.

## 3.8.8 · 2026-08-10

### Terminología unificada en todas las narraciones y corrección del objetivo descenso

- Toda la interfaz y las narraciones usan tres nombres distintos: **mínimo posible**, **garantía exacta** y **referencia conservadora**. Se eliminan de cara al usuario las etiquetas ambiguas **“puntaje que asegura”**, **“seguro (conservador)”**, **“piso seguro”** y **“piso ajustado”**.
- La **referencia conservadora** es un total suficiente: si se alcanza, asegura el objetivo, pero puede pedir puntos de más. La **garantía exacta** es el menor total comprobado que asegura.
- El relato general de “qué necesita”, playoffs, copas, descenso, Radar y escalera exacta comparte ahora la misma terminología. `lpf_scenarios.point_ladder` rotula sus filas garantizadas como **“Garantía exacta”**.
- En promedios, las tablas visibles dejan de hablar de “piso/techo” y muestran **“Mínimo final”** (si pierde todo) y **“Máximo final”** (si gana todo).
- `lpf_competition_narratives` usa `VENTANA_EXACTA = 8` como referencia del tramo final; ya no mantiene un umbral editorial separado de seis partidos.
- Se corrigió la combinación de **Tabla Anual + promedios** en `piso_no_descenso`: un equipo no se declara salvado por la Anual si todavía necesita puntos por promedios, y cuando la referencia de promedios es más exigente que la garantía anual manda el mayor total seguro.
- La fachada JSON agrega nombres explícitos `minimum_possible`, `exact_guarantee`, `conservative_reference` y `safe_value`; `floor` se conserva sólo como alias legado del contrato v1.
- La suite queda en **140 pruebas**.

## 3.8.7 · 2026-08-10

### Terminología más clara y ventana exacta unificada

- La interfaz deja de usar **“cota”** y deja de presentar **“piso”** como etiqueta principal para el objetivo. En lenguaje editorial se usan tres conceptos: **mínimo para seguir con chances**, **puntaje que asegura** y **puntaje seguro (conservador)**.
- El puntaje seguro conservador también asegura el objetivo si se alcanza; la diferencia es que, antes de ejecutar el optimizador exacto, puede pedir algún punto de más que el menor total realmente necesario.
- El espacio principal pasa de **“Pisos por objetivo”** a **“Puntos por objetivo”** y las tablas muestran **“Puntaje que asegura”** / **“Cálculo”**. Los nombres internos `piso_*` y el campo `floor` del contrato v1 se conservan por compatibilidad.
- Se corrigió una desincronización residual: una narración antigua activaba `point_ladder` con seis partidos restantes. Ahora todas las rutas usan `VENTANA_EXACTA = 8`. En un torneo de 16 fechas, sin postergados, el cálculo exacto puede aparecer desde la **Fecha 9** (después de jugar ocho partidos).
- El umbral es por **partidos restantes del equipo**, no por número nominal de fecha: los postergados pueden retrasar la entrada a la ventana exacta.

## 3.8.6 · 2026-08-10

### Corrección de arranque en Streamlit

- Se corrigió un `NameError` en `_lpf_refresh_quality`: después de extraer la lógica a `lpf_state.add_source_issues` había quedado una llamada residual al nombre antiguo `_lpf_add_source_issues`.
- La ruta de auditoría vuelve a pasar explícitamente `PROM_SOURCE_ISSUES` desde `st.session_state` al helper puro, preservando exactamente el comportamiento anterior.
- Se agregaron dos pruebas de regresión sobre el puente Streamlit → `lpf_state` para detectar referencias residuales a helpers extraídos antes del despliegue.
- No cambia ninguna fórmula ni contrato de cálculo; es una corrección de integración de la interfaz. La suite queda en **132 pruebas**.

## 3.8.5 · 2026-08-10

### Contrato JSON para la futura API de cálculos

- Se agregó `lpf_services.py`, una fachada pura que recibe payloads compatibles con JSON y delega en los motores existentes sin importar Streamlit, `requests` ni proveedores.
- Primer contrato versionado (`contract_version = "1"`) para cuatro operaciones: tabla/posiciones, escalera exacta de puntos, rango exacto de puesto en una ventana y piso por objetivo de corte.
- Todas las respuestas incluyen `calculation_version`; la versión del motor pasó a `lpf_version.py` para que Streamlit, auditoría y una futura API compartan la misma fuente sin importar el archivo principal. Esto corrige además el valor residual `3.8.2` que todavía tenía `AuditMetadata`.
- Se agregó `ContractError` con `code`, `message` y `field` para disponer de errores estables que una futura capa HTTP pueda mapear sin incorporar un framework web ahora.
- Se documentó el contrato en `API_CONTRACT.md`. No se agregó FastAPI, servidor HTTP, autenticación ni SDK de Opta.
- La suite sube de 122 a **130 pruebas**. Además se verificaron **980 casos aleatorios** de equivalencia del servicio de standings contra `lpf_standings._orden`, con cuatro configuraciones de desempate.

## 3.8.4 · 2026-08-10

### HTTP separado de los adaptadores de proveedor

- Se agregó `lpf_http.py`: concentra el transporte HTTP de las fuentes públicas sin importar Streamlit ni parsear datos. La caché sigue siendo responsabilidad del adaptador Streamlit y una futura API puede reutilizar o reemplazar el transporte.
- Se agregó `lpf_provider_adapters.py`: convierte HTML/JSON ya descargado de FutbolArgentino.com y ESPN a estructuras Python del dominio. No hace red, no persiste estado y no importa Streamlit.
- `futbolargentino_zones`, `futbolargentino_annual`, `espn_tabla`, `espn_lpf_zonas` y `espn_fixture` quedaron como wrappers de orquestación: fetch por una capa, parsing por otra.
- El scoreboard ESPN ya no escribe sesión durante el parsing: el adaptador devuelve `played`, `pending`, `schedule`, `event_meta` y mapas de fechas; Streamlit decide luego qué persistir.
- Se guardaron fixtures locales representativos de standings HTML, standings ESPN y scoreboards ESPN. La equivalencia se verificó contra el código 3.8.3 exacto para tablas, zonas, resultados, pendientes, deduplicación, agenda y metadatos.
- La suite sube de 115 a **122 pruebas**. Los nuevos tests cubren adaptadores sin red, nombres difíciles de FutbolArgentino.com, estados de ESPN y el transporte HTTP con `requests` simulado.
- La frontera para Opta queda explícita: un adaptador futuro debe producir las mismas estructuras del dominio; no necesita modificar `lpf_loading`, `lpf_state` ni los motores. No se agregó SDK de Opta ni framework de API.

## 3.8.3 · 2026-08-10

### Preparación de cargas desacoplada de I/O y Streamlit

- Se agregó `lpf_loading.py`, una capa pura entre los proveedores y `lpf_state`: normaliza resultados contra las zonas, prepara la carga offline y reconcilia la actualización automática sin hacer red, leer sesión ni persistir snapshots.
- `cargar_lpf_todo` y `cargar_lpf_espn` quedan como orquestadores de I/O/Streamlit. La lógica determinística de merge, avance de standings, reconstrucción de Anual, inferencia y diagnósticos se delega al nuevo módulo.
- Se definió `normalize_results_for_zones` como contrato mínimo reutilizable para cualquier proveedor: filas `(local, visitante, goles_local, goles_visitante)` entran con aliases/formato propios y salen canonicalizadas, filtradas a la nómina y deduplicadas. Un futuro adaptador Opta puede producir esta misma estructura sin tocar los motores.
- No se movieron todavía los fetchers de ESPN/FutbolArgentino.com ni se agregó un SDK/API: el siguiente límite seguro es separar fetch de parsing con fixtures locales antes de tocar red.
- La equivalencia se verificó contra el algoritmo 3.8.2 en 12 escenarios dirigidos que cubren carga offline, fuentes al día, scoreboard una fecha por delante e inferencia determinística.
- La suite sube de 109 a **115 pruebas**, con cobertura específica de normalización de resultados, carga offline, actualización automática, avance de standings, reconstrucción anual y rechazo de datos insuficientes.

## 3.8.2 · 2026-08-10

### Estado LPF desacoplado de Streamlit

- Se agregó `lpf_state.py`, que construye la foto canónica de la competencia con una función pura (`build_lpf_state`). Recibe zonas, resultados, Tabla Anual, Apertura, promedios, fixture y metadatos como parámetros; no importa Streamlit, `requests` ni código de proveedores.
- `_lpf_rebuild_state` queda como adaptador fino: lee la sesión, llama al constructor puro y persiste en Streamlit únicamente `LPF_APERTURA`, `LPF_ANUAL` y `LPF_DATA_QUALITY`. La prioridad de fuentes y los números no cambian.
- La validación de la foto fija del Apertura (`opening_is_valid`) y la incorporación de conflictos de procedencia (`add_source_issues`) también quedaron en la capa pura.
- La nueva frontera permite que una futura API construya exactamente el mismo estado de cálculo pasando payloads ya normalizados; un futuro proveedor Opta sólo deberá resolver su formato antes de esta función. No se agregó FastAPI ni un SDK de Opta.
- La equivalencia se comprobó contra la implementación 3.8.1 en cinco rutas: Apertura explícito, guardado, incorporado, derivado y estado sin Anual válida. Estado y auditoría resultaron idénticos.
- La suite sube de 103 a **109 pruebas**, con cobertura específica del constructor puro, prioridad de Apertura e inyección de alertas de fuente.

## 3.8.1 · 2026-08-10

### Motor de posiciones desacoplado de Streamlit

- El motor completo de ordenamiento (`_resolver`, `_orden`, `posiciones`, `tabla`) vive ahora en `lpf_standings.py` y recibe los criterios de desempate como dependencia explícita. Ya no lee `st.session_state` ni conoce la interfaz.
- `calculadora_futbol_argentino.py` conserva adaptadores mínimos para `posiciones` y `tabla`: toman los criterios elegidos en Streamlit y llaman al mismo motor puro. Esto preserva todos los call-sites y el comportamiento visible.
- Se definió `DEFAULT_CRITERIOS` como única configuración por defecto del motor y de la sesión Streamlit, sin confundir una lista vacía de criterios con el default.
- La extracción se verificó contra `_original_referencia/` en **1.470 casos aleatorios** y seis configuraciones de desempate, incluyendo mano a mano, fair play y ranking, con equivalencia exacta de orden, posiciones, estadísticas y DataFrame final.
- La suite sube de 98 a **103 pruebas**, con cobertura específica de inyección de criterios y de la salida pura del motor.

### Preparación para API y Opta

- La frontera queda explícita: **proveedor de datos → normalización/reconciliación → motores puros → Streamlit o futura API**.
- Una futura API debe importar los módulos de cálculo directamente, no el archivo Streamlit. Un futuro adaptador Opta debe convertir sus identificadores y payloads al modelo canónico antes de entrar al motor; ninguna dependencia de Opta debe vivir dentro de `lpf_standings`, `lpf_scenarios`, `lpf_exact` o `lpf_pisos`.
- No se agregó todavía un framework web ni una abstracción de proveedor: se deja el punto de extensión real sin sumar complejidad prematura.

## 3.8.0 · 2026-08-09

### Refactor incremental del monolito

- Octavo paso: la **derivación e inferencia de datos** (`derivar_apertura`, `_lpf_infer_missing_results`, `_asignar_nombres`) se movió a `lpf_derive.py`. Reconstruye la foto del Apertura desde la anual y las zonas, e infiere resultados faltantes cuando la tabla los fija de forma única. También se reubicó la tabla anual fija `TABLA_ANUAL_LPF_2026` a `lpf_data_2026.py`. Durante la extracción, el linter detectó que una constante de módulo (`_LPF_PROM_HISTORY_VERSION`) se había colado en el módulo equivocado; se corrigió antes de continuar.
- Séptimo paso: la **capa de reconciliación** vive en `lpf_reconcile.py`.
- Sexto paso: los **datos fijos de la temporada** viven en `lpf_data_2026.py`.
- Pasos previos: `lpf_text.py`, `lpf_intents.py`, `lpf_clubs.py`, `lpf_parsers.py`, `lpf_standings.py`.
- Todas las extracciones se verificaron con **equivalencia exacta** contra el original. Se agregó además una prueba del camino real de carga (`cargar_lpf_todo`) a través de los módulos extraídos, para garantizar que la app trae los datos correctamente. El archivo principal bajó de ~12.780 a ~11.300 líneas (unas 1.480 menos), repartidas en nueve módulos nuevos. La suite pasó de 10 a 98 pruebas.

### Pruebas

- Suite ampliada de 10 a 54 pruebas, todas por fuerza bruta o de equivalencia. Ahora se validan los tres motores exactos, no sólo el piso.
- `test_lpf_scenarios.py`: el motor MILP (`can_qualify`, `can_fail`, rangos de puesto, escalera de puntos, escenarios gana/empata/pierde) coincide con la enumeración exhaustiva en decenas de ligas al azar.
- `test_lpf_exact.py`: verifica la propiedad más importante del proyecto —que la línea de garantía y el piso por promedios **nunca declaran una garantía falsa**— y que nunca piden menos que la garantía exacta real.
- Agregados `tests/README.md`, `tests/conftest.py` y la configuración de `pytest` en `pyproject.toml`.

### Piso por objetivo (función nueva)

- Nuevo módulo `lpf_pisos.py`: unifica en un solo lugar el cálculo del **piso** de cada equipo para cada objetivo (playoffs, Libertadores, Sudamericana y no descender).
- Los tres objetivos de "quedar arriba de un corte" se resuelven con la misma función parametrizada por tabla base y corte, en vez de repetir la lógica.
- Distingue con rigor **mínimo posible** (menor puntaje con una combinación favorable, desempate a favor), **piso/garantía** (asegura sin depender de nadie ni de desempates, desempate en contra) y **cota conservadora** (ventanas de más de ocho fechas).
- "No descender" combina la Tabla Anual (motor exacto) y los promedios (cota segura por cocientes) y toma el piso más exigente de los dos.
- **Motor exacto de la definición, arreglado:** el Radar se activaba con el máximo global de partidos por jugar, así que un solo postergado en otra cancha ocultaba el piso exacto para toda la zona. Ahora se activa **por equipo**: cada club ve su escalera exacta apenas entra en sus últimas ocho fechas, sin importar los postergados ajenos.
- El espacio Pisos muestra además la **escalera exacta** completa (del mínimo posible a la garantía, con caminos de ejemplo en cada escalón), que es lo que el optimizador produce en la definición.
- **Ventana exacta ampliada de seis a ocho fechas.** Un benchmark sobre zonas de 16 equipos mostró que el costo por equipo se mantiene por debajo de ~2 s hasta ocho fechas, así que el piso exacto ahora aparece dos fechas antes. El umbral vive en una sola constante compartida (`lpf_pisos.VENTANA_EXACTA`) que usan tanto el Radar como el espacio Pisos, para que no se desincronicen.
- Reutiliza los motores ya validados (`point_ladder`, `safe_guarantee_line`, `safe_average_guarantee_points`); no reimplementa matemática.
- Nuevas pruebas `tests/test_lpf_pisos.py`: validación por fuerza bruta del mínimo y de la garantía en ligas chicas. 10 pruebas aprobadas.

### Experiencia de usuario

- Nuevo espacio **Pisos por objetivo** como puerta de entrada por defecto: una sola pantalla responde "¿cuántos puntos necesita?" con dos modos (un equipo con todos sus objetivos, o todos los equipos para un objetivo).

### Limpieza y consistencia

- Versión unificada en una única constante `__version__` que alimenta el título y `AuditMetadata.calculation_version` (antes convivían 3.5.4, 3.7.6, 3.7.22 y 3.0.0).
- Eliminada la definición duplicada de `_secret`.
- Archivado el código muerto `calculadora_mundial.py` en `legacy/` (no lo importaba nadie; compartía 163 de 170 funciones con la app).
- Corregidos f-strings sin marcadores, un import sin uso y una computación muerta (`safe_avg`) detectada en la revisión.
- Eliminadas todas las variables locales sin uso del archivo principal y un bloque de código inalcanzable después de un `return` en el ruteo del chat. El proyecto queda sin advertencias de la categoría F (nombres indefinidos, imports y variables sin uso).
- Recuperados los documentos `ARCHITECTURE.md` y `AUDITORIA.md` que el README referenciaba pero no existían; enlaces del README arreglados.
- Agregados `pyproject.toml` y `.gitignore`.



- Conectó la página de resultados de FutbolArgentino.com al actualizador automático; el parser ya existía, pero no se utilizaba desde la interfaz.
- Mantiene ESPN como segunda fuente y combina fotos parciales sin inferir partidos por los PJ.
- La actualización ahora sólo acepta marcadores que reconstruyan exactamente PJ, puntos, GF, GC y DG de las dos zonas.
- Si ninguna combinación coincide, conserva la última base válida y muestra los errores de cada proveedor.
- No incorporó Playwright: la fuente elegida entrega los resultados en el HTML inicial y funciona con `requests` + BeautifulSoup.

## 3.5.4

- Conservó sin cambios las funciones del panorama individual de playoffs, Libertadores y Sudamericana.
- Sustituyó los rangos generales demasiado amplios por conclusiones editoriales sobre ingreso, salida o permanencia en el top 8.
- Evitó repetir el mismo panorama de ventana en los dos partidos de un equipo.
- Fijó visualmente la regla LPF de ocho clasificados por zona y ocultó la configuración genérica mientras se usa ese torneo.
- Renombró “Partidos pendientes” como “Partidos por jugar”.
- Corrigió la alerta que trataba una fecha en curso como una fecha completa faltante.
- Elevó a 9 las pruebas automatizadas de esta revisión.

## 3.5.2

- Transformó el Chat libre en una experiencia **guiada + libre**.
- Incorporó selector de equipo y segundo equipo para comparaciones.
- Agregó categorías visibles para playoffs, copas, descenso, fecha, rendimiento, redacción, tablas y control de datos.
- Sumó buscador de funciones por palabra y botones que envían la consulta automáticamente.
- Añadió un índice completo de opciones sin eliminar el campo de escritura libre.
- Amplió la detección de consultas como «¿en qué zona está…?».
- Añadió pruebas de regresión específicas del descubrimiento de funciones del chat.
- Total de la entrega: 31 tests automatizados aprobados.

## 3.5

- Integró el impacto en copas y descenso dentro de **Mesa de redacción → Previa de la fecha**.
- Agregó el selector de capas **Copas / Descenso** para la vista general y la vista por partido.
- Copas informa puesto anual, puesto entre elegibles, cupo vigente, distancia a la línea y rango de la ventana.
- La vista individual diferencia qué ocurre si gana, empata o pierde: Libertadores, Sudamericana, puestos de copas o fuera de ellos.
- Descenso anual se limita a los últimos puestos y muestra distancia a la salvación y rangos exactos.
- Promedios se limita a la zona baja y calcula el coeficiente exacto posterior a cada resultado.
- Si faltan antecedentes válidos, se omite la capa de promedios sin inventar datos.
- Total de la entrega: 25 tests automatizados aprobados.

## 3.4

- Agregó un pantallazo narrativo de la fecha completa dentro de **Mesa de redacción → Previa de la fecha**.
- Incorporó el selector **Toda la fecha / Un partido**.
- La vista general resume ambas zonas y luego recorre todos los encuentros con contexto de tabla y rango de puestos.
- La vista por partido agrega ramas exactas gana/empata/pierde para los dos equipos.
- Los postergados quedan marcados con su fecha original.
- Si un equipo juega dos veces en la ventana, la vista general evita mostrar un rango simplificado engañoso; la vista individual usa el motor exacto.
- Las probabilidades se mantienen como bloque estimado separado.
- Total de la entrega: 23 tests automatizados aprobados.

## 3.3

- Mejoró la narrativa de Zona A y Zona B con PJ, DG, GF, igualdad del corte, distancias y tabla breve.
- Agregó relatos generales de Libertadores, Sudamericana y descenso.
- Incorporó explicación dinámica de cupos que se corren por campeones futuros.
- Sumó seguimiento de equipos vivos en Copa Argentina con lista manual, foto de octavos y cotejo ESPN.
- Sumó el reemplazo reglamentario de ARGENTINA 3 dentro de Copa Argentina.
- Incorporó las narrativas al Panel, Mesa de redacción, Visualizaciones y Chat.
- Amplió a 21 tests automatizados.

# Changelog

## 3.0.0 · 2026-08-01

### Base y auditoría

- Se agregó un constructor único de estado LPF.
- Las Zonas, la Tabla Anual, los Promedios, el fixture y los resultados se validan antes de publicar cuentas.
- La Tabla Anual se deriva de una foto fija del Apertura más las zonas actuales cuando esa foto es confiable.
- La Anual directa queda como alternativa únicamente si supera los controles.
- Los cálculos afectados se bloquean por dominio: playoffs, copas, promedios o descenso.
- Se incorporó un semáforo de calidad y un respaldo JSON desde la interfaz.
- Los partidos pasaron a tener identidad, jornada original, estado y procedencia.
- Se corrigió la inferencia de postergados: jugar una fecha posterior no convierte el partido anterior en jugado.

### Motor matemático

- Se agregó un optimizador exacto basado en `scipy.optimize.milp`.
- Nueva escalera de puntajes con mínimo todavía posible, clasificación condicionada y garantía matemática.
- Nuevos rangos exactos por puntos para ventanas en las que un equipo puede jugar dos veces.
- Se mantiene la garantía conservadora para horizontes grandes y se la rotula correctamente.
- Se eliminaron explicaciones falsas sobre reparto de puntos y marcadores futuros.

### Simulación

- La fortaleza temprana se regulariza con una referencia previa y ya no proyecta automáticamente cero por dos derrotas.
- “Qué le conviene” compara victoria local, empate y victoria visitante con la misma semilla.
- Se muestran cambios en puntos porcentuales, ruido estimado y nivel de impacto.
- Cuando ningún partido mueve la probabilidad de forma apreciable, se muestra una conclusión en lugar de muchas filas “da igual”.

### Experiencia de usuario

- Nuevo **Explorador guiado** para no depender de recordar comandos.
- Nuevo espacio de **Visualizaciones**.
- Nuevo panel de **Datos y auditoría**.
- El Chat queda disponible como modo libre.
- La previa distingue Fecha oficial, solo postergados y ventana completa.
- La ficha de equipo prioriza puesto, distancia al corte, techo, próximos partidos y dificultad editorial.
- Nuevo Radar de definición para las últimas seis fechas.

### Pruebas

- Pruebas de postergados, Tabla Anual derivada, Anual vieja, escalera exacta y ventanas dobles.
- Comparación del optimizador contra enumeración exhaustiva en casos pequeños.
- Total de la entrega: 13 pruebas automatizadas aprobadas.

## 3.1

- Tabla Anual reconstruida siempre desde Apertura fijo + zonas actuales.
- Foto fija del Apertura 2026 incorporada y verificada con los resultados de la primera fecha del Clausura.
- Migración automática de sesiones que conservaban una Tabla Anual vieja.
- La Tabla Anual importada deja de ser una fuente viva y queda como control.
- Advertencias y bloqueos filtrados por objetivo: playoffs, copas y descenso.
- Eliminado el mensaje general que invalidaba playoffs por un problema exclusivo de copas o Promedios.
- Nuevo Panel por equipo con Resumen completo como entrada predeterminada.
- Quince tests automatizados aprobados.

## 3.2

- Nuevo espacio visible **Escenarios** con las funciones adaptadas del proyecto del Mundial.
- Gana / empata / pierde reunido en una vista propia.
- Constructor **Qué pasa si…** para fijar resultados y mantener abiertos los demás partidos.
- Búsqueda de puesto puntual a partir de los puntajes alcanzables.
- Mejor y peor caso concreto con combinaciones de resultados que prueban los extremos.
- Distribución estimada de posiciones separada de los rangos exactos.
- Panel de clasificados, eliminados y equipos en carrera.
- Las mismas herramientas también se abren desde el Panel por equipo.
- Diecisiete tests automatizados aprobados.

## 3.5.1
- Restaurados los accesos principales visibles desde el comienzo.
- Agregados botones directos para las seis herramientas de Escenarios, incluida Distribución.
- Añadida prueba automática de regresión de navegación.
