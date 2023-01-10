import bpy

from bpy.types import Panel, Menu

from .classes import MB_PT_VIEW_3D



class MB_PT_ALIGN(MB_PT_VIEW_3D, Panel):
    bl_label = "MiterBox"

    def draw(self, context):
        scene = context.scene
        
        layout = self.layout

        row = layout.row()
        row.operator("object.mb_align", icon='SNAP_EDGE')
        row = layout.row()
        row.operator("object.mb_align_face", icon='AXIS_SIDE')



# Edit Mode RMB menu, based on LoopTools
class VIEW3D_MB_MT_edit_mesh_MiterBox(Menu):
    bl_label = "MiterBox"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.mb_align", icon='SNAP_EDGE')

        layout.operator("object.mb_align_face", icon='AXIS_SIDE')



# draw function for integration in menus, based on LoopTools
def mb_menu_func(self, context):
    self.layout.menu("VIEW3D_MB_MT_edit_mesh_MiterBox")
    self.layout.separator()
