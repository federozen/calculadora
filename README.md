# ⚽ Calculadora de Escenarios — Mundial 2026

App interactiva para analizar grupos del Mundial 2026: clasificación, desempate olímpico FIFA, escenarios posibles y probabilidades.

## 🚀 Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tu-app.streamlit.app)

## ✨ Funciones

| Sección | Descripción |
|---|---|
| 📊 Tabla y panorama | Tabla actual + estado de clasificación de cada equipo |
| ❓ ¿Qué necesita? | Qué resultados necesita un equipo para clasificar, ser 1º, etc. |
| 🎯 Puesto puntual | Qué combinaciones lo dejan exactamente en el puesto elegido |
| 🔀 ¿Qué pasa si…? | Fijás condiciones (gana X, empate…) y ves cómo queda el grupo |
| 🧮 Simular resultado | Ingresás un marcador exacto y ves la tabla resultante |
| 🎲 Probabilidades | Estimación Monte Carlo con modelo de Poisson |
| 📈 Distribución | En cuántos escenarios cae cada equipo en cada puesto |
| 🟰 ¿Qué le conviene? | El resultado propio ordenado de mejor a peor para clasificar |
| 🏆 Cuentas de liga | Puntos máximos, número mágico, quién ya aseguró o está eliminado |

## ⚙️ Desempate soportado

- **Olímpico FIFA 2026** — mano a mano primero (pts/dg/goles) → dg general → goles → fair play → ranking
- **Diferencia de gol primero** — Premier League, Bundesliga, Champions fase liga
- **Solo puntos** — sin desempate fino

## 📥 Cómo cargar datos

### Opción 1 — API automática (recomendado)
1. Registrate gratis en [football-data.org](https://www.football-data.org/client/register)
2. Pegá tu API key en el panel lateral
3. Elegí el torneo (`WC` para Mundial) y hacé clic en **Traer datos**
4. Seleccioná el grupo y cargalo

### Opción 2 — Pegar texto a mano
Pegá los resultados en el formato:
```
Grupo A
España 0-0 Cabo Verde
Uruguay 1-1 Arabia Saudita
España vs Uruguay
Cabo Verde vs Arabia Saudita
```
Los partidos jugados se escriben con marcador (`1-0`), los pendientes con `vs`.

## 🛠️ Instalación local

```bash
git clone https://github.com/tu-usuario/calculadora-mundial-2026
cd calculadora-mundial-2026
pip install -r requirements.txt
streamlit run calculadora_mundial.py
```

## 📦 Stack

- [Streamlit](https://streamlit.io/) — UI
- [Pandas](https://pandas.pydata.org/) — manejo de datos
- [NumPy](https://numpy.org/) — simulaciones Monte Carlo
- [football-data.org](https://www.football-data.org/) — API de partidos (opcional)

## 📝 Notas técnicas

- El desempate olímpico se aplica primero entre los empatados en puntos (mano a mano), luego criterios generales.
- El modelo de probabilidades usa distribución de Poisson con media configurable; es orientativo, no oficial.
- Con muchos partidos pendientes, el sistema reduce automáticamente el máximo de goles simulados para mantener el rendimiento.
- Compatible con cualquier liga o torneo que use grupos de 3+ equipos.
