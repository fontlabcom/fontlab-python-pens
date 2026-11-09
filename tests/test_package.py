# this_file: tests/test_package.py
"""Package-level guarantees: zero runtime dependencies and a complete public API."""

from __future__ import annotations

import subprocess
import sys
import textwrap

import fontlab_pens


def test_import_when_fresh_interpreter_without_fonttools_then_only_stdlib_modules_loaded():
    code = textwrap.dedent(
        """
        import sys
        sys.modules["fontTools"] = None  # simulate fontTools not installed
        before = set(sys.modules)
        import fontlab_pens
        loaded = {m.split(".")[0] for m in set(sys.modules) - before}
        foreign = sorted(m for m in loaded - {"fontlab_pens"}
                         if m not in sys.stdlib_module_names and not m.startswith("_"))
        print(",".join(foreign))
        """
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "", f"import fontlab_pens loaded non-stdlib modules: {out}"


def test_pen_error_when_fonttools_missing_then_plain_exception_subclass():
    code = textwrap.dedent(
        """
        import sys
        sys.modules["fontTools"] = None
        from fontlab_pens import PenError
        print(PenError.__mro__[1].__qualname__)
        """
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "Exception", f"without fontTools PenError must derive from Exception, got {out}"


def test_pen_error_when_fonttools_installed_then_subclasses_fonttools_pen_error():
    from fontTools.pens.basePen import PenError as FontToolsPenError

    assert issubclass(fontlab_pens.PenError, FontToolsPenError), (
        "fontlab_pens.PenError must subclass fontTools.pens.basePen.PenError"
    )
    try:
        raise fontlab_pens.ComponentError("x")
    except FontToolsPenError:
        pass
    else:  # pragma: no cover - the except branch is the assertion
        raise AssertionError("fontTools PenError handler must catch ComponentError")


def test_all_when_listed_then_every_name_resolves():
    missing = [name for name in fontlab_pens.__all__ if not hasattr(fontlab_pens, name)]
    assert not missing, f"__all__ names missing from the package: {missing}"


def test_version_when_installed_then_is_non_empty_string():
    assert isinstance(fontlab_pens.__version__, str) and fontlab_pens.__version__, (
        "__version__ must be a non-empty string"
    )


def test_null_pen_when_driven_then_accepts_every_call():
    pen = fontlab_pens.NullPen()
    pen.moveTo((0, 0))
    pen.lineTo((1, 1))
    pen.curveTo((1, 2), (2, 2), (3, 3))
    pen.qCurveTo((4, 4), (5, 5))
    pen.closePath()
    pen.endPath()
    pen.addComponent("a", (1, 0, 0, 1, 0, 0))
    pen.addVarComponent("a", None, {})
    assert True, "NullPen accepted the full protocol"
