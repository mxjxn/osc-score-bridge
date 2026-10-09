# Blender workflow

## Live preview

Open the OSC Bridge sidebar in the 3D View and click Listen. Incoming events appear in the live dashboard with track, SynthDef, note, voice, and control state. Enable automatic visual objects when you want a quick rig for tracks that do not have explicit mappings.

Use live preview to test mappings, timing, and the relationship between Generant and Blender. Live UDP timing is best effort and depends on the Blender UI timer.

## Mapping

Mappings connect a track or control to a Blender object and data path. Input and output ranges are remapped before keyframes or live values are applied. Step, linear, and Bezier interpolation are available where the target supports them. One source can drive multiple targets.

## Baking

1. Export an OSC score from Generant or Renoise OSC Sequencer, or create a text score.
2. Load the score in the OSC Bridge panel.
3. Configure mappings and camera routes.
4. Click Import / Bake.
5. Inspect the Rack OSC Score Empty, F-Curves, and timeline markers.
6. Stop the receiver before rendering.

Reimporting replaces the bridge-owned score animation and markers while retaining unrelated scene animation. Numeric values become custom-property keyframes. String and multi-argument states remain in an embedded score text and are reconstructed while scrubbing.

## Looping

Set the scene frame range and score duration before baking. For a seamless loop, make the final baked state equal to the first state and exclude the duplicate endpoint frame from the encoded video.
