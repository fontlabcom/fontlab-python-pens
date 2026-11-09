---
this_file: DEPENDENCIES.md
---

# Dependencies

## Runtime

None. The package uses only the Python standard library, so it installs into
FontLab's Python 3.11 without pulling in anything else. The native `fontgate`,
`fontlab` and `PythonQt` modules (used by later native pens) belong to FontLab
itself and are imported lazily inside functions.

## Test only

| Package | Why |
| --- | --- |
| `pytest` | Test runner. |
| `pytest-cov` | Enforces the 80% coverage gate. |
| `fontTools` | Parity oracle. The tests compare our recordings, bounds and areas with the fontTools pens of the same name, and use `floatToFixedToFloat` in one ported rounding test. `src/` imports it only optionally: when it is installed, `PenError` subclasses its `PenError`. |

`fontPens` and `ufoLib2` are not used. `test.sh` installs the test packages unpinned through `uv run --with`.
