from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / 'calculadora_futbol_argentino.py').read_text(encoding='utf-8')


def test_partial_history_is_not_rendered_as_primary_report_warning():
    assert 'issue.code != "fixture_history_partial"' in MAIN
    assert 'Historial de marcadores parcial: no cambia los PJ de la tabla ni los partidos restantes' in MAIN


def test_relegation_uses_bottom_table_language():
    assert 'no necesita superar a toda la tabla' in MAIN
    assert 'al menos un equipo' in MAIN
    assert 'modo="salvarse", mostrar_amenazas=False' in MAIN
    assert 'salvación condicionada' in MAIN
    assert 'escenario de descenso' in MAIN
