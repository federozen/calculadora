"""Transporte HTTP para las fuentes publicas usadas por la calculadora.

Este modulo hace solamente red: no parsea tablas, no conoce el estado LPF y no
importa Streamlit. La UI puede envolver estas funciones con su cache; una futura
API puede reutilizarlas o reemplazarlas por otro transporte sin tocar los parsers
ni los motores.
"""
from __future__ import annotations

import time
from typing import Any

import requests


def source_headers(referer: str = "") -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.7",
        "Cache-Control": "no-cache, no-store, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def fetch_html(url: str, *, referer: str = "", timeout: int = 30, retries: int = 1) -> tuple[str, str]:
    """Descarga HTML y devuelve ``(texto, url_final)`` con los errores historicos."""
    last_error: Exception | None = None
    for attempt in range(int(retries) + 1):
        try:
            response = requests.get(
                url,
                headers=source_headers(referer),
                timeout=timeout,
                allow_redirects=True,
            )
            if response.status_code == 200:
                text = response.text or ""
                if len(text.strip()) < 500:
                    raise RuntimeError(
                        f"respondió HTTP 200, pero entregó sólo {len(text)} caracteres"
                    )
                return text, response.url
            raise RuntimeError(
                f"respondió HTTP {response.status_code} en {response.url}"
            )
        except Exception as exc:
            last_error = exc
            if attempt < int(retries):
                time.sleep(1.25 * (attempt + 1))
    raise RuntimeError(str(last_error or "no se pudo descargar la página"))


def fetch_espn_json(url: str, *, timeout: int = 30, retries: int = 2) -> dict[str, Any]:
    """Consulta ESPN y devuelve JSON, sin cache ni efectos sobre la aplicacion."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.7",
        "Referer": "https://www.espn.com.ar/",
        "Cache-Control": "no-cache",
    }

    retryable_statuses = {429, 500, 502, 503, 504}
    last_error: str | None = None

    for attempt in range(int(retries) + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            last_error = (
                f"Error de red al consultar ESPN en {url}: "
                f"{exc.__class__.__name__}: {exc}"
            )
        else:
            if "/standings" in url:
                kind = "tabla de posiciones"
            elif "/scoreboard" in url:
                kind = "fixture/resultados"
            else:
                kind = "datos"

            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise RuntimeError(
                        f"ESPN respondió en {response.url}, pero la respuesta "
                        f"de {kind} no era JSON válido: {exc}"
                    ) from exc
                return payload

            message = (
                f"{kind}: ESPN respondió HTTP {response.status_code} "
                f"en {response.url}"
            )
            if response.status_code == 403:
                raise RuntimeError(
                    f"{message}. ESPN rechazó la solicitud automática. "
                    "Puede estar bloqueando la IP del servidor."
                )
            if response.status_code not in retryable_statuses:
                raise RuntimeError(message)
            last_error = message

        if attempt < int(retries):
            time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(last_error or f"No se pudo consultar ESPN en {url}")
