# Calculadora del Fútbol Argentino · LPF 2026 · versión 3.8.53

Aplicación editorial en Python y Streamlit para analizar playoffs por zonas, Tabla Anual, Libertadores, Sudamericana, descenso, promedios y escenarios de una fecha.

La versión vigente siempre está en `lpf_version.__version__` (única fuente de verdad compartida por Streamlit, auditoría y futuras interfaces). El historial completo está en `CHANGELOG.md`.

## Novedad 3.8.52 · matrices visuales y otra cancha por partido

- **Últimas fechas** adopta la lectura visual probada en la calculadora del Mundial: la matriz G/E/P se muestra como grilla coloreada con equipos en filas y resultados en columnas; el detalle tabular/exportable queda plegado.
- La **doble entrada** deja de pedir un segundo equipo. El selector pasa a `Partido de la otra cancha (sugerido, editable)` y las columnas son los tres desenlaces naturales del encuentro: gana local / empate / gana visitante.
- El encabezado usa la convención `equipo principal ↓ / partido de la otra cancha →`, por lo que queda un solo protagonista seleccionado durante todo el tablero.
- Cada celda conserva texto además del color: `ASEGURA`, `SIGUE ABIERTO`, `PUEDE ASEGURAR`, `PUEDE QUEDAR AFUERA` o `ELIMINADO`; los semáforos siguen siendo estados exactos, no probabilidad.
- Nuevo bloque **Partidos que más definen**: ordena las otras canchas por sensibilidad exacta y expresa el impacto como cantidad de **caminos exactos que cambian** entre el desenlace más favorable y el menos favorable.
- El árbol reducido, `¿Por qué?`, Zona de pelea y Reloj de definición se mantienen; no se agregan gráficos redundantes ni se mezclan frecuencias combinatorias con Monte Carlo.
- No cambia Public Service v1, DataProvider v2, snapshot schema 3 ni Runtime API 21. Validación: **352 pruebas** + `release check`.

## Novedad 3.8.51 · selección de equipo y comparadores sin ambigüedad

- **Últimas fechas** ya no elige un equipo principal de manera implícita al abrir: muestra `— Elegí un equipo —` y espera una selección explícita.
- La pantalla separa cuatro roles: **equipo principal** (lo elige el editor), **contexto automático** (clubes cercanos al principal/corte), **comparadores** (sólo los que el editor agrega) y **otra cancha clave** (sugerencia exacta y editable).
- La matriz G/E/P deja fijo al equipo principal y el segundo selector pasa a `Comparar también con… (opcional)`: ya no se puede desmarcar accidentalmente al protagonista del tablero.
- Los sugeridos cercanos al corte no se agregan solos; hay acciones explícitas `Agregar sugeridos` y `Quitar comparadores`.
- La doble entrada adopta la lectura `Equipo principal ↓ / equipo de la otra cancha →` y aclara qué representan filas y columnas, siguiendo la convención visual probada en la calculadora del Mundial.
- En Libertadores/Sudamericana, un club ya clasificado por vía directa sigue siendo elegible en el selector y se explica como **objetivo resuelto**, en vez de hacer saltar silenciosamente la selección a otro equipo.
- No cambia Public Service v1, DataProvider v2, snapshot schema 3 ni Runtime API 21. Validación: **352 pruebas** + `release check`.

## Novedad 3.8.50 · trazabilidad, frescura y handoff a desarrollo

- El snapshot canónico sube a **schema 3** e incorpora `traceability`: `snapshot_id` estable, proveedor, fuente, timestamps declarados, cobertura de resultados/fixture y resumen de calidad.
- `snapshot_id` depende del contenido competitivo y no de la procedencia: la misma foto recibida por `CurrentProvider`, CSV o un futuro Opta conserva la misma huella.
- `DataProvider` pasa a **v2** y agrega `ProviderData.provenance` (`source_name`, `source_updated_at`, `data_as_of`, `sources`, `warnings`). Schema/provider anteriores siguen soportados para compatibilidad.
- **Datos y auditoría** muestra fuente, antigüedad cuando existe timestamp, última fecha con resultados confirmados, cobertura y bloqueos. Si no hay timestamp verificable, se informa como desconocido en vez de inventarlo.
- `CsvProvider` usa el `mtime` más reciente como referencia si no recibe metadata explícita. `CurrentProvider` conserva la procedencia conocida de la sesión; la carga offline/manual queda explícitamente sin timestamp verificable.
- Nuevo `HANDOFF_DESARROLLO.md` con contratos estables, checklist de integración Opta, validaciones y deuda deliberada. Public Service permanece en **v1**; Runtime interno **21**.
- Validación de esta entrega: **351 pruebas** + `release check`; Ruff queda para la CI/equipo porque no está instalado en este entorno.

## Novedad 3.8.49 · DataProvider común para fuente actual, CSV y futuro Opta

- `lpf_data_provider.py` congela `DataProvider` v1 y `ProviderData`: zonas, resultados, Anual, Apertura, promedios previos, fixture, vías de clasificación y reglas llegan al snapshot con la misma forma sin importar el origen.
- Streamlit ya construye su snapshot a través de `CurrentProvider`; un guard de arquitectura impide volver a saltarse esa frontera.
- `CsvProvider` permite reproducir la misma entrada desde CSV y valida encabezados, resultados, fixture e interzonales. Los tests prueban que una misma foto vía fuente actual o CSV produce el mismo snapshot.
- `service_capabilities()` publica `data_provider_contract_version = 1` y las implementaciones de referencia `current` / `csv`. Un futuro Opta sólo debe implementar `load() -> ProviderData`; no toca motores ni reglas.
- No se agregó FastAPI ni SDK de Opta. Runtime interno **20**; Public Service sigue en **v1**. Suite: **346 pruebas**.


La versión 3 prioriza tres objetivos:

1. **Base coherente:** Zonas, Tabla Anual, promedios, fixture y resultados se reconcilian antes de habilitar una cuenta.
2. **Explicación honesta:** distingue hechos exactos, mínimo posible, total seguro, mínimo que asegura y estimaciones.
3. **Uso guiado:** ya no es necesario recordar preguntas del chat; el Explorador permite elegir equipo, objetivo y tarea.




## Novedad 3.8.48 · La propia app usa el contrato público

