# this_file: tests/test_scripts_demos.py
"""Execute the actual menu demos with real package APIs and detached data."""

import importlib.util
import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "Scripts"
PATHS = sorted(SCRIPTS.glob("*/*.py"))


def load_demo(path):
    spec = importlib.util.spec_from_file_location("menu_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reports_when_run_then_produce_real_detached_results():
    reports = {path.stem: load_demo(path).build_report() for path in PATHS}
    assert len(reports) == 3, "Every advertised demo must execute"
    json.dumps(reports, allow_nan=False)
    recording = reports["Recording Pen Demo"]
    assert recording["recording"] == recording["replayed"], "Replay must retain all commands"
    assert recording["recording"][1] == ("lineTo", ((100, 0),))
    transformed = reports["Transform Pen Demo"]
    assert transformed["original"][0] == ("moveTo", ((0, 0),))
    assert transformed["transformed"][0] == ("moveTo", ((10, 20),))
    assert transformed["transformed"][1] == ("lineTo", ((210, 20),))
    assert reports["Outline Measurements Demo"] == {
        "bounds": (0, 0, 200, 100),
        "signed_area": 20000,
    }


@pytest.mark.parametrize("path", PATHS, ids=lambda path: path.stem)
def test_main_when_launched_then_shows_same_report_with_unique_key(path, monkeypatch):
    shown = []
    monkeypatch.setitem(
        sys.modules,
        "fly.ap.proof.reports.model",
        SimpleNamespace(show_report=lambda report, **kw: shown.append((report, kw))),
    )
    expected = load_demo(path).build_report()
    runpy.run_path(str(path), run_name="__main__")
    assert len(shown) == 1
    report, options = shown[0]
    assert report == expected
    assert options["title"] == path.stem
    assert options["key"].endswith(path.stem.lower().replace(" ", "-"))


@pytest.mark.parametrize("path", PATHS, ids=lambda path: path.stem)
def test_main_when_report_window_fails_then_error_propagates(path, monkeypatch):
    def refused(*args, **kwargs):
        raise RuntimeError("report window unavailable")

    monkeypatch.setitem(
        sys.modules, "fly.ap.proof.reports.model", SimpleNamespace(show_report=refused)
    )
    with pytest.raises(RuntimeError, match="report window unavailable"):
        load_demo(path).main()
