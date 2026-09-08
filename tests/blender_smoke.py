import pathlib
import sys

import bpy


addon_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(addon_root.parent))
package = __import__(addon_root.name)
package.register()

try:
    scene = bpy.context.scene
    collection = package.performance_scene.build_scene()
    fixture = addon_root / "tests" / "fixtures" / "performance.osc"
    counts = package.performance_scene.bake_performance(str(fixture))

    assert (scene.render.resolution_x, scene.render.resolution_y) == (1080, 1920)
    assert scene.render.fps == 30
    assert (scene.frame_start, scene.frame_end) == (1, 800)
    assert len([obj for obj in collection.objects if obj.get("osc_ring")]) == 36
    assert counts == (1, 2, 2), counts
    assert scene["osc_baked_visual_rings"] == 2

    scene.frame_set(1)
    start_pattern = sorted(
        (round(obj.location.y, 5), obj.active_material.name)
        for obj in collection.objects
        if "osc_tile_row" in obj
    )
    scene.frame_set(801)
    end_pattern = sorted(
        (round(obj.location.y, 5), obj.active_material.name)
        for obj in collection.objects
        if "osc_tile_row" in obj
    )
    assert end_pattern == start_pattern
    print("PASS: Blender registration, portrait scene, score bake, and loop closure")
finally:
    package.unregister()
    bpy.ops.wm.quit_blender()
