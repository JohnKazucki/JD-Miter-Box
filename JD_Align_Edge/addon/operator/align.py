import bpy
import bmesh

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

    enable_operator : BoolProperty(name="Enabled", default=True)

    mov_vert_index : IntProperty(name="edge corner", default=0, min=0, max=1)
    mov_vert_connected_index : IntProperty(name="corner guide", default=0, min=0)

    @classmethod
    def poll(cls, context):
        if context.active_object.mode == 'EDIT':
            return True

    def execute(self, context):

        if not self.enable_operator:
            return {'FINISHED'}

        obj=context.active_object
        bm=bmesh.from_edit_mesh(obj.data)


        active_verts = []

        for index, v in enumerate(bm.select_history.active.verts):
            active_verts.append(v)

        selected_verts = []

        for v in bm.verts:
            if v.select and v not in active_verts:
                selected_verts.append(v)

        # TODO : doesn't work if active and selected edge have a third connected edge selected between them
        if len(selected_verts) > 2:
            self.report({'ERROR'}, "more than 2 selected edges")
            return {'CANCELLED'}
        if len(selected_verts) < 2:
            self.report({'ERROR'}, "not enough selected edges")
            return {'CANCELLED'}


        # get one of the selected vertices
        moving_vert = selected_verts[self.mov_vert_index]


        # taken from https://blenderartists.org/t/how-to-get-vertex-position-and-connected-vertices/1185279
        # get its connected vertices (filter out the other selected)
        mov_vert_connected=[]
        for l in moving_vert.link_edges:
            other_vert = l.other_vert(moving_vert)
            if other_vert not in selected_verts:
                mov_vert_connected.append(other_vert)

        connected_index = clamp(self.mov_vert_connected_index, 0, len(mov_vert_connected)-1)
        connected_vert = mov_vert_connected[connected_index]


        # get direction vector to first one
        dir_guide = connected_vert.co - moving_vert.co
        
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

        # print(intersections)

        inter_diff = intersections[0]-intersections[1]

        if inter_diff.length < 0.001:
            print("intersection found!")
            print(intersections[0])

            moving_vert.co = intersections[0]

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
