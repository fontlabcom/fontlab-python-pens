# this_file: tests/test_installer_archive.py
"""Source releases ship the fontlab-instamix stub and a valid install table."""

import re
import subprocess
import tarfile
import tomllib
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical_stub() -> bytes | None:
    """instamix's own stub bytes, from the package or a sibling checkout."""
    try:
        from fontlab_instamix import stub
    except ImportError:
        sibling = ROOT.parent / "fontlab-python-instamix" / "stub" / "install.vfpy"
        return sibling.read_bytes() if sibling.is_file() else None
    return stub.text().encode("utf-8")


STUB_HEADER = b"#FLM: Install this package into FontLab (fontlab-instamix)\n"
REVERSE_DNS = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)+$")  # instamix manifest.ID_PATTERN


def test_installer_when_read_then_is_instamix_stub():
    """install.vfpy is the short stub that delegates to fontlab-instamix."""
    source = (ROOT / "install.vfpy").read_bytes()
    assert source.startswith(STUB_HEADER), "install.vfpy must be the instamix stub"
    assert b"bootstrap.install_project(__file__)" in source, "stub must hand off to instamix"
    assert len(source.splitlines()) < 80, "stub must stay short; legacy installer is gone"
    canonical = canonical_stub()
    if canonical is not None:
        assert source == canonical, "install.vfpy must match instamix's canonical stub"


def test_pyproject_when_parsed_then_install_table_is_valid():
    """[tool.fontlab-install] carries the reverse-DNS id instamix requires."""
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    table = config["tool"]["fontlab-install"]
    assert REVERSE_DNS.match(table["id"]), f"bad extension id {table['id']!r}"


def test_sdist_when_built_then_ships_stub_and_version(tmp_path):
    """The archive carries the stub, its install table and a genuine version."""
    output = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--sdist", "--out-dir", str(output), str(ROOT)],
        check=True, capture_output=True, text=True, timeout=120,
    )
    archives = list(output.glob("*.tar.gz"))
    assert len(archives) == 1, "build must produce one source archive"
    with tarfile.open(archives[0]) as archive:
        prefix = archive.getnames()[0].split("/")[0] + "/"
        read = lambda name: archive.extractfile(prefix + name).read()
        installer, pkg_info, pyproject = read("install.vfpy"), read("PKG-INFO"), read("pyproject.toml")
    assert installer == (ROOT / "install.vfpy").read_bytes(), "installer bytes differ"
    metadata = BytesParser().parsebytes(pkg_info)
    config = tomllib.loads(pyproject.decode("utf-8"))
    assert metadata["Name"] == config["project"]["name"], "archive project identity differs"
    assert metadata["Version"], "PKG-INFO must carry the version instamix records"
    assert "fontlab-install" in config["tool"], "archive pyproject lost [tool.fontlab-install]"
