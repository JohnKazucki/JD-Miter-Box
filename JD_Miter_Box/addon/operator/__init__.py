import bpy

from .align import MB_OT_ALIGN
# from .align_face import MB_OT_ALIGN_FACE
from .align_f._op import MB_OT_ALIGN_FACE


classes = (
    MB_OT_ALIGN,
    MB_OT_ALIGN_FACE,
)


def register_operators():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister_operators():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
