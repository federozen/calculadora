"""Regresiones del guard de releases y del empaquetado sincronizado."""
from __future__ import annotations

from pathlib import Path
import shutil
import zipfile

from tools.release import (
    build_release_archives,
    read_release_state,
    required_core_files,
    verify_release_tree,
)

ROOT = Path(__file__).resolve().parents[1]


def _copy_release_tree(tmp_path: Path) -> Path:
    target = tmp_path / "repo"
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".pytest_cache", "__pycache__", "*.pyc", "*.zip"))
    return target


def test_release_actual_esta_sincronizado():
    report = verify_release_tree(ROOT)
    state = read_release_state(ROOT)
    assert report["ok"] is True
    assert report["version"] == state.version
    assert report["runtime_api"] == state.runtime_api
    assert report["critical_count"] == len(state.critical_components)


def test_core_incluye_bootstrap_y_todos_los_criticos():
    state = read_release_state(ROOT)
    core = required_core_files(ROOT)
    assert core[:3] == (
        "calculadora_futbol_argentino.py",
        "lpf_version.py",
        "lpf_runtime.py",
    )
    assert set(state.critical_components).issubset(core)


def test_release_detecta_pyproject_con_version_vieja(tmp_path):
    repo = _copy_release_tree(tmp_path)
    pyproject = repo / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = text.replace(f'version = "{read_release_state(ROOT).version}"', 'version = "0.0.0"')
    pyproject.write_text(text, encoding="utf-8")
    report = verify_release_tree(repo)
    assert report["ok"] is False
    assert any("pyproject.toml" in error for error in report["errors"])


def test_release_detecta_componente_critico_faltante(tmp_path):
    repo = _copy_release_tree(tmp_path)
    missing = read_release_state(repo).critical_components[0]
    (repo / missing).unlink()
    report = verify_release_tree(repo)
    assert report["ok"] is False
    assert any(missing in error for error in report["errors"])


def test_incremental_incluye_nucleo_completo_aunque_solo_cambie_un_doc(tmp_path):
    base = _copy_release_tree(tmp_path / "base")
    target = _copy_release_tree(tmp_path / "target")
    (target / "README.md").write_text((target / "README.md").read_text(encoding="utf-8") + "\nCambio menor.\n", encoding="utf-8")
    out = tmp_path / "out"
    paths = build_release_archives(target, out, base)
    with zipfile.ZipFile(paths["update"]) as zf:
        names = set(zf.namelist())
    assert "README.md" in names
    assert set(required_core_files(target)).issubset(names)


def test_sync_contiene_exactamente_nota_y_nucleo(tmp_path):
    out = tmp_path / "out"
    paths = build_release_archives(ROOT, out)
    with zipfile.ZipFile(paths["sync"]) as zf:
        names = set(zf.namelist())
    assert names == {"LEEME-SINCRONIZACION.txt", *required_core_files(ROOT)}
