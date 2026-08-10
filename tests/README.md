# Pruebas

Validación por **fuerza bruta** de los motores exactos: en ligas chicas se
enumeran todos los desenlaces posibles y se comparan, resultado por resultado,
contra lo que dicen los solucionadores. Es la evidencia de que "los números
siempre salen de Python y están validados".

La suite actual contiene **122 pruebas**.

| Archivo | Qué cubre |
| --- | --- |
| `test_lpf_scenarios.py` | Motor MILP: `can_qualify` / `can_fail`, rangos de puesto exactos, escalera de puntos (`point_ladder`) y escenarios gana/empata/pierde. |
| `test_lpf_exact.py` | Cotas conservadoras: la línea de garantía y el piso por promedios **nunca declaran una garantía falsa** y nunca piden menos que la garantía exacta real. |
| `test_lpf_text.py` | Utilidades de texto: normalización sin acentos y detección de equipos. |
| `test_lpf_intents.py` | Ruteo de intención del chat: consultas → `{"intent": ...}`. |
| `test_lpf_clubs.py` | Canonicalización de clubes: alias y variantes → nombre canónico. |
| `test_lpf_parsers.py` | Parsers de tablas pegadas: listas, promedios, fixture y Anual. |
| `test_lpf_state.py` | Estado canónico: constructor puro sin Streamlit, prioridad de Apertura, derivación y alertas de procedencia. |
| `test_lpf_loading.py` | Preparación de carga sin I/O: canonicalización de resultados, carga offline, actualización automática, avance de standings, reconstrucción anual y rechazo de fotos insuficientes. |
| `test_lpf_provider_adapters.py` | Fixtures locales de ESPN/FutbolArgentino.com: standings, zonas, scoreboards, estados, deduplicación y metadatos sin red. |
| `test_lpf_http.py` | Transporte HTTP con `requests` simulado; verifica que no mezcle parsing ni Streamlit. |
| `test_lpf_standings.py` | Motor puro de tabla: estadísticas, desempates configurables, mano a mano, fair play/ranking, posiciones y clasificador in/out/pelea. |
| `test_lpf_derive.py` | Derivación: reconstrucción del Apertura e inferencia determinista. |
| `test_lpf_reconcile.py` | Reconciliación: nóminas conocidas, estadísticas, merge sin duplicar, encaje en zonas. |
| `test_data_pipeline.py` | Integridad del flujo: fixture ↔ nóminas, 16 partidos por equipo, datos → tabla y pisos. |
| `test_lpf_pisos.py` | Piso por objetivo: mínimo posible y garantía por objetivo, invariantes y combinación de tablas en el descenso. |

Convenio de desempates (verificado en las pruebas):

- Mínimo posible / mejor puesto / `can_qualify`: desempate **a favor** (sólo
  cuentan los rivales estrictamente por encima).
- Garantía / peor puesto / `can_fail`: desempate **en contra** (cuentan los
  rivales iguales o por encima).

## Ejecutar

```bash
pip install -r requirements.txt
pip install pytest
python -m pytest -q
```