- Streamlit empieza a consumir `lpf_services.calculate()` en Previa, Últimas fechas/definición, puntos por objetivo, descenso exacto y la cifra destacada de chances para Playoffs/Copas.
- La UI vuelve a convertir JSON en DataFrame únicamente para mostrarlo; los cálculos principales ya cruzan la misma frontera que usaría una futura web externa.
- Datos y auditoría muestra versión del contrato/snapshot y fallbacks de compatibilidad de la sesión.
- Excepciones deliberadas: rival clave exacto y tablas completas de probabilidades siguen en sus helpers contextuales para evitar recomputación innecesaria.
- Public Service **v1**, Runtime interno **19**, suite **340 pruebas**.

## Novedad 3.8.47 · Contrato público mínimo listo para HTTP/Opta

- `lpf_services.calculate()` fija una superficie pública v1 de **7 operaciones**: `standings`, `preview`, `objective_points`, `objective_chances`, `definition`, `relegation` y `competition_batch`.
- El formato recomendado de entrada es el **snapshot canónico**; una integración externa ya no necesita reconstruir `base`, `remaining`, cortes ni la Tabla Anual reducida.
- `preview` devuelve Markdown + escenarios como JSON, sin filtrar `DataFrame`. `definition` conserva los condicionales y “¿Por qué?” exactos.
- `objective_chances` queda separado del motor exacto: **6.000 simulaciones por defecto**, salida rotulada como `estimated`, semilla explícita y 100% directo sin Monte Carlo cuando la plaza ya está resuelta por otra vía.
- `relegation` expone la foto actual + piso de permanencia opcional y marca la respuesta como incompleta si faltan antecedentes de promedios.
- No se agrega FastAPI todavía: un futuro servidor sólo tendrá que parsear JSON, llamar `calculate()` y mapear `ContractError` a HTTP.
- Runtime interno **19**; suite **335 pruebas**.


## Novedad 3.8.46 · Comparaciones sin preselecciones engañosas

- En **Visualizaciones → Últimas fechas → Matriz de la fecha**, sólo queda preseleccionado el equipo bajo la lupa. Los rivales cercanos al equipo/corte se muestran como sugerencias editoriales, pero el editor decide cuáles agregar.
- La selección de la matriz ahora tiene estado separado por equipo bajo la lupa, evitando heredar comparaciones elegidas para otro club.
- **Rival clave** conserva su sugerencia automática porque surge del impacto exacto de la otra cancha, pero la interfaz la rotula como sugerencia editable y aclara que no es aleatoria.

## Novedad 3.8.45 · Definición directa desde el snapshot

- `calculate_definition()` acepta ahora `snapshot + team + objective + round/fecha`; ya no hace falta preparar `base`, `remaining`, `pending_matches` ni `cutoff`. Para Playoffs sólo se agrega `zone`.
- `competition_batch` suma `type=definition`, con la misma resolución automática para **Playoffs, Libertadores y Sudamericana**.
- La fecha se resuelve contra el fixture/pending canónico del snapshot. `round` es el campo estable y `fecha` un alias editorial; si no se informa, se usa la jornada operativa vigente.
- Si el objetivo ya está resuelto por una vía directa, la definición se devuelve como resuelta antes de enumerar ramas.
- En **Visualizaciones → Últimas fechas** aparece una guía visible de `🔍 ¿Por qué?`: debajo de la matriz general, dentro de la matriz de rival clave y antes del Reloj de definición para G/E/P.
- Runtime interno **19**; suite **328 pruebas**.


## Novedad 3.8.44 · Snapshot con objetivos de Playoffs y Copas

- El snapshot canónico sube a **schema 2** e incorpora `qualification`: universo elegible, corte efectivo y vías directas para **Playoffs, Libertadores y al menos Sudamericana**.
- `prepare_competition_snapshot()` acepta campeones/vías internacionales y reglas de formato sin mezclar esos datos con las reglas de descenso.
- `competition_batch` agrega `objective_status` y permite usar `objective=playoffs|libertadores|sudamericana` también en `objective_points`, `point_ladder` y `rank_window`, sin enviar una Tabla Anual reducida ni repetir el `cutoff`.
- Un club ya clasificado a Libertadores por otra vía se devuelve como **objetivo resuelto**, con su motivo, en vez de aparecer como equipo desconocido. Para Sudamericana, esa misma plaza superior se reconoce como objetivo ya cumplido.
- Snapshots schema 1 siguen aceptándose para consultas antiguas; las consultas directas por objetivo requieren el contexto schema 2.
- Runtime interno **18**; suite **323 pruebas**.


## Novedad 3.8.43 · Definición reutilizable fuera de Streamlit

- El contexto de **Playoffs / Libertadores / al menos Sudamericana** ya no se arma dentro de la UI: `lpf_editorial_definition.objective_context` recibe datos explícitos y devuelve tabla efectiva, corte y vías directas.
- La garantía y la primera fecha en la que puede alcanzarse el total que asegura también quedan en helpers puros.
- Nuevo `definition_snapshot`: zona de pelea + matriz G/E/P + rival clave opcional + prueba + garantía + reloj en una estructura JSON-safe, sin probabilidades.
- `lpf_services.calculate_definition()` expone ese mismo paquete para una futura API/Opta sin importar Streamlit. El contrato externo sigue en versión 1 porque la operación es aditiva.
- Runtime interno **17**; suite **317 pruebas**.


## Novedad 3.8.42 · “¿Por qué?” también para lo que no alcanza

- La explicación exacta distingue **asegura / no asegura todavía / queda dentro del corte esta fecha / depende / queda eliminado / objetivo inalcanzable**.
- Cuando un resultado propio no basta, muestra qué parte falta: condición favorable suficiente, condición necesaria o, si existe, una **condición adversa suficiente para quedar afuera**.
- Estar dentro del corte al terminar una jornada ya no se redacta como clasificación asegurada cuando todavía quedan fechas.
- La matriz general multiequipo agrega un “¿Por qué?” seleccionable por equipo y G/E/P. Todo sigue siendo enumeración matemática, separada de Monte Carlo.
- Runtime interno **16**; suite **312 pruebas**.

## Novedad 3.8.41 · Definición visual exacta

