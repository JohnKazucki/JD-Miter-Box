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
    best_fit = 1
    for vert in verts:

        # project vertex coordinate onto orientation plane
        # without projecting, vertices in front of or behind the rotation axis (along the normal) would still be valid
        # but these vertices are not good indicators for the rotation axis
        # (projected) vertices in line with the rotation axis are not good indicators of rotation direction
        offset_dir = vert.co - rot_edge[0].co
        offset_v = offset_dir.dot(normal) * normal
        orig_coor = vert.co - offset_v

        dir = orig_coor - rot_edge[0].co

        dir.normalize()
        rot_axis = rot_axis.normalized()

        # TODO : will still fail for when the face being rotated is very thin in the direction perpendicular to the normal and rotation edge
        # could be improved by considering both verts and edge centers

        if abs(dir.dot(rot_axis)) < best_fit:
            best_fit = abs(dir.dot(rot_axis))
            orig_vert_co = orig_coor

    new_coor = rotate_point_around_axis(rot_axis, orig_vert_co, 20)

    v_diff = new_coor - orig_coor
    if v_diff.dot(normal) < 0:        
        rot_axis *= -1

    return rot_axis
