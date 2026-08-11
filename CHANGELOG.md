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
