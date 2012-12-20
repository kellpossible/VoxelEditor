"""
addon-voxel-painter.py
This file is part of VoxelPainter

Copyright (C) 2012 - Luke Frisken

VoxelPainter is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

VoxelPainter is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with VoxelPainter. If not, see <http://www.gnu.org/licenses/>.
"""


import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, \
                          FloatVectorProperty, EnumProperty, PointerProperty
from bpy.types import Operator
from mathutils import Vector
from bpy_extras import view3d_utils

#Miscelaneous Functions and classes
def get_active(context):
    return context.scene.objects.active

def set_active(context, obj):
    #if(obj is None):
        #print("active:None")
    context.scene.objects.active = obj

def select_none(context, active=False):
    bpy.ops.object.select_all(action='DESELECT')
    if(not active):
        set_active(context, None)

class SelectionBackup(object):
    def __init__(self, context):
        self.context = context
        self.bases = self.context.selected_bases.copy()
        self.active = get_active(self.context)

    def restore(self):
        select_none(self.context)
        for b in self.bases:
            #check that the object still exists
            if(b in self.context.selectable_bases):
                try:
                    b.select = True
                except:
                    pass
        #print("restoring active")
        set_active(self.context, self.active)
        #print("done restoring active")





#Voxel Editor base classes
class VoxelRayIntersection(object):
    def __init__(self, voxel, loc, nor, dist_squared):
        self.voxel = voxel
        self.dist_squared = dist_squared
        self.loc = loc
        self.nor = nor

    def __str__(self):
        return "VRI Vox:{0}, Dist:{1}".format(
            self.voxel.obj.name,
            self.dist_squared)


class Voxel(object):
    #Operator Poll Functions
    @classmethod
    def poll_voxel_mesh(cls, obj):
        if(obj.type != 'MESH'):
            return False

        if(obj.parent is not None):
            if(VoxelArray.poll_voxelarray_empty_created(obj.parent)):
                return True

        return False

    def __init__(self, obj, context):
        self.obj = obj
        self.context = context

    def copy_props(self, dic):
        """copy voxel properties to an external dictionary dic"""

    @classmethod
    def gen_get_name(cls, vec):
        """Get the string for the object name using position vector"""
        return "Voxel" +  "({0}, {1}, {2})".format(vec[0], vec[1], vec[2])

    def gen_set_name(self, vec):
        """Set voxel object name"""
        self.obj.name =  self.gen_get_name(vec)

    def ray_cast(self, ray_origin, ray_target):
        """Wrapper for ray casting that moves the ray into object space"""

        # get the ray relative to the object
        matrix_inv = self.obj.matrix_world.inverted()
        ray_origin_obj = matrix_inv * ray_origin
        ray_target_obj = matrix_inv * ray_target

        # cast the ray
        hit, normal, face_index = self.obj.ray_cast(ray_origin_obj, ray_target_obj)

        if face_index != -1:
            #hit relative to world
            hit_world = self.obj.matrix_world * hit
            dist_squared = (hit_world - ray_origin).length_squared
            vri = VoxelRayIntersection(self, hit, normal, dist_squared)
            return vri
        else:
            return None

        #keep this here for reference in case I decide to use
        #duplis for the voxels
        #def visible_objects_and_duplis():
            #"""Loop over (object, matrix) pairs (mesh only)"""

            #for obj in context.visible_objects:
                #if obj.type == 'MESH':
                    #yield (obj, obj.matrix_world.copy())

                #if obj.dupli_type != 'NONE':
                    #obj.dupli_list_create(scene)
                    #for dob in obj.dupli_list:
                        #obj_dupli = dob.object
                        #if obj_dupli.type == 'MESH':
                            #yield (obj_dupli, dob.matrix.copy())

    def select(self, active=True):
        """Select the voxel in the blender viewport"""

        self.obj.select = True
        if active:
            set_active(self.context, self.obj)

    def deselect(self, active=False):
        """Deselect the voxel in the blender viewport"""
        self.obj.select = False
        if(get_active(self.context) == self.obj):
            set_active(self.context, None)

    def delete(self):
        select_none(self.context)
        self.select()
        bpy.ops.object.delete()

    def intersect_mesh(self, obj):
        """run a boolean intersect operation between a mesh object and the voxel
        and the resultant mesh is parented to the voxel"""
        select_none(bpy.context)
        self.select()
        print("Active:", self.context.active_object)
        print("Object:", self.context.object)
        bpy.ops.object.duplicate() #duplicate selected object
        #duplicated object is now selected and active
        print("Active:", self.context.active_object)
        print("Object:", self.context.object)
        isect_obj = bpy.context.active_object
        isect_obj.name = self.obj.name + "_isect"
        isect_obj.parent = self.obj
        isect_obj.location = Vector((0.0, 0.0, 0.0))
        #bpy.ops.object.modifier_add(type='BOOLEAN')
        #select_none(bpy.context)
        isect_obj.select = True
        set_active(bpy.context, isect_obj)
        print(isect_obj.type)
        print(isect_obj.name)
        bpy.ops.object.modifier_add()
        #ssurf_mod = isect_obj.modifiers[0]
        #bool_mod = self.obj.modifiers["Boolean"]
        #bool_mod.object = obj
        #bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        #bpy.ops.object.modifier_apply(modifier=ssurf_mod.name)

    def get_local_location(self):
        return self.obj.location