- **Últimas fechas** deja de apoyarse en gráficos de margen abstractos y pasa a una lectura periodística: **Zona de pelea**, **matriz G/E/P seleccionable**, **semáforo compacto**, **matriz de rival clave**, **árbol reducido** y **reloj de definición**.
- El objetivo activo puede ser **Playoffs, Libertadores o al menos Sudamericana**. Para copas se usa la Tabla Anual sin los clasificados directos a Libertadores y el corte efectivo correspondiente; las vías directas se muestran aparte.
- Las dos matrices permiten elegir equipos. En la doble entrada se selecciona el equipo principal y el rival a cruzar; los demás partidos quedan abiertos y se enumeran exactamente dentro de cada celda.
- Nuevo **“¿Por qué?”** a demanda: cuando una rama asegura o elimina, explica la prueba matemática (puntos tras la fecha, combinaciones verificadas y cantidad máxima/mínima de rivales que todavía pueden superarlo). Las condiciones suficientes se distinguen de las meramente necesarias.
- `lpf_editorial_definition.py` concentra la transformación editorial sin Streamlit. `lpf_conditionals.py` agrega prueba auditable y matriz de rival clave. `LPF_RUNTIME_API` sube a **16** porque el nuevo módulo entra al núcleo crítico. Suite: **309 pruebas**.


## Novedad 3.8.40 · El objetivo no se pierde al cambiar de vista

- Playoffs, Libertadores, al menos Sudamericana y Descenso comparten un **objetivo activo** entre Panel por equipo, Mesa de redacción, Visualizaciones y chat.
- El explorador del chat muestra ese objetivo y sus atajos genéricos ya no fuerzan Playoffs.
- Previa y “La otra cancha” permiten elegir una **fecha oficial específica** en todas las vistas principales; el chat entiende también “Fecha N”.
- La otra cancha no fabrica recomendaciones si la clasificación internacional ya está resuelta por una vía directa o si el equipo está fuera del área de riesgo de descenso usada por esa herramienta.
- Suite: **301 pruebas**. Runtime interno: **15**.

## Novedad 3.8.39 · Previa y probabilidades con criterios visibles

- Las simulaciones publicables generales quedaron unificadas en **6.000** corridas.
- La Previa distingue próximo partido real, fecha oficial y fecha + postergados.
- Los interzonales de playoffs usan el rival real; la narrativa separa PJ, partidos por jugar y puntos totales.
- Suite: **296 pruebas**.

## Novedad 3.8.38 · Qué tiene que pasar + descenso sin desempates falsos

- **Visualizaciones → Últimas fechas → Condicionales de un equipo** agrega una matriz **EXACTA** de la próxima fecha para cada rama: si gana, empata o pierde. Enumera sólo las otras canchas capaces de mover su zona y separa **asegura playoffs / sigue en carrera / queda eliminado**.
- La misma vista agrega dos gráficos: estado matemático de la pelea y posición al cierre de la fecha, más una narrativa que busca condiciones simples suficientes del tipo **“X no gana y Y pierde”** cuando realmente alcanzan.
- Las barras son **frecuencia combinatoria, NO probabilidad**: cada combinación de resultados ajenos cuenta una vez. El Monte Carlo de “La otra cancha” sigue aparte y rotulado como ESTIMADO.
- La herramienta se habilita desde que el equipo entra en la ventana exacta de **8 partidos o menos**; con **4 o menos** muestra explícitamente **Modo definición**, porque ahí los condicionales suelen volverse editorialmente decisivos.
- Auditoría de descenso: si hay igualdad en una posición de descenso, la app deja de elegir un “último” por DG. Informa **partido desempate** y, si el empate es por promedios, también reconoce que la identidad del descenso por la Anual puede depender de quién baje primero por esa vía.
- Se agregan `lpf_conditionals.py` y `lpf_relegation.py` al núcleo crítico. `LPF_RUNTIME_API` sube a **15**. Suite: **290 pruebas**.

## Novedad 3.8.37 · Copas: puntos por Tabla Anual sin confundir vías directas

- **Puntos por objetivo** deja de presentar los pisos de copas como si describieran todas las vías de clasificación: ahora las filas dicen explícitamente **Libertadores por Tabla Anual** y **Al menos Sudamericana por Tabla Anual**.
- Ganar el Clausura o la Copa Argentina sigue siendo una vía independiente y no se convierte artificialmente en un número de puntos de la Anual.
- Los equipos que ya tienen una plaza directa dejan de desaparecer de la vista. Por ejemplo, Belgrano (campeón del Apertura) figura como **ya clasificado a Libertadores por una vía directa**, sin atribuir esa plaza a un mínimo de puntos.
- En la tabla de todos los equipos, los clasificados por otra vía aparecen con `Tipo de dato = Vía directa`; el resto conserva exactamente el mismo motor de pisos por corte.
- No cambia la matemática de la vía anual ni el runtime interno. `LPF_RUNTIME_API` permanece en **14**. Suite: **279 pruebas**.

## Novedad 3.8.36 · Escalera exacta coherente entre pantallas

- Se corrige una inconsistencia del tramo final: `point_ladder` ya no cuenta partidos entre dos equipos ajenos a la tabla que está resolviendo.
- Los **interzonales se conservan** si uno de sus equipos pertenece a la zona, porque sí pueden modificar sus puntos.
- Con ocho fechas por jugar el fixture LPF tiene 120 partidos globales, pero sólo 64 pueden mover una zona: antes Radar/Escenarios podían apagar el solver por superar el límite de 110 mientras Puntos por objetivo sí calculaba; ahora todos comparten la misma lectura.
- No cambia la firma del motor ni el runtime interno. `LPF_RUNTIME_API` permanece en **14**. Suite: **274 pruebas**.

## Novedad 3.8.35 · Últimas fechas más visuales y chat dentro de Mesa de redacción

- **Chat libre** deja de ocupar un acceso principal: toda su funcionalidad queda dentro de **Mesa de redacción → Consultas y chat**. Las sesiones viejas que apuntaban a Chat libre migran automáticamente a Mesa de redacción.
- **Visualizaciones → Últimas fechas** pasa a funcionar como un tablero de definición: tabla exacta por zona, gráfico de puntos actuales + margen disponible y calendario comparado.
- Para un equipo elegido muestra el condicional **gana / empata / pierde** del próximo partido, con mejor/peor puesto y gráfico del rango.
- Dentro de la ventana exacta se puede abrir la **escalera exacta por puntaje final**; además hay un cálculo opcional ESTIMADO de qué resultados ajenos de la fecha modifican más su chance de playoffs.
- No cambia ninguna fórmula del motor. `LPF_RUNTIME_API` permanece en **14**. Suite: **272 pruebas**.

