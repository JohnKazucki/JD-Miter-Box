
import bpy
import bmesh

from bpy.types import Operator

import gpu
from gpu_extras.batch import batch_for_shader

from mathutils import Vector

from enum import Enum
import traceback

from .rotate import rotate_verts, fix_rot_dir
from .project import project_verts
from .slide import get_slide_directions

from .axis import update_axis


from ...utility.addon import get_prefs

from ...utility.bmesh import get_selected_edge_verts, get_selected_verts, get_selected_edges
from ...utility.mesh import coors_loc_to_world, coor_loc_to_world


from ...utility.interaction import face_normal_cursor

from ...utility.shaders.primitives import edges, plane_center, line, points
from ...utility.draw.core import JDraw_Text_Box_Multi



class Modes(Enum):
    Rotate = 0
    Project = 1
    Slide = 2

Align_Face_kb_general = {
                        'mode' :
                            {'key':'V', 'desc':"Mode", 'var':'mode'},
}


class Modify(Enum):
    Mod_None = 0
    Axis = 1
    Align_Face = 2
    Angle = 3
    Projection_Dir = 4

Align_Face_kb_modify = {
                        'angle' :
                            {'key':'G', 'desc':"Angle", 'var':'str_angle', 'state':3},
                        'rot_axis' :
                            {'key':'R', 'desc':"Rotation Axis", 'state':1},
                        'align_to_face' :
                            {'key':'F', 'desc':"Align to Face", 'state':2},
                        'orient_dir' :
                            {'key':'B', 'desc':"Orientation", 'state':4},
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

        self.update()

        return {"RUNNING_MODAL"}

    def setup(self, event):

        self.selected_edges = get_selected_edges(self.bm)
        self.selected_verts = get_selected_verts(self.bm)
        self.selected_edge_verts = get_selected_edge_verts(self.bm)

        self.new_point_coors = [v.co for v in self.selected_verts]
        self.new_edge_verts_coors = [v.co for v in self.selected_edge_verts]

        self.rot_edge = [v for v in self.selected_edges[0].verts]
        if self.bm.select_mode == {'EDGE'}:
            self.rot_edge = [v for v in self.bm.select_history.active.verts]
        
        self.rot_axis = self.rot_edge[0].co - self.rot_edge[1].co
        self.rot_axis.normalize()
        self.rot_pivot = self.rot_edge[0].co + (self.rot_edge[0].co - self.rot_edge[1].co)/2

        self.active_face = self.bm.faces.active
        self.sel_faces = [x for x in self.bm.faces if x.select]
        if self.active_face not in self.sel_faces:
            self.active_face = self.sel_faces[0]
        self.normal = self.active_face.normal 

        self.input_angle = 0.0
        self.angle = 0.0

        self.slide_dirs = []

        self.setup_colors()
        self.setup_input()
        self.setup_UI()


    def setup_colors(self):
        prefs = get_prefs()

        self.c_preview_geo = prefs.color.c_preview_geo

        self.c_selected_geo = prefs.color.c_selected_geo
        self.c_selected_geo_sec = prefs.color.c_selected_geo_sec

        self.c_active_geo = prefs.color.c_active_geo

        self.s_vertex = prefs.size.s_vertex
        

    def setup_input(self):
        # input management variables
        default_mode = Modes.Slide
        self.mode = default_mode.name
        self.mode_index = default_mode.value

        self.modify = Modify.Mod_None.value

        self.mouse_loc = Vector((0,0))

        self.snapping = False

    
    def setup_UI(self):
        self.str_angle = "%.2f" %0


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

        # Confirm
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            self.remove_shaders(context)

            for index, vert in enumerate(self.selected_verts):
                vert.co = self.new_point_coors[index]
            
            bmesh.update_edit_mesh(self.objdata)

            return {'FINISHED'}

        # Adjust
        if event.type == 'MOUSEMOVE':
            self.mouse_loc = Vector((event.mouse_region_x, event.mouse_region_y))
            self.dist = event.mouse_x - event.mouse_prev_x

        # Snapping
        if event.type in ('LEFT_CTRL', 'RIGHT_CTRL'):
            if event.value == 'PRESS':
                self.snapping = True
            elif event.value == 'RELEASE':
                self.snapping = False

        # Cycle modes
        if event.type == Align_Face_kb_general['mode']['key'] and event.value == 'PRESS':
            self.mode_index += 1
            self.mode_index %= len(Modes)
            self.mode = Modes(self.mode_index).name


        # Projection/Slide mode - orientation normal 
        if self.mode == Modes.Project.name or self.mode == Modes.Slide.name:
            if event.type == Align_Face_kb_modify['orient_dir']['key'] and event.value == 'PRESS':
                self.dist = 0
                if self.modify != Modify.Projection_Dir.value:
                    self.modify = Modify.Projection_Dir.value
                else:
                    self.modify = Modify.Mod_None.value

        # Any mode - angle
        if event.type == Align_Face_kb_modify['angle']['key'] and event.value == 'PRESS':
            self.dist = 0
            if self.modify != Modify.Angle.value:
                self.modify = Modify.Angle.value
            else:
                self.modify = Modify.Mod_None.value

        # Any mode - rotation axis
        if event.type == Align_Face_kb_modify['rot_axis']['key'] and event.value == 'PRESS':
            self.dist = 0
            if self.modify != Modify.Axis.value:
                self.modify = Modify.Axis.value
            else:
                self.modify = Modify.Mod_None.value



        self.update_input(context)
        self.update()

        context.area.tag_redraw()

        return {"RUNNING_MODAL"}


    def update(self):
        if self.mode == Modes.Rotate.name:
            self.new_point_coors = rotate_verts(self.selected_verts, self.angle, self.rot_axis, self.rot_edge)
            self.new_edge_verts_coors = rotate_verts(self.selected_edge_verts, self.angle, self.rot_axis, self.rot_edge)
        if self.mode == Modes.Project.name:
            self.new_point_coors = project_verts(self.selected_verts, self.angle, self.rot_pivot, self.rot_axis, self.normal)
            self.new_edge_verts_coors = project_verts(self.selected_edge_verts, self.angle, self.rot_pivot, self.rot_axis, self.normal)
        if self.mode == Modes.Slide.name:
            self.slide_dirs = get_slide_directions(self.selected_verts, self.normal)
            self.new_point_coors = project_verts(self.selected_verts, self.angle, self.rot_pivot, self.rot_axis, self.normal, self.slide_dirs)
            
            self.edge_slide_dirs = get_slide_directions(self.selected_edge_verts, self.normal)
            self.new_edge_verts_coors = project_verts(self.selected_edge_verts, self.angle, self.rot_pivot, self.rot_axis, self.normal, self.edge_slide_dirs)        


    def update_input(self, context):
        if self.modify == Modify.Projection_Dir.value:
            face_normal = face_normal_cursor(self.mouse_loc, context)
            if face_normal:
                self.normal = face_normal

        if self.modify == Modify.Angle.value:
            self.input_angle += self.dist/5
            self.angle = self.input_angle

            # if snapping enabled
            if self.snapping:
                self.angle /= 5
                self.angle = round(self.angle)
                self.angle *= 5

            self.str_angle = "%.2f" %self.angle

        if self.modify == Modify.Axis.value:
            self.rot_edge, self.rot_axis, self.rot_pivot = update_axis(self, context)
            self.rot_axis = fix_rot_dir(self.selected_verts, self.rot_axis, self.rot_edge, self.normal)


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
        

        # projection/slide orientation direction
        if self.mode == Modes.Project.name or self.mode == Modes.Slide.name:
            axis_z = self.normal
            axis_x = self.normal.cross(Vector((0,0,1)))
            axis_y = self.normal.cross(axis_x)

            axis_x.normalize()
            axis_y.normalize()
            axis_z.normalize()

            center = self.rot_edge[0].co + (self.rot_edge[1].co-self.rot_edge[0].co)/2
            center = coor_loc_to_world(center, self.obj)

            coors = [v.co for v in self.selected_edge_verts]

            coors_x = [coor[0] for coor in coors]
            min_x = min(coors_x)
            max_x = max(coors_x)
            coors_y = [coor[1] for coor in coors]
            min_y = min(coors_y)
            max_y = max(coors_y)

            size_x = abs(max_x-min_x)
            size_y = abs(max_y-min_y)

            size = max([size_x, size_y])/2

            plane_center(center, axis_x, axis_y, axis_z, size, size, self.c_selected_geo_sec)
            line(center, axis_x, axis_y, axis_z, size, 2, self.c_selected_geo_sec)
        # --------------------------------------------------

        # slide direction edges
        if self.mode == Modes.Slide.name:

            self.slide_edges = []

            for index, position in enumerate(self.new_point_coors):

                self.slide_edges.append(position - (self.slide_dirs[index]*0.1))
                self.slide_edges.append(position + (self.slide_dirs[index]*0.1))
            
            # slide edges

            coors = self.slide_edges
            world_coors = coors_loc_to_world(coors, self.obj)
            edges(world_coors, 1, self.c_preview_geo)
        # --------------------------------------------------


        # rotation axis

        gpu.state.line_width_set(3)

        coors = [v.co for v in self.rot_edge]
        world_coors = coors_loc_to_world(coors, self.obj)

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", self.c_active_geo)
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)

        # --------------------------------------------------

        # new point positions
        coors = self.new_point_coors
        world_coors = coors_loc_to_world(coors, self.obj)
        points(world_coors, self.s_vertex, self.c_preview_geo)

        # new edge positions

        coors = self.new_edge_verts_coors
        world_coors = coors_loc_to_world(coors, self.obj)
        edges(world_coors, 1, self.c_preview_geo)




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
        kb_value = ": {var}"

        # general
        for _, keys in Align_Face_kb_general.items():
            status = ""
            if keys.get('var'):
                status = kb_value.format(var=getattr(self, keys['var']))
            texts.append(kb_string.format(key=keys['key'], desc=keys['desc'])+status)

        texts.append("")

        # modify keys
        for _, keys in Align_Face_kb_modify.items():
            value = ""
            if keys.get('var'):
                value = str(getattr(self, keys['var']))
            state = ""
            if keys.get('state') == self.modify:
                state = " - Modifying"
            
            status = kb_value.format(var=value + state)
            texts.append(kb_string.format(key=keys['key'], desc=keys['desc'])+status)

        texts.append("")

        texts.append("Hold Ctrl for snapping")

        textbox = JDraw_Text_Box_Multi(x=self.mouse_loc[0]+10, y=self.mouse_loc[1]-10, strings=texts, size=15)
        textbox.draw()

    # ------------------------------
