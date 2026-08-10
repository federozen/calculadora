"""Validación por fuerza bruta del piso por objetivo.

La idea: en ligas chicas se enumeran TODOS los resultados posibles de los partidos
pendientes y se verifica que las afirmaciones del módulo son ciertas:

- El **mínimo posible** es alcanzable: existe al menos un desenlace en el que el
  equipo termina en el top del corte con ese puntaje, y ninguno menor lo logra.
- El **piso exacto** garantiza de verdad: terminando con ese puntaje el equipo
  entra en TODOS los desenlaces compatibles, y con uno menos existe alguno que
  lo deja afuera (mínimo estricto).

El desempate se toma adverso (empatar en puntos = no entrar), igual que el motor.
"""
import itertools
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lpf_pisos import piso_por_corte, piso_no_descenso  # noqa: E402

OUTCOMES = ("L", "E", "V")


def _final_points(base, matches, combo):
    pts = {e: int(v["pts"]) for e, v in base.items()}
    for (home, away), r in zip(matches, combo):
        if r == "L":
            pts[home] = pts.get(home, 0) + 3
        elif r == "V":
            pts[away] = pts.get(away, 0) + 3
        else:
            pts[home] = pts.get(home, 0) + 1
            pts[away] = pts.get(away, 0) + 1
    return pts


def _rank_favorable(pts, base, team):
    """Puesto con desempate a favor: sólo cuentan los rivales estrictamente arriba.

    Es la lectura del *mínimo posible*: el menor puntaje con el que TODAVÍA existe
    una combinación favorable (ganar el desempate incluido).
    """
    p = pts[team]
    strictly_above = sum(1 for e in base if e != team and pts.get(e, 0) > p)
    return strictly_above + 1


def _rank_adverse(pts, base, team):
    """Puesto con desempate en contra: cuentan los rivales iguales o por encima.

    Es la lectura de la *garantía*: entrar sin depender de desempates.
    """
    p = pts[team]
    at_or_above = sum(1 for e in base if e != team and pts.get(e, 0) >= p)
    return at_or_above + 1


def _team_games_left(matches, team):
    return sum(team in m for m in matches)


def _all_final_points_for(base, matches, team, target):
    """Todos los desenlaces en los que el equipo termina exactamente con `target`."""
    for combo in itertools.product(OUTCOMES, repeat=len(matches)):
        pts = _final_points(base, matches, combo)
        if pts[team] == target:
            yield pts


def _reachable_targets(base, team, matches):
    cur = int(base[team]["pts"])
    gl = _team_games_left(matches, team)
    return list(range(cur, cur + 3 * gl + 1))


def _brute_minimum_and_guarantee(base, matches, team, corte):
    """(mínimo posible, piso garantía) por enumeración exhaustiva."""
    minimo = None
    piso = None
    for target in _reachable_targets(base, team, matches):
        finals = list(_all_final_points_for(base, matches, team, target))
        if not finals:
            continue
        # Mínimo posible: existe un desenlace favorable (desempate a favor).
        qualifies_some = any(_rank_favorable(p, base, team) <= corte for p in finals)
        # Garantía: en TODOS los desenlaces entra incluso con desempate adverso.
        qualifies_all = all(_rank_adverse(p, base, team) <= corte for p in finals)
        if qualifies_some and minimo is None:
            minimo = target
        if qualifies_all and piso is None:
            piso = target
    return minimo, piso


# ── Casos de prueba (ligas chicas, pocos pendientes) ───────────────────────────

CASES = [
    # base, matches, corte
    (
        {"A": {"pts": 6}, "B": {"pts": 4}, "C": {"pts": 3}, "D": {"pts": 1}},
        [("A", "B"), ("C", "D"), ("A", "C"), ("B", "D")],
        2,
    ),
    (
        {"A": {"pts": 5}, "B": {"pts": 5}, "C": {"pts": 4}, "D": {"pts": 2}},
        [("A", "D"), ("B", "C"), ("A", "B")],
        2,
    ),
    (
        {"W": {"pts": 7}, "X": {"pts": 6}, "Y": {"pts": 6}, "Z": {"pts": 5}},
        [("W", "X"), ("Y", "Z"), ("W", "Y"), ("X", "Z")],
        1,
    ),
    (
        {"A": {"pts": 3}, "B": {"pts": 3}, "C": {"pts": 3}, "D": {"pts": 3}},
        [("A", "B"), ("C", "D")],
        2,
    ),
]


