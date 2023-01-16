import bpy


addon_name = __name__.partition('.')[0]


def get_prefs():
    return bpy.context.preferences.addons[addon_name].preferences