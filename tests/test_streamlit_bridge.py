"""Regresiones de integración estática entre Streamlit y los módulos extraídos."""
from __future__ import annotations

import ast
from pathlib import Path


MAIN = Path(__file__).resolve().parents[1] / "calculadora_futbol_argentino.py"


def _module_tree() -> ast.Module:
    return ast.parse(MAIN.read_text(encoding="utf-8"), filename=str(MAIN))


def test_refresh_quality_usa_helper_puro_de_source_issues():
    tree = _module_tree()
    refresh = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_lpf_refresh_quality"
    )
    called_names = {
        node.func.id
        for node in ast.walk(refresh)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "add_source_issues" in called_names
    assert "_lpf_add_source_issues" not in called_names


def test_add_source_issues_esta_importado_desde_lpf_state():
    tree = _module_tree()
    imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "lpf_state"
        for alias in node.names
    }
    assert "add_source_issues" in imports
