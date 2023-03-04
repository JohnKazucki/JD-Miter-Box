import bpy

from mathutils import Vector
from mathutils.geometry import intersect_line_plane

from ...utility.math import rotate_point_around_axis



def project_verts(verts, angle, pivot, rot_axis, normal, directions=[], align_dir=None):

    new_point_coors = []
    # old_point_coors = [vert.co for vert in verts]

    for vert in verts:

        vert_co = vert.co

        # in slide mode, each vert has its own projection direction
        if directions:
            dir = directions[vert.index]
            if abs(dir.dot(normal)) > .98:
                if align_dir:
                    dir = align_dir
                else:
                    dir = normal

        # in projection mode
        else:
            dir = normal

        diff = intersect_line_plane(vert_co, vert_co+dir, pivot, normal)
        if not diff:
            diff = Vector((0,0,0))
        v_offset = vert_co-diff

        pivot_offset = v_offset.dot(normal)
        pivot_offset *= normal

        plane_normal = rotate_point_around_axis(rot_axis, normal, angle)

        # in slide mode, offset the pivot of the plane which we intersect with to find the new point
        # this puts it in the correct location for a given vert
        if directions:
            pivot += pivot_offset
            v_offset = Vector((0,0,0))
    
        new_coor = intersect_line_plane(vert_co, vert_co+dir, pivot, plane_normal)
        if not new_coor:
            new_coor = Vector((0,0,0))

        new_coor += v_offset

        new_point_coors.append(new_coor)

    return new_point_coors
