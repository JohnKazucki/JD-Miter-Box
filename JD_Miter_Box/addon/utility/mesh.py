import bpy

def vert_pair_other_vert(verts, vert):
    """
    returns other element in list from the one that is given
    """

    verts = verts.copy()
    verts.remove(vert)

    return verts[0]

def coors_loc_to_world(coors, obj):
    world_coors = []

    for coor in coors:
        world_coors.append(coor_loc_to_world(coor, obj))

    return world_coors

def coor_loc_to_world(coor, obj):
    world_coor = obj.matrix_world @ coor
    return world_coor

def coor_world_to_loc(coor, obj):
    inverse_world_matrix = obj.matrix_world.inverted_safe()
    world_coor = inverse_world_matrix @ coor
    return world_coor
