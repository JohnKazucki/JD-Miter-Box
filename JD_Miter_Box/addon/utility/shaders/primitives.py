import bpy

import gpu
from gpu_extras.batch import batch_for_shader

from mathutils import Vector

from ..math import rotate_to_space


def plane_center(location, axis_x, axis_y, axis_z, size, color):
    # TRIS
    gpu.state.blend_set('ALPHA')

    size = size/2

    positions = (
        Vector((-size,  size, 0)), Vector((size,  size, 0)),
        Vector((-size, -size, 0)), Vector((size, -size, 0))
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