class VoxelArray(object):
    """VoxelArray is a utility class to facilitate accessing the sparse voxel
    array, and saving to blend file.
    An example usage would be:
    va = VoxelArray(context.object)
    va[0, 0, 0] = Voxel(...)
    during assignment Voxel object is converted to blender's python ID property
    format.
    Currently voxels are based on objects in blender. This is convenient, because
    it saves me work (in terms of saving the data to blend file, but it is also
    crap because performance is bad. There is a limit of around 2000 voxels. Because
    I've designed this program to be fairly modular, it shouldn't be too much work
    in the future to replace this with an ID property system, which could possibly
    be cached, but then the problem is displaying the voxels. Drawing in opengl is
    quite a bit of extra work, and doesn't integrate as nicely. Doing stuff in edit
    mode in a single object would be faster, but is more likely to result in user error
    by editing the shape of the voxel array."""

    #Operator Poll Functions
    @classmethod
    def poll_voxelarray_empty(cls, obj):
        return obj is not None and obj.type == 'EMPTY'

    @classmethod
    def poll_voxelarray_empty_created(cls, obj):
        if(cls.poll_voxelarray_empty(obj)):
            if(obj.vox_empty.created):
                return True

        return False

    @classmethod
    def poll_can_boolean(cls, obj):
        """Method to check whether object is valid for a boolean intersection
        between itself and a voxel array"""
        if(obj.type != 'MESH'):
            return False
        if(Voxel.poll_voxel_mesh(obj)):
            return False
        return True

    #yield functions
    @classmethod
    def voxelarrays_scene(cls, context):
        for obj in context.scene.objects:
            if cls.poll_voxelarray_empty(obj):
                yield VoxelArray(obj, context)

    #class property accessors
    @classmethod
    def get_selected(cls, context):
        for va in cls.voxelarrays_scene(context):
            if va.is_selected():
                return va

        return None

    @classmethod
    def clear_selected(cls, context):
        for va in cls.voxelarrays_scene(context):
            va.deselect()


    def __init__(self, obj, context):
        """obj is the object in the context of the caller/creator"""
        self.obj = obj
        self.context = context
        self.props = self.obj.vox_empty

    def is_selected(self):
        return self.obj.vox_empty.selected

    def is_created(self):
        return self.obj.vox_empty.created

    def select(self):
        self.clear_selected(self.context)
        self.obj.vox_empty.selected = True

    def deselect(self):
        self.obj.vox_empty.selected = False

    def global_to_local(self, pos):
        """Convert global position to local position"""
        matrix = self.obj.matrix_world.inverted()
        return matrix * pos

    def local_to_global(self, pos):
        return self.obj.matrix_world * pos

    def new_vox(self, pos):
        #TODO: need to add check for replacing existing voxel
        #pos_local = self.obj.matrix_world * pos
        bpy.ops.mesh.primitive_cube_add()
        vox = Voxel(get_active(self.context), self.context)
        vox.obj.location = pos
        #vox.obj.scale = self.obj.scale
        #svox.obj.rotation_euler = self.obj.rotation_euler
        #print("active", get_active(self.context).name)
        #print("self.obj", self.obj.name)
        #print("vox.obj", vox.obj.name)
        vox.obj.parent = self.obj
        vox.gen_set_name(pos)
        return vox

    def del_vox_pos(self, pos):
        #TODO: delete or rethink this function and if it's needed
        vox = self.get_vox(pos)
        if vox is not None:
            override = {'selected_bases':[vox.obj]}
            bpy.ops.delete(override)
            return True
        else:
            return False

    def voxels(self):
        for c in self.obj.children:
            yield Voxel(c, self.context)


    def get_vox_pos(self, pos):
        key_str = Voxel.gen_get_name(pos)

        for c in self.obj.children:
            if(c.name == key_str):
                return Voxel(c, self.context)

        return None

    def intersect_ray(self, ray_origin, ray_target):
        """return list of voxel ray intersection instances
        [VoxelRayIntersection, ...]"""
        isects = []
        for voxel in self.voxels():
            isect = voxel.ray_cast(ray_origin, ray_target)
            if isect is not None:
                isects.append(isect)

        if len(isects) == 0:
            return None
        else:
            return isects

    def get_intersect_obj(self):
        isect_obj_name = self.obj.vox_empty.intersect_obj
        if(isect_obj_name == ""):
            return None

        isect_obj = self.context.scene.objects[isect_obj_name]
        return isect_obj

    def intersect_mesh(self, obj):
        for voxel in self.voxels():
            voxel.intersect_mesh(obj)

    def __getitem__(self, index):
        """overload the "for in" method"""
        return self.obj.children.__getitem__(index)

    def get_name(self):
        return self.obj.name

    def __str__(self):
        return str(self.obj)

    def __len__(self):
        return len(self.obj.children)


