import bpy

from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d, region_2d_to_location_3d



def mouse_2d_to_3d(context, mouse_location):

    region = context.region
    rv3d = bpy.context.space_data.region_3d

    view_loc = region_2d_to_origin_3d(region, rv3d, mouse_location)
    view_dir = region_2d_to_vector_3d(region, rv3d, mouse_location)

    pos_3d = region_2d_to_location_3d(region, rv3d, mouse_location, view_loc+view_dir)

    return pos_3d
