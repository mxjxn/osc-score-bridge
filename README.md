# OSC Score Bridge

A Blender add-on that receives live musical events over OSC and maps recorded **SuperCollider** score data to **Blender animations**.

## Live performance quick start

1. Install and enable the add-on, then open **View3D → Sidebar (`N`) → OSC Bridge**.
2. Expand **Live Performance** and click **Listen**. The default UDP port is `57141`.
3. Start an OSC sender. The Ambient Companion server reports `Blender OSC mirror 127.0.0.1:57141` when its mirror is active.
4. Enable browser audio and connect `sclang`, then play the sequencer or evaluate `~wcNote.(\bass, 48, 1)`.
5. The dashboard shows the track, SynthDef, note and active voice count. With **Create visuals for new tracks** enabled, one reactive object is created per musical track.

Click **Build Portrait Tunnel** for the first designed performance scene. It creates:

- a 1080 × 1920 Eevee composition at 30 FPS;
- an 800-frame, 12-bar timeline at 108 BPM;
- 44 rows of bass-reactive floor tiles with an exact 33-row seamless wrap;
- two transparent, pad-reactive displaced glass walls;
- a pool of 36 psychedelic segmented drum rings in six patterns;
- portrait camera movement and a glow compositor.

The loop is rendered on frames 1–800. Frame 801 is the duplicate loop state and should not be included in the video.

Load a recorded text `.osc` take in the main file control and click **Bake Score to Tunnel** to create deterministic timeline animation. Live OSC is not used during the final render. The baker converts bass notes to tile impulses, pad voice activity to wall displacement, and a restrained subset of drum hits to pooled ring flythroughs.

OSC bundles retain their timestamps, so the add-on queues events until their intended audio time. Use **Create / Refresh Visual Rig** to arrange the known track objects in one collection.

### Live OSC protocol

Send messages to UDP port `57141` (configurable in the panel). Plain OSC messages and timestamped OSC bundles are accepted.

| Address | Arguments | Purpose |
|---|---|---|
| `/companion/note` | `track, nodeID, synth, parameter, value...` | Start a voice |
| `/companion/set` | `track, nodeID, parameter, value...` | Change or gate a voice |
| `/companion/free` | `track, nodeID` | End a voice |
| `/companion/choke` | `track` | Choke open/closed drum voices |
| `/rack/control` | `name, value` | Named normalized control (`value` finite, clamped 0–1) |
| `/rack/reset` | _(none)_ | Clear queued events + active voices and reset live envelopes |

Recognized performance tracks are `bass`, `drums`, and `pad`. The dashboard still displays other track names, and the generic visual rig can create an object for each one. Parameters such as `freq`, `amp`, `decay`, `type`, and `spread` drive the supplied scene. Any synth can now auto-expire with explicit `duration`/`dur`, and voices still close immediately via `/companion/free` or `gate <= 0` in `/companion/set`.

Named controls appear in the **Live Performance** panel and can be mapped like other tracks (track name format: `control.<name>`). Mapping targets support regular RNA paths, custom properties (for example `["glow"]`), and modifier paths including Geometry Nodes-style inputs (for example `modifiers["GeometryNodes"]["Input_2"]`).

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

### Recorded score workflow

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

The bridge reads a text score: one timestamped OSC message per line. The output file looks like:

```
0.0 /s_new sine 1000 0 0 freq 440 amp 0.3 sustain 1
1.0 /s_new sine 1001 0 0 freq 880 amp 0.2 sustain 0.5
```

Patterns work too — `Pbind` → `asScore()` → same writer.

### Minimal live sender example (Python)

```python
from pythonosc.udp_client import SimpleUDPClient

client = SimpleUDPClient("127.0.0.1", 57141)
client.send_message("/companion/note", ["bass", 1001, "sampler", "freq", 110, "amp", 0.25, "duration", 0.6])
client.send_message("/rack/control", ["bloom", 1.2])  # clamped to 1.0
client.send_message("/companion/free", ["bass", 1001])
client.send_message("/rack/reset", [])
```

## Features

- **Live dashboard** — inspect incoming notes and active voices by track and SynthDef
- **Automatic visual rig** — create independent bass, drum and pad objects without manual paths
- **Timestamp-aware OSC** — follow scheduled SuperCollider events in sync with browser audio
- **Auto-detect** tracks from `/s_new`, `/n_set`, and `/c_set` messages
- **Range mapping** — remap any input range to any output range per mapping
- **Interpolation** — Step (percussive), Linear (smooth), or Bezier
- **Multi-target** — map one track to multiple objects
- **Re-bakeable** — overwrites cleanly, no manual cleanup needed
- **Blender 5.x** slotted actions fully supported
- **In-panel docs** — Guide, Format reference, and Tips tabs right in the UI

## Requirements

- Blender 4.2+ (tested on 5.2)
- SuperCollider 3.13+ (for generating `.osc` files)
- No audio hardware needed

## License

MIT
