
from mathutils import Vector, Quaternion, Matrix

import math

def clamp(number, minVal, maxVal):
    return max(minVal, min(number, maxVal))


def sign(n):
    if n<0: return -1
    elif n>0: return 1
    else: return None

def round_to_integer(number, stepsize=5):
    number /= stepsize
    number = round(number)
    number *= stepsize

    return number


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


def rotate_point_around_axis(axis, point, angledeg):

    if axis.length != 1.0:
        axis = axis.normalized()

    rot_quat = Quaternion(axis, math.radians(angledeg))

    new_point = rot_quat @ point

    return new_point


# based on https://stackoverflow.com/questions/19621069/3d-rotation-matrix-rotate-to-another-reference-system
def rotate_to_space(vectors, axis_x, axis_y, axis_z):
    rotMat = Matrix(( (axis_x[0], axis_y[0], axis_z[0]),
                    (axis_x[1], axis_y[1], axis_z[1]),
                    (axis_x[2], axis_y[2], axis_z[2]),   ))

    new_vectors = []
    for vec in vectors:
        vec = rotMat @ vec
        new_vectors.append(vec)

    return new_vectors