"""
OSC Score Bridge — Baker
Converts mappings into Blender F-Curves with keyframes.

Uses keyframe_insert() for Blender 5.x compatibility
(new animation system / slotted actions).
"""

import bpy
import math
from . import parser as osc_parser


def remap(value, in_min, in_max, out_min, out_max):
    """Map a value from input range to output range."""
    if in_max == in_min:
        return out_min
    t = (value - in_min) / (in_max - in_min)
    return out_min + t * (out_max - out_min)


def bake_mappings(scene, on_progress=None):
    """
    Bake all mappings into F-Curves.

    Args:
        scene: Blender scene with osc_bridge settings
        on_progress: optional callback(current, total) for UI updates

    Returns:
        (baked_count, errors_list)
    """
    settings = scene.osc_bridge_settings
    mappings = settings.mappings
    fps = settings.fps
    frame_start = settings.frame_start

    if not settings.osc_file:
        return 0, ["No OSC file loaded"]

    # Parse the OSC file fresh
    try:
        tracks = osc_parser.parse_osc_file(
            bpy.path.abspath(settings.osc_file)
        )
    except Exception as e:
        return 0, [f"Parse error: {e}"]

    baked = 0
    errors = []
    total = len(mappings)

    for i, mapping in enumerate(mappings):
        if on_progress:
            on_progress(i, total)

        track_name = mapping.track_name
        if track_name not in tracks:
            errors.append(f"Track '{track_name}' not found in OSC file")
            continue

        events = tracks[track_name]
        if not events:
            errors.append(f"Track '{track_name}' has no events")
            continue

        try:
            _bake_single(mapping, events, scene, fps, frame_start)
            mapping.baked = True
            baked += 1
        except Exception as e:
            errors.append(f"'{track_name}': {e}")

    return baked, errors


def _bake_single(mapping, events, scene, fps, frame_start):
    """Bake a single mapping using keyframe_insert()."""

    # Resolve the target object
    obj_name = mapping.target_object.strip()
    if obj_name:
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            raise ValueError(f"Object '{obj_name}' not found")
    else:
        raise ValueError("No target object specified")

    data_path = mapping.target_data_path
    array_index = mapping.target_array_index

    # Ensure animation data + action exist
    if obj.animation_data is None:
        obj.animation_data_create()
    if obj.animation_data.action is None:
        obj.animation_data.action = bpy.data.actions.new(
            name=f"OSC_{mapping.track_name}"
        )

    action = obj.animation_data.action

    # Remove existing keyframes on this data_path/index
    _clear_fcurves_for(action, data_path, array_index)

    # Set interpolation mode mapping
    interp_map = {
        "STEP": "CONSTANT",
        "LINEAR": "LINEAR",
        "BEZIER": "BEZIER",
    }
    blender_interp = interp_map.get(mapping.interp_mode, "CONSTANT")

    # Insert keyframes by setting frame first, then value, then inserting.
    # Order matters: frame_set triggers depsgraph eval which applies existing
    # F-curves, so we must set our value AFTER frame_set to avoid overwrites.
    for time_sec, raw_value in events:
        frame = int(time_sec * fps) + frame_start
        value = remap(
            raw_value,
            mapping.in_min, mapping.in_max,
            mapping.out_min, mapping.out_max,
        )

        # 1. Move to target frame (applies any existing animation)
        scene.frame_set(frame)
        # 2. Set our remapped value (overwrites whatever depsgraph did)
        _set_property_value(obj, data_path, array_index, value)
        # 3. Insert keyframe at current frame with current value
        obj.keyframe_insert(data_path, index=array_index)

    # Set interpolation on all keyframe points
    _set_interpolation(action, data_path, array_index, blender_interp)


def _set_property_value(obj, data_path, array_index, value):
    """Set a property value on an object, handling nested paths."""
    if "." in data_path and not data_path.startswith("["):
        # Nested path like "active_material.emission_strength"
        parts = data_path.split(".")
        current = obj
        for part in parts[:-1]:
            current = getattr(current, part, None)
            if current is None:
                raise ValueError(
                    f"Cannot resolve path segment '{part}' in '{data_path}'"
                )
        prop = getattr(current, parts[-1])
        try:
            prop[array_index] = value
        except TypeError:
            setattr(current, parts[-1], value)
    else:
        prop = getattr(obj, data_path)
        try:
            prop[array_index] = value
        except TypeError:
            setattr(obj, data_path, value)


def _get_all_fcurves(action):
    """
    Get all F-curves from an action, handling both legacy
    and Blender 5.x slotted actions.
    Yields (fcurves_collection, parent) tuples.
    """
    # Legacy: direct fcurves
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        yield fcurves
        return

    # Blender 5.x: layers → strips → channelbags → fcurves
    layers = getattr(action, "layers", None)
    if layers is None:
        return

    for layer in layers:
        strips = getattr(layer, "strips", None)
        if strips is None:
            continue
        for strip in strips:
            channelbags = getattr(strip, "channelbags", None)
            if channelbags is None:
                continue
            for cb in channelbags:
                fcs = getattr(cb, "fcurves", None)
                if fcs:
                    yield fcs


def _clear_fcurves_for(action, data_path, array_index):
    """Remove existing F-curves for a specific data_path/index."""
    for fcurves in _get_all_fcurves(action):
        fc = fcurves.find(data_path, index=array_index)
        if fc is not None:
            fcurves.remove(fc)


def _set_interpolation(action, data_path, array_index, interp):
    """Set interpolation on keyframe points."""
    for fcurves in _get_all_fcurves(action):
        fc = fcurves.find(data_path, index=array_index)
        if fc is None:
            continue

        for kp in fc.keyframe_points:
            kp.interpolation = interp

        if interp == "BEZIER":
            for kp in fc.keyframe_points:
                kp.handle_left_type = "AUTO_CLAMPED"
                kp.handle_right_type = "AUTO_CLAMPED"

        fc.update()


def clear_baked(scene):
    """Remove all baked F-Curves for OSC mappings."""
    settings = scene.osc_bridge_settings
    removed = 0

    for mapping in settings.mappings:
        if not mapping.baked:
            continue

        obj_name = mapping.target_object.strip()
        if not obj_name:
            continue

        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            continue

        anim_data = getattr(obj, "animation_data", None)
        if anim_data is None or anim_data.action is None:
            continue

        action = anim_data.action
        _clear_fcurves_for(
            action,
            mapping.target_data_path,
            mapping.target_array_index,
        )
        removed += 1
        mapping.baked = False

    return removed
