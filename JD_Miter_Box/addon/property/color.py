import bpy

from bpy.props import FloatVectorProperty

from mathutils import Vector


class BM_Color(bpy.types.PropertyGroup):

    c_preview_geo : FloatVectorProperty(
        name = "Preview Geometry", description = "color for preview of geometry",
        size = 4, min = 1, max = 1,
        subtype='COLOR', default=(.9, .9, .9, 1)
    )

    c_selected_geo : FloatVectorProperty(
        name = "Selected Geometry", description = "color for highlighting the selected geometry",
        size = 4, min = 1, max = 1,
        subtype='COLOR', default=(1, 1, 0, 1)
    )

    c_selected_geo_sec : FloatVectorProperty(
        name = "Selected Geometry Secondary", description = "secondary color for highlighting the selected geometry",
        size = 4, min = 1, max = 1,
        subtype='COLOR', default=(.7, .7, 0, 1)
    )

    c_active_geo : FloatVectorProperty(
        name = "Active Geometry", description = "color for highlighting the active geometry",
        size = 4, min = 1, max = 1,
        subtype='COLOR', default=(0, .9, .4, 1.0)
    )

    c_error_geo : FloatVectorProperty(
        name = "Error Geometry", description = "color for errors on geometry",
        size = 4, min = 1, max = 1,
        subtype='COLOR', default=(.8, .1, .3, 1.0)
    )

    c_error_geo_sec : FloatVectorProperty(
        name = "Error Geometry Secondary", description = "secondary color for errors on geometry",
        size = 4, min = 1, max = 1,
        subtype='COLOR', default=(.6, 0, .2, .7)
    )

    
color_prefs = {'c_preview_geo': "Preview Geometry", 'c_selected_geo': "Selected Geometry", 'c_selected_geo_sec': "Selected Geometry Secondary",
                'c_active_geo': "Active Geometry", 'c_error_geo': "Error Geometry", 'c_error_geo_sec': "Error Geometry Secondary"
}
    


def draw_color(prefs, layout):
    
    layout.label(text="Drawing Colors", icon='RESTRICT_COLOR_ON')

    # Tools
    box = layout.box()

    for prop, text in color_prefs.items():

        row = box.row()
        row.prop(prefs.color, prop, text=text)


    # row = box.row()
    # row.prop(prefs.color, 'c_selected_geo', text='Selected Geo')
