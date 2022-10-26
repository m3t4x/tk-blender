# ----------------------------------------------------------------------------
# Copyright (c) 2022, Brendan Fitzgerald.
#
# Your use of this software as distributed in this GitHub repository, is
# governed by the Apache License 2.0
#
# Your use of the Shotgun Pipeline Toolkit is governed by the applicable
# license agreement between you and Autodesk / Shotgun.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
bl_info = {
    "name": "Shotgrid Extended Plugin",
    "description": "Additional Functionality for Shotgrid Toolkit Engine for Blender",
    "author": "Brendan Fitzgerald",
    "license": "GPL",
    "deps": "",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "Shotgrid",
    "warning": "",
    "wiki_url": "https://github.com/c1112/tk-blender/releases",
    "tracker_url": "https://github.com/c1112/tk-blender/issues",
    "link": "https://github.com/c1112/tk-blender",
    "support": "COMMUNITY",
    "category": "User Interface",
}

from bpy.types import Panel, Scene, Collection, UIList, PropertyGroup, Operator, OUTLINER_MT_collection
from bpy.props import PointerProperty, EnumProperty, CollectionProperty, IntProperty
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import persistent
from bpy import data
from bpy import ops
import sgtk
import bpy

################################################################################
#   ENGINE CLASSES FOR PUBLISH PANEL
################################################################################

class SGTKPROPERTIES_ListItem(PropertyGroup):
    """Group of properties representing an item in the list."""
    collectionTypes = [
                        ("ABC", "ABC", ""),
                        ]
    collectionProfiles = [
                        ("Geometry", "Geometry", ""),
                        ("Camera", "Camera", ""),
                        ]

    collection: PointerProperty(
           name="Name",
           description="Collection to be exported",
           type=Collection,
           )

    type: EnumProperty(
           name="File Type",
           items=collectionTypes,
           description="File Type",
           default="ABC")

    profile: EnumProperty(
           name="Profile",
           items=collectionProfiles,
           description="Profile to use for Export",
           default="Geometry")

class SGTKPROPERTIES_UL_List(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        type_icon = {
                    'ABC' : 'COLLECTION_COLOR_01',
        }
        profile_icon = {
                    'Geometry' : 'MESH_DATA',
                    'Camera' : 'CAMERA_DATA',
        }

        collection_item = item.collection
        if collection_item is not None:
            collection_name = collection_item.name
        else:
            collection_name = ' '

        #To support all 3 different kinds of layouts
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
                layout.label(text=collection_name, icon = 'OUTLINER_COLLECTION')
                layout.label(text=item.type, icon=type_icon[item.type])
                layout.label(text=item.profile, icon=profile_icon[item.profile])

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

class SGTKPROPERTIES_OT_NewItem(Operator):
    """Add a new item to the list."""

    bl_idname = "sgtk_aux_exports.new_item"
    bl_label = "Add a new item"

    def execute(self, context):
        latest_index = len(context.scene.sgtk_aux_exports)
        listItem = context.scene.sgtk_aux_exports.add()
        context.scene.sgtk_aux_exports_index = latest_index

        return{'FINISHED'}

class SGTKPROPERTIES_OT_DeleteItem(Operator):
    """Delete the selected item from the list."""

    bl_idname = "sgtk_aux_exports.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.sgtk_aux_exports

    def execute(self, context):
        sgtk_aux_exports = context.scene.sgtk_aux_exports
        index = context.scene.sgtk_aux_exports_index

        sgtk_aux_exports.remove(index)
        context.scene.sgtk_aux_exports_index = min(max(0, index - 1), len(sgtk_aux_exports) - 1)

        return{'FINISHED'}



################################################################################
#   UI CLASSES FOR PUBLISH PANEL
################################################################################

class SGTKPropertiesPanel:
    ''' Base Class for the SGTK Panel '''
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

class SGTKPROPERTIES_PT_main(SGTKPropertiesPanel, Panel):
    bl_label = "Shotgrid Publish Properties"
    def draw(self, context):
        pass

class SGTKPROPERTIES_PT_aux_exports(SGTKPropertiesPanel, Panel):
    bl_label = "Additional Publish Items"
    bl_parent_id = "SGTKPROPERTIES_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.template_list("SGTKPROPERTIES_UL_List", "The_List", scene,
                          "sgtk_aux_exports", scene, "sgtk_aux_exports_index")

        row = layout.row()
        row.operator('sgtk_aux_exports.new_item', text='New')
        row.operator('sgtk_aux_exports.delete_item', text='Remove')

        if scene.sgtk_aux_exports_index >= 0 and scene.sgtk_aux_exports:
            item = scene.sgtk_aux_exports[scene.sgtk_aux_exports_index]

            row = layout.row()
            row.prop_search(item, "collection", data, "collections")
            row.prop(item, "type")
            row.prop(item, "profile")


