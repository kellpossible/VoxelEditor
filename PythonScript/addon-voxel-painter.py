import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, \
                          FloatVectorProperty, EnumProperty, PointerProperty
from bpy.types import Operator

class Voxel(object):
    def copy_props(self, dic):
        """copy voxel properties to an external dictionary dic"""


class VoxelArray(object):
    """VoxelArray is a utility class to facilitate accessing the sparse voxel
    array, and saving to blend file.
    An example usage would be:
    va = VoxelArray(context.object)
    va[0, 0, 0] = Voxel(...)
    during assignment Voxel object is converted to blender's python ID property
    format."""
    def __init__(self, obj):
        """obj is the object in the context of the caller/creator"""
        self.obj = obj
        if("VoxelArray" not in obj):
            obj["VoxelArray"] = {}

        self.prop_dic = obj["VoxelArray"]

    def key_to_str(self, key):
        """key is a string in format of (int, int, int)"""
        return "({0}, {1}, {2})".format(key[0], key[1], key[2])

    def get_vox_dic(self, key, create=False):
        """if create is set to True, then
        if no error will be thrown on the event that
        the key does not exist no prop_dic, but rather
        we create a new voxel in the prop_dic"""

        key_str = self.key_to_str(key)
        print(key_str)

        if(key_str not in self.prop_dic and create):
            self.prop_dic[key_str] = {}

        return self.prop_dic[key_str]

    def __setitem__(self, key, vox):
        """key is a string in format of (int, int, int)
        value is a Voxel instance"""
        vox_dic = self.get_vox_dic(key, create=True)
        vox.copy_props(vox_dic)

    def __getitem__(self, key):
        """key is a string in format of (int, int, int)
        returns an instance of Voxel, remember to delete
        when finished"""
        vox_dic = self.get_vox_dic(key)

    def __delitem__(self, key):
        """key is a string in format of (int, int, int)
        returns an instance of Voxel, remember to delete
        when finished"""
        vox_dic = self.get_vox_dic(key)

    def __contains__(self, key):
        """key is a string in format of (int, int, int)
        returns an instance of Voxel, remember to delete
        when finished"""
        vox_dic = self.get_vox_dic(key)

    def get(self, key):
        """key is a string in format of (int, int, int)
        returns an instance of Voxel, remember to delete
        when finished"""
        vox_dic = self.get_vox_dic(key)


class CreateVoxelsOperator(Operator):
    """Operator to create and enable voxels on an empty"""

    bl_idname = "object.create_voxels"
    bl_label = "Create Voxels"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        obj.vox_empty.created = True
        va = VoxelArray(obj)
        del va


        return {'FINISHED'}

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
        if not obj.vox_empty.created:
            self.layout.operator("object.create_voxels", text="Create")


    def draw(self, context):
        layout = self.layout
        obj = context.object
        layout.active = obj.vox_empty.created

        row = layout.row()
        row.label(text="Hello world!", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")


class VoxelMesh_obj_prop(bpy.types.Panel):
    """This class is the panel that goes with objects which represent the individual
    voxels in the voxel array. """
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
    bpy.utils.register_module(__name__)
    bpy.types.Object.vox_empty = PointerProperty(type=VoxelEmpty_props)



def unregister():
    bpy.utils.unregister_class(VoxelMesh_obj_prop)
    bpy.utils.unregister_class(VoxelEmpty_obj_prop)
    del bpy.types.Object.vox


if __name__ == "__main__":
    register()
