import bpy
import bmesh

from bpy.types import Operator

import gpu
from gpu_extras.batch import batch_for_shader

from mathutils import Vector

from enum import Enum
import traceback

from ...utility.addon import get_prefs

from ...utility.bmesh import get_selected_verts, get_selected_edges
from ...utility.mesh import coors_loc_to_world

from ...utility.interaction import face_normal_cursor
from ...utility.shaders.primitives import plane_center, line

from ...utility.draw.core import JDraw_Text_Box_Multi



class Modes(Enum):
    Rotate = 0
    Project = 1
    Slide = 2

Align_Face_kb_general = {
                        'mode' :
                            {'key':'V', 'desc':"Mode", 'var':'mode'},
}


class MB_OT_ALIGN_FACE(Operator):
    bl_idname = "object.mb_align_face"
    bl_label = "Align Face"
    bl_description = "Aligns Selected Face to Active Face"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object.mode == 'EDIT' and len(context.selected_objects) == 1:

            return True

    def invoke(self, context, event):

        self.obj=context.active_object
        self.objdata = self.obj.data
        self.bm=bmesh.from_edit_mesh(self.obj.data)

        self.setup(event)

        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_3d, (context,), 'WINDOW', 'POST_VIEW')
        self.draw_UI_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_2d, (context, ), 'WINDOW', 'POST_PIXEL')
            
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def setup(self, event):

        self.selected_edges = get_selected_edges(self.bm)
        self.selected_verts = get_selected_verts(self.bm)

        self.rot_edge = [v for v in self.selected_edges[0].verts]

        self.setup_colors()
        self.setup_input()



        self.active_face = self.bm.faces.active
        self.sel_faces = [x for x in self.bm.faces if x.select]
        if self.active_face not in self.sel_faces:
            self.active_face = self.sel_faces[0]
        self.normal = self.active_face.normal 

        self.mouse_loc = Vector((0,0))


    def setup_colors(self):
        prefs = get_prefs()

        self.c_preview_geo = prefs.color.c_preview_geo

        self.c_selected_geo = prefs.color.c_selected_geo
        self.c_selected_geo_sec = prefs.color.c_selected_geo_sec

        self.c_active_geo = prefs.color.c_active_geo

        self.s_vertex = prefs.size.s_vertex
        

    def setup_input(self):
        # input management variables
        self.mode = Modes.Rotate.name
        self.mode_index = Modes.Rotate.value

    def modal(self, context, event):

        # Free navigation
        if event.type in ('MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'):
            return {'PASS_THROUGH'}

        # Cancel
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            # not needed I think, but doesn't hurt to free the bmesh even if we didn't edit it
            bmesh.update_edit_mesh(self.objdata)

            self.remove_shaders(context)
            return {'CANCELLED'}

        # Adjust
        if event.type == 'MOUSEMOVE':
            self.mouse_loc = Vector((event.mouse_region_x, event.mouse_region_y))

        # Cycle modes
        if event.type == Align_Face_kb_general['mode']['key'] and event.value == 'PRESS':
            self.mode_index += 1
            self.mode_index %= len(Modes)
            self.mode = Modes(self.mode_index).name



        face_normal = face_normal_cursor(self.mouse_loc, context)
        if face_normal:
            self.normal = face_normal

        context.area.tag_redraw()

        return {"RUNNING_MODAL"}


    # -- SHADERS

    def remove_shaders(self, context):
        '''Remove shader handle.'''

        if self.draw_handle != None:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")
            context.area.tag_redraw()

        if self.draw_UI_handle != None:
            self.draw_UI_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_UI_handle, "WINDOW")
            context.area.tag_redraw()


    def safe_draw_shader_3d(self, context):

        try:
            self.draw_shaders_3d(context)
        except Exception:
            print("3D Shader Failed in Miter Box - Align Face")
            traceback.print_exc()
            self.remove_shaders(context)

    def draw_shaders_3d(self, context):
        

        if self.mode == Modes.Project.name:
            axis_z = self.normal
            axis_x = self.normal.cross(Vector((0,0,1)))
            axis_y = self.normal.cross(axis_x)

            axis_x.normalize()
            axis_y.normalize()
            axis_z.normalize()

            center = self.rot_edge[0].co + (self.rot_edge[1].co-self.rot_edge[0].co)/2

            plane_center(center, axis_x, axis_y, axis_z, 0.5, self.c_selected_geo_sec)
            line(center, axis_x, axis_y, axis_z, .2, 2, self.c_selected_geo_sec)
            # --------------------------------------------------

        # LINES
        # ROTATION AXIS

        gpu.state.line_width_set(3)

        coors = [v.co for v in self.rot_edge]
        world_coors = coors_loc_to_world(coors, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", self.c_active_geo)
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)




    def safe_draw_shader_2d(self, context):

        try:
            self.draw_shaders_2d(context)
        except Exception:
            print("2D Shader Failed in Miter Box - Align Face")
            traceback.print_exc()
            self.remove_shaders(context)

    def draw_shaders_2d(self, context):

        texts = []

        kb_string = "({key}) {desc}"
        kb_status = ": {var}"

        # general
        for _, keys in Align_Face_kb_general.items():
            if keys.get('var'):
                status = kb_status.format(var=getattr(self, keys['var']))
            texts.append(kb_string.format(key=keys['key'], desc=keys['desc'])+status)

        textbox = JDraw_Text_Box_Multi(x=self.mouse_loc[0]+10, y=self.mouse_loc[1]-10, strings=texts, size=15)
        textbox.draw()

    # ------------------------------
