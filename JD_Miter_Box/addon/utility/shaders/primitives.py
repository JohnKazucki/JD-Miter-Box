import bpy

import gpu
from gpu_extras.batch import batch_for_shader

from mathutils import Vector

from ..math import rotate_to_space


def plane_center(location, axis_x, axis_y, axis_z, size_x, size_y, color):
    # TRIS
    gpu.state.blend_set('ALPHA')

    size_x = size_x/2
    size_y = size_y/2

    positions = (
        Vector((-size_x,  size_y, 0)), Vector((size_x,  size_y, 0)),
        Vector((-size_x, -size_y, 0)), Vector((size_x, -size_y, 0))
        )

    indices = ((0, 1, 2), (2, 1, 3))

    positions = rotate_to_space(positions, axis_x, axis_y, axis_z)

    for vec in positions:
        vec += location

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": positions}, indices=indices)

    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)  

    gpu.state.blend_set('NONE')   


def line(location, axis_x, axis_y, axis_z, length, thickness, color):
        # LINES
        gpu.state.line_width_set(thickness)

        
        world_coors = [Vector((0,0,0)), Vector((0,0,length))]

        world_coors = rotate_to_space(world_coors, axis_x, axis_y, axis_z)

        for vec in world_coors:
            vec += location

        shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": world_coors})

        shader_moving_lines.bind()
        shader_moving_lines.uniform_float("color", color)
        batch_moving_lines.draw(shader_moving_lines)

        gpu.state.line_width_set(1)

def edges(locations, thickness, color):

    gpu.state.line_width_set(thickness)

    shader_moving_lines = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch_moving_lines = batch_for_shader(shader_moving_lines, 'LINES', {"pos": locations})

    shader_moving_lines.bind()
    shader_moving_lines.uniform_float("color", color)
    batch_moving_lines.draw(shader_moving_lines)

    gpu.state.line_width_set(1)


def points(locations, size, color):

    gpu.state.point_size_set(size)

    shader_dots = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch_dots = batch_for_shader(shader_dots, 'POINTS', {"pos": locations})

    shader_dots.bind()
    shader_dots.uniform_float("color", color)
    batch_dots.draw(shader_dots)

    gpu.state.point_size_set(1)
