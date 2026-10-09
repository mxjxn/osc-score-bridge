"""Generant score cues: synth-independent OSC and deterministic Blender baking."""
import hashlib
import json
import math

import bpy
from bpy.app.handlers import persistent
from bpy.props import CollectionProperty, IntProperty, PointerProperty, StringProperty


def validate_score(score):
    if score.get('format') != 'rack-osc-score' or score.get('version') != 1:
        raise ValueError('Choose a Generant OSC score JSON file')
    duration = score.get('durationSeconds')
    events = score.get('events')
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError('Invalid score duration')
    if not isinstance(events, list) or len(events) > 1000000:
        raise ValueError('Invalid event list')
    previous = -1
    for event in events:
        seconds = event.get('seconds'); address = event.get('address'); args = event.get('args')
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < previous or seconds < 0 or seconds >= duration:
            raise ValueError('Events must be sorted and inside the score duration')
        if not isinstance(address, str) or not address.startswith('/') or len(address) > 128 or any(c in address for c in '\x00"\\'):
            raise ValueError('Invalid OSC address')
        if event.get('kind') not in ('event', 'state', 'curve') or not isinstance(args, list) or len(args) > 32:
            raise ValueError('Invalid cue type or arguments')
        if any(type(value) not in (str, int, float) or (isinstance(value, str) and ('\x00' in value or len(value) > 256)) or (isinstance(value, (int, float)) and not math.isfinite(value)) for value in args):
            raise ValueError('Invalid cue argument')
        previous = seconds
    return score


def property_key(address):
    key = 'osc:' + address
    return key if len(key.encode('utf8')) <= 63 else 'osc:' + hashlib.sha256(address.encode('utf8')).hexdigest()[:56]


def value_of(args):
    return args[0] if len(args) == 1 else json.dumps(args, ensure_ascii=False)


def score_object(scene):
    obj = bpy.data.objects.get(scene.get('rack_osc_object', ''))
    if obj is None or not obj.get('rack_osc_owned') or obj.name not in scene.objects:
        obj = bpy.data.objects.new('Rack OSC Score', None)
        obj['rack_osc_owned'] = True
        scene.collection.objects.link(obj)
        scene['rack_osc_object'] = obj.name
    return obj


def apply_live(address, args):
    scene = bpy.context.scene; obj = score_object(scene); key = property_key(address)
    scene['osc:last_address'] = address
    scene['osc:last_args'] = json.dumps(args, ensure_ascii=False)
    if not args:
        obj[key] = int(obj.get(key, 0) if isinstance(obj.get(key, 0), (int, float)) else 0) + 1
    else:
        obj[key] = value_of(args)
    for route in scene.rack_osc_cameras:
        if route.address == address and route.camera and route.camera.type == 'CAMERA':
            scene.camera = route.camera
    if args and isinstance(args[0], (int, float)):
        from . import live
        live._apply_control_mappings(address, args[0])


def reset_live():
    scene = bpy.context.scene; obj = bpy.data.objects.get(scene.get('rack_osc_object', ''))
    if obj and obj.get('rack_osc_owned'):
        for key in obj.keys():
            if key.startswith('osc:'):
                obj[key] = 0.0 if isinstance(obj[key], (int, float)) else ''
    for key in list(scene.keys()):
        if key.startswith('osc:'):
            del scene[key]


_cache = {}


@persistent
def apply_string_states(scene, *_args):
    text = bpy.data.texts.get(scene.get('rack_osc_score_text', ''))
    if not text:
        return
    raw = text.as_string()
    if _cache.get('raw') != raw:
        try:
            score = validate_score(json.loads(raw))
        except (ValueError, TypeError):
            return
        _cache['raw'] = raw
        _cache['events'] = [event for event in score['events'] if event['args'] and not (len(event['args']) == 1 and type(event['args'][0]) in (int, float))]
    seconds = (scene.frame_current - scene.get('rack_osc_start', 1)) / (scene.render.fps / scene.render.fps_base)
    obj = score_object(scene); states = {}
    for event in _cache['events']:
        if event['seconds'] > seconds:
            break
        states[property_key(event['address'])] = value_of(event['args'])
    for event in _cache['events']:
        key = property_key(event['address'])
        if key in states: obj[key] = states[key]
        elif key in obj: del obj[key]


