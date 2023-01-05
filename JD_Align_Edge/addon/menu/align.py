import bpy

from bpy.types import Panel

from .classes import AE_PT_VIEW_3D

class AE_PT_ALIGN(AE_PT_VIEW_3D, Panel):
    bl_label = "JD Align"

    def draw(self, context):
        scene = context.scene
        
        layout = self.layout

        row = layout.row()
        row.operator("object.ae_align", icon='SNAP_EDGE')
