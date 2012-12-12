import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, \
                          FloatVectorProperty, EnumProperty, PointerProperty
from bpy.types import Operator
from mathutils import Vector

def get_active(context):
    return context.scene.objects.active

def set_active(context, obj):
    context.scene.objects.active = obj

class SelectionBackup(object):
    def __init__(self, context):
        self.context = context
        self.bases = self.context.selected_bases.copy()
        self.active = get_active(self.context)

    def restore(self):
        for b in self.context.selected_bases:
            b.object.select = False
            set_active(self.context, None)

        for b in self.bases:
            b.object.select = True
            set_active(self.context, self.active)



def vec_to_key(vec):
    """key is a string in format of (int, int, int)"""
    return "({0}, {1}, {2})".format(vec[0], vec[1], vec[2])

class Voxel(object):
    def __init__(self, obj):
        self.obj = obj

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
    def __init__(self, obj, context):
        """obj is the object in the context of the caller/creator"""
        self.obj = obj
        self.context = context
        self.props = self.obj.vox_empty

    def new_vox(self, pos):
        #need to add check for replacing existing voxel
        sb = SelectionBackup(self.context)
        bpy.ops.mesh.primitive_cube_add(location = pos)
        vox = Voxel(get_active(self.context))
        print("active", get_active(self.context).name)
        print("self.obj", self.obj.name)
        print("vox.obj", vox.obj.name)
        vox.obj.parent = self.obj
        vox.obj.name = vec_to_key(pos)
        sb.restore()

        return vox

    def del_vox(self, pos):
        vox = self.get_vox(pos)
        if vox is not None:
            override = {'selected_bases':[vox.obj]}
            bpy.ops.delete(override)
            return True
        else:
            return False

    def get_vox(self, pos):
        key_str = "Voxel" + vec_to_key(pos)

        for c in self.obj.children:
            if(c.name == key_str):
                return Voxel(c)

        return None


class CreateVoxelsOperator(Operator):
    """Operator to create and enable voxels on an empty"""

    bl_idname = "object.create_voxels"
    bl_label = "Create Voxels"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        obj.vox_empty.created = True
        va = VoxelArray(obj, context)
        va.new_vox(Vector((1, 2, 3)))

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
