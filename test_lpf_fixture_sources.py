

def test_lpf_oficial_listing_descubre_cierres_y_notas_vivas_de_fecha():
    from lpf_fixture_sources import parse_lpf_official_listing_html

    html = """
    <html><body>
      <a href="/notas/primera/2026/08/15/agenda-de-la-fecha-6/">Racing y Boca empataron 1 a 1</a>
      <a href="/notas/primera/2026/08/15/agenda-de-la-fecha-6/">Leer más</a>
      <a href="/notas/primera/2026/09/10/se-mueve-la-novena/">Culminó la novena</a>
      <a href="/notas/primera/2026/09/07/hoy-arranca-la-fecha-8/">Adiós a la fecha 8</a>
      <a href="/notas/primera/2026/08/25/programacion-de-la-fecha-7-5/">Se fue la séptima</a>
      <a href="/notas/primera/2026/08/24/agenda-de-la-fecha-6/">Todo sobre la sexta</a>
      <a href="/notas/primera/2026/09/16/conferencia/">Conferencia del clásico rosarino</a>
      <a href="/notas/proyeccion/2026/08/15/resultados/">Proyección goleó</a>
      <a href="https://www.ligaprofesional.ar/notas/primera/2026/08/09/programacion-de-la-fecha-4-3/">Cerró la 4 en el Kempes</a>
    </body></html>
    """
    rows = parse_lpf_official_listing_html(
        html, base_url="https://www.ligaprofesional.ar/notas/primera/"
    )
    assert [row["title"] for row in rows] == [
        "Racing y Boca empataron 1 a 1",
        "Culminó la novena",
        "Adiós a la fecha 8",
        "Se fue la séptima",
        "Todo sobre la sexta",
        "Cerró la 4 en el Kempes",
    ]
    assert all("/notas/primera/2026/" in row["url"] for row in rows)
    assert [row["round"] for row in rows] == [6, 9, 8, 7, 6, 4]


def test_lpf_oficial_listing_incluye_agendas_de_fecha_pero_no_conferencias():
    from lpf_fixture_sources import parse_lpf_official_listing_html

    html = """
    <a href="/notas/primera/2026/09/16/programacion-de-la-fecha-10/">Programación de la fecha 10</a>
    <a href="/notas/primera/2026/09/01/agenda-de-la-8-a-la-11/">Agenda de la 8 a la 11</a>
    <a href="/notas/primera/2026/09/05/conferencia-rosarina/">Conferencia del clásico rosarino</a>
    """
    rows = parse_lpf_official_listing_html(
        html, base_url="https://www.ligaprofesional.ar/notas/primera/"
    )
    assert [row["title"] for row in rows] == [
        "Programación de la fecha 10",
        "Agenda de la 8 a la 11",
    ]


def test_lpf_oficial_article_parsea_ambos_formatos_y_descarta_programados():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <html><body><article>
      <p>Fecha 6 – Interzonal</p>
      <p>Aldosivi 1 – 3 Unión -TNT Sports-</p>
      <p>Estudiantes (Río Cuarto) 0 – San Lorenzo 0</p>
      <p>River 2 – Vélez 2</p>
      <p>Racing 1 – Boca 1</p>
      <p>19.00 Tigre – Central Córdoba -TNT Sports-</p>
      <p>La nota dice que Lanús le ganó a Argentinos, pero sin marcador estructurado.</p>
    </article></body></html>
    """
    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/notas/primera/test/",
    )
    played = {
        (row["home"], row["away"]): (row["home_score"], row["away_score"])
        for row in rows
    }
    assert played[("Aldosivi", "Unión")] == (1, 3)
    assert played[("Estudiantes de Río Cuarto", "San Lorenzo")] == (0, 0)
    assert played[("River Plate", "Vélez Sarsfield")] == (2, 2)
    assert played[("Racing", "Boca Juniors")] == (1, 1)
    assert ("Tigre", "Central Córdoba") not in played
    assert all(row["source"] == "Liga Profesional de Fútbol" for row in rows)


def test_lpf_oficial_article_formato_real_fecha6_extrae_12_jugados_y_no_programados():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    lines = [
        "Aldosivi 1 – 3 Unión -TNT Sports-",
        "Estudiantes (Río Cuarto) 0 – San Lorenzo 0",
        "Gimnasia 2 – 3 Gimnasia (Mza.)",
        "Atlético Tucumán 0 – 0 Instituto",
        "Independiente 0 – Ind. Rivadavia Mza. 0",
        "Newell’s 2 – Banfield 1",
        "Huracán 0 – Deportivo Riestra 0",
        "Sarmiento 2 – Estudiantes 0",
        "Barracas Central 1 – Platense 2",
        "Belgrano 1 – Defensa y Justicia 2",
        "River 2 – Vélez 2",
        "Racing 1 – Boca 1",
        "19.00 Tigre – Central Córdoba -TNT Sports-",
        "21.15 Lanús – Argentinos -TNT Sports-",
        "21.15 Talleres – Rosario Central -ESPN Premium-",
    ]
    html = "<article>" + "".join(f"<p>{line}</p>" for line in lines) + "</article>"
    rows = parse_lpf_official_results_article_html(
        html, canon_club=canon_club, official_fixture=LPF_FIXTURE, expected_round=6
    )
    assert len(rows) == 12
    assert {row["round"] for row in rows} == {6}
    assert ("River Plate", "Vélez Sarsfield", 2, 2) in {
        (row["home"], row["away"], row["home_score"], row["away_score"])
        for row in rows
    }



def test_lpf_oficial_article_limita_cuerpo_y_fecha_para_no_sumar_relacionados():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <html><body>
      <article>
        <h1>Culminó la novena</h1>
        <p>Fecha 9</p>
        <p>Tigre 0 – Rosario Central 1 (Zona B)</p>
        <p>Antecedente: Rosario Central 2 – 1 Estudiantes (Río Cuarto)</p>
      </article>
      <aside>
        <p>Rosario Central 2 – 1 Argentinos</p>
        <p>Estudiantes (Río Cuarto) 4 – 0 Racing</p>
      </aside>
    </body></html>
    """
    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/notas/primera/2026/09/10/se-mueve-la-novena/",
        expected_round=9,
    )
    assert [(row["home"], row["away"], row["home_score"], row["away_score"]) for row in rows] == [
        ("Tigre", "Rosario Central", 0, 1)
    ]


