# OSC protocol

OSC Score Bridge listens on UDP port 57141 by default. It accepts plain OSC messages and timestamped OSC bundles.

## Companion messages

| Address | Arguments | Purpose |
|---|---|---|
| /companion/note | track, node id, synth, key/value pairs | Start a voice |
| /companion/set | track, node id, key/value pairs | Update or gate a voice |
| /companion/free | track, node id | End a voice |
| /companion/choke | track | Choke active voices |

The default performance mapping recognizes bass, drums, and pad tracks. Other track names remain available to the generic visual rig.

## Generant control messages

| Address | Arguments | Purpose |
|---|---|---|
| /rack/control | name, normalized value | Apply a named control mapping |
| /rack/reset | none | Reset pending events, voices, and cue state |
| /song/part1 | optional values | Store a cue or marker property |

Reserved /rack, /companion, and /transport reset messages control bridge state. Other addresses can be handled as score cues.

## Score data

A text score contains one timestamped message per line. A minimal line has a time, an address, and arguments:

    0.0 /s_new sine 1000 0 0 freq 440 amp 0.3
    1.0 /song/part1

Generant's song exporter writes ordered OSC tracks and position cues using the same timeline used for playback.
