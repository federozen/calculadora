from collections import Counter

from lpf_data_quality import fixture_records, pending_pairs


def _row(pj, pts=0, gf=0, ga=0):
    return {"pj": pj, "pts": pts, "gf": gf, "ga": ga, "dg": gf - ga}


def _fixture():
    return [
        {"f": 1, "l": "A", "v": "B", "zona": "A"},
        {"f": 1, "l": "C", "v": "D", "zona": "A"},
        {"f": 2, "l": "A", "v": "C", "zona": "A"},
        {"f": 2, "l": "B", "v": "D", "zona": "A"},
        {"f": 3, "l": "A", "v": "D", "zona": "A"},
        {"f": 3, "l": "B", "v": "C", "zona": "A"},
    ]


def test_uniform_table_frontier_downgrades_missing_history_to_warning():
    zones = {"A": {
        "A": _row(2, 4, 2, 1),
        "B": _row(2, 3, 1, 1),
        "C": _row(2, 2, 1, 1),
        "D": _row(2, 1, 0, 1),
    }}
    records, issues = fixture_records(_fixture(), [("A", "B", 1, 0)], zones)
    assert any(issue.code == "fixture_history_partial" and issue.level == "warning" for issue in issues)
    assert not any(issue.code == "fixture_unconfirmed" and issue.level == "blocked" for issue in issues)
    assert Counter(r.status for r in records) == {"played": 1, "unconfirmed": 3, "scheduled": 2}
    assert pending_pairs(records) == [("A", "D"), ("B", "C")]


def test_uneven_pj_keeps_missing_history_blocked():
    zones = {"A": {
        "A": _row(2, 3, 1, 0),
        "B": _row(1, 0, 0, 1),
        "C": _row(1, 0, 0, 0),
        "D": _row(0, 0, 0, 0),
    }}
    _records, issues = fixture_records(_fixture(), [("A", "B", 1, 0)], zones)
    assert any(issue.code == "fixture_unconfirmed" and issue.level == "blocked" for issue in issues)


def test_later_explicit_round_disables_uniform_frontier_fallback():
    zones = {"A": {
        "A": _row(2, 3, 1, 0),
        "B": _row(2, 1, 0, 1),
        "C": _row(2, 1, 0, 0),
        "D": _row(2, 0, 0, 0),
    }}
    _records, issues = fixture_records(_fixture(), [("A", "D", 1, 0)], zones)
    assert any(issue.code == "fixture_unconfirmed" and issue.level == "blocked" for issue in issues)


def test_real_lpf_shape_49_known_86_historical_unknown_105_future():
    from lpf_data_2026 import LPF_FIXTURE

    teams = sorted({str(game["l"]) for game in LPF_FIXTURE} | {str(game["v"]) for game in LPF_FIXTURE})
    assert len(teams) == 30

    # Foto sintética equivalente en estructura a 9 PJ por club. Usamos 0-0 para
    # que los 49 resultados parciales sean inequívocamente compatibles con la
    # tabla sin introducir datos reales en el fixture de regresión.
    zones = {
        "A": {team: _row(9, 9, 0, 0) for team in teams[:15]},
        "B": {team: _row(9, 9, 0, 0) for team in teams[15:]},
    }
    historical = [g for g in LPF_FIXTURE if int(g["f"]) <= 9]
    assert len(historical) == 135
    known = [(str(g["l"]), str(g["v"]), 0, 0) for g in historical[:49]]

    records, issues = fixture_records(LPF_FIXTURE, known, zones)
    counts = Counter(r.status for r in records)

    assert counts == {"played": 49, "unconfirmed": 86, "scheduled": 105}
    assert len(pending_pairs(records)) == 105
    assert all(r.round_number >= 10 for r in records if r.status == "scheduled")
    assert any(issue.code == "fixture_history_partial" and issue.level == "warning" for issue in issues)
    assert not any(issue.level == "blocked" for issue in issues)