def test_lpf_oficial_article_infiere_fecha_del_cuerpo_y_rechaza_cruce_de_otro_round():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <article>
      <p>Fecha 9</p>
      <p>Tigre 0 – Rosario Central 1</p>
      <p>Rosario Central 2 – 1 Estudiantes (Río Cuarto)</p>
    </article>
    """
    rows = parse_lpf_official_results_article_html(
        html, canon_club=canon_club, official_fixture=LPF_FIXTURE
    )
    assert {(row["home"], row["away"], row["round"]) for row in rows} == {
        ("Tigre", "Rosario Central", 9)
    }


def test_lpf_oficial_seis_fechas_auditadas_no_pueden_superar_90_resultados():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import merge_match_records, parse_lpf_official_results_article_html

    records = []
    for round_number in range(4, 10):
        games = [row for row in LPF_FIXTURE if int(row.get("f") or 0) == round_number]
        assert len(games) == 15
        body = [f"<p>Fecha {round_number}</p>"]
        body.extend(f"<p>{row['l']} 0 – 0 {row['v']}</p>" for row in games)
        html = "<html><body><article>" + "".join(body) + "</article>"
        # Dos tarjetas relacionadas que antes podían contaminar el parseo global.
        html += "<aside><p>Rosario Central 2 – 1 Argentinos</p><p>Estudiantes (Río Cuarto) 4 – 0 Racing</p></aside></body></html>"
        records.extend(parse_lpf_official_results_article_html(
            html,
            canon_club=canon_club,
            official_fixture=LPF_FIXTURE,
            expected_round=round_number,
        ))
    merged = merge_match_records(records)
    assert len(merged) == 90
    assert {row["round"] for row in merged} == {4, 5, 6, 7, 8, 9}

def test_lpf_oficial_listing_acepta_permalink_corto_y_excluye_apertura_fechado():
    from lpf_fixture_sources import parse_lpf_official_listing_html

    html = """
    <html><body>
      <a href="/?p=85379">Cerró la 4 en el Kempes</a>
      <a href="/?p=85943">Todo sobre la sexta</a>
      <a href="/notas/primera/2026/03/15/agenda-de-la-fecha-11-3/">Estudiantes remontó y le ganó 2 a 1 a Gimnasia de Mendoza</a>
      <a href="/notas/primera/2026/09/10/se-mueve-la-novena/">Culminó la novena</a>
    </body></html>
    """
    rows = parse_lpf_official_listing_html(
        html, base_url="https://www.ligaprofesional.ar/notas/primera/"
    )
    assert [row["title"] for row in rows] == [
        "Cerró la 4 en el Kempes",
        "Todo sobre la sexta",
        "Culminó la novena",
    ]
    assert not any("2026/03/" in row["url"] for row in rows)


def test_lpf_oficial_article_rechaza_marcadores_del_apertura_aunque_la_pareja_exista():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <html><body><article>
      <h1>Estudiantes remontó y le ganó 2 a 1 a Gimnasia de Mendoza</h1>
      <p>La Liga Profesional de Fútbol presenta la fecha 11 del Torneo Apertura Mercado Libre.</p>
      <p>Platense 0 – Vélez 2 (Zona A)</p>
      <p>Rosario Central 2 – Banfield 1 (Zona B)</p>
    </article></body></html>
    """
    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/notas/primera/2026/03/15/agenda-de-la-fecha-11-3/",
    )
    assert rows == []


