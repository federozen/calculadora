"""Parsers HTML genéricos usados por la carga avanzada, sin red ni Streamlit."""
import ast
from pathlib import Path

from competition_html_adapters import parse_cross_table_html, parse_standings_table_html

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_standings_table_html_conserva_formato_historico():
    text, error = parse_standings_table_html(_fixture("generic_standings.html"))
    assert error is None
    assert text.splitlines() == [
        "Atlético Norte, 10, 4, +6",
        "Deportivo Sur, 8, 4, +2",
        "Central, 6, 4, +0",
        "Unión Oeste, 3, 4, -3",
    ]


def test_parse_cross_table_html_detecta_una_rueda_y_pendientes_sin_duplicar():
    played, pending, error, note = parse_cross_table_html(_fixture("generic_cross_table.html"))
    assert error is None
    assert note.startswith("una sola rueda")
    assert played == [
        ("A", "B", 2, 1),
        ("B", "C", 0, 0),
        ("C", "D", 3, 2),
    ]
    assert pending == [("A", "C"), ("A", "D"), ("B", "D")]


def test_parse_cross_table_html_detecta_ida_y_vuelta():
    played, pending, error, note = parse_cross_table_html(_fixture("generic_cross_table_double.html"))
    assert error is None
    assert note == "torneo ida y vuelta"
    assert ("A", "B", 2, 1) in played
    assert ("B", "A", 1, 0) in played
    assert ("A", "C") in pending and ("C", "A") in pending


def test_parsers_html_no_dependen_de_red_ni_streamlit():
    import competition_html_adapters

    source = Path(competition_html_adapters.__file__).read_text(encoding="utf-8")
    assert "import requests" not in source
    assert "import streamlit" not in source


def test_wrappers_del_main_solo_transportan_y_delegan():
    main = Path(__file__).resolve().parents[1] / "calculadora_futbol_argentino.py"
    tree = ast.parse(main.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in {"partidos_desde_url", "tabla_desde_url"}
    }
    assert set(functions) == {"partidos_desde_url", "tabla_desde_url"}

    for node in functions.values():
        assert not any(isinstance(child, (ast.Import, ast.ImportFrom)) for child in ast.walk(node))
        calls = {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        assert "fetch_url_text" in calls

    cross_calls = {
        child.func.id
        for child in ast.walk(functions["partidos_desde_url"])
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    standings_calls = {
        child.func.id
        for child in ast.walk(functions["tabla_desde_url"])
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    assert "parse_cross_table_html" in cross_calls
    assert "parse_standings_table_html" in standings_calls