## Novedad 3.8.34 · Previa por equipo fuera del monolito

- Nuevo `lpf_preview.py`: construye el texto y la tabla exacta de la Previa por equipo sin leer Streamlit ni red.
- `lpf_previa_equipo_texto` queda como adaptador corto: resuelve agenda, `n_anual` y contexto de copas desde sesión y delega en el módulo puro.
- Se verificó equivalencia exacta contra 3.8.33 en Playoffs, Descenso y Copas, comparando Markdown, DataFrame y atributos de exportación.
- `LPF_RUNTIME_API` sube a **14** y `lpf_preview.py` entra al núcleo crítico. Suite: **269 pruebas**.


## Novedad 3.8.32 · Releases verificables y paquetes sincronizados

- Nuevo `tools/release.py`: valida de forma estática la versión, el runtime requerido por la app, todos los componentes críticos, `pyproject.toml`, README, CHANGELOG y la sintaxis Python antes de empaquetar.
- El constructor genera siempre un ZIP completo, un ZIP de **sincronización de núcleo** y, si recibe una versión base, un incremental que incluye el núcleo completo aunque sólo haya cambiado un archivo de UI o documentación.
- `pyproject.toml` deja de quedar congelado en 3.8.1: desde esta versión su metadata también debe coincidir con `lpf_version.__version__`.
- El runtime interno no cambia: sigue en **13** porque no se modificó ningún contrato de la app. Suite: **261 pruebas**.


## Novedad 3.8.31 · Promedios con contrato explícito

- Nuevo `lpf_averages.py`: separa **antecedentes de temporadas previas** de **totales acumulados usados para el promedio**.
- Se corrige un error de denominador: la temporada 2026 toma tanto puntos como PJ de la Tabla Anual; los PJ del Clausura ya no reemplazan los PJ anuales.
- La foto interna sincronizada valida la corrección en **30/30 equipos**. Boca, por ejemplo, queda en 159 puntos / 90 PJ, igual que la fuente, no 159/74.
- El Monte Carlo de descenso recibe previas y construye `average_totals` antes de simular; la vista exacta, snapshots y simulación comparten ahora la misma frontera.
- `LPF_RUNTIME_API` sube a **13**. Suite: **255 pruebas**.

## Novedad 3.8.30 · Orden de Accesos principales

- **Puntos por objetivo** pasa al último lugar de la barra **Accesos principales**.
- **Panel por equipo** queda como primer acceso y también como vista inicial cuando no hay una selección previa guardada.
- No cambia ninguna función, cálculo ni destino de navegación. `LPF_RUNTIME_API` permanece en **12**. Suite: **247 pruebas**.

## Novedad 3.8.29 · Auditoría del modelo probabilístico

- Se detectó y corrigió una inconsistencia activa: **“Realidad y proyección”** usaba 27% de empate, localía 1,08 y una fuerza distinta, mientras el Monte Carlo principal usaba 26%, localía 1,22 y `lpf_form`. Ahora ambos usan el mismo kernel y la misma fuerza canónica.
- La simulación de zona ya respeta el **rival interzonal real y su localía** cuando el fixture/fortaleza están disponibles; antes ese partido podía caer al respaldo de “rival promedio”.
- La vista **Puntos y puesto final** informa cuántas corridas sostienen la mediana condicionada y advierte si son menos de 100.
- Auditoría congelada con la foto real del Clausura al 11/08/2026 20:28 ART (59 partidos, Talleres–Lanús pendiente): el modelo canónico tuvo log-loss 1,037 frente a 1,057 del modelo alternativo. La muestra es chica y **no se usó para recalibrar parámetros**.
- `LPF_RUNTIME_API` sube a **12** e incorpora `lpf_competitive_context.py` al núcleo crítico. Suite: **246 pruebas**.

## Novedad 3.8.28 · Contexto Monte Carlo explícito

- `lpf_simulation.build_simulation_context` arma la Anual, la tabla reducida, cupos y bases de simulación sin leer estado de interfaz.
- `_lpf_ctx` conserva la firma histórica, pero sólo aporta los fallbacks de Apertura, Anual directa y reemplazo de Copa Argentina que estaban guardados en sesión.
- La extracción se comparó contra 3.8.27 en **500/500** estados con equivalencia exacta.
- `LPF_RUNTIME_API` sube a **11**. Suite: **237 pruebas**.

## Novedad 3.8.27 · Primitivas Monte Carlo fuera de Streamlit

- Nuevo `lpf_simulation.py`: simula posiciones/puntos por zona, suma de puntos de todos los pendientes y cumplimiento de objetivos sin importar Streamlit ni red.
- La fuerza sigue entrando desde `lpf_form.py`; el wrapper Streamlit sólo aporta esa fuerza y conserva las firmas históricas.
- Equivalencia contra 3.8.26: 500 casos de zona + 500 wrappers, 800 matrices globales y 900 máscaras de objetivos, sin diferencias.
- `LPF_RUNTIME_API` sube a **10** y `lpf_simulation.py` entra en el núcleo crítico. Suite: **234 pruebas**.

## Novedad 3.8.26 · Forma y fuerza de simulación desacopladas

- `lpf_form.py` concentra la forma reciente, las rachas y la fuerza regularizada usada por chances, previa, “qué le conviene” y la distribución de puntos por puesto.
- El modelo recibe la foto del Apertura por parámetro; ya no necesita leer `session_state` para calcular una fuerza. Streamlit conserva sólo un wrapper que aporta ese antecedente.
- No cambian pesos ni probabilidades: se mantiene exactamente el modelo 3.8.25. La equivalencia se comprobó con **1.000 + 800 + 400 casos** contra la implementación anterior.
- `LPF_RUNTIME_API` sube a **9** y `lpf_form.py` entra en el núcleo crítico. Suite: **229 pruebas**.


## Novedad 3.8.25 · Puesto específico: estimación útil y extremos separados

- En **Escenarios → Puntos y puesto final**, elegir 8º (o cualquier otro puesto) ya no muestra una lista de extremos matemáticos como si todos fueran igual de representativos.
- La vista principal usa **6.000 simulaciones** y toma sólo las corridas en las que el equipo termina en el puesto elegido. Muestra **mediana estimada**, **50% central**, frecuencia por puntaje y chance de terminar en ese puesto.
- La mediana es probabilística: se calcula sobre las corridas condicionadas al puesto, no sobre los puntajes alcanzables.
- Los extremos matemáticos quedan aparte, bajo una opción explícita **sin probabilidad**, y sólo se publican como puesto exacto si existe un escenario que lo define por puntos sin necesitar un desempate futuro.
- `LPF_RUNTIME_API` sube a **8** porque Streamlit requiere el nuevo solver de `lpf_scenarios`. Suite: **224 pruebas**.


