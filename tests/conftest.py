# this_file: tests/conftest.py
"""Route host-free Scripts through a Fly namespace double and real Pens modules."""

import sys
from types import ModuleType

import pytest

import fontlab_pens
import fontlab_pens.fontlab


@pytest.fixture(autouse=True)
def fly_namespace(monkeypatch):
    """Keep script import routing separate from fake native implementation details."""
    fly = ModuleType("fly")
    fly.__path__ = []
    fly.pens = fontlab_pens
    monkeypatch.setitem(sys.modules, "fly", fly)
    monkeypatch.setitem(sys.modules, "fly.pens", fontlab_pens)
    monkeypatch.setitem(sys.modules, "fly.pens.fontlab", fontlab_pens.fontlab)
    assert sys.modules["fly.pens"] is sys.modules["fontlab_pens"]
    assert sys.modules["fly.pens.fontlab"] is sys.modules["fontlab_pens.fontlab"]
