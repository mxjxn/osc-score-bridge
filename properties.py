"""
OSC Score Bridge — Property Groups
Defines the data structures stored in the Blender scene.
"""

import bpy
from bpy.props import (
    StringProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    BoolProperty,
    CollectionProperty,
    PointerProperty,
    FloatVectorProperty,
)
from bpy.types import PropertyGroup


class OSCBridgeTrack(PropertyGroup):
    """A detected parameter track from the OSC file."""

    name: StringProperty(
        name="Track Name",
        description="e.g. sine.freq, saw.amp, control_0",
    )
    event_count: IntProperty(name="Events", default=0)
    min_val: FloatProperty(name="Min", default=0.0)
    max_val: FloatProperty(name="Max", default=1.0)
    duration: FloatProperty(name="Duration", default=0.0)
    selected: BoolProperty(name="Selected", default=False)


class OSCBridgeMapping(PropertyGroup):
    """A mapping from an OSC track to a Blender property."""

    # Source track
    track_name: StringProperty(
        name="Track",
        description="OSC track to drive this mapping",
    )

    # Target property
    target_object: StringProperty(
        name="Object",
        description="Name of the Blender object (leave empty for scene/world)",
    )
    target_data_path: StringProperty(
        name="Data Path",
        description="Property path, e.g. rotation_euler, location, energy",
    )
    target_array_index: IntProperty(
        name="Array Index",
        description="For vector properties: 0=X/Red, 1=Y/Green, 2=Z/Blue",
        default=0,
        min=0,
    )

    # Input range
    in_min: FloatProperty(name="In Min", default=0.0)
    in_max: FloatProperty(name="In Max", default=1.0)

    # Output range
    out_min: FloatProperty(name="Out Min", default=0.0)
    out_max: FloatProperty(name="Out Max", default=1.0)

    # Interpolation
    interp_mode: EnumProperty(
        name="Interpolation",
        items=[
            ("STEP", "Step", "Hold value until next event (instant changes)"),
            ("LINEAR", "Linear", "Ramp between consecutive events"),
            ("BEZIER", "Bezier", "Smooth bezier curves between events"),
        ],
        default="STEP",
    )

    # F-Curve creation
    use_action: BoolProperty(
        name="Use Action",
        description="Store keyframes in an Action data-block (recommended)",
        default=True,
    )

    # Status
    baked: BoolProperty(name="Baked", default=False)
    expand: BoolProperty(name="Expand", default=True)


class OSCBridgeSettings(PropertyGroup):
    """Main settings stored on the Scene."""

    osc_file: StringProperty(
        name="OSC File",
        description="Path to the .osc score file",
        subtype="FILE_PATH",
        default="",
    )

    tracks: CollectionProperty(type=OSCBridgeTrack)
    mappings: CollectionProperty(type=OSCBridgeMapping)

    track_index: IntProperty(name="Track Index", default=0)
    mapping_index: IntProperty(name="Mapping Index", default=0)

    frame_start: IntProperty(
        name="Start Frame",
        description="Frame to start baking from",
        default=1,
    )
    fps: FloatProperty(
        name="FPS",
        description="Frames per second for time-to-frame conversion",
        default=24.0,
        min=1.0,
    )

    # Active tab for docs panel
    docs_tab: EnumProperty(
        name="Docs Tab",
        items=[
            ("GUIDE", "Guide", "Quick start guide"),
            ("FORMAT", "Format", "OSC file format reference"),
            ("TIPS", "Tips", "Tips and tricks"),
        ],
        default="GUIDE",
    )