## Novedad 3.8.24 · Contexto de copas desacoplado

- `lpf_qualification.py` también normaliza los clasificados ya fijos a Libertadores, los equipos vivos en Copa Argentina y la marca de actualización/fuente usada por las narrativas.
- Los helpers del archivo Streamlit sólo leen los fallbacks de sesión y delegan; una API puede aportar esos datos explícitamente sin importar la UI.
- La implementación se comparó contra 3.8.23 en **600 estados de sesión / 1.800 comparaciones** y mantiene exactamente las mismas salidas.
- `LPF_RUNTIME_API` sube a **7** para impedir que el archivo principal nuevo se mezcle con un `lpf_qualification.py` viejo. Suite: **217 pruebas**.


## Novedad 3.8.23 · Anual y plazas de copas desacopladas

- `lpf_qualification.py` concentra la construcción autoritativa de la Tabla Anual y el reparto reglamentario de plazas de Libertadores/Sudamericana sin Streamlit ni red.
- `lpf_anual_base` y `lpf_plazas_copas` quedan como wrappers de UI: sólo aportan candidatos de sesión y delegan la lógica.
- La implementación se comparó contra 3.8.22 en **300 casos de Anual + 600 combinaciones de cupos** con equivalencia exacta.
- `LPF_RUNTIME_API` sube a **6** y el nuevo módulo entra en el chequeo previo de despliegue. Suite: **213 pruebas**.


## Novedad 3.8.22 · Carga de resultados desacoplada

- `lpf_result_updates.py` aplica resultados pendientes sobre copias de las zonas y calcula qué equipos cambiaron de puesto, sin Streamlit ni red.
- La Mesa de redacción conserva el formulario y la persistencia de sesión, pero ya no contiene las reglas de actualización de PJ/GF/GA/DG/PTS ni el cálculo de cambios de posiciones.
- La lógica nueva se comparó contra 3.8.21 en **500 + 300 casos** y el wrapper completo en **250 ejecuciones** con equivalencia exacta.
- `LPF_RUNTIME_API` sube a **5** y el módulo entra en el chequeo de despliegue. Suite: **206 pruebas**.


## Novedad 3.8.21 · Agenda real de la Previa desacoplada

- `lpf_schedule.py` concentra la lógica pura de calendario: hora argentina, agenda por partido, jornada operativa, postergados y orden por fecha/hora real.
- La Previa sigue leyendo la programación disponible desde Streamlit, pero ya no decide dentro de la UI qué partido es realmente el próximo ni qué encuentros pertenecen al mismo día.
- La implementación se comparó contra 3.8.20 en **120 fotos** y **720 consultas de alcance** con equivalencia exacta.
- `LPF_RUNTIME_API` sube a **4** y el nuevo módulo entra en el chequeo de despliegue. Suite: **200 pruebas**.


## Novedad 3.8.20 · Escenarios más claros

- **“Puntaje y puesto”** pasa a llamarse **“Puntos y puesto final”**.
- La pantalla separa la escalera de puntos para clasificar de la búsqueda de un puesto específico.
- La búsqueda por puesto explica que el mismo total puede producir posiciones distintas según otros resultados y desempates.
- La tabla usa columnas directas: puntos finales, mejor puesto y peor puesto con esos puntos. Suite: **194 pruebas**.

## Novedad 3.8.19 · Revalidación de sesiones fuera de Streamlit

- `_lpf_refresh_quality` ya no decide cómo migrar una sesión vieja ni reconstruye la Tabla Anual dentro de la UI.
- `lpf_state.refresh_lpf_quality_state` recibe zonas, candidatos de Apertura, Anual, promedios, fixture, resultados y alertas de fuente; devuelve Apertura seleccionado, Anual autoritativa y auditoría sin leer `session_state`.
- Streamlit sólo persiste los valores devueltos. La implementación se comparó contra 3.8.18 en **7 escenarios dirigidos** y conservó exactamente reporte y efectos de sesión.
- Como el archivo principal requiere esta nueva frontera de `lpf_state`, `LPF_RUNTIME_API` sube a **3** en todos los módulos críticos. Suite: **192 pruebas**.

## Novedad 3.8.18 · Respaldo válido fuera de Streamlit

- El último respaldo de zonas + Tabla Anual se construye, serializa, escribe y recupera en `lpf_table_backup.py`; ese módulo no importa Streamlit ni proveedores.
- Streamlit conserva sólo una copia opcional en sesión y delega el filesystem. Se mantiene la prioridad **sesión → disco**, el vencimiento de una semana y la lectura de formatos legacy.
- La recuperación se comparó contra 3.8.17 en cinco escenarios y conserva exactamente las mismas salidas/diagnósticos.
- `lpf_table_backup.py` entra en el chequeo de compatibilidad de despliegue. Suite: **189 pruebas**.

## Novedad 3.8.17 · Política de fuentes fuera de Streamlit

- `lpf_tables_with_fallback` ya no decide dentro del archivo principal qué combinación usar entre ESPN, FutbolArgentino.com, último respaldo y Tabla Anual local.
- La prioridad vive en `lpf_table_selection.select_lpf_tables`, módulo puro sin Streamlit, red, disco ni estado de sesión.
- Streamlit queda como orquestador: obtiene candidatos, carga el respaldo/locales, delega la decisión y sólo persiste una foto cuando corresponde.
- La nueva política se comparó contra 3.8.16 en **9 escenarios dirigidos** y devolvió exactamente las mismas tablas, fuentes, advertencias, errores y decisiones de guardado.
- `lpf_table_selection.py` entra en el chequeo de compatibilidad de despliegue. Suite: **180 pruebas**.


## Novedad 3.8.16 · Fixture FutbolArgentino.com sin orquestación de red en Streamlit

