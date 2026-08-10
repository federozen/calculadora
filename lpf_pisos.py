"""Piso por objetivo — el mínimo que cada equipo necesita para cada meta.

Este módulo unifica un cálculo que hasta ahora estaba disperso: para cada objetivo
(playoffs, Libertadores, Sudamericana, no descender) responde tres números con
significado distinto y sin mezclarlos:

- **Mínimo posible:** el menor puntaje final con el que *todavía existe* una
  combinación de resultados que logra el objetivo. No es una garantía.
- **Piso (garantía exacta):** el menor puntaje que asegura el objetivo sin
  depender de otros resultados ni de desempates. Sale del optimizador MILP.
- **Piso conservador:** una cota segura para ventanas grandes, cuando el motor
  exacto no se activa. Nunca declara una garantía falsa; puede pedir algún punto
  de más.

Todos los objetivos de tipo "quedar por encima de un corte" (playoffs y las dos
copas) comparten la misma estructura: un conjunto de equipos y un corte. Por eso
se resuelven con la misma función; sólo cambian la tabla base y el corte.

El módulo es Python puro (sin Streamlit) y reutiliza los motores ya validados
por fuerza bruta en ``lpf_scenarios`` y ``lpf_exact``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from lpf_scenarios import point_ladder
from lpf_exact import safe_average_guarantee_points, safe_guarantee_line

# El motor exacto se reserva para el tramo final: es un problema de optimización
# entera y se encarece con ventanas grandes. Medido sobre zonas de 16 equipos, el
# costo por equipo se mantiene por debajo de ~2 s hasta ocho fechas, así que ese es
# el umbral. Es por equipo: cada club usa el motor exacto apenas entra en sus
# últimas ocho fechas, sin importar los postergados de otras canchas.
VENTANA_EXACTA = 8
MAX_MATCHES = 140


@dataclass
class PisoObjetivo:
    """Resultado de piso para un equipo y un objetivo puntual."""

    clave: str
    nombre: str
    aplica: bool = True
    estado: str = "pelea"          # "in" | "out" | "pelea"
    puntos_hoy: int = 0
    techo: int = 0
    minimo_posible: int | None = None
    piso_exacto: int | None = None
    piso_conservador: int | None = None
    exacto: bool = False
    detalle: str = ""
    caminos: list = None  # escalera exacta: [(puntos, estado, ejemplo)]

    def __post_init__(self):
        if self.caminos is None:
            self.caminos = []

    @property
    def piso(self) -> int | None:
        """Mejor piso disponible: el exacto si existe, si no el conservador."""
        return self.piso_exacto if self.piso_exacto is not None else self.piso_conservador

    def lectura(self) -> str:
        """Frase corta lista para publicar."""
        if not self.aplica:
            return self.detalle or "No aplica para este equipo."
        if self.estado == "in":
            return f"Ya lo tiene asegurado con {self.puntos_hoy} puntos; no depende de nadie."
        if self.estado == "out":
            return f"Sin chances: aun ganando todo llega a {self.techo} y no alcanza."
        piso = self.piso
        if piso is None:
            return "En carrera; el piso exacto se calcula en el tramo final."
        faltan = max(0, piso - self.puntos_hoy)
        base = "garantiza" if self.exacto else "es una cota segura para"
        cola = "" if faltan == 0 else f" (le faltan {faltan})"
        return f"Con {piso} puntos {base} {self.nombre}{cola}."


def _pts(base: Mapping[str, object], team: str) -> int:
    value = base.get(team, 0)
    if isinstance(value, Mapping):
        return int(value.get("pts", 0))
    return int(value)


def _techo(base: Mapping[str, object], rest: Mapping[str, int], team: str) -> int:
    return _pts(base, team) + 3 * int(rest.get(team, 0))


def _estado_corte(base: Mapping[str, object], rest: Mapping[str, int], team: str, corte: int) -> str:
    """in = ya adentro del top ``corte``; out = ya afuera; pelea = indefinido."""
    pts = {e: _pts(base, e) for e in base}
    techo = {e: pts[e] + 3 * int(rest.get(e, 0)) for e in base}
    arriba = sum(1 for x in base if x != team and techo[x] >= pts[team])
    inalcanzable = sum(1 for x in base if x != team and pts[x] > techo[team])
    if arriba < corte:
        return "in"
    if inalcanzable >= corte:
        return "out"
    return "pelea"


def _matches_del_pool(pend: Sequence[tuple[str, str]], pool: set[str]) -> list[tuple[str, str]]:
    """Sólo los partidos que tocan a un equipo del pool.

    Un equipo del pool también suma puntos contra rivales de afuera; esos partidos
    quedan incluidos (el motor los usa como puntos "libres"). Los cruces internos
    reparten como máximo tres puntos entre ambos.
    """
    return [(a, b) for a, b in pend if a in pool or b in pool]


def piso_por_corte(
    base: Mapping[str, object],
    rest: Mapping[str, int],
    pend: Sequence[tuple[str, str]],
    team: str,
    corte: int,
    *,
    clave: str,
    nombre: str,
) -> PisoObjetivo:
    """Piso para "quedar entre los primeros ``corte`` de ``base``".

    Sirve igual para playoffs (zona, corte 8), Libertadores (tabla reducida, corte
    de plazas directas) y Sudamericana (tabla reducida, corte ampliado).
    """
    if team not in base:
        return PisoObjetivo(clave, nombre, aplica=False, detalle="El equipo no está en esta tabla.")

    pts_hoy = _pts(base, team)
    techo = _techo(base, rest, team)
    estado = _estado_corte(base, rest, team, corte)
    resultado = PisoObjetivo(
        clave=clave, nombre=nombre, estado=estado,
        puntos_hoy=pts_hoy, techo=techo,
    )
    if estado == "in":
        resultado.minimo_posible = pts_hoy
        resultado.piso_exacto = pts_hoy
        resultado.exacto = True
        return resultado
    if estado == "out":
        return resultado

    pool = set(base)
    matches = _matches_del_pool(pend, pool)
    games_left = int(rest.get(team, 0))

    # Cota conservadora: siempre disponible. safe_guarantee_line devuelve el mayor
    # puntaje con el que `corte` rivales todavía pueden igualar al equipo; sumar uno
    # garantiza terminar por encima de ese grupo.
    try:
        linea = safe_guarantee_line(base, rest, matches, team, corte)
        if linea is not None and linea >= pts_hoy - 1:
            resultado.piso_conservador = min(techo, max(pts_hoy, linea + 1))
    except Exception:
        resultado.piso_conservador = None

    # Motor exacto en el tramo final.
    if matches and 0 < games_left <= VENTANA_EXACTA and len(matches) <= MAX_MATCHES:
        try:
            ladder = point_ladder(base, matches, team, corte, max_rows=6, max_matches=MAX_MATCHES)
            if ladder.get("available"):
                resultado.minimo_posible = ladder.get("minimum_possible")
                if ladder.get("guarantee") is not None:
                    resultado.piso_exacto = int(ladder["guarantee"])
                    resultado.exacto = True
                # Guardar la escalera (puntos → estado → camino de ejemplo).
                for row in ladder.get("rows", []) or []:
                    ejemplo = ""
                    ej_list = getattr(row, "example", None)
                    if ej_list:
                        ejemplo = "; ".join(ej_list[:2])
                    resultado.caminos.append((
                        int(getattr(row, "final_points", 0)),
                        str(getattr(row, "status", "")),
                        ejemplo,
                    ))
        except Exception:
            pass

    return resultado


def piso_no_descenso(
    anual: Mapping[str, object],
    rest: Mapping[str, int],
    pend: Sequence[tuple[str, str]],
    team: str,
    *,
    n_anual: int = 1,
    prom_totales: Mapping[str, tuple[int, int]] | None = None,
    n_prom: int = 1,
) -> PisoObjetivo:
    """Piso para NO descender.

    En la LPF se baja por dos vías: el último de la Tabla Anual y el peor promedio.
    Para estar salvado hay que estarlo en **las dos** tablas, así que el piso
    efectivo es el mayor de los dos. La parte anual se resuelve con el motor exacto
    (en el tramo final) y la de promedios con la cota conservadora por cocientes.
    """
    nombre = "no descender"
    if team not in anual:
        return PisoObjetivo("descenso", nombre, aplica=False, detalle="El equipo no está en la Anual.")

    total = len(anual)
    corte_salvacion = max(1, total - int(n_anual))  # quedar dentro del top (N - descensos)
    parte_anual = piso_por_corte(
        anual, rest, pend, team, corte_salvacion, clave="descenso", nombre=nombre,
    )

    piso_prom = None
    detalle_prom = ""
    if prom_totales and team in prom_totales:
        totales = {e: int(v[0]) for e, v in prom_totales.items()}
        jugados = {e: int(v[1]) for e, v in prom_totales.items()}
        restantes = {e: int(rest.get(e, 0)) for e in prom_totales}
        pool = set(prom_totales)
        matches = _matches_del_pool(pend, pool)
        try:
            extra = safe_average_guarantee_points(
                totales, jugados, restantes, matches, team, int(n_prom),
            )
            if extra is not None:
                piso_prom = _pts(anual, team) + int(extra)
                detalle_prom = "Incluye el piso por promedios (cota segura por cocientes)."
        except Exception:
            piso_prom = None

    # Combinar: hay que salvarse en las dos tablas.
    resultado = PisoObjetivo(
        clave="descenso", nombre=nombre,
        estado=parte_anual.estado,
        puntos_hoy=parte_anual.puntos_hoy, techo=parte_anual.techo,
        minimo_posible=parte_anual.minimo_posible,
    )
    pisos = [p for p in (parte_anual.piso_exacto, piso_prom) if p is not None]
    if parte_anual.piso_exacto is not None and piso_prom is not None:
        resultado.piso_exacto = parte_anual.piso_exacto
        resultado.piso_conservador = max(pisos)
        resultado.exacto = (piso_prom <= parte_anual.piso_exacto)
    elif piso_prom is not None:
        resultado.piso_conservador = piso_prom
    else:
        resultado.piso_exacto = parte_anual.piso_exacto
        resultado.piso_conservador = parte_anual.piso_conservador
        resultado.exacto = parte_anual.exacto
    resultado.detalle = detalle_prom
    if resultado.estado == "in":
        resultado.exacto = True
        resultado.piso_exacto = resultado.puntos_hoy
    return resultado


def objetivos_de_equipo(
    zonas: Mapping[str, Mapping[str, object]],
    anual: Mapping[str, object],
    reducida: Sequence[str],
    n_lib: int,
    team: str,
) -> list[dict]:
    """Objetivos aplicables a un equipo, con su tabla base y su corte.

    Devuelve especificaciones ``{clave, nombre, base, corte}`` para los objetivos
    de corte; el descenso se calcula aparte porque combina dos tablas.
    """
    specs: list[dict] = []
    zona = next((lab for lab, b in zonas.items() if team in b), None)
    if zona is not None:
        specs.append({
            "clave": "playoffs", "nombre": "los playoffs (top 8 de zona)",
            "base": dict(zonas[zona]), "corte": 8,
        })
    reducida = list(reducida)
    if team in reducida and anual:
        base_red = {e: anual[e] for e in reducida if e in anual}
        specs.append({
            "clave": "libertadores", "nombre": "la Libertadores",
            "base": base_red, "corte": int(n_lib),
        })
        specs.append({
            "clave": "sudamericana", "nombre": "al menos la Sudamericana",
            "base": base_red, "corte": int(n_lib) + 6,
        })
    return specs


def pisos_de_equipo(
    zonas: Mapping[str, Mapping[str, object]],
    anual: Mapping[str, object],
    reducida: Sequence[str],
    n_lib: int,
    rest: Mapping[str, int],
    pend: Sequence[tuple[str, str]],
    team: str,
    *,
    n_anual: int = 1,
    prom_totales: Mapping[str, tuple[int, int]] | None = None,
    n_prom: int = 1,
) -> list[PisoObjetivo]:
    """Todos los pisos aplicables a un equipo, en orden editorial."""
    salida: list[PisoObjetivo] = []
    for spec in objetivos_de_equipo(zonas, anual, reducida, n_lib, team):
        salida.append(piso_por_corte(
            spec["base"], rest, pend, team, spec["corte"],
            clave=spec["clave"], nombre=spec["nombre"],
        ))
    if anual and team in anual:
        salida.append(piso_no_descenso(
            anual, rest, pend, team,
            n_anual=n_anual, prom_totales=prom_totales, n_prom=n_prom,
        ))
    return salida


def tabla_pisos_objetivo(
    base: Mapping[str, object],
    rest: Mapping[str, int],
    pend: Sequence[tuple[str, str]],
    corte: int,
    *,
    clave: str,
    nombre: str,
    orden: Sequence[str] | None = None,
) -> list[dict]:
    """Filas listas para tabla: el piso de *cada* equipo para un mismo objetivo."""
    equipos = list(orden) if orden else list(base)
    filas: list[dict] = []
    for e in equipos:
        if e not in base:
            continue
        p = piso_por_corte(base, rest, pend, e, corte, clave=clave, nombre=nombre)
        filas.append({
            "Equipo": e,
            "PTS": p.puntos_hoy,
            "Restan": int(rest.get(e, 0)),
            "Techo": p.techo,
            "Mínimo posible": p.minimo_posible,
            "Piso (garantía)": p.piso,
            "Exacto": "Sí" if p.exacto else "Cota",
            "Estado": {"in": "Adentro", "out": "Afuera", "pelea": "En carrera"}.get(p.estado, p.estado),
        })
    return filas
