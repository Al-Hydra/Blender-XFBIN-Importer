import importlib.util

blender_loader = importlib.util.find_spec('bpy')

bl_info = {
    "name": "XFBIN File Importer/Exporter",
    "author": "SutandoTsukai181, HydraBladeZ, Dei, TheLeonX",
    "version": (1, 6, 1),
    "blender": (4, 2, 0),
    "location": "File > Import-Export",
    "description": "Import/Export XFBIN files found in CC2's Storm Engine games.",
    "warning": "",
    "doc_url": "https://github.com/SutandoTsukai181/cc2_xfbin_blender/wiki",
    "wiki_url": "https://github.com/SutandoTsukai181/cc2_xfbin_blender/wiki",
    "tracker_url": "https://github.com/SutandoTsukai181/cc2_xfbin_blender/issues",
    "category": "Import-Export",
}

if blender_loader:
    from .blender.addon import *