class SGTKPROPERTIES_PT_publishing(SGTKPropertiesPanel, Panel):
    bl_label = "Tag Publish Items"
    bl_parent_id = "SGTKPROPERTIES_PT_main"

    def draw(self, context):
       layout = self.layout
       layout.use_property_split = True
       layout.use_property_decorate = False
       row = layout.row()
       row.prop_search(context.scene, "sgtk_link_collection", data, "collections", text="Tag Link Collection")
       row = layout.row()
       row.prop_search(context.scene, "sgtk_link_collection", data, "collections", text="Tag Append Collection")
       row = layout.row()
       row.prop_search(context.scene, "sgtk_abc_collection", data, "collections", text="Alembic Publish Collection")



################################################################################
# Register plugin and run functions for publish panel
################################################################################

classes = (
    SGTKPROPERTIES_ListItem,
    SGTKPROPERTIES_UL_List,
    SGTKPROPERTIES_OT_NewItem,
    SGTKPROPERTIES_OT_DeleteItem,
    SGTKPROPERTIES_PT_main,
    SGTKPROPERTIES_PT_publishing,
    SGTKPROPERTIES_PT_aux_exports,
)

def pp_draw_menu(self, context):
    layout = self.layout
    layout.operator('Scene.sgtk_link_collection')

def pp_register():
    for cls in classes:
        register_class(cls)
    OUTLINER_MT_collection.append(pp_draw_menu)
    #add all the scene varibles that store the information inside the blendfile
    Scene.sgtk_link_collection = PointerProperty(type=Collection)
    Scene.sgtk_append_collection = PointerProperty(type=Collection)
    Scene.sgtk_abc_collection = PointerProperty(type=Collection)
    Scene.sgtk_aux_exports = CollectionProperty(type=SGTKPROPERTIES_ListItem)
    Scene.sgtk_aux_exports_index = IntProperty(name = "Index for sgtk_aux_exports", default = 0)

def pp_unregister():
    for cls in classes:
        unregister_class(cls)

################################################################################
################################################################################
################################################################################
################################################################################

@persistent
def sg_render_path(kwargs):
    """ function generates the autopath from the shotgun template
    """
    #Calling Shotgun
    sgengine = sgtk.platform.current_engine()
    #check to make it's set to an entity
    if sgengine.context.entity is None:
        return

    context = sgengine.context.entity.get('type')
    tk = sgengine.tank

    #Calling Current application
    current_app = "blender"
    current_file = bpy.data.filepath
    current_renderlayer = bpy.context.scene.name

    #Get the right template based on the context
    if context == 'Shot':
        shotworkPath = tk.templates['%s_shot_work' % current_app]
        shotrenderPath = tk.templates['%s_shot_render' % current_app]
    if context == 'Asset':
        shotworkPath = tk.templates['%s_asset_work' % current_app]
        shotrenderPath = tk.templates['%s_asset_render' % current_app]

    fields = shotworkPath.get_fields(current_file)
    custom_fields = { "scene": current_renderlayer,
                     "SEQ": "####",
                     }
    fields.update(custom_fields)

    sgpath = shotrenderPath.apply_fields(fields)

    #add the file path to the application
    bpy.context.scene.render.filepath = sgpath

    return


#list of handlers that the path generation function is attached to
bhandle = bpy.app.handlers
rp_handlers = [ bhandle.save_post,
                bhandle.load_post,
                bhandle.render_pre,
                bhandle.depsgraph_update_post,
                ]

def rp_register():
    for handle in rp_handlers:
        handle.append(sg_render_path)

def rp_unregister():
    for handle in rp_handlers:
        handle.remove(sg_render_path)


################################################################################
################################################################################
#   Run all register functions for plugin
################################################################################
################################################################################
def register():
    #publish panel register
    pp_register()
    #render path register
    rp_register()

def unregister():
    #publish panel unregister
    pp_unregister()
    #render path
    rp_register()

if __name__ == "__main__":
    register()
