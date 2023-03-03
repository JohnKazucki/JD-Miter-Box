import bpy

from ...utility.math import rotate_point_around_axis



def rotate_verts(verts, angle, rot_axis, rot_edge):

    new_point_coors = []
    old_point_coors = [vert.co for vert in verts]

    for old_coor in old_point_coors:
        old_coor = old_coor.copy()
        old_coor -= rot_edge[0].co

        new_coor = rotate_point_around_axis(rot_axis, old_coor, angle)

        new_coor += rot_edge[0].co

        new_point_coors.append(new_coor)

    return new_point_coors

def rotate_normals(normals, angle, rot_axis):
    
    new_normals = []

    for normal in normals:

        old_normal = normal.copy()
        new_normal = rotate_point_around_axis(rot_axis, old_normal, angle)

        new_normals.append(new_normal)

    return new_normals


def fix_rot_dir(verts, rot_axis, rot_edge, normal):
    verts = [v for v in verts if v not in rot_edge]
    for vert in verts:
        dir = vert.co - rot_edge[0].co
        dir.normalize()
        rot_axis = rot_axis.normalized()

        if abs(dir.dot(rot_axis)) < 1:
            orig_vert = vert
            break

    new_coor = rotate_verts([orig_vert], 10, rot_axis, rot_edge)[0]

    v_diff = new_coor - orig_vert.co
    if v_diff.dot(normal) < 0:        
        rot_axis *= -1

    return rot_axis
