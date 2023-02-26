import bpy
from bpy_extras import view3d_utils



def face_normal_cursor(mouse_loc, context):

    region = context.region
    rv3d = context.region_data
    coord = mouse_loc

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

    # raycast to face
    # get normal


    depsgraph = context.evaluated_depsgraph_get()
    result, loc, norm_ws, index, obj, matrix = context.scene.ray_cast(depsgraph, ray_origin, view_vector)

    if result:
        return norm_ws

    else:
        return None