def bake_score(scene, score, start=1):
    validate_score(score); fps = scene.render.fps / scene.render.fps_base; obj = score_object(scene)
    obj.animation_data_clear()
    for key in list(obj.keys()):
        if key.startswith('osc:'): del obj[key]
    for marker in list(scene.timeline_markers):
        if marker.name.startswith('[Generant OSC] '): scene.timeline_markers.remove(marker)
    counts = {}
    for event in score['events']:
        key = property_key(event['address']); frame = start + event['seconds'] * fps
        if not event['args']:
            counts[key] = counts.get(key, 0) + 1; value = counts[key]
        elif len(event['args']) == 1 and type(event['args'][0]) in (int, float):
            value = event['args'][0]
        else:
            value = None
        if value is not None:
            obj[key] = float(value); obj.keyframe_insert(data_path='["'+key+'"]', frame=frame, group='Generant OSC')
        if event['kind'] != 'curve':
            marker = scene.timeline_markers.new('[Generant OSC] ' + event['address'], frame=round(frame))
            for route in scene.rack_osc_cameras:
                if route.address == event['address'] and route.camera and route.camera.type == 'CAMERA': marker.camera = route.camera
    action = obj.animation_data.action if obj.animation_data else None
    if action:
        curves = list(action.fcurves) if hasattr(action, 'fcurves') else [curve for layer in action.layers for strip in layer.strips for bag in strip.channelbags for curve in bag.fcurves]
        for curve in curves:
            for point in curve.keyframe_points: point.interpolation = 'CONSTANT'
    text = bpy.data.texts.get(scene.get('rack_osc_score_text', '')) or bpy.data.texts.new('Generant OSC Score.json')
    text.clear(); text.write(json.dumps(score)); scene['rack_osc_score_text'] = text.name; scene['rack_osc_start'] = start
    scene.frame_set(scene.frame_current); return obj


class RACKOSC_CameraRoute(bpy.types.PropertyGroup):
    address: StringProperty(name='Address', default='/song/part1')
    camera: PointerProperty(name='Camera', type=bpy.types.Object, poll=lambda self, obj: obj.type == 'CAMERA')


class RACKOSC_OT_add_camera(bpy.types.Operator):
    bl_idname = 'rackosc.add_camera'; bl_label = 'Add camera cue'; bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context): context.scene.rack_osc_cameras.add(); return {'FINISHED'}


class RACKOSC_OT_remove_camera(bpy.types.Operator):
    bl_idname = 'rackosc.remove_camera'; bl_label = 'Remove camera cue'; bl_options = {'REGISTER', 'UNDO'}
    index: IntProperty()
    def execute(self, context): context.scene.rack_osc_cameras.remove(self.index); return {'FINISHED'}


class RACKOSC_OT_import_score(bpy.types.Operator):
    bl_idname = 'rackosc.import_score'; bl_label = 'Import / bake Generant OSC score'; bl_options = {'REGISTER', 'UNDO'}
    filepath: StringProperty(subtype='FILE_PATH'); filter_glob: StringProperty(default='*.json', options={'HIDDEN'})
    def invoke(self, context, event): context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}
    def execute(self, context):
        try:
            with open(self.filepath, encoding='utf8') as handle: score = validate_score(json.load(handle))
            bake_score(context.scene, score, context.scene.frame_start)
        except Exception as exc:
            self.report({'ERROR'}, str(exc)); return {'CANCELLED'}
        self.report({'INFO'}, f"Baked {len(score['events'])} cues to Rack OSC Score; frame range unchanged"); return {'FINISHED'}


class RACKOSC_PT_cues(bpy.types.Panel):
    bl_label = 'Generant Cues'; bl_idname = 'RACKOSC_PT_cues'; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'OSC Bridge'
    def draw(self, context):
        layout = self.layout; layout.operator('rackosc.import_score'); layout.operator('rackosc.add_camera')
        for i, route in enumerate(context.scene.rack_osc_cameras):
            row = layout.row(align=True); row.prop(route, 'address', text=''); row.prop(route, 'camera', text=''); row.operator('rackosc.remove_camera', text='', icon='X').index = i
        layout.label(text='Values: Generant OSC → custom properties osc:/address')
        layout.label(text='Empty messages increment a trigger counter.'); layout.label(text=str(context.scene.get('osc:last_address', 'No cue received')))


classes = (RACKOSC_CameraRoute, RACKOSC_OT_add_camera, RACKOSC_OT_remove_camera, RACKOSC_OT_import_score, RACKOSC_PT_cues)


def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.rack_osc_cameras = CollectionProperty(type=RACKOSC_CameraRoute)
    if apply_string_states not in bpy.app.handlers.frame_change_post: bpy.app.handlers.frame_change_post.append(apply_string_states)


def unregister():
    if apply_string_states in bpy.app.handlers.frame_change_post: bpy.app.handlers.frame_change_post.remove(apply_string_states)
    del bpy.types.Scene.rack_osc_cameras
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