class VoxelEmpty_props(bpy.types.PropertyGroup):
    """This class stores all the overall properties for the voxel array"""
    intersect_obj = StringProperty(name="Intersect Obj",
                                    description="Object to conduct intersection with voxels")

    created = BoolProperty(
        name="VoxelArray Created",
        description="Voxel array has been created",
        default=False)

    selected = BoolProperty(
        name="VoxelArray Selected",
        description="Voxel array has been selected for editing",
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
        return VoxelArray.poll_voxelarray_empty(context.object)

    def draw_header(self, context):
        obj = context.object
        if not obj.vox_empty.created:
            self.layout.operator("object.create_voxels", text="Create")


    def draw(self, context):
        layout = self.layout
        obj = context.object
        va = VoxelArray(obj, context)
        layout.active = va.is_created()

        if(not va.is_selected()):
            layout.operator("object.set_active_voxelarray", text="Set Active")

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")

        if va.is_created():
            row = layout.row()
            nvoxels = len(va)
            row.label(text="Voxels:{0}".format(nvoxels))


        # -- VoxelArray -> Mesh intersection ---
        #set to only display intersect value when the selected
        #object is valid for intersectiong
        #TODO: change this to use a custom property collection for searching
        #and selection of the object.
        row = layout.row()
        isect_label_text = "Intersect With Object:"
        #print(obj.vox_empty.intersect_obj)
        #row.prop(data=obj.vox_empty, property="intersect_obj")
        isect_obj = va.get_intersect_obj()
        if(isect_obj is not None):
            valid_isect_obj = VoxelArray.poll_can_boolean(isect_obj)
        else:
            valid_isect_obj = False

        if(valid_isect_obj):
            row.operator("object.intersect_mesh_voxels", text=isect_label_text)
        else:
            row.label(text=isect_label_text)

        row = layout.row()
        row.prop_search(context.object.vox_empty, "intersect_obj",
                        context.scene, "objects", icon = 'OBJECT_DATA', text = "")
        #row.prop_search(data=obj.vox_empty,
                        #property="intersect_obj",
                        #search_data=context.scene.objects,
                        #search_property="name")


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
        return Voxel.poll_voxel_mesh(obj)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.label(text="Hello world!", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")


class SetActiveVoxelArray(Operator):
    bl_idname = "object.set_active_voxelarray"
    bl_label = "Set the active VoxelArray"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        va = VoxelArray(obj, context)
        va.select()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return VoxelArray.poll_voxelarray_empty(context.active_object)

class IntersectMeshVoxelsOperator(Operator):
    """Operator to intersect between mesh object and the voxel array"""
    bl_idname = "object.intersect_mesh_voxels"
    bl_label = "Intersect Voxels Mesh"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        va = VoxelArray(obj, context)
        isect_obj = va.get_intersect_obj()
        print("Intersecting:" + isect_obj.name)
        va.intersect_mesh(isect_obj)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return VoxelArray.poll_voxelarray_empty_created(context.object)

class CreateVoxelsOperator(Operator):
    """Operator to create and enable voxels on an empty"""

    bl_idname = "object.create_voxels"
    bl_label = "Create Voxels"
    bl_options = {'UNDO'}

    def execute(self, context):
        #sb = SelectionBackup(context)
        obj = context.object
        obj.vox_empty.created = True
        va = VoxelArray(obj, context)
        va.new_vox(Vector((0, 0, 2)))
        va.select()
        del va
        #sb.restore()
        #del sb
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return VoxelArray.poll_voxelarray_empty(context.active_object)


class EditVoxelsOperator(bpy.types.Operator):
    """Modal object selection with a ray cast
    TODO: implement some options in the operator option panel, see if
    it's possible to put buttons in there for utility things while
    editing the voxels.
    One thing I would also like to do is add some opengl visual feedback
    when editing in this operator"""
    bl_idname = "view3d.edit_voxels"
    bl_label = "Voxel Editor"

    def pick_voxel(self, context, event, voxelarray):
        """Run this function on left mouse, execute the ray cast
        TODO: report/go through some problems with selecting in the
        operator_modal_view3d_raycast.py. Most of the problem is
        when trying to click close to the edge of the object.
        The distance values are often mucked up"""
        # get the context arguments
        ray_max=10000.0
        region = context.region
        rv3d = context.region_data
        coord = event.mouse_region_x, event.mouse_region_y

        # get the ray from the viewport and mouse
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * ray_max)
        #TODO: raise some kind of error, or do a check/poll on this operator
        #to ensure that there has been a voxel array created and selected

        isects = voxelarray.intersect_ray(ray_origin, ray_target)

        best_dist_squared = ray_max * ray_max
        best_isect = None

        if isects is None:
            return None

        for isect in isects:
            dist_squared = isect.dist_squared
            if(dist_squared < best_dist_squared):
                best_dist_squared = dist_squared
                best_isect = isect

        return best_isect

    def select_voxel(self, context, event):
        sb = SelectionBackup(context)
        va = VoxelArray.get_selected(context)
        isect = self.pick_voxel(context, event, va)
        if(isect is None):
            sb.restore()
            return None
        vox = isect.voxel
        sb.restore()
        vox.select()
        return vox

    def add_voxel(self, context, event):
        sb = SelectionBackup(context)
        va = VoxelArray.get_selected(context)
        isect = self.pick_voxel(context, event, va)
        if(isect is None):
            sb.restore()
            return None

        vox = isect.voxel
        base_loc = vox.get_local_location()
        new_loc = isect.nor * 2 + base_loc #add new voxel in direction normal

        new_vox = va.new_vox(new_loc)
        sb.restore()
        #TODO: add a toggle for the select after placement
        new_vox.select()
        return new_vox

    def delete_voxel(self, context, event):
        sb = SelectionBackup(context)
        va = VoxelArray.get_selected(context)
        isect = self.pick_voxel(context, event, va)
        #select_none(context)
        if(isect is not None):
            vox = isect.voxel
            vox.delete()
            sb.restore()
            return True
        else:
            sb.restore()
            return False

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.add_voxel(context, event)
            return {'RUNNING_MODAL'}

        if event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
            #TODO: check return value, and cancel operator if
            #nothing was deleted
            retval = self.delete_voxel(context, event)
            if(retval == False):
                #TODO: add an option for this
                return {'CANCELLED'}

        if event.type in {'ESC'}:
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Object.vox_empty = PointerProperty(type=VoxelEmpty_props)



def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Object.vox_empty

if __name__ == "__main__":
    register()
