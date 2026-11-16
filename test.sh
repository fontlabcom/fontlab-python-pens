#!/bin/sh
# this_file: test.sh
# Runs the suite on Python 3.11; fontTools is a test-only oracle.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
cd "$here"
uv run --no-project --python 3.11 --with pytest --with pytest-cov --with fontTools --with-editable "$here" python -m pytest -q --cov=fontlab_pens --cov-fail-under=80 tests "$@"
