from distutils.log import debug
import bpy
import bmesh

import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d

import traceback

from mathutils import Vector
from mathutils.geometry import intersect_line_line

from bpy.types import Operator
from bpy.props import IntProperty, BoolProperty


from ..utility.math import clamp

class AE_OT_ALIGN(Operator):
    bl_idname = "object.ae_align"
    bl_label = "Align Edge"
    bl_description = "Aligns Selected Edge to Active Edge"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object.mode == 'EDIT':
            return True

    def invoke(self, context, event):

        self.obj=context.active_object
        self.objdata = self.obj.data
        self.bm=bmesh.from_edit_mesh(self.obj.data)

        active_verts = []

        for index, v in enumerate(self.bm.select_history.active.verts):
            active_verts.append(v)

        selected_verts = []

        for v in self.bm.verts:
            if v.select and v not in active_verts:
                selected_verts.append(v)

        self.edge_selected = selected_verts
        # self.edge_selected_coor = [vert.co for vert in selected_verts]

        self.edge_active = active_verts
        # self.edge_active_coor = [vert.co for vert in active_verts]


        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_3d, (context,), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        context.area.tag_redraw()

        # Free navigation
        if event.type in ('MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'):
            return {'PASS_THROUGH'}

        # Cancel
        elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            self.remove_shaders(context)
            return {'CANCELLED'}

        # Adjust
        elif event.type == 'MOUSEMOVE':
            self.mouse_loc = (event.mouse_region_x, event.mouse_region_y)

            self.closest_active_vert = self.get_closest_active_vert(context)
            mov_vert_connected = self.get_moving_vert_connected_verts(self.closest_active_vert, self.edge_selected)

            self.moving_lines = self.get_moving_edge_lines(self.closest_active_vert, mov_vert_connected)

            self.guide_edge, guide_vert = self.get_moving_edge_by_angle(context, self.closest_active_vert, mov_vert_connected, self.mouse_loc)

            other_vert_loc, self.new_vert_loc = self.find_intersection_point(self.closest_active_vert, guide_vert, self.edge_selected, self.edge_active)

            self.new_edge = [other_vert_loc, self.new_vert_loc, self.closest_active_vert.co, self.new_vert_loc]

        # Confirm
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            self.remove_shaders(context)

            if self.new_vert_loc == self.mouse_loc:
                self.report({'ERROR'}, "No valid intersection point found!")
                return {'FINISHED'}

            self.closest_active_vert.co = self.new_vert_loc
            bmesh.update_edit_mesh(self.objdata)

            return {'FINISHED'}

        return {"RUNNING_MODAL"}
        

    def get_closest_active_vert(self, context):
        region = context.region
        rv3d = bpy.context.space_data.region_3d

        active_edge_dist_to_cursor = []

        for vert in self.edge_selected:
            coor = coor_loc_to_world(vert.co, self.obj)
            SS_vert = location_3d_to_region_2d(region, rv3d, coor, default=None)

            difference = Vector(self.mouse_loc) - SS_vert
            active_edge_dist_to_cursor.append(difference.length)

        index = active_edge_dist_to_cursor.index(min(active_edge_dist_to_cursor))
        closest_active_vert = self.edge_selected[index]

        return closest_active_vert

    def get_moving_vert_connected_verts(self, moving_vert, selected_verts):
        # taken from https://blenderartists.org/t/how-to-get-vertex-position-and-connected-vertices/1185279
        # get its connected vertices (filter out the other selected)
        mov_vert_connected=[]
        for l in moving_vert.link_edges:
            other_vert = l.other_vert(moving_vert)
            if other_vert not in selected_verts:
                mov_vert_connected.append(other_vert)

        return mov_vert_connected

    def get_moving_edge_lines(self, active_vert, moving_verts):
        
        moving_edges = []

        for vert in moving_verts:
            moving_edges += [active_vert.co, vert.co]

        return moving_edges

        # return [active_vert.co, moving_verts[0].co, active_vert.co, moving_verts[1].co]

    def get_moving_edge_by_angle(self, context, active_vert, moving_verts, SS_mouse_loc):

        region = context.region
        rv3d = bpy.context.space_data.region_3d

        active_vert_co = coor_loc_to_world(active_vert.co, self.obj)
        SS_mouse_loc = Vector(SS_mouse_loc)
        
        SS_active_vert = location_3d_to_region_2d(region, rv3d, active_vert_co, default=None)

        SS_moving_verts = []
        for vert in moving_verts:
            vert_co = coor_loc_to_world(vert.co, self.obj)
            SS_mov_vert = location_3d_to_region_2d(region, rv3d, vert_co, default=None)
            SS_moving_verts.append(SS_mov_vert)

        V_to_mouse = SS_mouse_loc-SS_active_vert
        V_to_mouse = V_to_mouse.normalized()


        V_to_mov_verts = []
        for SS_vert in SS_moving_verts:
            V_to_mov_vert = SS_vert-SS_active_vert
            V_to_mov_vert = V_to_mov_vert.normalized()
            V_to_mov_verts.append(V_to_mov_vert)


        dot_products = []

        for v_to_vert in V_to_mov_verts:
            dotproduct = V_to_mouse.dot(v_to_vert)
            dot_products.append(dotproduct)

        closest_vert = moving_verts[dot_products.index(max(dot_products))]

        guide_edge = [active_vert.co, closest_vert.co]

        return guide_edge, closest_vert


    def find_intersection_point(self, moving_vert, guide_vert, selected_verts, active_verts):

        selected_verts = selected_verts.copy()

        # get direction vector to first one
        dir_guide = guide_vert.co - moving_vert.co
        
        guide_co_0 = moving_vert.co
        guide_co_1 = moving_vert.co + dir_guide

        # active edge is the parallel edge
        # get its direction vector
        dir_paral = active_verts[0].co - active_verts[1].co

        # get the OTHER selected vertex
        selected_verts.remove(moving_vert)
        other_vert = selected_verts[0]
        # use that position and the same vert + the direction vector as the second line
        paral_co_0 = other_vert.co
        paral_co_1 = other_vert.co + dir_paral

        intersections = intersect_line_line(guide_co_0, guide_co_1, paral_co_0, paral_co_1)
        inter_diff = intersections[0]-intersections[1]
        
        if inter_diff.length < 0.001:
            # print("intersection found!")
            # print(intersections[0])

            return other_vert.co, intersections[0]
        
        else:
            return other_vert.co, self.mouse_loc

            

    def remove_shaders(self, context):
        '''Remove shader handle.'''

        if self.draw_handle != None:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")
            context.area.tag_redraw()


    def safe_draw_shader_3d(self, context):

        try:
            self.draw_shaders_3d(context)
        except Exception:
            print("3D Shader Failed in JD Align Edge")
            traceback.print_exc()
            self.remove_shaders(context)


    def draw_shaders_3d(self, context):

        # white
        para_edge_color = (.9, 1, .9, 1.0)

        if self.new_vert_loc == self.mouse_loc:
            # redish
            para_edge_color = (.9, .1, .3, 1.0)

        # LINES
        # active edge, the guide edge

        gpu.state.line_width_set(3)

        coors = [vert.co for vert in self.edge_active]
        world_coors = coors_loc_to_world(coors, self.obj)

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": world_coors})

        shader.bind()
        shader.uniform_float("color", para_edge_color)
        batch.draw(shader)

        gpu.state.line_width_set(1)

        # LINES
        # selected edge, will be made parallel

        coors = [vert.co for vert in self.edge_selected]
        world_coors = coors_loc_to_world(coors, self.obj)

        shader_active = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_active = batch_for_shader(shader_active, 'LINES', {"pos": world_coors})

        shader_active.bind()
        shader_active.uniform_float("color", (1, 1, 0, 1.0))
        batch_active.draw(shader_active)


        # POINT
        # point of selected edge that will be moved to make the edge parallel

        gpu.state.point_size_set(10)

        world_coors = coor_loc_to_world(self.closest_active_vert.co, self.obj)

        shader_dots = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_dots = batch_for_shader(shader_dots, 'POINTS', {"pos": [world_coors]})

        shader_dots.bind()
        shader_dots.uniform_float("color", (1, 1, 0, 1.0))
        batch_dots.draw(shader_dots)

        gpu.state.point_size_set(1)


        # LINES
        # possible guide edges along which edge will be moved to make it parallel

        world_coors = coors_loc_to_world(self.moving_lines, self.obj)


        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", (.7, .7, 0, 1.0))
        batch_moving_lines.draw(shader_moving_lines)


        # LINES
        # active guide edge, along which edge will be moved to make it parallel

        gpu.state.line_width_set(2)

        world_coors = coors_loc_to_world(self.guide_edge, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", para_edge_color)
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)

        

        # the return value when no intersection is found is the mouse location
        if self.new_vert_loc != self.mouse_loc:

            # LINES
            # where edge will be placed

            world_coors = coors_loc_to_world(self.new_edge, self.obj)

            shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

            shader_moving_lines.bind()
            shader_moving_lines.uniform_float("color", (1, 1, 1, 1.0))
            batch_moving_lines.draw(shader_moving_lines)


            # POINT
            # where the point of the selected edge will be moved to upon confirm

            world_coors = coor_loc_to_world(self.new_vert_loc, self.obj)

            gpu.state.point_size_set(10)

            shader_dots = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            batch_dots = batch_for_shader(shader_dots, 'POINTS', {"pos": [world_coors]})

            shader_dots.bind()
            shader_dots.uniform_float("color", (1, 1, 1, 1.0))
            batch_dots.draw(shader_dots)

            gpu.state.point_size_set(1)




def coors_loc_to_world(coors, obj):
    world_coors = []

    for coor in coors:
        world_coors.append(coor_loc_to_world(coor, obj))

    return world_coors

def coor_loc_to_world(coor, obj):
    world_coor = obj.matrix_world @ coor
    return world_coor