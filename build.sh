#!/usr/bin/env bash
# this_file: build.sh
# Build the sdist and wheel into dist/. hatch-vcs takes the version from the
# latest vX.Y.Z git tag (a dev version when HEAD is past the tag or dirty).
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail
cd "$(dirname "$0")"
rm -rf dist
uv build --out-dir dist
ls -l dist
