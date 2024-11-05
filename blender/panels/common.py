from typing import Dict, Type

import bpy
from bpy.app.handlers import persistent
from bpy.props import (BoolProperty, FloatProperty, IntProperty,
                       PointerProperty, StringProperty, EnumProperty)
from bpy.types import Operator, PropertyGroup, UILayout, UIList

# Globals
XFBIN_LISTS = list()
XFBIN_SEARCH_LISTS = list()
XFBIN_CLIPBOARD: Dict[Type, PropertyGroup] = dict()
XFBIN_POINTERS: PropertyGroup = None
XFBIN_OPERATORS = (('new_item', 'New', 'ADD'), ('delete_item', 'Remove', 'REMOVE'),
                   ('move_item', 'Up', 'TRIA_UP'), ('move_item', 'Down', 'TRIA_DOWN'),
                   ('copy_item', 'Copy', 'COPYDOWN'), ('paste_item', 'Paste', 'PASTEDOWN'),)


@persistent
def clear_clipboard(dummy):
    # Reset the clipboard whenever a new file is loaded
    global XFBIN_CLIPBOARD
    XFBIN_CLIPBOARD = dict()


def matrix_prop(ui_layout: UILayout, data, prop_name: str, length: int, text=''):
    """Draw props from a VectorProperty in a 4x4 layout (or less, if the items are less than 4)."""

    ui_layout.label(text=text)
    box = ui_layout.box().grid_flow(row_major=True, columns=4, even_rows=True, even_columns=True)
    for i in range(length//4):
        for j in range(i*4, (i+1)*4):
            box.prop(data, prop_name, index=j, text='')

    for i in range((length // 4) * 4, (length // 4) * 4 + (length % 4)):
        box.prop(data, prop_name, index=i, text='')


def matrix_prop_group(ui_layout: UILayout, data, prop_name: str, length: int, text=''):
    """Same as above, but from a CollectionProperty containing a PropertyGroup with a \"value\" property."""

    collection = data.path_resolve(prop_name)
    ui_layout.label(text=text)
    box = ui_layout.box().grid_flow(row_major=True, columns=4, even_rows=True, even_columns=True)
    for i in range(length//4):
        for j in range(i*4, (i+1)*4):
            box.prop(collection[j], 'value', text='')

    for i in range((length // 4) * 4, (length // 4) * 4 + (length % 4)):
        box.prop(collection[i], 'value', text='')

def matrix_prop_search(ui_layout: UILayout, data, prop_name: str, search_data: 'AnyType', search_property: str, length: int, text=''):
    
    collection = data.path_resolve(prop_name)
    ui_layout.label(text=text)
    box = ui_layout.box().grid_flow(row_major=True, columns=4, even_rows=True, even_columns=True)
    for i in range(length//4):
        for j in range(i*4, (i+1)*4):
            box.prop_search(collection[j], 'value', search_data, search_property, text='')

    for i in range((length // 4) * 4, (length // 4) * 4 + (length % 4)):
        box.prop_search(collection[i], 'value', search_data, search_property, text='')

class StringPropertyGroup(PropertyGroup):
    value: StringProperty()


class IntPropertyGroup(PropertyGroup):
    value: IntProperty()


class FloatPropertyGroup(PropertyGroup):
    value: FloatProperty()


class BoolPropertyGroup(PropertyGroup):
    value: BoolProperty()


class EmptyPropertyGroup(PropertyGroup):
    def update_empty(self, context):
        if self.empty:
            self.value = self.empty.name

    def update_value(self, context):
        self.update_name()

    def poll_empty(self, object):
        return object.type == 'EMPTY' and object.parent and object.parent.type == 'ARMATURE'

    empty: PointerProperty(
        type=bpy.types.Object,
        name='Empty Object',
        update=update_empty,
        poll=poll_empty,
    )

    value: StringProperty(
        update=update_value,
    )

    def update_name(self):
        self.name = self.value


class ObjectPropertyGroup(PropertyGroup):
    def update_object(self, context):
        if self.object:
            self.value = self.object.name

    def update_value(self, context):
        self.update_name()

    def poll_object(self, object):
        return object.parent and object.parent.type == 'ARMATURE'

    object: PointerProperty(
        type=bpy.types.Object,
        name='Object',
        update=update_object,
        poll=poll_object,
    )

    value: StringProperty(
        update=update_value,
    )

    def update_name(self):
        self.name = self.value


def deepcopy_items(from_obj, to_obj):
    """Performs a deepcopy on from a dictionary (or bpy_struct) to another."""

    for k, v in from_obj.items():
        if hasattr(v, 'items') and callable(v.items):
            if to_obj.get(k) is None:
                to_obj[k] = v
            else:
                deepcopy_items(v, to_obj[k])
        else:
            to_obj[k] = v


class XFBIN_PANEL_OT_CopyPropertyGroup(Operator):
    """Copy the contents of this panel"""

    bl_idname = 'xfbin_panel.copy_group'
    bl_label = 'Copy a PropertyGroup'

    prop_path: StringProperty()
    prop_name: StringProperty()

    def execute(self, context):
        #global XFBIN_POINTERS

        if not globals().get('XFBIN_POINTERS'):
            # Create a new empty just to store the pointers
            XFBIN_POINTERS = bpy.data.objects.new('xfbin_dummy', None).xfbin_pointers

        prop = context.object.path_resolve(self.prop_path)
        key = type(prop).__name__

        # Deepcopy the property group to the XFBIN_POINTERS property group, and store a reference to the value in the clipboard
        deepcopy_items(prop, XFBIN_POINTERS.path_resolve(key))
        XFBIN_CLIPBOARD[key] = XFBIN_POINTERS[key]

        self.report({'INFO'}, f'Copied {self.prop_name} from object: "{context.object.name}"')
        return{'FINISHED'}


class XFBIN_PANEL_OT_PastePropertyGroup(Operator):
    """Paste the properties in the clipboard to this panel"""

    bl_idname = 'xfbin_panel.paste_group'
    bl_label = 'Overwrite existing properties?'

    prop_path: StringProperty()
    prop_name: StringProperty()

    def execute(self, context):
        prop = context.object.path_resolve(self.prop_path)
        item = XFBIN_CLIPBOARD.get(type(prop).__name__)

        if item is None:
            self.report({'ERROR_INVALID_CONTEXT'}, 'No item of this type has been copied before')
            return{'CANCELLED'}

        deepcopy_items(item, context.object.path_resolve(self.prop_path))

        self.report({'INFO'}, f'Pasted {self.prop_name} to object: "{context.object.name}"')
        return{'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


def draw_copy_paste_ops(layout: UILayout, path: str, name: str):
    """Draws Copy and Paste operators and sets their prop path and name"""
    row = layout.row()
    for op, txt, icn in (('copy_group', 'Copy', 'COPYDOWN'), ('paste_group', 'Paste', 'PASTEDOWN')):
        opr = row.operator(f'xfbin_panel.{op}', text=txt, icon=icn)
        opr.prop_path = path
        opr.prop_name = name


# UIList code adapted from here https://sinestesia.co/blog/tutorials/using-uilists-in-blender/
class XFBIN_LIST_UL_List(UIList):
    """UIList."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text='')

class XFBIN_LIST_UL_SearchList(UIList):
    """UIList."""

    search_property = bpy.data
    search_data = "objects"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text=item.name)
            layout.prop_search(item, 'name', bpy.data, self.search_data, text='')

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text='')


# TODO: Change this to be more dynamic, instead of relying on a fixed value
# Create a separate list for each unique list to be shown in a single object
# This is needed to avoid the lists being scrolled/expanded at the same time
for i in range(10):
    panel_idname = f'XFBIN_LIST_UL_List_{i}'
    panel = type(panel_idname,
                 (XFBIN_LIST_UL_List,),
                 {'bl_idname': panel_idname, },
                 )
    
    XFBIN_LISTS.append(panel)

for i in range(10):
    panel_idname = f'XFBIN_LIST_UL_SearchList_{i}'
    panel = type(panel_idname,
                 (XFBIN_LIST_UL_SearchList,),
                 {'bl_idname': panel_idname, },
                 )
    
    XFBIN_SEARCH_LISTS.append(panel)


class XFBIN_LIST_OT_NewItem(Operator):
    """Add a new item to the list"""

    bl_idname = 'xfbin_list.new_item'
    bl_label = 'Add a new item'

    prop_path: StringProperty()
    collection: StringProperty()
    index: StringProperty()

    def execute(self, context):
        prop = context.object.path_resolve(self.prop_path)
        collection = prop.path_resolve(self.collection)

        collection.add().update_name()
        prop[self.index] = len(collection) - 1

        return{'FINISHED'}


class XFBIN_LIST_OT_DeleteItem(Operator):
    """Delete the selected item from the list"""

    bl_idname = 'xfbin_list.delete_item'
    bl_label = 'Deletes an item'

    prop_path: StringProperty()
    collection: StringProperty()
    index: StringProperty()

    def execute(self, context):
        prop = context.object.path_resolve(self.prop_path)
        collection = prop.path_resolve(self.collection)
        index = prop.path_resolve(self.index)

        if not collection:
            self.report({'ERROR_INVALID_CONTEXT'}, 'Cannot delete an item when the list is empty')
            return{'CANCELLED'}

        name = collection[index].name
        collection.remove(index)
        prop[self.index] = min(max(0, index - 1), len(collection) - 1)

        self.report({'INFO'}, f'Deleted "{name}" from the list')
        return{'FINISHED'}


class XFBIN_LIST_OT_MoveItem(Operator):
    """Move an item in the list"""

    bl_idname = 'xfbin_list.move_item'
    bl_label = 'Move an item in the list'

    direction: bpy.props.EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', ''),
        )
    )

    prop_path: StringProperty()
    collection: StringProperty()
    index: StringProperty()

    def execute(self, context):
        prop = context.object.path_resolve(self.prop_path)
        collection = prop.path_resolve(self.collection)
        index = prop.path_resolve(self.index)

        if not collection:
            self.report({'ERROR_INVALID_CONTEXT'}, 'Cannot move an item when the list is empty')
            return{'CANCELLED'}

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        collection.move(neighbor, index)

        # Move index of an item render queue while clamping it.
        list_length = len(collection) - 1
        new_index = index + (-1 if self.direction == 'UP' else 1)

        prop[self.index] = max(0, min(new_index, list_length))

        return{'FINISHED'}


class XFBIN_LIST_OT_CopyItem(Operator):
    """Copy an item from the list"""

    bl_idname = 'xfbin_list.copy_item'
    bl_label = 'Copy an item'

    prop_path: StringProperty()
    collection: StringProperty()
    index: StringProperty()

    def execute(self, context):
        #global XFBIN_POINTERS

        if not globals().get('XFBIN_POINTERS'):
            # Create a new empty just to store the pointers
            XFBIN_POINTERS = bpy.data.objects.new('xfbin_dummy', None).xfbin_pointers

        prop = context.object.path_resolve(self.prop_path)
        collection = prop.path_resolve(self.collection)
        index = prop.path_resolve(self.index)

        if not collection:
            self.report({'ERROR_INVALID_CONTEXT'}, 'Cannot copy from an empty list')
            return{'CANCELLED'}

        key = type(collection[index]).__name__

        # Deepcopy the property group to the XFBIN_POINTERS property group, and store a reference to the value in the clipboard
        deepcopy_items(collection[index], XFBIN_POINTERS.path_resolve(key))
        XFBIN_CLIPBOARD[key] = XFBIN_POINTERS[key]

        self.report({'INFO'}, f'Copied "{collection[index].name}" from the list')
        return{'FINISHED'}


class XFBIN_LIST_OT_PasteItem(Operator):
    """Paste an item from the clipboard to the list"""

    bl_idname = 'xfbin_list.paste_item'
    bl_label = 'Paste an item'

    prop_path: StringProperty()
    collection: StringProperty()
    index: StringProperty()

    def execute(self, context):
        prop = context.object.path_resolve(self.prop_path)
        collection = prop.path_resolve(self.collection)

        # Create a new item in the list
        dummy = collection.add()
        item = XFBIN_CLIPBOARD.get(type(dummy).__name__)

        if item is None:
            # Remove the dummy
            collection.remove(len(collection) - 1)
            self.report({'ERROR_INVALID_CONTEXT'}, 'No item of this type has been copied before')
            return{'CANCELLED'}

        # Set the index to the new item and copy its properties to the dummy item
        prop[self.index] = len(collection) - 1
        deepcopy_items(item, dummy)

        self.report({'INFO'}, f'Pasted "{dummy.name}" to the list')
        return{'FINISHED'}


def draw_xfbin_list(layout: UILayout, list_index: int, data, path: str, collection_name: str, index_name: str, enable_text: bool = True):
    """Draws a list using the layout and populates it with the given collection and index."""

    row = layout.split(factor=0.80)
    row.template_list(f'XFBIN_LIST_UL_List_{list_index}', 'xfbin_list', data, collection_name, data, index_name)

    col = row.column()
    for op, txt, icn in XFBIN_OPERATORS:
        if enable_text:
            opr = col.operator(f'xfbin_list.{op}', text=txt, icon=icn)
        else:
            opr = col.operator(f'xfbin_list.{op}',text="", icon=icn)
        opr.prop_path = path
        opr.collection = collection_name
        opr.index = index_name

        if op == 'move_item':
            opr.direction = txt.upper()

    #layout.label(text='Selected Item:')


def draw_xfbin_list_search(layout: UILayout, list_index: int, data, path: str, collection_name: str, index_name: str):
    """Draws a list using the layout and populates it with the given collection and index."""

    row = layout.split(factor=0.80)
    row.template_list(f'XFBIN_LIST_UL_SearchList_{list_index}', 'xfbin_list', data, collection_name, data, index_name)

    col = row.column()
    for op, txt, icn in XFBIN_OPERATORS:
        opr = col.operator(f'xfbin_list.{op}', text=txt, icon=icn)
        opr.prop_path = path
        opr.collection = collection_name
        opr.index = index_name

        if op == 'move_item':
            opr.direction = txt.upper()

    layout.label(text='Selected Item:')


common_classes = (
    StringPropertyGroup,
    IntPropertyGroup,
    FloatPropertyGroup,
    BoolPropertyGroup,
    EmptyPropertyGroup,
    ObjectPropertyGroup,
    XFBIN_PANEL_OT_CopyPropertyGroup,
    XFBIN_PANEL_OT_PastePropertyGroup,
    *XFBIN_LISTS,
    *XFBIN_SEARCH_LISTS,
    XFBIN_LIST_OT_NewItem,
    XFBIN_LIST_OT_DeleteItem,
    XFBIN_LIST_OT_MoveItem,
    XFBIN_LIST_OT_CopyItem,
    XFBIN_LIST_OT_PasteItem,
)
