from lpf_clubs import canon_club
from lpf_data_2026 import LPF_FIXTURE
from lpf_fixture_sources import parse_lpf_official_results_article_html


def test_lpf_oficial_article_wordpress_br_preserva_fragmentos_atomicos():
    games = [row for row in LPF_FIXTURE if int(row.get("f") or 0) == 9]
    assert len(games) == 15
    body = ["Fecha 9"]
    body.extend(f"{row['l']} 0 – 0 {row['v']}" for row in games)
    html = (
        "<html><body><article><p>"
        + "<br>".join(body)
        + "</p></article>"
        + "<aside><p>Rosario Central 2 – 1 Argentinos</p></aside></body></html>"
    )

    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/notas/primera/2026/09/10/se-mueve-la-novena/",
        expected_round=9,
    )

    assert len(rows) == 15
    assert {row["round"] for row in rows} == {9}
    assert not any(
        row["home"] == "Rosario Central" and row["away"] == "Argentinos Juniors"
        for row in rows
    )
