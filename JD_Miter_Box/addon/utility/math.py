
from mathutils import Vector

import math

def clamp(number, minVal, maxVal):
    return max(minVal, min(number, maxVal))


def sign(n):
    if n<0: return -1
    elif n>0: return 1
    else: return None



# based on https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
def distance_perpendicular_point_to_edge_2d(point, edge_p0, edge_p1):
    """
    returns closest perpendicular distance between point and edge
    """

    two_times_area = abs( (edge_p1[0]-edge_p0[0])*(edge_p0[1]-point[1]) - (edge_p0[0]-point[0])*(edge_p1[1]-edge_p0[1]) )
    base = math.sqrt( math.pow((edge_p1[0]-edge_p0[0]), 2) + math.pow((edge_p1[1]-edge_p0[1]), 2) )

    dist_perp_edge = two_times_area/base

    return dist_perp_edge


def distance_point_to_edge_2d(point, p0, p1):

    midpoint = Vector(((p0[0]+p1[0])/2,(p0[1]+p1[1])/2))
    dist_to_line = midpoint-point
    dist_to_line = dist_to_line.length

    return dist_to_line
