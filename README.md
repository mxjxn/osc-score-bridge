# OSC Score Bridge

OSC Score Bridge is a Blender add-on for receiving event data over OSC and applying it to Blender properties, objects, cameras, and animation timelines.

It is the Blender-side companion to [Generant](https://github.com/mxjxn/Generant), a desktop workstation that sequences notes, controls, curves, and arbitrary markers. Generant produces the events; this add-on previews them live or bakes them into deterministic Blender data.

## Install

1. Download or clone this repository.
2. In Blender, open Edit → Preferences → Add-ons → Install from Disk.
3. Select a packaged zip or the add-on directory.
4. Enable OSC Score Bridge.
5. Open the OSC Bridge tab in the 3D View sidebar.

The default UDP port is 57141.

## Basic workflow

1. Start Generant or another OSC sender.
2. Use Live Performance → Listen for live preview.
3. Map incoming controls to Blender properties, or configure score cues.
4. For a final render, import an OSC score and bake it to F-Curves, custom properties, and timeline markers.
5. Render with the receiver stopped; the baked scene contains the animation data.

Live preview is useful for performance and setup. Baking is the deterministic path for rendering.

## Supported data

- timestamped note-on, note-off, set, free, and choke messages;
- normalized control values;
- numeric and string state changes;
- sampled curves and easing;
- arbitrary markers such as /song/part1;
- camera routes and custom cue properties.

The add-on can also create a generic visual rig for incoming tracks and build the included portrait tunnel demo scene.

## Documentation

- [OSC protocol and addresses](docs/protocol.md)
- [Blender workflow and baking](docs/blender-workflow.md)
- [Development and packaging](docs/development.md)
- [Generant workstation](https://mxjxn.github.io/Generant/)

## Tests

    python3 -m unittest discover -s tests -v
    python3 -m py_compile *.py

The Blender smoke test requires Blender. Parser and protocol tests run without Blender.

## License

MIT. See [LICENSE](LICENSE).
