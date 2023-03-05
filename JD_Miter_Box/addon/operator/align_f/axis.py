import bpy

from bpy_extras.view3d_utils import location_3d_to_region_2d

from ...utility.mesh import coors_loc_to_world
from ...utility.math import distance_point_to_edge_2d

def update_axis(self, context):
    region = context.region
    rv3d = bpy.context.space_data.region_3d
    
    closest_edge = None
    min_distance = None

    for index, edge in enumerate(self.selected_edges):
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

    rot_edge = [v for v in closest_edge.verts]

    rot_axis = rot_edge[0].co - rot_edge[1].co
    rot_pivot = rot_edge[0].co + (rot_edge[0].co - rot_edge[1].co)/2

    return rot_edge, rot_axis, rot_pivot