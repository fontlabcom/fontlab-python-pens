---
this_file: src_docs/md/installation.md
---

# Installation

FontLab Pens needs Python 3.11 or later and has no runtime dependencies. It is not on PyPI; install a tagged release from GitHub.

## Into FontLab 9

1. Download or clone [fontlab-python-pens](https://github.com/fontlabcom/fontlab-python-pens).
2. Open `install.vfpy` in FontLab 9: double-click it or drop it onto the FontLab window.
3. Restart FontLab.

`install.vfpy` is a short stub that hands the work to [FontLab Instamix](https://fontlabcom.github.io/fontlab-python-instamix/). If Instamix is missing, the stub installs it from PyPI first. Instamix then installs the package into FontLab's own `site-packages` and records it under the extension id `com.fontlab.pens`.

The examples and Scripts also need FontLab Fly 1.3.0 or later, which provides the `fly.pens` and `fly.fl` aliases. Install Fly separately; older Fly releases without `fly.pens` cannot run them.

## Into a Python environment

```sh
uv pip install "fontlab-python-pens @ git+https://github.com/fontlabcom/fontlab-python-pens@v1.0.9"
```

Replace `v1.0.9` with the release you want. Outside FontLab the pure-Python pens work fully; the native pens need FontLab's `fontgate` or `fontlab` module and raise when you call them without it.

## Check the install

```python
import fontlab_pens
print(fontlab_pens.__version__)
```

In FontLab, run this in the Scripting panel. A version number means FontLab's Python can import the package.
