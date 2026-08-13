"""Verifica y empaqueta releases sin depender de Streamlit ni de la red.

Uso habitual::

    python tools/release.py check
    python tools/release.py build --base-dir /ruta/a/version/anterior --output-dir /mnt/data

El constructor siempre incluye el bootstrap y el núcleo crítico completos en los
paquetes incrementales. Así un cambio pequeño de UI no puede dejar en producción un
``lpf_runtime.py`` o un componente crítico de una versión anterior.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re
import zipfile

EXCLUDED_DIRS = {".git", ".pytest_cache", ".ruff_cache", "__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
BOOTSTRAP_FILES = (
    "calculadora_futbol_argentino.py",
    "lpf_version.py",
    "lpf_runtime.py",
)


@dataclass(frozen=True)
class ReleaseState:
    version: str
    runtime_api: int
    required_runtime_api: int
    critical_components: tuple[str, ...]
    pyproject_version: str | None


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        if value is None:
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            return ast.literal_eval(value)
    raise ValueError(f"No se encontró {name} en {path.name}")


def _pyproject_version(path: Path) -> str | None:
    if not path.exists():
        return None
    in_project = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            in_project = line == "[project]"
            continue
        if not in_project:
            continue
        match = re.match(r'version\s*=\s*["\']([^"\']+)["\']\s*$', line)
        if match:
            return match.group(1)
    return None


def read_release_state(root: str | Path) -> ReleaseState:
    root = Path(root)
    version = str(_literal_assignment(root / "lpf_version.py", "__version__"))
    runtime_api = int(_literal_assignment(root / "lpf_runtime.py", "LPF_RUNTIME_API"))
    critical = tuple(_literal_assignment(root / "lpf_runtime.py", "CRITICAL_COMPONENTS"))
    required = int(_literal_assignment(root / "calculadora_futbol_argentino.py", "_REQUIRED_RUNTIME_API"))
    return ReleaseState(
        version=version,
        runtime_api=runtime_api,
        required_runtime_api=required,
        critical_components=critical,
        pyproject_version=_pyproject_version(root / "pyproject.toml"),
    )


def required_core_files(root: str | Path) -> tuple[str, ...]:
    state = read_release_state(root)
    ordered = list(BOOTSTRAP_FILES)
    for filename in state.critical_components:
        if filename not in ordered:
            ordered.append(filename)
    return tuple(ordered)


def _iter_python_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def verify_release_tree(root: str | Path) -> dict[str, object]:
    root = Path(root)
    errors: list[str] = []
    try:
        state = read_release_state(root)
    except (OSError, SyntaxError, ValueError, TypeError) as exc:
        return {"ok": False, "errors": [f"No se pudo leer el release: {exc}"]}

    if state.runtime_api != state.required_runtime_api:
        errors.append(
            f"Runtime desalineado: lpf_runtime={state.runtime_api}, app={state.required_runtime_api}."
        )
    if len(state.critical_components) != len(set(state.critical_components)):
        errors.append("CRITICAL_COMPONENTS contiene archivos duplicados.")

    for filename in state.critical_components:
        path = root / filename
        if not path.exists():
            errors.append(f"Falta componente crítico: {filename}.")
            continue
        try:
            found = int(_literal_assignment(path, "LPF_RUNTIME_API"))
        except (OSError, SyntaxError, ValueError, TypeError):
            found = None
        if found != state.runtime_api:
            errors.append(
                f"{filename}: LPF_RUNTIME_API={found!r}; esperado {state.runtime_api}."
            )

    if state.pyproject_version != state.version:
        errors.append(
            f"pyproject.toml declara {state.pyproject_version!r}; lpf_version.py declara {state.version!r}."
        )

    readme = root / "README.md"
    if not readme.exists() or state.version not in readme.read_text(encoding="utf-8").splitlines()[0]:
        errors.append(f"README.md no publica la versión {state.version} en su título.")
    changelog = root / "CHANGELOG.md"
    if not changelog.exists() or re.search(
        rf"^##\s+{re.escape(state.version)}(?:\s|$)", changelog.read_text(encoding="utf-8"), re.MULTILINE
    ) is None:
        errors.append(f"CHANGELOG.md no tiene una entrada para {state.version}.")

    for path in _iter_python_files(root):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append(f"No compila {path.relative_to(root)}: {exc}")

    return {
        "ok": not errors,
        "version": state.version,
        "runtime_api": state.runtime_api,
        "critical_count": len(state.critical_components),
        "core_files": list(required_core_files(root)),
        "errors": errors,
    }


def _is_release_file(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if rel.as_posix() == ".streamlit/secrets.toml":
        return False
    return path.is_file()


def _release_files(root: Path) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if _is_release_file(path, root)
    }


def changed_files(base_root: str | Path, target_root: str | Path) -> tuple[list[str], list[str]]:
    base_root = Path(base_root)
    target_root = Path(target_root)
    base = _release_files(base_root)
    target = _release_files(target_root)
    changed = [
        rel for rel, path in target.items()
        if rel not in base or path.read_bytes() != base[rel].read_bytes()
    ]
    removed = sorted(set(base) - set(target))
    return sorted(changed), removed


def _write_zip(zip_path: Path, root: Path, files: list[str], prefix: str = "") -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(dict.fromkeys(files)):
            path = root / rel
            if not path.is_file():
                raise FileNotFoundError(path)
            arcname = f"{prefix}{rel}" if prefix else rel
            zf.write(path, arcname)


def build_release_archives(
    root: str | Path,
    output_dir: str | Path,
    base_dir: str | Path | None = None,
) -> dict[str, str]:
    root = Path(root).resolve()
    output_dir = Path(output_dir).resolve()
    report = verify_release_tree(root)
    if not report["ok"]:
        raise ValueError("Release inválido:\n- " + "\n- ".join(report["errors"]))
    state = read_release_state(root)
    all_files = sorted(_release_files(root))
    full_path = output_dir / f"chat-calculadora-{state.version}.zip"
    _write_zip(full_path, root, all_files, prefix="chat-calculadora-main/")

    core_files = list(required_core_files(root))
    sync_note = root / "LEEME-SINCRONIZACION.txt"
    note_created = False
    if not sync_note.exists():
        sync_note.write_text(
            f"Sincronización del núcleo {state.version}.\n"
            "Copiá todos los .py de este ZIP a la raíz del repositorio y reemplazá los existentes.\n",
            encoding="utf-8",
        )
        note_created = True
    sync_path = output_dir / f"sincronizacion-nucleo-{state.version}.zip"
    _write_zip(sync_path, root, ["LEEME-SINCRONIZACION.txt", *core_files])
    if note_created:
        sync_note.unlink()

    result = {"full": str(full_path), "sync": str(sync_path)}
    if base_dir is not None:
        base_dir = Path(base_dir).resolve()
        base_version = str(_literal_assignment(base_dir / "lpf_version.py", "__version__"))
        changed, removed = changed_files(base_dir, root)
        if removed:
            raise ValueError(
                "El incremental no puede representar archivos eliminados. Usá el ZIP completo. "
                + "Eliminados: " + ", ".join(removed)
            )
        update_files = sorted(set(changed).union(core_files))
        update_path = output_dir / f"actualizacion-{base_version}-a-{state.version}.zip"
        _write_zip(update_path, root, update_files)
        result["update"] = str(update_path)
    return result


def _default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Valida versión, runtime, núcleo y sintaxis.")
    check.add_argument("--root", default=str(_default_root()))
    build = sub.add_parser("build", help="Construye ZIP completo, sync e incremental opcional.")
    build.add_argument("--root", default=str(_default_root()))
    build.add_argument("--output-dir", required=True)
    build.add_argument("--base-dir")
    args = parser.parse_args(argv)

    if args.command == "check":
        report = verify_release_tree(args.root)
        print(f"versión={report.get('version')} runtime={report.get('runtime_api')} críticos={report.get('critical_count')}")
        if report["ok"]:
            print("release OK")
            return 0
        for error in report["errors"]:
            print(f"ERROR: {error}")
        return 1

    try:
        paths = build_release_archives(args.root, args.output_dir, args.base_dir)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    for kind, path in paths.items():
        print(f"{kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