- Las dos consultas de resultados de FutbolArgentino.com, sus cache-busters y los fallos parciales se coordinan ahora en `lpf_http.fetch_futbolargentino_results_pages`.
- `futbolargentino_fixture` conserva la caché de Streamlit, pero ya no arma URLs ni controla el ciclo de requests; sólo interpreta y valida las respuestas obtenidas.
- La ruta se comparó contra 3.8.15 en cuatro escenarios dirigidos y conserva salida, errores y URLs consultadas. Suite: **172 pruebas**.
- El contrato interno de deploy sube a `LPF_RUNTIME_API = 2`; al actualizar esta versión hay que reemplazar **todos los archivos incluidos en el ZIP de actualización** para que el chequeo previo pueda detectar mezclas.
- Football-data y Apify siguen deshabilitados y no se reactivaron.

## Novedad 3.8.15 · Scoreboards ESPN sin orquestación de red en Streamlit

- La ventana de resultados/fixture ESPN (fecha inicial, bloques de 21 días, límite de consultas y fallos parciales) vive ahora en `lpf_http.fetch_espn_scoreboard_window`.
- `espn_fixture` conserva la caché de Streamlit inyectando `_espn_get`, pero ya no construye requests ni fechas por su cuenta; el parser sigue en `lpf_provider_adapters`.
- La ruta fue comparada contra 3.8.14 con transporte simulado y conserva exactamente salida y metadatos. `lpf_http.py` también entra en el chequeo previo de archivos desincronizados. Suite: **170 pruebas**.
- Football-data y Apify se confirmaron deshabilitados en la UI actual; no se movieron ni se reactivaron.

## Novedad 3.8.14 · URLs avanzadas sin parsing dentro de Streamlit

- `tabla_desde_url` y `partidos_desde_url` quedaron como wrappers finos: descargan el HTML y delegan la interpretación.
- `competition_html_adapters.py` parsea tablas de posiciones y matrices equipo × equipo sin red ni Streamlit.
- `lpf_http.fetch_url_text` concentra el transporte histórico de esas URLs sin cambiar su semántica.
- Hay fixtures locales para tabla, una rueda e ida/vuelta, comparados contra el código 3.8.13.
- El runtime también verifica que el nuevo adaptador esté presente en deploys manuales. Suite: **166 pruebas**.

## Novedad 3.8.13 · Snapshot versionado y validado

- La foto canónica de competencia declara `snapshot_schema_version = "1"`, independiente de la versión del motor y del contrato de servicios.
- Antes de ejecutar un batch se validan estructura e invariantes simples: equipos/zonas, pendientes, `remaining` y reglas. Si una foto está desincronizada, falla antes de llegar al optimizador.
- El batch acepta directamente el sobre completo de `prepare_competition_snapshot`, además del `result` crudo.
- `service_capabilities()` publica las operaciones y tipos de consulta soportados, la versión del snapshot y la ventana exacta de 8 partidos.
- No se agregó servidor HTTP ni SDK de Opta. Suite: **160 pruebas**.

## Corrección 3.8.12 · Deploy sincronizado

- Streamlit comprueba al arrancar que los módulos críticos pertenecen al mismo nivel de compatibilidad antes de importarlos.
- Si detecta un archivo viejo o faltante, se detiene con un mensaje claro que enumera qué módulos hay que actualizar, en vez de terminar más adelante con un `NameError` o `AttributeError`.
- El sidebar muestra la versión efectiva del motor (la toma de `lpf_version.__version__`) para verificar rápidamente qué commit tomó Streamlit Cloud.
- Este cambio no toca ninguna fórmula ni resultado. Suite: **154 pruebas**.

## Novedad 3.8.11 · Total seguro vs. mínimo que asegura

- La interfaz y todas las narraciones dejan de usar **“garantía exacta”** y **“referencia conservadora”** como etiquetas visibles.
- **Total seguro** significa: si el equipo llega a esa marca, el objetivo queda asegurado, pero todavía puede existir un total menor que también lo asegure.
- **Mínimo que asegura** significa: el motor exacto comprobó que es el menor total alcanzable que asegura el objetivo en todos los escenarios compatibles.
- Antes de la ventana exacta se muestra el **total seguro** y se dice expresamente que todavía no sabemos si es el menor. Con ocho partidos restantes o menos se busca el **mínimo que asegura**.
- Los máximos individuales de rivales se muestran uno por línea y se aclara que no todos pueden alcanzarlos simultáneamente por los cruces entre sí.
- La API agrega los alias editoriales `minimum_guarantee` y `safe_total`; mantiene `exact_guarantee`, `conservative_reference`, `safe_value` y `floor` por compatibilidad.

## Corrección 3.8.10 · Compatibilidad de actualización parcial

La UI y la fachada de servicios toleran temporalmente objetos `PisoObjetivo` de 3.8.7 o anteriores. Esto evita `AttributeError` si un despliegue manual reemplaza el archivo principal pero deja un `lpf_pisos.py` viejo. La recomendación sigue siendo desplegar todos los archivos del paquete de actualización.

## Novedad 3.8.9 · Foto completa para Streamlit/API

- `lpf_snapshot.py` reúne en una sola foto JSON-safe zonas, Anual, Apertura, jugados, pendientes, partidos restantes, antecedentes de promedios, fixture, reglas y auditoría.
- `lpf_services.prepare_competition_snapshot` prepara esa foto y `calculate_competition_batch` permite ejecutar varias consultas sobre la misma entrada sin repetir carga/reconciliación.
- El batch cubre puntos por objetivo, escalera exacta, rango de puesto y descenso combinado Anual + promedios.
- La fórmula que arma los totales de promedios salió de Streamlit y quedó en `lpf_pisos.promedio_totales`, compartida por UI y futura API.
- No se agregó servidor HTTP ni SDK de Opta. Un futuro adaptador Opta sólo debe producir la entrada normalizada para esta misma foto.
- Suite de esa versión: **147 pruebas**.

## Novedad 3.8.8 · Nombres editoriales unificados

- Desde 3.8.11, la app usa **mínimo posible**, **total seguro** y **mínimo que asegura** para no mezclar números con significados distintos.
- El total seguro asegura si se alcanza, pero puede pedir puntos de más; el mínimo que asegura es el menor total comprobado.
- Promedios muestra **Mínimo final** (si pierde todo) y **Máximo final** (si gana todo), en lugar de “piso/techo”.
- Se corrigió el objetivo combinado de no descenso para que Anual y promedios se evalúen juntos antes de declarar al equipo salvado.
- Suite de esa versión: **140 pruebas**.

## Corrección 3.8.6 · Streamlit

