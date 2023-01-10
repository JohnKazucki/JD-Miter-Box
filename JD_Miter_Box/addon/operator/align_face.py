import bpy
import bmesh

from bpy.types import Operator

import traceback

import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d

from mathutils import Vector

from ..utility.math import distance_point_to_edge_2d

from ..utility.mesh import coors_loc_to_world



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


        self.edges = []

        for e in self.bm.edges:
            # if e.select:
            self.edges.append(e)

        # set up variables
        self.setup()

        self.update(event, context)

        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_3d, (context,), 'WINDOW', 'POST_VIEW')
        # self.draw_UI_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_2d, (context, ), 'WINDOW', 'POST_PIXEL')
            
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def setup(self):
        pass

            
        

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
            self.update(event, context)

        # Confirm
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            self.remove_shaders(context)

            return {'FINISHED'}

        context.area.tag_redraw()

        return {"RUNNING_MODAL"}


    def update(self, event, context):
        
        self.mouse_loc = Vector((event.mouse_region_x, event.mouse_region_y))


        region = context.region
        rv3d = bpy.context.space_data.region_3d
        
        closest_edge = None
        min_distance = None

        for index, edge in enumerate(self.edges):
            verts = [v.co for v in edge.verts]
            coors = coors_loc_to_world(verts, self.obj)
            SS_verts = []
            for coor in coors:
                SS_verts.append(location_3d_to_region_2d(region, rv3d, coor, default=None))

            if index == 0:
                closest_edge = edge
                min_distance = distance_point_to_edge_2d(self.mouse_loc, SS_verts[0], SS_verts[1])

            curr_dist = distance_point_to_edge_2d(self.mouse_loc, SS_verts[0], SS_verts[1])

            if curr_dist <= min_distance:
                min_distance = curr_dist
                closest_edge = edge

        self.line = [v.co for v in closest_edge.verts]


    def remove_shaders(self, context):
        '''Remove shader handle.'''

        if self.draw_handle != None:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")
            context.area.tag_redraw()

        # if self.draw_UI_handle != None:
        #     self.draw_UI_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_UI_handle, "WINDOW")
        #     context.area.tag_redraw()


    def safe_draw_shader_3d(self, context):

        try:
            self.draw_shaders_3d(context)
        except Exception:
            print("3D Shader Failed in Miter Box - Align Face")
            traceback.print_exc()
            self.remove_shaders(context)

    def draw_shaders_3d(self, context):

        # LINES

        gpu.state.line_width_set(3)

        world_coors = coors_loc_to_world(self.line, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", (0, .9, .4, 1.0))
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

        pass