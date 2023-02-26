import bpy

from bpy.props import FloatVectorProperty

from mathutils import Vector


class BM_Color(bpy.types.PropertyGroup):

    c_preview_geo : FloatVectorProperty(
        name = "Preview Geometry", description = "color for preview of geometry",
        size = 4, min = 0.0, max = 1.0,
        subtype='COLOR', default=(1.0, 1.0, 1.0, 0.9)
    )

    c_selected_geo : FloatVectorProperty(
        name = "Selected Geometry", description = "color for highlighting the selected geometry",
        size = 4, min = 0.0, max = 1.0,
        subtype='COLOR', default=(1, 1, 0.1, 0.9)
    )

    c_selected_geo_sec : FloatVectorProperty(
        name = "Selected Geometry Secondary", description = "secondary color for highlighting the selected geometry",
        size = 4, min = 0.0, max = 1.0,
        subtype='COLOR', default=(.7, .6, 0.25, 0.4)
    )

    c_active_geo : FloatVectorProperty(
        name = "Active Geometry", description = "color for highlighting the active geometry",
        size = 4, min = 0.0, max = 1.0,
        subtype='COLOR', default=(0.0, .9, .4, 0.9)
    )

    c_error_geo : FloatVectorProperty(
        name = "Error Geometry", description = "color for errors on geometry",
        size = 4, min = 0.0, max = 1.0,
        subtype='COLOR', default=(.8, .1, .3, 0.9)
    )

    c_error_geo_sec : FloatVectorProperty(
        name = "Error Geometry Secondary", description = "secondary color for errors on geometry",
        size = 4, min = 0.0, max = 1.0,
        subtype='COLOR', default=(.6, 0.0, .2, .7)
    )

    
    
color_prefs = [{'c_preview_geo': "Preview Geometry"}, 
                0,
                {'c_selected_geo': "Selected Geometry", 'c_selected_geo_sec': "Selected Geometry Secondary"},
                0,
                {'c_active_geo': "Active Geometry", 
                'c_error_geo': "Error Geometry", 'c_error_geo_sec': "Error Geometry Secondary"}
]
    
def draw_color(prefs, layout):

    column = layout.column()
    column.label(text="Drawing Colors", icon='RESTRICT_COLOR_ON')

    # colors
    box = column.box()

    for item in color_prefs:

        if item == 0:
            row = box.row()
            row.separator()
            continue            

        for prop, text in item.items():
            row = box.row()
            row.prop(prefs.color, prop, text=text)
