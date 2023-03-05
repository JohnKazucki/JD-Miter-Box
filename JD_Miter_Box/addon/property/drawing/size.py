import bpy

from bpy.props import IntProperty

from mathutils import Vector


class BM_Size(bpy.types.PropertyGroup):

    s_vertex : IntProperty(
        name = "Vertex Size", description = "How big vertices are drawn in tools. \nBoth selected and preview vertices",
        subtype = 'PIXEL', default = 5, min = 1, soft_max = 30
    )

    
    
size_prefs = [{'s_vertex': "Size of vertices"},
]
    
def draw_size(prefs, layout):

    column = layout.column()
    column.label(text="Drawing Sizes", icon='GREASEPENCIL')

    # size
    box = column.box()

    for item in size_prefs:

        if item == 0:
            row = box.row()
            row.separator()
            continue            

        for prop, text in item.items():
            row = box.row()
            row.prop(prefs.size, prop, text=text)       
