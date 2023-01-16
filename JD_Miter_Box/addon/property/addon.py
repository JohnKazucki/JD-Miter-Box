import bpy

from bpy.props import PointerProperty

from ..utility.addon import addon_name, get_prefs


from .color import BM_Color, draw_color

class BM_Props(bpy.types.AddonPreferences):
    bl_idname = addon_name

    color : PointerProperty(type=BM_Color)

    def draw(self, context):

        prefs = get_prefs()

        layout = self.layout

        # General settings
        box = layout.box()

        # Drawing settings
        box = layout.box()
        draw_color(prefs, box)
