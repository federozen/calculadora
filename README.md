# Calculadora del Fútbol Argentino · LPF 2026 · versión 3.8.4

Aplicación editorial en Python y Streamlit para analizar playoffs por zonas, Tabla Anual, Libertadores, Sudamericana, descenso, promedios y escenarios de una fecha.

La versión vigente siempre está en la constante `__version__` de `calculadora_futbol_argentino.py` (única fuente de verdad). El historial completo está en `CHANGELOG.md`.

La versión 3 prioriza tres objetivos:

1. **Base coherente:** Zonas, Tabla Anual, promedios, fixture y resultados se reconcilian antes de habilitar una cuenta.
2. **Explicación honesta:** distingue hechos exactos, garantías matemáticas, cotas conservadoras y estimaciones.
3. **Uso guiado:** ya no es necesario recordar preguntas del chat; el Explorador permite elegir equipo, objetivo y tarea.

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

## Novedad 3.8.0 · Pisos por objetivo

- Nuevo espacio **Pisos por objetivo**, la puerta de entrada por defecto: en una sola pantalla responde cuántos puntos necesita cada equipo para cada meta.
- El módulo `lpf_pisos.py` unifica el cálculo del piso de playoffs, Libertadores, Sudamericana y no descender. Los tres primeros son el mismo problema —quedar por encima de un corte en un conjunto de equipos— y se resuelven con la misma función.
- Para cada objetivo informa tres números que no se mezclan: **mínimo posible** (existe una combinación favorable), **piso/garantía** (asegura sin depender de nadie ni de desempates) y **cota conservadora** (para ventanas de más de ocho fechas).
- "No descender" combina Tabla Anual (exacta) y promedios (cota segura) y toma el piso más exigente.
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

- **Pisos por objetivo:** acceso principal por defecto. Cuántos puntos necesita cada equipo para cada meta.
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

La aplicación evita llamar “piso” a números diferentes:

- **Corte actual:** puntos que tiene hoy el último clasificado.
- **Mínimo todavía posible:** menor puntaje con el que existe una combinación favorable.
- **Garantía matemática:** puntaje con el que entra sin depender de otros resultados ni desempates.
- **Corte estimado:** rango probable de la simulación; nunca se presenta como certeza.

Cuando a un equipo le quedan más de ocho partidos, el informe usa una **garantía conservadora**: una cota segura que podría pedir algún punto de más. Apenas entra en sus últimas ocho fechas, el Radar habilita el optimizador exacto y arma la escalera de puntajes. El umbral se aplica **por equipo**, así que un partido postergado en otra cancha no bloquea el cálculo exacto del resto.

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
- `lpf_exact.py`: núcleo determinístico original y cotas seguras.
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
