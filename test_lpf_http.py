"""Pruebas del transporte HTTP aislado, siempre con requests simulado."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lpf_http  # noqa: E402


class _Response:
    def __init__(self, *, status=200, url="https://final.test/x", text="x" * 600, payload=None):
        self.status_code = status
        self.url = url
        self.text = text
        self._payload = payload if payload is not None else {"ok": True}

    def json(self):
        return self._payload


def test_fetch_html_solo_transporta_y_devuelve_url_final(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return _Response(url="https://final.test/tabla")

    monkeypatch.setattr(lpf_http.requests, "get", fake_get)
    text, final_url = lpf_http.fetch_html(
        "https://source.test/tabla", referer="https://source.test/", retries=0
    )
    assert len(text) == 600
    assert final_url == "https://final.test/tabla"
    assert calls[0][1]["headers"]["Referer"] == "https://source.test/"


def test_fetch_url_text_conserva_transporte_generico_historico(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return _Response(status=404, text="pagina tal cual")

    monkeypatch.setattr(lpf_http.requests, "get", fake_get)
    assert lpf_http.fetch_url_text("https://source.test/wiki", timeout=17) == "pagina tal cual"
    assert calls == [(
        "https://source.test/wiki",
        {"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 17},
    )]


def test_fetch_espn_json_no_parsea_el_payload(monkeypatch):
    payload = {"events": [{"id": "raw"}]}
    monkeypatch.setattr(
        lpf_http.requests,
        "get",
        lambda *args, **kwargs: _Response(payload=payload),
    )
    assert lpf_http.fetch_espn_json(
        "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard",
        retries=0,
    ) == payload


def test_lpf_http_no_depende_de_streamlit():
    source = open(lpf_http.__file__, encoding="utf-8").read()
    assert "import streamlit" not in source


def test_fetch_espn_scoreboard_window_preserva_ventana_lpf_y_limite():
    import datetime as dt

    calls = []

    def fake_get(url, *, timeout):
        calls.append((url, timeout))
        return {"url": url}

    result = lpf_http.fetch_espn_scoreboard_window(
        "arg.1",
        dias=30,
        timeout=17,
        max_req=3,
        get_json=fake_get,
        today=dt.date(2026, 8, 10),
    )

    assert result["start_date"] == dt.date(2026, 7, 1)
    assert result["end_date"] == dt.date(2026, 9, 9)
    assert result["requests"] == 3
    assert result["failed_chunks"] == 0
    assert result["limited"] is True
    assert len(result["payloads"]) == 4  # cabecera + tres bloques
    assert [url for url, _ in calls] == [
        "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates=20260701-20260721",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates=20260722-20260811",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates=20260812-20260901",
    ]
    assert {timeout for _, timeout in calls} == {17}


def test_fetch_espn_scoreboard_window_conserva_bloques_fallidos():
    import datetime as dt

    calls = []

    def fake_get(url, *, timeout):
        calls.append(url)
        if "dates=20260722-20260811" in url:
            raise RuntimeError("fallo simulado")
        return {"url": url}

    result = lpf_http.fetch_espn_scoreboard_window(
        "arg.1",
        dias=30,
        max_req=4,
        get_json=fake_get,
        today=dt.date(2026, 8, 10),
    )

    assert result["requests"] == 4
    assert result["failed_chunks"] == 1
    assert result["limited"] is False
    assert len(result["payloads"]) == 4  # cabecera + tres bloques exitosos


def test_fetch_espn_scoreboard_window_fecha_futura_vuelve_a_hoy():
    import datetime as dt

    calls = []

    def fake_get(url, *, timeout):
        calls.append(url)
        return {"url": url}

    result = lpf_http.fetch_espn_scoreboard_window(
        "eng.1",
        dias=7,
        desde="2027-01-01",
        get_json=fake_get,
        today=dt.date(2026, 8, 10),
    )

    assert result["start_date"] == dt.date(2026, 8, 10)
    assert result["end_date"] == dt.date(2026, 8, 17)
    assert result["requests"] == 1
    assert result["limited"] is False
    assert calls[-1].endswith("?dates=20260810-20260817")


def test_fetch_futbolargentino_results_pages_preserva_cache_buster_y_fallos():
    calls = []

    def fake_get(url, *, referer, timeout):
        calls.append((url, referer, timeout))
        if "clausura" in url:
            raise RuntimeError("fallo simulado")
        return "<html>ok</html>", "https://final.test/resultados"

    result = lpf_http.fetch_futbolargentino_results_pages(
        (
            "https://source.test/resultados",
            "https://source.test/clausura/resultados?x=1",
        ),
        referer="https://source.test/",
        timeout=19,
        get_html=fake_get,
        timestamp=1234,
    )

    assert result["timestamp"] == 1234
    assert [call[0] for call in calls] == [
        "https://source.test/resultados?_lpf_refresh=1234",
        "https://source.test/clausura/resultados?x=1&_lpf_refresh=1235",
    ]
    assert {call[1] for call in calls} == {"https://source.test/"}
    assert {call[2] for call in calls} == {19}
    assert result["attempts"] == [
        {
            "source_url": "https://source.test/resultados",
            "request_url": "https://source.test/resultados?_lpf_refresh=1234",
            "html": "<html>ok</html>",
            "final_url": "https://final.test/resultados",
            "error": "",
        },
        {
            "source_url": "https://source.test/clausura/resultados?x=1",
            "request_url": "https://source.test/clausura/resultados?x=1&_lpf_refresh=1235",
            "html": "",
            "final_url": "",
            "error": "fallo simulado",
        },
    ]
