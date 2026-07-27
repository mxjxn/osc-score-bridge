# OSC Score Bridge

A Blender addon that maps **SuperCollider** score data to **Blender animations** — without realtime audio.

Generate an OSC score file in SuperCollider, load it in Blender, map any parameter (frequency, amplitude, etc.) to any animatable property, and bake it to F-Curves. No audio hardware required.

## Install

1. Download or clone this repo
2. In Blender: **Edit → Preferences → Add-ons → Install from Disk**
3. Select the folder (or zip it first)
4. Enable "OSC Score Bridge"

Look for the **OSC Bridge** tab in the N-sidebar (`N` key in the 3D viewport).

## How It Works

```
SuperCollider NRT          Blender
┌─────────────┐          ┌─────────────────┐
│  score.scd  │  .osc    │  OSC Bridge     │
│  sclang     ├─────────►│  Parse → Map    │
│             │  file    │  Bake → F-Curve │
└─────────────┘          └─────────────────┘
```

### 3-Step Workflow

1. **Load** a `.osc` file — tracks are auto-detected (`sine.freq`, `saw.amp`, `control_0`, etc.)
2. **Map** a track to a Blender property with custom input/output ranges
3. **Bake** — generates F-Curve keyframes on the timeline

### Example Mapping

| OSC Track | Target | Input Range | Output Range | Result |
|---|---|---|---|---|
| `sine.freq` | `rotation_euler[2]` | 440–660 Hz | 0.0–6.283 rad | Each note spins the object |
| `saw.amp` | `location[1]` | 0.0–0.2 | -2.0–2.0 m | Bass moves object vertically |
| `noise.amp` | `scale[0]` | 0.0–0.15 | 0.5–1.5 | Noise bursts scale the object |

## Generating OSC Files

SuperCollider 3.13 doesn't have a built-in OSC score export. Here's a minimal working example:

```supercollider
SynthDef(\sine, { |out = 0, freq = 440, amp = 0.3, sustain = 1|
    var env = EnvGen.kr(Env.linen(0.01, sustain, 0.1), doneAction: 2);
    var sig = SinOsc.ar(freq) * amp * env;
    Out.ar(out, sig ! 2);
}).add;

{
    var score = Score([
        [0.0, [\s_new, \sine, 1000, 0, 0, \freq, 440, \amp, 0.3, \sustain, 1]],
        [1.0, [\s_new, \sine, 1001, 0, 0, \freq, 880, \amp, 0.2, \sustain, 0.5]],
    ]);

    // Custom writer — saves timestamp + OSC address per line
    ~writeOSCFile.value(score, "myscore.osc");
}.value;
```

The output file looks like:

```
0.0 /s_new sine 1000 0 0 freq 440 amp 0.3 sustain 1
1.0 /s_new sine 1001 0 0 freq 880 amp 0.2 sustain 0.5
```

Patterns work too — `Pbind` → `asScore()` → same writer.

## Features

- **Auto-detect** tracks from `/s_new`, `/n_set`, and `/c_set` messages
- **Range mapping** — remap any input range to any output range per mapping
- **Interpolation** — Step (percussive), Linear (smooth), or Bezier
- **Multi-target** — map one track to multiple objects
- **Re-bakeable** — overwrites cleanly, no manual cleanup needed
- **Blender 5.x** slotted actions fully supported
- **In-panel docs** — Guide, Format reference, and Tips tabs right in the UI

## Requirements

- Blender 4.2+ (tested on 5.2 LTS)
- SuperCollider 3.13+ (for generating `.osc` files)
- No audio hardware needed

## License

MIT
