import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty, FloatProperty

class MoveOperator(Operator):
    """Move operator"""
    bl_idname = "object.move_operator"
    bl_label = "Move Operator"
    bl_options = {'REGISTER', 'UNDO'}

    direction = FloatVectorProperty(
        name="direction",
        default=(1.0, 0.0, 0.0),
        subtype='XYZ',
        description="move direction")

    distance = FloatProperty(
        name="distance",
        default=1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        description="distance")

    def execute(self, context):
        dir_nor = self.direction.normalized()
        context.active_object.location += self.distance * dir_nor
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and ob.mode == 'OBJECT'

def add_object_button(self, context):
    self.layout.operator(
        MoveOperator.bl_idname,
        text=MoveOperator.__doc__,
        icon='PLUGIN')

def register():
    bpy.utils.register_class(MoveOperator)
    bpy.types.VIEW3D_MT_object.remove(add_object_button)
    bpy.types.VIEW3D_MT_object.append(add_object_button)


if __name__ == "__main__":
    register()



