import bpy

import gpu
from gpu_extras.batch import batch_for_shader

from mathutils import Vector

from ..math import rotate_to_space, rotate_point_around_axis


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

def line_p2p(start, end, thickness, color):
    
    # LINES
    gpu.state.line_width_set(thickness)

    coors = [start, end]

    shader_line = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch_line = batch_for_shader(shader_line, 'LINES', {"pos": coors})

    shader_line.bind()
    shader_line.uniform_float("color", color)
    batch_line.draw(shader_line)

    


def line_2d(start, end, thickness, color):
        # LINE
        gpu.state.line_width_set(thickness)

        world_coors = [start, end]

        shader_line = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch_line = batch_for_shader(shader_line, 'LINES', {"pos": world_coors})

        shader_line.bind()
        shader_line.uniform_float("color", color)
        batch_line.draw(shader_line)

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


def arc(center, axis_x, axis_y, axis_z, radius, angle, thickness, color):
        # LINE
        gpu.state.line_width_set(thickness)

        world_coors = []

        # every 5 degrees, we need angle/5 points
        angle_pts = abs(int(angle/5))
        if angle_pts != 0:
            angle_div = angle/angle_pts
        else:
            angle_div = 0

        for i in range(int(angle_pts)+1):
            point = rotate_point_around_axis(Vector((1,0,0)), Vector((0, radius, 0)), angle_div*i)
            world_coors.append(point)

        world_coors = rotate_to_space(world_coors, axis_x, axis_y, axis_z)

        for vec in world_coors:
            vec += center

        shader_arc = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch_arc = batch_for_shader(shader_arc, 'LINE_STRIP', {"pos": world_coors})

        shader_arc.bind()
        shader_arc.uniform_float("color", color)
        batch_arc.draw(shader_arc)

        gpu.state.line_width_set(1)    

        # POINTS
        if world_coors:
            point_coors = [world_coors[0], world_coors[-1]]
            points(point_coors, thickness*3, color)
