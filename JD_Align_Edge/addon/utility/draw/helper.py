import bpy, blf, gpu
from bgl import *
from gpu_extras.batch import batch_for_shader


# --- PRIMITIVE DRAWING

def object_coor3d_to_2d(context, object_location):
    from bpy_extras.view3d_utils import location_3d_to_region_2d


    region = context.region
    rv3d = bpy.context.space_data.region_3d
    location = location_3d_to_region_2d(region, rv3d, object_location, default=None)

    return location


# adapted from ST3 course part 5-8
def make_vertices(x, y, width, height):

    top_left =  (x        , y + height)
    bot_left =  (x        , y)
    top_right = (x + width, y + height)
    bot_right = (x + width, y)

    verts = verts = [top_left, bot_left, top_right, bot_right]

    return verts


# from ST3 course part 5-8
def draw_quad(vertices=[], color=(1,1,1,1)):
    '''Vertices = Top Left, Bottom Left, Top Right, Bottom Right'''

    indices = [(0, 1, 2), (1, 2, 3)]
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    glEnable(GL_BLEND)
    batch.draw(shader)
    glDisable(GL_BLEND)

    del shader
    del batch


# -------------------------------------------


# --- FORMATTING

def format_and_append(textlist, inputlist):
    for entry in inputlist:
        formattype = entry[1]
        text = entry[0]
        if formattype == 'NONE':
            pass
        if formattype == 'XYZ_H':
            text = "X: {X}  Y: {Y}  Z: {Z}".format(X=round(text[0], 3), 
                                                    Y=round(text[1], 3), 
                                                    Z=round(text[2], 3))

        textlist.append(text)
