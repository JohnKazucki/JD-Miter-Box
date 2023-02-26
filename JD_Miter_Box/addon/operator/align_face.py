import bpy
import bmesh

from bpy.types import Operator

import traceback
from enum import Enum

import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d

from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_plane

from bpy_extras import view3d_utils

from ..utility.addon import get_prefs
from ..utility.draw.core import JDraw_Text_Box_Multi

import math
from ..utility.math import distance_point_to_edge_2d, rotate_point_around_axis, clamp

from ..utility.mesh import coors_loc_to_world, coor_loc_to_world
from ..utility.bmesh import get_connected_faces_of_vert, get_connected_verts

Align_Face_kb_general = {
                        'mode' :
                            {'key':'V', 'desc':"Mode", 'var':'mode'},
                        'input' :
                            {'key':'R', 'desc':"Adjusting", 'var':'inputmode'},
}

class Modes(Enum):
    Rotate = 0
    Project = 1
    Slide = 2

class InputModes(Enum):
    Axis = 0
    Angle = 1
    Face = 2

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
        self.update()

        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_3d, (context,), 'WINDOW', 'POST_VIEW')
        self.draw_UI_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader_2d, (context, ), 'WINDOW', 'POST_PIXEL')
            
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def setup(self, event):

        self.edge_verts = []
        self.edges = []

        for e in self.bm.edges:
            if e.select:
                self.edge_verts += e.verts
                self.edges.append(e)

        self.rot_edge = [v for v in self.edges[0].verts]

        self.selected_verts = []

        for v in self.bm.verts:
            if v.select:
                self.selected_verts.append(v)

        # remove the vertices belonging to the rotation axis edge from the selected vertices
        self.moving_verts = [x for x in self.selected_verts if x not in self.rot_edge]

        self.mouse_loc_prev = Vector((event.mouse_region_x, event.mouse_region_y))
        self.mouse_loc = Vector((0,0))

        self.offset = self.rot_edge[0].co

        self.angle = 0

        self.slide_dirs = []
        
        # input management variables
        self.mode = Modes.Rotate.name
        self.mode_index = Modes.Rotate.value

        self.inputmode = InputModes.Axis.name
        self.input_index = InputModes.Axis.value
        
        # TODO : add a mode or autodetect whether to use the active face normal, or the average normal of all selected faces
        self.active_face = self.bm.faces.active
        self.sel_faces = [x for x in self.bm.faces if x.select]
        if self.active_face not in self.sel_faces:
            self.active_face = self.sel_faces[0]
        self.normal = self.active_face.normal       

        

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
            self.dist = event.mouse_x - event.mouse_prev_x

        # Cycle modes
        if event.type == Align_Face_kb_general['mode']['key'] and event.value == 'PRESS':
            self.mode_index += 1
            self.mode_index %= len(Modes)
            self.mode = Modes(self.mode_index).name

        # Cycle Input modes
        if event.type == Align_Face_kb_general['input']['key'] and event.value == 'PRESS':
            self.input_index += 1
            self.input_index %= len(InputModes)
            self.inputmode = InputModes(self.input_index).name


        # Confirm
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            self.remove_shaders(context)

            for index, vert in enumerate(self.moving_verts):
                vert.co = self.new_point_coors[index]
            
            bmesh.update_edit_mesh(self.objdata)

            return {'FINISHED'}


        self.update_input(context)
        self.update()

        context.area.tag_redraw()

        return {"RUNNING_MODAL"}


    def update_input(self, context):
        if self.inputmode == InputModes.Axis.name:
            self.update_axis(context)

        if self.inputmode == InputModes.Angle.name:
            self.angle += self.dist/5

        if self.inputmode == InputModes.Face.name:
            self.angle = 0

            # get normal
            face_normal = self.update_face(context)

            # calculate angle
            if face_normal:
                dot = face_normal.dot(self.normal)
                if dot:
                    # account for floating point inaccuracies
                    dot = clamp(dot, -1, 1)
                    self.angle = math.degrees(math.acos(dot))

                    new_normal = rotate_point_around_axis(self.rot_axis, self.normal, self.angle)

                    # print(1-new_normal.dot(face_normal))

                    if 1- new_normal.dot(face_normal) > .0001:
                        self.angle *= -1
            

    def update_axis(self, context):
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

        self.rot_edge = [v for v in closest_edge.verts]
        # remove the vertices belonging to the rotation axis edge from the selected vertices
        self.moving_verts = [x for x in self.selected_verts if x not in self.rot_edge]

        self.update()  


    def update_face(self, context):

        scene = context.scene
        region = context.region
        rv3d = context.region_data
        coord = self.mouse_loc

        # get the ray from the viewport and mouse
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        ray_target = ray_origin + view_vector      

        # raycast to face
        # get normal


        depsgraph = context.evaluated_depsgraph_get()
        result, loc, norm_ws, index, obj, matrix = context.scene.ray_cast(depsgraph, ray_origin, view_vector)

        if result:
            return norm_ws

        else:
            return None


        

    def update(self):

        self.rot_axis = self.rot_edge[0].co - self.rot_edge[1].co
        self.fix_rot_dir()

        if self.mode == Modes.Rotate.name:
            self.new_point_coors = self.rotate_verts(self.moving_verts, self.angle)
            self.new_edge_coors = self.rotate_verts(self.edge_verts, self.angle)

        if self.mode == Modes.Project.name:
            self.new_point_coors = self.project_verts(self.moving_verts, self.angle, self.normal)
            self.new_edge_coors = self.project_verts(self.edge_verts, self.angle, self.normal)

        if self.mode == Modes.Slide.name:
            self.slide_dirs = self.get_slide_directions(self.moving_verts, self.normal)
            self.new_point_coors = self.project_verts(self.moving_verts, self.angle, self.normal, self.slide_dirs)
            edge_slide_dirs = self.get_slide_directions(self.edge_verts, self.normal)
            self.new_edge_coors = self.project_verts(self.edge_verts, self.angle, self.normal, edge_slide_dirs)

            self.slide_edges = []

            for index, vert in enumerate(self.moving_verts):

                self.slide_edges.append(vert.co - (self.slide_dirs[index]*5))
                self.slide_edges.append(vert.co + (self.slide_dirs[index]*5))

    # TODO : this should really not be run during update
    def fix_rot_dir(self):
        orig_coor = self.moving_verts[0]
        new_coor = self.rotate_verts([orig_coor], 10)[0]

        v_diff = new_coor - orig_coor.co

        if v_diff.dot(self.normal) < 0:
            # print("reversing")
            self.rot_axis *= -1


    def rotate_verts(self, verts, angle):

        new_point_coors = []
        old_point_coors = [vert.co for vert in verts]

        for old_coor in old_point_coors:
            old_coor = old_coor.copy()
            old_coor -= self.rot_edge[0].co

            new_coor = rotate_point_around_axis(self.rot_axis, old_coor, angle)

            new_coor += self.rot_edge[0].co

            new_point_coors.append(new_coor)

        return new_point_coors

    
    def get_slide_directions(self, verts, normal):

        slide_directions = []

        for vert in verts:
            # get the connected vertices that are not part of the selection
            connected_verts = get_connected_verts(vert, exclude_selected=True)
            connected_faces = get_connected_faces_of_vert(vert, exclude_selected=True)

            # means we have adjacent faces to build a slide direction from
            if connected_faces:
                face_N = connected_faces[0].normal
                face_tan = face_N.cross(normal)
                face_bitan = face_tan.cross(face_N)

                dir_ideal = face_bitan
                dir = dir_ideal
            # geo has no unselected slide edges or faces, so must be an internal part of the selection
            else:
                dir_ideal = normal
                dir = dir_ideal
            
            # means there are slide edges we can use
            if connected_verts:

                # find the edge to slide on that is most in line with the ideal direction
                max_dot = 0
                for vert_end in connected_verts:
                    dir_option = vert_end.co - vert.co
                    dir_option = dir_option.normalized()

                    dir_dot = abs(dir_option.dot(dir_ideal))
                    if dir_dot > max_dot:
                        max_dot = dir_dot
                        dir = dir_option

            # append the slide direction to dirs list
            slide_directions.append(dir)

        # return list
        return slide_directions

    def project_verts(self, verts, angle, normal, directions=[]):

        new_point_coors = []
        old_point_coors = [vert.co for vert in verts]

        for index, vert in enumerate(old_point_coors):

            if directions:
                dir = directions[index]
            else:
                dir = normal

            # get offset from ideal plane that goes through rotation axis (prior to rotation)
            plane_point = self.rot_edge[0].co.copy()

            diff = intersect_line_plane(vert, vert+dir, plane_point, normal)
            if not diff:
                diff = Vector((0,0,0))
            v_offset = vert-diff

            pivot_offset = v_offset.dot(normal)
            pivot_offset *= normal

            plane_normal = rotate_point_around_axis(self.rot_axis, normal, angle)

            if directions:
                plane_point += pivot_offset
                v_offset = Vector((0,0,0))
      
            new_coor = intersect_line_plane(vert, vert+dir, plane_point, plane_normal)
            if not new_coor:
                new_coor = Vector((0,0,0))

            new_coor += v_offset

            new_point_coors.append(new_coor)

        return new_point_coors


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

        prefs = get_prefs()
        c_preview_geo = prefs.color.c_preview_geo
        c_selected_geo = prefs.color.c_selected_geo
        c_selected_geo_sec = prefs.color.c_selected_geo_sec
        c_active_geo = prefs.color.c_active_geo

        s_vertex = prefs.size.s_vertex


        # LINES
        # ROTATION AXIS

        gpu.state.line_width_set(3)

        
        coors = [v.co for v in self.rot_edge]
        world_coors = coors_loc_to_world(coors, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", c_active_geo)
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)


        # --------------------------------------------------
        # --------------------------------------------------

        # POINT
        # where points are
        gpu.state.point_size_set(s_vertex)

        coors = [vert.co for vert in self.moving_verts]
        world_coors = coors_loc_to_world(coors, self.obj)

        shader_dots = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_dots = batch_for_shader(shader_dots, 'POINTS', {"pos": world_coors})

        shader_dots.bind()
        shader_dots.uniform_float("color", c_selected_geo)
        batch_dots.draw(shader_dots)

        gpu.state.point_size_set(1)

        # LINES
        # where edges are

        gpu.state.line_width_set(1)

        coors = [vert.co for vert in self.edge_verts]
        world_coors = coors_loc_to_world(coors, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", c_selected_geo)
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)

        # --------------------------------------------------
        # --------------------------------------------------


        # POINT
        # where points will be moved to
        gpu.state.point_size_set(s_vertex)

        world_coors = coors_loc_to_world(self.new_point_coors, self.obj)

        shader_dots = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_dots = batch_for_shader(shader_dots, 'POINTS', {"pos": world_coors})

        shader_dots.bind()
        shader_dots.uniform_float("color", c_preview_geo)
        batch_dots.draw(shader_dots)

        gpu.state.point_size_set(1)

        # LINES
        # where edges will be moved to

        gpu.state.line_width_set(1)

        world_coors = coors_loc_to_world(self.new_edge_coors, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", c_preview_geo)
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)



        if self.mode == Modes.Slide.name:

            # LINES
            # Slide edges

            gpu.state.line_width_set(1)

            world_coors = coors_loc_to_world(self.slide_edges, self.obj)

            shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

            shader_moving_lines.bind()
            shader_moving_lines.uniform_float("color", c_selected_geo_sec)
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