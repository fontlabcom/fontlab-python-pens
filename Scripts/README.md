---
this_file: Scripts/README.md
---
# Package demos

- [Recording Pen Demo](Contours/Recording%20Pen%20Demo.py)
- [Transform Pen Demo](Contours/Transform%20Pen%20Demo.py)
- [Outline Measurements Demo](Reports/Outline%20Measurements%20Demo.py)

Run a demo from FontLab's Scripts menu. Each opens an App read-only, nonmodal snapshot report; no open font is needed. Install this package and its declared dependencies, plus `fontlab-fly` and `fontlab-fontlabapp` providing `proof.reports.model.show_report` for the menu UI. Copy the functional subfolders from this `Scripts` directory into FontLab’s Scripts folder (or use `install.vfpy` where provided); the demos are also included in the source distribution.

The data belongs to the demo and is detached from open documents. No script edits font data, history, selection, preferences, Output or clipboard. API and UI errors propagate rather than reporting false success.

Outside FontLab, load a script with `runpy.run_path(path)` and call the returned `build_report` function to obtain its JSON-ready results without importing Fly, Qt or native FontLab modules. Calling `main` requires the FontLab report UI.
