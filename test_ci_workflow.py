from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_ci_workflow_runs_on_push_and_pull_request():
    text = _workflow_text()
    assert "push:" in text
    assert "pull_request:" in text
    assert "actions/checkout@v4" in text
    assert "actions/setup-python@v5" in text


def test_ci_workflow_runs_tests_lint_and_release_guard():
    text = _workflow_text()
    required = (
        'python -m pip install -e ".[dev]"',
        "python -m pytest -q",
        "python -m ruff check --select F,E9 *.py tests/*.py tools/*.py",
        "python tools/release.py check",
    )
    for command in required:
        assert command in text
    assert "continue-on-error" not in text


def test_ci_workflow_limits_permissions_and_time():
    text = _workflow_text()
    assert "contents: read" in text
    assert "timeout-minutes: 15" in text
    assert "cancel-in-progress: true" in text