- Corregida una referencia residual a `_lpf_add_source_issues` que podía producir `NameError` al entrar al newsroom/auditoría en Streamlit.
- `_lpf_refresh_quality` usa ahora explícitamente `lpf_state.add_source_issues` con los mensajes guardados en la sesión.
- Se agregaron pruebas de regresión del puente entre la interfaz y los módulos extraídos. Suite de esa versión: **132 pruebas**.

## Novedad 3.8.5 · Contrato de cálculos para una futura API

- `lpf_services.py` expone cálculos con entrada/salida JSON-safe y, desde 3.8.9, una foto canónica reutilizable con consultas por lote.
- Los servicios sólo traducen/validan el contrato y reutilizan los motores existentes; no hay matemática duplicada.
- Todas las respuestas llevan `contract_version` y `calculation_version`. Los errores de entrada usan `ContractError` con código y campo estables.
- `lpf_version.py` es ahora la única fuente de versión, por lo que una API no necesita importar Streamlit para identificar el motor.
- `API_CONTRACT.md` documenta payloads y respuestas. Todavía no se agregó un framework HTTP ni un SDK de Opta.
- Suite: **130 pruebas** más 980 comparaciones aleatorias de equivalencia del servicio de standings.

## Novedad 3.8.4 · Proveedores desacoplados de HTTP

- `lpf_http.py` hace únicamente transporte HTTP y no conoce Streamlit ni el modelo LPF.
- `lpf_provider_adapters.py` transforma respuestas ya descargadas de ESPN/FutbolArgentino.com en estructuras del dominio sin red ni estado de UI.
- Los scoreboards ESPN devuelven resultados, pendientes, agenda y metadatos; la persistencia queda en el wrapper Streamlit.
- Hay respuestas de ejemplo guardadas en `tests/fixtures/`, por lo que los parsers se validan offline.
- La frontera queda: **proveedor → transporte → adaptador → `lpf_loading` → `lpf_state` → motores → Streamlit/API**. Un futuro Opta entra como otro adaptador, sin tocar la matemática.
- Suite: **122 pruebas**, con equivalencia contra 3.8.3 para las rutas de parsing extraídas.

## Novedad 3.8.3 · Entrada de datos preparada para API/Opta

- `lpf_loading.py` separa la preparación determinística de datos del I/O: no importa Streamlit, no hace requests y no persiste snapshots.
- `cargar_lpf_todo` y `cargar_lpf_espn` quedan como adaptadores: obtienen/leen datos y delegan normalización, merge, reconciliación e inferencia.
- `normalize_results_for_zones` define una entrada común de resultados para proveedores actuales o futuros; un adaptador Opta sólo deberá traducir su payload a esa estructura canónica.
- El flujo queda explícito: **proveedor → fetch/adaptador → `lpf_loading` → `lpf_state` → motores → Streamlit o futura API**.
- No se agregó todavía FastAPI ni SDK de Opta. La suite queda en **115 pruebas** y la preparación de carga se comparó por equivalencia contra 3.8.2 en rutas offline y automáticas.

## Novedad 3.8.2 · Estado y motor desacoplados

- El orden, las posiciones y la tabla se calculan ahora en `lpf_standings.py` sin leer Streamlit ni depender de una fuente de datos.
- El estado LPF canónico se arma en `lpf_state.py`: las fuentes ya normalizadas entran por parámetros y Streamlit queda sólo como consumidor/persistencia.
- Los criterios de desempate se pasan de forma explícita al motor; la interfaz conserva un adaptador mínimo que inyecta la selección de la sesión.
- Estas separaciones permiten que una futura API use el mismo núcleo matemático y el mismo constructor de estado; un futuro adaptador Opta se limita a normalizar datos antes del cálculo.
- El motor de posiciones conserva su validación de 1.470 casos aleatorios; el constructor de estado se comparó con la 3.8.1 en cinco rutas de carga.

## Novedad 3.8.0 · Puntos por objetivo

- Nuevo espacio **Puntos por objetivo**, la puerta de entrada por defecto: en una sola pantalla responde cuántos puntos necesita cada equipo para cada meta.
- El módulo `lpf_pisos.py` unifica el cálculo del piso de playoffs, Libertadores, Sudamericana y no descender. Los tres primeros son el mismo problema —quedar por encima de un corte en un conjunto de equipos— y se resuelven con la misma función.
- Para cada objetivo informa tres números que no se mezclan: **mínimo posible** (existe una combinación favorable), **total seguro** (sabemos que alcanza, aunque puede pedir puntos de más) y **mínimo que asegura** (menor total comprobado que asegura sin depender de nadie ni de desempates).
- "No descender" combina Tabla Anual y promedios y toma la exigencia segura más alta de las dos vías.
- Validado por fuerza bruta en `tests/test_lpf_pisos.py`.

Ver `CHANGELOG.md` para el detalle de esta y las versiones anteriores.

> **¿Vas a continuar el desarrollo (humano o IA)?** Leé primero `INSTRUCCIONES_IA.md`: explica el estado del proyecto, el patrón seguro de extracción de módulos, cómo probar equivalencia y la hoja de ruta de lo que falta.

## Mejora 3.5.2

- El **Chat libre** pasó a funcionar también como **Chat guiado**.
- Nuevo explorador con selector de equipo, rival para comparar y categorías temáticas.
- Buscador de funciones por palabra: playoffs, Libertadores, Sudamericana, descenso, promedios, previa, distribución y otras.
- Cada opción se ejecuta con un botón y envía automáticamente la consulta al chat.
- Se agregó un índice completo de capacidades y se mantiene el campo de texto para preguntas propias y seguimientos.
- Se incorporaron pruebas de regresión para conservar el catálogo, el buscador y la entrada libre.


## Corrección 3.5.1

- Restaurados como botones visibles los seis espacios principales.
- Accesos directos desde el comienzo a todas las herramientas de Escenarios, incluida **Distribución**.
- Las herramientas de Escenarios ya no quedan ocultas dentro de pestañas: se eligen desde un selector visible.
- Se mantienen sin cambios las narrativas de la fecha, Copas y Descenso de la versión 3.5.


## Novedades 3.5

