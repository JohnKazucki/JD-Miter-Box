import bpy

from .align import MB_PT_ALIGN, VIEW3D_MB_MT_edit_mesh_MiterBox
from .align import mb_menu_func

classes = (
    MB_PT_ALIGN, VIEW3D_MB_MT_edit_mesh_MiterBox
)


def register_menus():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(mb_menu_func)


def unregister_menus():

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(mb_menu_func)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
