#!/usr/bin/env bash
# this_file: publish.sh
# Build and upload to PyPI with `uv publish`. Refuses a dirty checkout or an
# untagged HEAD, so only clean vX.Y.Z releases are published.
# Tag first with: uvx gitnextver --directory .
# Credentials: set UV_PUBLISH_TOKEN (or pass uv publish options as arguments).
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail
cd "$(dirname "$0")"
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
    echo "Refusing to publish: the working tree is dirty." >&2
    git status --short >&2
    exit 1
fi
TAG="$(git describe --exact-match --tags --match 'v[0-9]*.[0-9]*.[0-9]*' HEAD 2>/dev/null)" || {
    echo "Refusing to publish: HEAD has no vX.Y.Z tag. Run: uvx gitnextver --directory ." >&2
    exit 1
}
./build.sh
VERSION="${TAG#v}"
shopt -s nullglob
ARTIFACTS=(dist/*-"$VERSION"-*.whl dist/*-"$VERSION".tar.gz)
if [[ ${#ARTIFACTS[@]} -ne 2 ]]; then
    echo "Refusing to publish: dist/ does not hold exactly one $VERSION wheel and sdist." >&2
    ls dist >&2
    exit 1
fi
uv publish "$@" "${ARTIFACTS[@]}"
