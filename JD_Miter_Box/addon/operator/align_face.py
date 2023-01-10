import bpy
import bmesh

from bpy.types import Operator

import traceback
import math
from enum import Enum

import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d

from mathutils import Vector, Matrix

from ..utility.draw.core import JDraw_Text_Box_Multi

from ..utility.math import distance_point_to_edge_2d, rotate_point_around_axis

from ..utility.mesh import coors_loc_to_world

Align_Face_kb_general = {'mode' :
    {'key':'V', 'desc':"Mode", 'var':'mode'},
}

class Modes(Enum):
    Rotate = 0
    Project = 1

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

        # set up variables
        self.setup(event)
        self.update(event, context)

        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_3d, (context,), 'WINDOW', 'POST_VIEW')
        self.draw_UI_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_2d, (context, ), 'WINDOW', 'POST_PIXEL')
            
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def setup(self, event):

        self.edge_verts = []

        for e in self.bm.edges:
            if e.select:
                self.edge_verts += e.verts

        self.active_verts = []

        for index, v in enumerate(self.bm.select_history.active.verts):
            self.active_verts.append(v)

        self.selected_verts = []

        for v in self.bm.verts:
            if v.select and v not in self.active_verts:
                self.selected_verts.append(v)

        self.mouse_loc_start = (event.mouse_region_x, event.mouse_region_y)

        self.offset = self.active_verts[0].co

        self.angle = 0
        self.mode = Modes.Rotate.name

        # input management variables
        self.index = 0
            
        

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
            self.mouse_loc = (event.mouse_region_x, event.mouse_region_y)

            dist_from_start = Vector(self.mouse_loc)-Vector(self.mouse_loc_start)
            dist_from_start = dist_from_start[0]

            self.angle = dist_from_start/3

            self.update(event, context)

        # Cycle modes
        if event.type == Align_Face_kb_general['mode']['key'] and event.value == 'PRESS':
            self.index += 1
            self.index %= len(Modes)
            self.mode = Modes(self.index).name
            self.update(event, context)

        # Confirm
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            self.remove_shaders(context)

            for index, vert in enumerate(self.selected_verts):
                vert.co = self.new_point_coors[index]
            
            bmesh.update_edit_mesh(self.objdata)

            return {'FINISHED'}

        context.area.tag_redraw()

        return {"RUNNING_MODAL"}


    def update(self, event, context):

        self.rot_axis = self.active_verts[0].co - self.active_verts[1].co    

        self.new_point_coors = self.rotate_verts(self.selected_verts)
        self.new_edge_coors = self.rotate_verts(self.edge_verts)

        # oldpoint_pos = self.selected_verts[0].co.copy()
        # oldpoint_pos -= self.offset

        # self.rot_axis = self.active_verts[0].co - self.active_verts[1].co        
        # self.new_point_co = rotate_point_around_axis(self.rot_axis, oldpoint_pos, self.angle)

        # self.new_point_co += self.offset



        # self.mouse_loc = Vector((event.mouse_region_x, event.mouse_region_y))


        # region = context.region
        # rv3d = bpy.context.space_data.region_3d
        
        # closest_edge = None
        # min_distance = None

        # for index, edge in enumerate(self.edges):
        #     verts = [v.co for v in edge.verts]
        #     coors = coors_loc_to_world(verts, self.obj)
        #     SS_verts = []
        #     for coor in coors:
        #         SS_verts.append(location_3d_to_region_2d(region, rv3d, coor, default=None))

        #     if index == 0:
        #         closest_edge = edge
        #         min_distance = distance_point_to_edge_2d(self.mouse_loc, SS_verts[0], SS_verts[1])

        #     curr_dist = distance_point_to_edge_2d(self.mouse_loc, SS_verts[0], SS_verts[1])

        #     if curr_dist <= min_distance:
        #         min_distance = curr_dist
        #         closest_edge = edge

        # self.line = [v.co for v in closest_edge.verts]


    def rotate_verts(self, verts):

        new_point_coors = []
        old_point_coors = [vert.co for vert in verts]

        for old_coor in old_point_coors:
            old_coor = old_coor.copy()
            old_coor -= self.offset

            new_coor = rotate_point_around_axis(self.rot_axis, old_coor, self.angle)

            if self.mode == Modes.Project.name:
                new_coor = self.rotation_length_compensation(new_coor)

            new_coor += self.offset

            new_point_coors.append(new_coor)

        return new_point_coors


    def rotation_length_compensation(self, new_coor):
        perp_0 = new_coor.cross(self.rot_axis)
        perp_to_axis = perp_0.cross(self.rot_axis)
        perp_to_axis = perp_to_axis.normalized()

        scaling_factor = 1/math.cos(math.radians(self.angle))

        if perp_to_axis.length != 0:

            scaling_mat = Matrix.Scale(scaling_factor, 4, perp_to_axis)

            new_coor = new_coor @ scaling_mat

        return new_coor


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

        # LINES

        gpu.state.line_width_set(1)

        world_coors = coors_loc_to_world(self.new_edge_coors, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", (.9, .9, .9, 1.0))
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)

        # LINES

        gpu.state.line_width_set(3)

        coors = [vert.co for vert in self.active_verts]
        world_coors = coors_loc_to_world(coors, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", (0, .9, .4, 1.0))
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)

        # POINT

        gpu.state.point_size_set(10)

        world_coors = coors_loc_to_world(self.new_point_coors, self.obj)

        shader_dots = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_dots = batch_for_shader(shader_dots, 'POINTS', {"pos": world_coors})

        shader_dots.bind()
        shader_dots.uniform_float("color", (1, 1, 0, 1.0))
        batch_dots.draw(shader_dots)

        gpu.state.point_size_set(1)


    def safe_draw_shader_2d(self, context):

        try:
            self.draw_shaders_2d(context)
        except Exception:
            print("2D Shader Failed in Miter Box - Align Face")
            traceback.print_exc()
            self.remove_shaders(context)

    def draw_shaders_2d(self, context):

        texts = ["Angle: %.2f" %self.angle]

        kb_string = "({key}) {desc}"
        kb_status = ": {var}"

        # general
        for _, keys in Align_Face_kb_general.items():
            if keys.get('var'):
                status = kb_status.format(var=getattr(self, keys['var']))
            texts.append(kb_string.format(key=keys['key'], desc=keys['desc'])+status)

        textbox = JDraw_Text_Box_Multi(x=self.mouse_loc[0]+10, y=self.mouse_loc[1]-10, strings=texts, size=15)
        textbox.draw()