- La previa de cada partido puede sumar ahora el impacto en **Libertadores, Sudamericana y descenso**.
- Nuevo selector para activar o desactivar por separado las capas **Copas** y **Descenso**.
- Copas muestra posición en la Anual, lugar en la carrera por los cupos, cupo actual, distancia al corte y rango posible de la ventana.
- La vista individual explica qué cambia si el equipo gana, empata o pierde y distingue zona de Libertadores, Sudamericana o fuera de copas.
- Descenso se limita a los últimos puestos de la Tabla Anual o de los promedios.
- Para los promedios informa el coeficiente exacto posterior a una victoria, empate o derrota.
- La narrativa evita saturar: no incluye equipos con posibilidades matemáticas remotas al comienzo del torneo.


## Novedades 3.4

- Nueva narrativa breve para la previa de una fecha completa.
- Pantallazo inicial de las dos zonas con líder, corte, primero afuera, puntos y diferencia de gol.
- Relato partido por partido con posición actual, situación respecto del top 8 y rango posible al cierre de la ventana.
- Selector **Toda la fecha / Un partido** dentro de la Mesa de redacción.
- En la vista individual se agregan ramas exactas: qué puesto puede ocupar cada equipo si gana, empata o pierde.
- Los postergados aparecen identificados con su fecha original y los equipos que juegan dos veces no reciben un rango simplificado incorrecto.
- Las probabilidades permanecen separadas y rotuladas como estimación.


## Novedades 3.3

- Relatos de zonas con PTS, PJ, DG, GF, igualdad del corte y tabla resumida.
- Panoramas narrativos de Libertadores, Sudamericana y descenso.
- Explicación de cómo los campeones pueden hacer correr los cupos por la Tabla General.
- Seguimiento editable y cotejable de los equipos vivos en Copa Argentina.
- Campo para el reemplazo de ARGENTINA 3 cuando la plaza debe heredarse dentro de Copa Argentina.
- Nuevos accesos guiados para no depender de memorizar preguntas del chat.


## Instalación

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run calculadora_futbol_argentino.py
```

## Espacios de trabajo

- **Puntos por objetivo:** acceso principal por defecto. Cuántos puntos necesita cada equipo para cada meta.
- **Panel por equipo:** elegí equipo, objetivo y pregunta.
- **Escenarios:** herramientas adaptadas de la calculadora del Mundial: gana/empata/pierde, qué pasa si, puesto puntual, mejor/peor caso, distribución y clasificados/eliminados.
- **Mesa de redacción:** informes de previa y post fecha listos para trabajar.
- **Visualizaciones:** vistas por equipo, zona, próxima fecha, otra cancha y Radar final.
- **Chat guiado + libre:** catálogo por categorías, buscador, botones por equipo y consultas abiertas para seguimientos contextuales.
- **Datos y auditoría:** semáforo de calidad, inconsistencias, partidos inferidos y respaldo.

## Flujo recomendado

1. Cargar la foto offline, actualizar desde el proveedor disponible o pegar los datos.
2. Abrir **Datos y auditoría**.
3. Corregir cualquier bloqueo de Zonas, Tabla Anual o Promedios.
4. Trabajar desde el **Panel por equipo**.
5. Abrir **Escenarios** para explorar combinaciones concretas sin recordar comandos.
6. Abrir **Visualizaciones** o **Mesa de redacción** para profundizar y publicar.

## Cuatro referencias distintas

La aplicación separa con nombres claros cuatro referencias distintas:

- **Corte actual:** puntos que tiene hoy el último clasificado.
- **Mínimo posible:** menor puntaje con el que existe una combinación favorable.
- **Total seguro:** una marca que sabemos que alcanza, aunque puede pedir puntos de más.
- **Mínimo que asegura:** menor total comprobado con el que entra sin depender de otros resultados ni desempates.
- **Corte estimado:** rango probable de la simulación; nunca se presenta como certeza.

Cuando a un equipo le quedan más de ocho partidos, el informe usa un **total seguro**. Apenas entra en sus últimos ocho partidos, el Radar habilita el optimizador exacto, busca el **mínimo que asegura** y arma la escalera de puntajes. En un torneo de 16 fechas, sin postergados, esto ocurre desde la Fecha 9. El umbral se aplica **por equipo y por partidos restantes**, así que los postergados propios sí pueden retrasarlo.

## Datos y fuente de verdad

La prioridad de la versión 3 es:

1. Resultados explícitos para identificar partidos jugados.
2. Foto fija del Apertura más las zonas vigentes para reconstruir la Tabla Anual.
3. Tabla Anual directa solamente si pasa los controles.
4. Inferencia por PJ únicamente como respaldo, siempre rotulada.

Los partidos tienen identidad propia. Un encuentro postergado no se considera jugado solo porque el equipo haya disputado una fecha posterior.

## Exacto, garantía y estimación

- **Exacto:** puntos, PJ, techo, rango por resultados, escenarios factibles y escalera calculada por optimización.
- **Garantía conservadora:** línea segura usada cuando el cálculo exacto completo no se activa.
- **Estimado:** Monte Carlo, dificultad, corte probable e impacto de otras canchas.

El modelo de lenguaje opcional interpreta consultas y redacta. Los números salen siempre de Python.

## Arquitectura

- `calculadora_futbol_argentino.py`: aplicación y compatibilidad con la versión anterior.
- `lpf_models.py`: objetos de dominio, auditoría y resultados estructurados.
- `lpf_data_quality.py`: normalización y reconciliación de Zonas, Anual, Promedios, fixture y resultados.
- `lpf_http.py`: transporte HTTP sin parsing ni Streamlit.
- `lpf_provider_adapters.py`: ESPN/FutbolArgentino.com → estructuras del dominio, sin red.
- `lpf_loading.py`: preparación/reconciliación de cargas ya adaptadas.
- `lpf_state.py`: construcción del estado canónico LPF.
- `lpf_scenarios.py`: optimización exacta para escalera, rangos y ventanas con postergados.
- `lpf_exact.py`: núcleo determinístico original y garantías conservadoras.
- `tests/`: pruebas unitarias, fuerza bruta e invariantes.

Más detalle en [ARCHITECTURE.md](ARCHITECTURE.md).

## Verificación

```bash
python -m py_compile calculadora_futbol_argentino.py lpf_*.py
python -m pytest -q
```

## Documentación

- `AUDITORIA.md`: reglas, alcance de exactitud y controles.
- `ARCHITECTURE.md`: flujo técnico y módulos.
- `GUIA_DATOS.md`: actualización, reconciliación y resolución de conflictos.
- `CHANGELOG.md`: cambios de esta versión.
