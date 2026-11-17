---
this_file: src_docs/md/development-and-limits.md
---

# Development and limits

## Running the tests

```sh
./test.sh
```

This runs pytest on Python 3.11 through `uv`. fontTools is installed only for the tests, and coverage must stay at 80% or above. The command installs the checkout with `--with-editable`: pytest's `pythonpath = ["src"]` does not reach subprocesses, and isolated Python (`-I`) ignores `PYTHONPATH`. Without that install, seven subprocess import checks fail.

## Parity with fontTools

`tests/test_parity.py` sends the same scripted drawings to the fontTools class and to the `fontlab_pens` class, then compares recordings, bounds and areas. The drawings cover lines, cubics, super-beziers, multi-off quadratic strings, off-curve-only (`None`-terminated) TrueType contours, open contours, components and transforms. The relevant upstream fontTools tests are ported in `tests/ported/`.

## Known FontLab behaviour

- A native commit can leave partial geometry if a later write or notification fails. The exception propagates and the pen stays spent; drawing again with another pen can duplicate geometry. An exception inside the drawing body commits nothing.
- With the default `notify=None`, layer appends keep existing raw element payloads. Cached `glyph.fgGlyph` snapshots and expanded dependent component views may stay stale until FontLab rebuilds them.
- History initialization makes the first Undo after a notified write restore the previous geometry. It does not make whole-font history safe: the notification can change timestamps of unrelated glyphs, and history is scoped to the glyph window.
- FontLab's smooth property setter can move neighbouring handles, so `FlPointPen` writes the raw Smooth flag after building the contour. G2, Hobby and raw control-node flags are not represented by the point protocol's boolean `smooth`.
- A closed quadratic contour that starts with an on-curve `qcurve` and no preceding off-curves reads back as `line`. The geometry is identical; FontLab stores both as "on".

## Building this site

The site source is `src_docs/mkdocs.yml` and Markdown under `src_docs/md`. `src_docs/build.sh` builds it with ProperDocs and the MaterialX theme into `docs/`. Every push to `main` rebuilds and qualifies the generated output.
