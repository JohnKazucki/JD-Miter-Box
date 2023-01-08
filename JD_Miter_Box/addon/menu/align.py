import bpy

from bpy.types import Panel

from .classes import MB_PT_VIEW_3D

class MB_PT_ALIGN(MB_PT_VIEW_3D, Panel):
    bl_label = "MiterBox"

    def draw(self, context):
        scene = context.scene
        
        layout = self.layout

        row = layout.row()
        row.operator("object.mb_align", icon='SNAP_EDGE')