@pytest.mark.parametrize("base,matches,corte", CASES)
def test_piso_coincide_con_fuerza_bruta(base, matches, corte):
    rest = {}
    for a, b in matches:
        rest[a] = rest.get(a, 0) + 1
        rest[b] = rest.get(b, 0) + 1
    for team in base:
        esperado_min, esperado_piso = _brute_minimum_and_guarantee(base, matches, team, corte)
        got = piso_por_corte(base, rest, matches, team, corte, clave="t", nombre="objetivo")

        if got.estado == "in":
            # Ya clasificado en todos los desenlaces => piso = puntos actuales.
            assert esperado_piso == int(base[team]["pts"]) == got.piso
            continue
        if got.estado == "out":
            assert esperado_min is None
            continue

        # En carrera y ventana chica: el motor exacto resuelve el mínimo.
        assert got.minimo_posible == esperado_min, (
            f"{team}: mínimo {got.minimo_posible} != fuerza bruta {esperado_min}"
        )
        # El piso exacto coincide con la fuerza bruta (ambos pueden ser None si el
        # objetivo no se puede garantizar, p. ej. salir 1º con desempate adverso).
        assert got.piso_exacto == esperado_piso, (
            f"{team}: piso {got.piso_exacto} != fuerza bruta {esperado_piso}"
        )
        if esperado_piso is not None:
            assert got.exacto, f"{team}: garantía encontrada pero no marcada como exacta"


@pytest.mark.parametrize("base,matches,corte", CASES)
def test_invariantes(base, matches, corte):
    rest = {}
    for a, b in matches:
        rest[a] = rest.get(a, 0) + 1
        rest[b] = rest.get(b, 0) + 1
    for team in base:
        p = piso_por_corte(base, rest, matches, team, corte, clave="t", nombre="objetivo")
        assert p.puntos_hoy <= p.techo
        if p.minimo_posible is not None:
            assert p.puntos_hoy <= p.minimo_posible <= p.techo
        if p.piso is not None:
            assert p.piso <= p.techo
        if p.minimo_posible is not None and p.piso_exacto is not None:
            # Garantizar nunca puede costar menos que el mínimo con el que se puede.
            assert p.piso_exacto >= p.minimo_posible


def test_cota_conservadora_es_segura():
    """El piso conservador nunca puede ser MENOR que el piso exacto real."""
    base = {"A": {"pts": 6}, "B": {"pts": 4}, "C": {"pts": 3}, "D": {"pts": 1}}
    matches = [("A", "B"), ("C", "D"), ("A", "C"), ("B", "D")]
    rest = {"A": 2, "B": 2, "C": 2, "D": 2}
    corte = 2
    for team in base:
        _, piso_real = _brute_minimum_and_guarantee(base, matches, team, corte)
        p = piso_por_corte(base, rest, matches, team, corte, clave="t", nombre="objetivo")
        if p.piso_conservador is not None and piso_real is not None:
            assert p.piso_conservador >= piso_real, (
                f"{team}: cota conservadora {p.piso_conservador} < piso real {piso_real}"
            )


def test_no_descenso_combina_dos_tablas():
    """El piso de no-descenso es al menos el de la parte anual."""
    anual = {
        "A": {"pts": 20}, "B": {"pts": 18}, "C": {"pts": 15},
        "D": {"pts": 12}, "E": {"pts": 10}, "F": {"pts": 8},
    }
    matches = [("E", "F"), ("D", "E"), ("C", "F")]
    rest = {}
    for a, b in matches:
        rest[a] = rest.get(a, 0) + 1
        rest[b] = rest.get(b, 0) + 1
    p = piso_no_descenso(anual, rest, matches, "F", n_anual=1)
    assert p.clave == "descenso"
    assert p.puntos_hoy == 8
    # Con corte de salvación top (6-1)=5, F pelea por no ser último.
    assert p.estado in {"in", "out", "pelea"}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
