import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, \
                          FloatVectorProperty, EnumProperty, PointerProperty
from bpy.types import Operator

class CreateVoxelsOperator(Operator):
    """Operator to create and enable voxels on an empty"""

    bl_idname = "object.create_voxels"
    bl_label = "Create Voxels"
    bl_options = {'UNDO'}

    def execute(self, context):
        pass

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.type == 'EMPTY'


class VoxelEmpty_props(bpy.types.PropertyGroup):
    """This class stores all the overall properties for the voxel array"""
    created = BoolProperty(
        name="Voxels Created",
        description="Voxel array has been created",
        default=False)


class VoxelEmpty_obj_prop(bpy.types.Panel):
    """This class is the panel that goes with the empty representing, and storing
    all the data for the voxel array"""
    bl_label = "Voxel Array"
    bl_idname = "OBJECT_PT_voxelempty"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if(context.object is not None):
            if(context.object.type == 'EMPTY'):
                return True

        return False

    def draw_header(self, context):
        obj = context.object


    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.label(text="Hello world!", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")


class VoxelMesh_obj_prop(bpy.types.Panel):
    bl_label = "Voxel Properties"
    bl_idname = "OBJECT_PT_voxelmesh"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        #TODO check that parent EMPTY has voxel array initialised
        obj = context.object
        if(obj is not None):
            if(obj.type == 'MESH'):
                if(obj.parent is not None):
                    pobj = obj.parent
                    if(obj.parent_type == 'OBJECT'):
                        if(pobj.type == 'EMPTY'):
                            return True

        return False

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.label(text="Hello world!", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")


def register():
    bpy.utils.register_class(VoxelMesh_obj_prop)
    bpy.utils.register_class(VoxelEmpty_obj_prop)


def unregister():
    bpy.utils.unregister_class(VoxelMesh_obj_prop)
    bpy.utils.unregister_class(VoxelEmpty_obj_prop)


if __name__ == "__main__":
    register()
