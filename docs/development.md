# Development

## Files

- __init__.py — Blender add-on registration and version metadata.
- live.py — UDP listener, timestamp queue, live controls, and dashboard.
- cues.py — synth-independent score cues, state, markers, and baking.
- baker.py — mapping and Blender property/keyframe helpers.
- parser.py — text OSC score parsing.
- performance_scene.py — supplied live performance scene and visual rig.
- properties.py and ui.py — Blender settings and panels.
- protocol.py — shared address, timing, reset, and voice helpers.

## Checks

    python3 -m unittest discover -s tests -v
    python3 -m py_compile *.py
    ./scripts/package.sh

The package script creates dist/osc_score_bridge-1.2.0.zip. Generated dist/, renders/, Blender recovery files, and Python bytecode are ignored.

The canonical repository is mxjxn/osc-score-bridge. Generant packages this checkout through its bridge packaging helper; the vendored copy in Generant is a release artifact.