def test_lpf_oficial_article_acepta_clausura_en_permalink_corto():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <html><body><article>
      <h1>Cerró la 4 en el Kempes</h1>
      <p>La Liga Profesional de Fútbol presenta la fecha 4 del Torneo Clausura Mercado Libre 2026.</p>
      <p>Rosario Central 2 – 1 Aldosivi (Zona B)</p>
      <p>Ind. Rivadavia Mza. 2 – 1 Estudiantes (Río Cuarto) (Zona B)</p>
    </article></body></html>
    """
    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/?p=85379",
    )
    assert {(row["home"], row["away"], row["home_score"], row["away_score"]) for row in rows} == {
        ("Rosario Central", "Aldosivi", 2, 1),
        ("Independiente Rivadavia", "Estudiantes de Río Cuarto", 2, 1),
    }


def test_lpf_oficial_article_rechaza_url_preclausura_aunque_no_nombre_apertura():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

    html = """
    <html><body><article>
      <h1>Rosario Central venció a Banfield</h1>
      <p>Rosario Central 2 – Banfield 1 (Zona B)</p>
    </article></body></html>
    """
    rows = parse_lpf_official_results_article_html(
        html,
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.ligaprofesional.ar/notas/primera/2026/03/15/resultado/",
    )
    assert rows == []


def test_lpf_oficial_permalink_corto_no_auditado_no_se_acepta():
    from lpf_fixture_sources import _lpf_official_url_is_current_clausura

    assert _lpf_official_url_is_current_clausura(
        "https://www.ligaprofesional.ar/?p=85379", allow_short_post=True
    )
    assert not _lpf_official_url_is_current_clausura(
        "https://www.ligaprofesional.ar/?p=70000", allow_short_post=True
    )


def test_lpf_oficial_article_wordpress_br_preserva_fragmentos_atomicos():
    """Regresion 3.8.68: una fecha completa puede vivir en un solo <p> con <br>."""
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_lpf_official_results_article_html

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


def test_tyc_fixture_clausura_parsea_135_resultados_y_respeta_fecha():
    """3.8.70: TyC puede reconstruir las nueve fechas sin leer el fixture futuro."""
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_tyc_clausura_results_html

    parts = [
        "<html><body><article>",
        "<h2>El fixture del Torneo Clausura 2026: cruces y fechas</h2>",
        "<h4>Fecha 10</h4><li>Central Córdoba – Defensa y Justicia</li>",
        "<h2>Resultados del Torneo Clausura 2026</h2>",
    ]
    for round_number in range(1, 10):
        parts.append(f"<h4>Fecha {round_number}</h4>")
        for row in LPF_FIXTURE:
            if int(row.get("f") or 0) == round_number:
                parts.append(f"<li>{row['l']} 0-0 {row['v']}</li>")
    parts.append("<h2>Te puede interesar</h2><li>River Plate 9-9 Boca Juniors</li>")
    parts.append("</article></body></html>")

    rows = parse_tyc_clausura_results_html(
        "".join(parts),
        canon_club=canon_club,
        official_fixture=LPF_FIXTURE,
        source_url="https://www.tycsports.com/test",
    )

    assert len(rows) == 135
    assert {row["round"] for row in rows} == set(range(1, 10))
    assert all(row["source"] == "TyC Sports" for row in rows)
    assert not any(row["round"] == 10 for row in rows)


def test_tyc_fixture_clausura_resuelve_alias_reales():
    from lpf_clubs import canon_club
    from lpf_data_2026 import LPF_FIXTURE
    from lpf_fixture_sources import parse_tyc_clausura_results_html

    html = """
    <article>
      <h2>Resultados del Torneo Clausura 2026</h2>
      <h4>Fecha 9</h4>
      <li>Newell’s 1-1 Vélez</li>
      <li>Defensa y Justicia 2-0 Gimnasia (Mza.)</li>
      <li>Ind. Rivadavia Mza. 4-3 Aldosivi</li>
      <li>Instituto 2-1 Estudiantes (Río Cuarto)</li>
    </article>
    """
    rows = parse_tyc_clausura_results_html(
        html, canon_club=canon_club, official_fixture=LPF_FIXTURE
    )
    got = {
        (r["home"], r["away"]): (r["home_score"], r["away_score"])
        for r in rows
    }
    assert got[("Newell's Old Boys", "Vélez Sarsfield")] == (1, 1)
    assert got[("Defensa y Justicia", "Gimnasia de Mendoza")] == (2, 0)
    assert got[("Independiente Rivadavia", "Aldosivi")] == (4, 3)
    assert got[("Instituto", "Estudiantes de Río Cuarto")] == (2, 1)
