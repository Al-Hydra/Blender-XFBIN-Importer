from typing import Type

import bpy
from bpy.props import PointerProperty
from bpy.types import PropertyGroup

from .exporter import ExportXfbin, menu_func_export
from .importer import (ImportXFBIN, DropXFBIN, XFBIN_FH_import, menu_func_import, XFBIN_UL_IMPORT_LIST, XFBIN_OT_IMPORT_ADD_FILE,
                        XFBIN_OT_IMPORT_REMOVE_FILE, XFBIN_OT_IMPORT_CLEAR_FILES,
                        XFBIN_OT_IMPORT_MOVE_FILE, XFBIN_IMPORT_FILES)
from .panels.anm_chunks_panel import (AnmChunksListPropertyGroup,
                                      anm_chunks_classes)
from .panels.clump_panel import (ClumpPropertyGroup, clump_classes,
                                 clump_property_groups)
from .panels.materials_panel import (XfbinMaterialPropertyGroup,
                                     XfbinMatClipboardPropertyGroup,
                                     XfbinSceneManagerPropertyGroup,
                                        material_classes,
                                        material_property_groups)
from .panels.common import EmptyPropertyGroup, clear_clipboard, common_classes
from .panels.nud_mesh_panel import (NudMeshPropertyGroup, nud_mesh_classes,
                                    nud_mesh_property_groups)
from .panels.nud_panel import (NudPropertyGroup, nud_classes,
                               nud_property_groups)
from .panels.texture_chunks_panel import (TextureChunksListPropertyGroup,
                                          texture_chunks_classes,
                                          texture_chunks_property_groups)
from .panels.dynamics_panel import (DynamicsPropertyGroup,
                                    XfbinDynamicsClipboardPropertyGroup,
                                    XfbinDynamicsBoneBuffer,
                                    dynamics_chunks_classes,
                                    dynamics_chunks_property_groups
                                    
                                    )
from .panels.modelhit_panel import (ModelHitPropertyGroup,
                                    ModelHitMesh,
                                    model_hit_property_groups,
                                    model_hit_classes)

#from .common.shaders import CustomNodeTest

XfbinPointersGroup: Type

classes = (
    #CustomNodeTest,
    *common_classes,
    XFBIN_FH_import,
    XFBIN_UL_IMPORT_LIST,
    XFBIN_OT_IMPORT_ADD_FILE,
    XFBIN_OT_IMPORT_REMOVE_FILE,
    XFBIN_OT_IMPORT_CLEAR_FILES,
    XFBIN_OT_IMPORT_MOVE_FILE,
    XFBIN_IMPORT_FILES,
    ImportXFBIN,
    DropXFBIN,
    ExportXfbin,
    *texture_chunks_classes,
    *material_classes,
    *clump_classes,
    *nud_classes,
    *nud_mesh_classes,
    *dynamics_chunks_classes,
    *model_hit_classes,
    *anm_chunks_classes,
)


def register():
    global XfbinPointersGroup
    

    for c in classes:
        bpy.utils.register_class(c)

    # add to the export / import menu
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    

    # Add Xfbin and Nud properties data
    bpy.types.Object.xfbin_clump_data = PointerProperty(type=ClumpPropertyGroup)  # Applies to armatures only
    bpy.types.Object.xfbin_nud_data = PointerProperty(type=NudPropertyGroup)  # Applies to empties only
    bpy.types.Object.xfbin_mesh_data = PointerProperty(type=NudMeshPropertyGroup)  # Applies to meshes only
    bpy.types.Object.xfbin_dynamics_data = PointerProperty(type=DynamicsPropertyGroup)
    bpy.types.Object.xfbin_modelhit_data = PointerProperty(type=ModelHitPropertyGroup)
    bpy.types.Object.xfbin_modelhit_mesh_data = PointerProperty(type=ModelHitMesh)

    bpy.types.Scene.xfbin_texture_chunks_data = PointerProperty(type=TextureChunksListPropertyGroup)
    bpy.types.Scene.xfbin_scene = PointerProperty(type=XfbinSceneManagerPropertyGroup)
    bpy.types.Material.xfbin_material_data = PointerProperty(type=XfbinMaterialPropertyGroup)

    # Applies to empties only
    
    bpy.types.Object.xfbin_anm_chunks_data = PointerProperty(type=AnmChunksListPropertyGroup)
    bpy.types.Scene.xfbin_import_files = PointerProperty(type=XFBIN_IMPORT_FILES)

    # Define a new class with exec() because we can't set type hints with type()
    pointers_def = 'class XfbinPointersGroup(PropertyGroup): '
    for pg_type in (EmptyPropertyGroup, XFBIN_IMPORT_FILES, *clump_property_groups, *nud_property_groups, *nud_mesh_property_groups,
    *texture_chunks_property_groups, *dynamics_chunks_property_groups, *model_hit_property_groups, *material_property_groups):
        pointers_def += f'{pg_type.__name__}: PointerProperty(type={pg_type.__name__}); '

    # Make a copy of the locals dict and add all of the necessary classes to it
    locals_dict = locals().copy()
    for c in (PropertyGroup, PointerProperty, *classes):
        locals_dict.update({f'{c.__name__}': c})

    exec(pointers_def, locals_dict)

    # Get the class we just defined
    XfbinPointersGroup = locals_dict['XfbinPointersGroup']

    # Register and set it as a property in Object
    bpy.utils.register_class(XfbinPointersGroup)
    bpy.types.Object.xfbin_pointers = PointerProperty(type=XfbinPointersGroup)

    bpy.app.handlers.load_post.append(clear_clipboard)

    #create pointer properties to be used as a clipboard
    bpy.types.Scene.xfbin_clipboard = PointerProperty(type=XfbinPointersGroup)
    bpy.types.Scene.xfbin_material_clipboard = PointerProperty(type=XfbinMatClipboardPropertyGroup)
    bpy.types.Scene.xfbin_dynamics_clipboard = PointerProperty(type=XfbinDynamicsClipboardPropertyGroup)
    bpy.types.Scene.xfbin_dynamics_bone_buffer = PointerProperty(type=XfbinDynamicsBoneBuffer)


def unregister():
    global XfbinPointersGroup

    del bpy.types.Object.xfbin_clump_data
    del bpy.types.Object.xfbin_nud_data
    del bpy.types.Object.xfbin_mesh_data
    del bpy.types.Material.xfbin_material_data
    del bpy.types.Scene.xfbin_texture_chunks_data
    del bpy.types.Object.xfbin_anm_chunks_data
    del bpy.types.Object.xfbin_dynamics_data
    del bpy.types.Object.xfbin_modelhit_data
    del bpy.types.Object.xfbin_modelhit_mesh_data
    del bpy.types.Object.xfbin_pointers
    del bpy.types.Scene.xfbin_clipboard
    del bpy.types.Scene.xfbin_material_clipboard
    del bpy.types.Scene.xfbin_dynamics_clipboard
    del bpy.types.Scene.xfbin_dynamics_bone_buffer
    del bpy.types.Scene.xfbin_import_files

    bpy.utils.unregister_class(XfbinPointersGroup)

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    # remove from the export / import menu
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    bpy.app.handlers.load_post.remove(clear_clipboard)
