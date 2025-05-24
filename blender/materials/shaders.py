import bpy, os
from mathutils import Vector
from bpy.types import NodeSocket, Node, NodeTree, NodeCustomGroup
path = os.path.dirname(os.path.realpath(__file__))

from ..panels.materials_panel import XfbinMaterialPropertyGroup, XfbinMaterialTexturesPropertyGroup, XfbinTextureChunkPropertyGroup

#Materials
def F00A(self, mesh, xfbin_mat, mesh_flags):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#check if F00A_Material exists
	material = bpy.data.materials.get('F00A_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = ['F00A_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	NUTextures: XfbinMaterialTexturesPropertyGroup =  mat_data.NUTextures
	texture: XfbinTextureChunkPropertyGroup = NUTextures[0]

	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")
	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	#load celshade.png
	if not bpy.data.images.get('celshade'):
		celshade = bpy.data.images.load(f"{path}/celshade.png")
		celshade.name = 'celshade'

	#find the shader node
	shader_node = material.node_tree.nodes.get('XFBIN SHADER')

	#get material params from the mesh
	meshmat = mesh.materials[0]

	for prop in meshmat.properties:
		if prop.name == "NU_toneOffsetParam":
			shader_node.inputs['toneOffsetParam'].default_value = prop.values[0]
		elif prop.name == "NU_celShadeParam":
			shader_node.inputs['celShadeParam'].default_value = prop.values[0]
	
	return material

def _02_F00A(self, mesh, xfbin_mat, mesh_flags):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#check if F00A_Material exists
	material = bpy.data.materials.get('2F00A_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = ['2F00A_Material']
		material = data_to.materials[0]
	
 
	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")
	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'
	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	#load celshade.png
	if not bpy.data.images.get('celshade'):
		celshade = bpy.data.images.load(f"{path}/celshade.png")
		celshade.name = 'celshade'
	
	#set tex2 and 3 to use celshade
	tex3_node = material.node_tree.nodes.get('celShade1')
	tex3_node.image = bpy.data.images.get('celshade')
	tex4_node = material.node_tree.nodes.get('celShade2')
	tex4_node.image = bpy.data.images.get('celshade')

	#find the shader node
	shader_node = material.node_tree.nodes.get('XFBIN SHADER')

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	shader_node.inputs['uvOffset1 Offset X'].default_value = mat_data.uvOffset1[0]
	shader_node.inputs['uvOffset1 Offset Y'].default_value = mat_data.uvOffset1[1]
	shader_node.inputs['uvOffset1 Scale X'].default_value = mat_data.uvOffset1[2]
	shader_node.inputs['uvOffset1 Scale Y'].default_value = mat_data.uvOffset1[3]


	#get material params from the mesh
	meshmat = mesh.materials[0]

	for prop in meshmat.properties:
		if prop.name == "NU_toneOffsetParam":
			shader_node.inputs['toneOffsetParam'].default_value = prop.values[0]
		elif prop.name == "NU_celShadeParam":
			shader_node.inputs['celShadeParam'].default_value = prop.values[0]
		elif prop.name == "NU_blendType":
			shader_node.inputs['blendType'].default_value = prop.values[0]
	
	#set blend Rate
	shader_node.inputs['blendRate1'].default_value = mat_data.blendRate[0]
	shader_node.inputs['blendRate2'].default_value = mat_data.blendRate[1]
	
	return material

def _01_F002(self, mesh, xfbin_mat, mesh_flags):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#check if F00A_Material exists
	material = bpy.data.materials.get('1F002_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = ['1F002_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")
	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	#find the shader node
	shader_node = material.node_tree.nodes.get('XFBIN SHADER')

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	#get material params from the mesh
	meshmat = mesh.materials[0]

	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material

def _01_F003(self, mesh, xfbin_mat, mesh_flags):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#check if F00A_Material exists
	material = bpy.data.materials.get('1F003_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = ['1F003_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")
	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'

	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	#find the shader node
	shader_node = material.node_tree.nodes.get('XFBIN SHADER')

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material

def _03_F002(self, mesh, xfbin_mat, mesh_flags, shader_name = '3F002'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#check if F00A_Material exists
	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/3F002.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")
	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'
	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")

	#find the shader node
	shader_node = material.node_tree.nodes.get(shader_name)

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	shader_node.inputs['uvOffset1 Offset X'].default_value = mat_data.uvOffset1[0]
	shader_node.inputs['uvOffset1 Offset Y'].default_value = mat_data.uvOffset1[1]
	shader_node.inputs['uvOffset1 Scale X'].default_value = mat_data.uvOffset1[2]
	shader_node.inputs['uvOffset1 Scale Y'].default_value = mat_data.uvOffset1[3]

	#blendrate
	shader_node.inputs['blendRate Tex1'].default_value = mat_data.blendRate[0]
	shader_node.inputs['blendRate Tex2'].default_value = mat_data.blendRate[1]

	#get material params from the mesh
	meshmat = mesh.materials[0]

	for prop in meshmat.properties:
		if prop.name == "NU_blendType":
			shader_node.inputs['blendType'].default_value = prop.values[0]

	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material


def _01_F008(self, mesh, xfbin_mat, mesh_flags, shader_name = '1F008'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#check if F00A_Material exists
	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name

	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")
	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'

	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'
	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	#find the shader node
	shader_node = material.node_tree.nodes.get("XFBIN SHADER")

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	shader_node.inputs['falloff'].default_value = mat_data.fallOff
	shader_node.inputs["Glare"].default_value = mat_data.glare

	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material


def _03_F008(self, mesh, xfbin_mat, mesh_flags, shader_name = '3F008'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#check if F00A_Material exists
	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/3F008.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name

	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]
	texture3: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[2]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")
	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'

	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'
	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex3_node = material.node_tree.nodes.get('Tex3')
	tex3_node.image = bpy.data.images.get(f"{texture3.name}_0")

	#set texture wrap mode
	if texture3.wrapModeS == '3':
		tex3_node.extension = 'EXTEND'
	
	
	#find the shader node
	shader_node = material.node_tree.nodes.get(shader_name)

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	shader_node.inputs['uvOffset1 Offset X'].default_value = mat_data.uvOffset1[0]
	shader_node.inputs['uvOffset1 Offset Y'].default_value = mat_data.uvOffset1[1]
	shader_node.inputs['uvOffset1 Scale X'].default_value = mat_data.uvOffset1[2]
	shader_node.inputs['uvOffset1 Scale Y'].default_value = mat_data.uvOffset1[3]

	shader_node.inputs['falloff'].default_value = mat_data.fallOff

	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material



def _05_F002(self, mesh, xfbin_mat, mesh_flags, shader_name = '5F002'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/5F002.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]

	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	

	shader_node = material.node_tree.nodes.get(shader_name)

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material


def _05_F00D(self, mesh, xfbin_mat, mesh_flags):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get('5F00D_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = ['5F00D_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	
	#find the shader node
	shader_node = material.node_tree.nodes.get('XFBIN SHADER')

	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material


def _07_F002(self, mesh, xfbin_mat, mesh_flags, shader_name = '7F002'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/7F002.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	#check if pointLightPos0 object exists
	pointLightPos0 = bpy.data.objects.get('pointLightPos0')

	if pointLightPos0:
		#make sure it's linked to the scene
		if pointLightPos0.users_scene:
			pass
		else:
			bpy.context.collection.objects.link(pointLightPos0)
	else:
		#create a point lamp
		pointLightPos0 = bpy.data.lights.new(name='pointLightPos0', type='POINT')
		pointLightPos0.energy = 1

		#create an object for the lamp
		pointLightPos0_obj = bpy.data.objects.new('pointLightPos0', pointLightPos0)
		pointLightPos0_obj.location = (0, 0, 0)

		#link the lamp to the scene
		bpy.context.collection.objects.link(pointLightPos0_obj)
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	
	#find the shader node
	shader_node = material.node_tree.nodes.get('7F002')

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset1 Offset X'].default_value = mat_data.uvOffset1[0]
	shader_node.inputs['uvOffset1 Offset Y'].default_value = mat_data.uvOffset1[1]
	shader_node.inputs['uvOffset1 Scale X'].default_value = mat_data.uvOffset1[2]
	shader_node.inputs['uvOffset1 Scale Y'].default_value = mat_data.uvOffset1[3]

	shader_node.inputs['blendRate Tex1'].default_value = mat_data.blendRate[0]
	shader_node.inputs['blendRate Tex2'].default_value = mat_data.blendRate[1]
	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material


def _19_F002(self, mesh, xfbin_mat, mesh_flags, shader_name = '19F002'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/20F00A_19F002.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]
	texture3: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[2]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'
	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex3_node = material.node_tree.nodes.get('Tex3')
	tex3_node.image = bpy.data.images.get(f"{texture3.name}_0")

	#set texture wrap mode
	if texture3.wrapModeS == '3':
		tex3_node.extension = 'EXTEND'

	if not tex3_node.image:
		tex3_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	
	
	#find the shader node
	shader_node = material.node_tree.nodes.get(f'{shader_name}')

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	#set shader params
	for prop in mesh.materials[0].properties:
		if prop.name == "NU_toneOffsetParam":
			shader_node.inputs['toneOffsetParam'].default_value = prop.values[0]
		elif prop.name == "NU_celShadeParam":
			shader_node.inputs['celShadeParam'].default_value = prop.values[0]
		elif prop.name == "NU_uvScaleScreen":
			shader_node.inputs['uvScaleScreen Offset X'].default_value = prop.values[0]
			shader_node.inputs['uvScaleScreen Offset Y'].default_value = prop.values[1]
			shader_node.inputs['uvScaleScreen Scale X'].default_value = prop.values[2]
			shader_node.inputs['uvScaleScreen Scale Y'].default_value = prop.values[3]
		elif prop.name == "NU_falloff":
			shader_node.inputs['falloff'].default_value = prop.values[0]

	return material


def _01_F801(self, mesh, xfbin_mat, mesh_flags, shader_name = '1F801'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]
	hatching_n: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[2]
	hatching1: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[3]
	texture3: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[4]
	texture4: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[5]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'
	try:
		tex2_node.image.colorspace_settings.name = 'Non-Color'
	except:
		pass
	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex3_node = material.node_tree.nodes.get('Tex3')
	tex3_node.image = bpy.data.images.get(f"{texture3.name}_0")

	#set texture wrap mode
	if texture3.wrapModeS == '3':
		tex3_node.extension = 'EXTEND'
	try:
		tex3_node.image.colorspace_settings.name = 'Non-Color'
	except:
		pass
	if not tex3_node.image:
		tex3_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
  
	tex4_node = material.node_tree.nodes.get('Tex4')
	tex4_node.image = bpy.data.images.get(f"{texture4.name}_0")
 
	#set texture wrap mode
	if texture4.wrapModeS == '3':
		tex4_node.extension = 'EXTEND'
	
	try:
		tex4_node.image.colorspace_settings.name = 'Non-Color'
	except:
		pass
	
	
	#find the shader node
	shader_node = material.node_tree.nodes.get(f'XFBIN SHADER')

	#set uvOffset and uvScale
	'''shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]'''

	#set shader params
	for prop in mesh.materials[0].properties:
		if prop.name == "NU_lightingParam":
			shader_node.inputs['lightingParam X'].default_value = prop.values[0]
			shader_node.inputs['lightingParam Y'].default_value = prop.values[1]
		elif prop.name == "NU_msParam0":
			shader_node.inputs['msParam X'].default_value = prop.values[0]
			shader_node.inputs['msParam Y'].default_value = prop.values[1]
			shader_node.inputs['msParam Z'].default_value = prop.values[2]
			shader_node.inputs['msParam W'].default_value = prop.values[3]
		elif prop.name == "NU_hatchingParam":
			shader_node.inputs['hatchingParam X'].default_value = prop.values[0]
			shader_node.inputs['hatchingParam Y'].default_value = prop.values[1]
			shader_node.inputs['hatchingParam Z'].default_value = prop.values[2]
			shader_node.inputs['hatchingParam W'].default_value = prop.values[3]
		elif prop.name == "NU_specularParam":
			shader_node.inputs['specularParam X'].default_value = prop.values[0]
			shader_node.inputs['specularParam Y'].default_value = prop.values[1]
			shader_node.inputs['specularParam Z'].default_value = prop.values[2]
			shader_node.inputs['specularParam W'].default_value = prop.values[3]
		elif prop.name == "NU_outline0Param":
			shader_node.inputs['outline0Param X'].default_value = prop.values[0]
			shader_node.inputs['outline0Param Y'].default_value = prop.values[1]
			shader_node.inputs['outline0Param Z'].default_value = prop.values[2]
			shader_node.inputs['outline0Param W'].default_value = prop.values[3]

	return material


def _01_F130(self, mesh, xfbin_mat, mesh_flags, shader_name = '1F130'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#check if F00A_Material exists
	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material
	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")
	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'
	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")

	#find the shader node
	shader_node = material.node_tree.nodes.get("XFBIN SHADER")

	#get material params from the mesh
	meshmat = mesh.materials[0]

	#set shadows culling
	material.use_backface_culling_shadow = True
	
	return material


def _20_F000(self, mesh, xfbin_mat, mesh_flags, shader_name = '20F000'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/20F00A_19F002.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]
	texture3: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[2]
	texture4: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[3]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'
	
	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex3_node = material.node_tree.nodes.get('Tex3')
	tex3_node.image = bpy.data.images.get(f"{texture3.name}_0")

	#set texture wrap mode
	if texture3.wrapModeS == '3':
		tex3_node.extension = 'EXTEND'

	if not tex3_node.image:
		tex3_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	

	tex4_node = material.node_tree.nodes.get('Tex4')
	tex4_node.image = bpy.data.images.get(f"{texture4.name}_0")

	#set texture wrap mode
	if texture4.wrapModeS == '3':
		tex4_node.extension = 'EXTEND'

	if not tex4_node.image:
		tex4_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	#get celshade.png
	if not bpy.data.images.get('celshade'):
		celshade = bpy.data.images.load(f"{path}/celshade.png")
		celshade.name = 'celshade'
	
	#set tex5 to use celshade
	tex5_node = material.node_tree.nodes.get('Tex5')
	tex5_node.image = bpy.data.images.get('celshade')

	
	#find the shader node
	shader_node = material.node_tree.nodes.get(f'{shader_name}')

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 Offset X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Offset Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Scale X'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 Scale Y'].default_value = mat_data.uvOffset0[3]

	#set shader params
	for prop in mesh.materials[0].properties:
		if prop.name == "NU_toneOffsetParam":
			shader_node.inputs['toneOffsetParam'].default_value = prop.values[0]
		elif prop.name == "NU_celShadeParam":
			shader_node.inputs['celShadeParam'].default_value = prop.values[0]
		elif prop.name == "NU_uvScaleScreen":
			shader_node.inputs['uvScaleScreen Offset X'].default_value = prop.values[0]
			shader_node.inputs['uvScaleScreen Offset Y'].default_value = prop.values[1]
			shader_node.inputs['uvScaleScreen Scale X'].default_value = prop.values[2]
			shader_node.inputs['uvScaleScreen Scale Y'].default_value = prop.values[3]
		elif prop.name == "NU_falloff":
			shader_node.inputs['falloff'].default_value = prop.values[0]
	

	#set scene framerate to 30
	bpy.context.scene.render.fps = 30
	#set scene frame end to 30
	bpy.context.scene.frame_end = 30
	#play the animation
	bpy.ops.screen.animation_play()
	

	return material

def _07_F00D(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '07F00D'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	#material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	#Remove Unnecessary nodes
	material.node_tree.nodes.clear()

	#remove node groups with the same name to prevent issues with min and max values of some nodes
	if bpy.data.node_groups.get(nodegrp):
		bpy.data.node_groups.remove(bpy.data.node_groups.get(nodegrp))

	#Create a new node tree to be used later
	nodetree = bpy.data.node_groups.new(nodegrp, 'ShaderNodeTree')

	#Create a node group to organize nodes and inputs
	nodegroup = material.node_tree.nodes.new('ShaderNodeGroup')
	nodegroup.name = nodegrp
	nodegroup.location = (721, 611)
	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Nodes
	normal = nodegroup.node_tree.nodes.new('ShaderNodeNormal')
	normal.location = (-696, 350)

	diffuse_bsdf = nodegroup.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
	diffuse_bsdf.location = (-519, 304)

	shader_rgb = nodegroup.node_tree.nodes.new('ShaderNodeShaderToRGB')
	shader_rgb.location = (-327, 305)

	math_greater = nodegroup.node_tree.nodes.new('ShaderNodeMath')
	math_greater.location = (-163, 320)
	math_greater.operation = 'GREATER_THAN'
	math_greater.inputs[1].default_value = 0.00

	lighten = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	lighten.location = (47, 300)
	lighten.blend_type = 'LIGHTEN'
	lighten.inputs[0].default_value = 1
	lighten.inputs[2].default_value = (0.2,0.2,0.2,1)

	multiply1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply1.location = (256, 131)
	multiply1.blend_type = 'MULTIPLY'
	multiply1.inputs[0].default_value = 1

	add1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	add1.location = (256, 131)
	add1.blend_type = 'ADD'
	add1.inputs[0].default_value = 1

	multiply2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply2.location = (476, 81)
	multiply2.blend_type = 'MULTIPLY'
	multiply2.inputs[0].default_value = 1

	multiply3 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply3.location = (476, 81)
	multiply3.blend_type = 'MULTIPLY'
	multiply3.inputs[0].default_value = 1

	multiply4 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply4.location = (476, 81)
	multiply4.blend_type = 'MULTIPLY'
	multiply4.inputs[0].default_value = 1

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (264, -261)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (696, -113)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-56, -112)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha 1')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha 2')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Shadow Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Colors')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Alpha')

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (886, 4)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-84, -552)
	uv1.uv_map = 'UV_0'

	uv2 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv2.location = (-78, -308)
	uv2.uv_map = 'UV_1'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (174, 720)
	tex1.name = 'Diffuse 1'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (178, 420)
	tex2.name = 'Diffuse 2'

	tex3 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex3.location = (178, 420)
	tex3.name = 'Shadoow'

	vcol = material.node_tree.nodes.new('ShaderNodeVertexColor')

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (1091, 520)

	#Link nodes
	nodegroup.node_tree.links.new(normal.outputs[0], diffuse_bsdf.inputs[2])

	nodegroup.node_tree.links.new(diffuse_bsdf.outputs['BSDF'], shader_rgb.inputs['Shader'])

	nodegroup.node_tree.links.new(shader_rgb.outputs['Color'], math_greater.inputs[0])

	nodegroup.node_tree.links.new(math_greater.outputs[0], lighten.inputs[1])

	nodegroup.node_tree.links.new(lighten.outputs[0], multiply1.inputs[1])

	nodegroup.node_tree.links.new(multiply1.outputs[0], add1.inputs[1])

	nodegroup.node_tree.links.new(add1.outputs[0], multiply2.inputs[1])

	nodegroup.node_tree.links.new(multiply2.outputs[0], multiply3.inputs[1])

	nodegroup.node_tree.links.new(multiply3.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(multiply4.outputs[0], mix_shader.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], multiply1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[1], multiply4.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[2], add1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[3], add1.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[4], multiply2.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[5], multiply3.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[6], multiply4.inputs[2])

	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])
	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[2])
	material.node_tree.links.new(tex2.outputs[1], nodegroup.inputs[3])

	material.node_tree.links.new(uv2.outputs[0], tex3.inputs[0])
	material.node_tree.links.new(tex3.outputs[0], nodegroup.inputs[4])

	material.node_tree.links.new(vcol.outputs[0], nodegroup.inputs[5])
	material.node_tree.links.new(vcol.outputs[1], nodegroup.inputs[6])


	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
		tex1.image = bpy.data.images.get(image_name)
		image_name2 = f'{xfbin_mat.texture_groups[0].texture_chunks[1].name}_0'
		tex2.image = bpy.data.images.get(image_name2)
		image_name3 = f'{xfbin_mat.texture_groups[0].texture_chunks[2].name}_0'
		tex3.image = bpy.data.images.get(image_name3)
		if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')

	return material


def _07_F010(self, meshmat,  xfbin_mat, matname, mesh, nodegrp = '07F020'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	#material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	#Remove Unnecessary nodes
	material.node_tree.nodes.clear()

	#remove node groups with the same name to prevent issues with min and max values of some nodes
	if bpy.data.node_groups.get(nodegrp):
		bpy.data.node_groups.remove(bpy.data.node_groups.get(nodegrp))

	#Create a new node tree to be used later
	nodetree = bpy.data.node_groups.new(nodegrp, 'ShaderNodeTree')

	#Create a node group to organize nodes and inputs
	nodegroup = material.node_tree.nodes.new('ShaderNodeGroup')
	nodegroup.name = nodegrp
	nodegroup.location = (721, 611)
	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Nodes
	normal = nodegroup.node_tree.nodes.new('ShaderNodeNormal')
	normal.location = (-796, -394)

	diffuse_bsdf = nodegroup.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
	diffuse_bsdf.location = (-619, -440)

	shader_rgb = nodegroup.node_tree.nodes.new('ShaderNodeShaderToRGB')
	shader_rgb.location = (-427, -439)

	math_greater = nodegroup.node_tree.nodes.new('ShaderNodeMath')
	math_greater.location = (-263, -424)
	math_greater.operation = 'GREATER_THAN'
	math_greater.inputs[1].default_value = 0.06

	lighten = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	lighten.location = (-66, -421)
	lighten.blend_type = 'LIGHTEN'
	lighten.inputs[0].default_value = 1
	lighten.inputs[2].default_value = (0.2,0.2,0.2,1)

	multiply1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply1.location = (156, -397)
	multiply1.blend_type = 'MULTIPLY'
	multiply1.inputs[0].default_value = 1

	mix1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix1.location = (404, -321)
	mix1.blend_type = 'MIX'

	multiply2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply2.location = (647, -235)
	multiply2.blend_type = 'MULTIPLY'
	multiply2.inputs[0].default_value = 1

	multiply3 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply3.location = (867, -175)
	multiply3.blend_type = 'MULTIPLY'
	multiply3.inputs[0].default_value = 1

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (984, -449)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (1121, -151)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-91, -133)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Texture 1')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Texture 2')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Mask Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Shadow Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Colors')
	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (1341, -137)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-1806, 328)
	uv1.uv_map = 'UV_0'

	uv2 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv2.location = (-1908, -197)
	uv2.uv_map = 'UV_1'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (-1390, 545)
	tex1.name = 'Diffuse1'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (-1390, 286)
	tex2.name = 'Diffuse2'

	tex3 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex3.location = (-1390, 24)
	tex3.name = 'Mask'

	tex4 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex4.location = (-1390, -241)
	tex4.name = 'Shadow'

	vcol = material.node_tree.nodes.new('ShaderNodeVertexColor')
	vcol.location = (-1349, -521)

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (1091, 520)

	#Link nodes
	nodegroup.node_tree.links.new(normal.outputs[0], diffuse_bsdf.inputs[2])

	nodegroup.node_tree.links.new(diffuse_bsdf.outputs['BSDF'], shader_rgb.inputs['Shader'])

	nodegroup.node_tree.links.new(shader_rgb.outputs['Color'], math_greater.inputs[0])

	nodegroup.node_tree.links.new(math_greater.outputs[0], lighten.inputs[1])

	nodegroup.node_tree.links.new(lighten.outputs[0], multiply1.inputs[1])

	nodegroup.node_tree.links.new(multiply1.outputs[0], mix1.inputs[1])

	nodegroup.node_tree.links.new(mix1.outputs[0], multiply2.inputs[1])

	nodegroup.node_tree.links.new(multiply2.outputs[0], multiply3.inputs[1])

	nodegroup.node_tree.links.new(multiply3.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], multiply1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[1], mix_shader.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[2], mix1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[3], mix1.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[4], multiply2.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[5], multiply3.inputs[2])

	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(uv2.outputs[0], tex2.inputs[0])
	material.node_tree.links.new(uv2.outputs[0], tex3.inputs[0])
	material.node_tree.links.new(uv2.outputs[0], tex4.inputs[0])
	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[2])
	material.node_tree.links.new(tex3.outputs[0], nodegroup.inputs[3])
	material.node_tree.links.new(tex4.outputs[0], nodegroup.inputs[4])
	material.node_tree.links.new(vcol.outputs[0], nodegroup.inputs[5])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
		tex1.image = bpy.data.images.get(image_name)
		image_name2 = f'{xfbin_mat.texture_groups[0].texture_chunks[1].name}_0'
		tex2.image = bpy.data.images.get(image_name2)
		image_name3 = f'{xfbin_mat.texture_groups[0].texture_chunks[3].name}_0'
		tex3.image = bpy.data.images.get(image_name3)
		image_name4 = f'{xfbin_mat.texture_groups[0].texture_chunks[2].name}_0'
		tex4.image = bpy.data.images.get(image_name4)
		if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')

	return material

def _03_F00F(self, mesh, xfbin_mat, mesh_flags, shader_name = '3F00F'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/3F00F.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]
	texture3: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[2]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'

	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex3_node = material.node_tree.nodes.get('Tex3')
	tex3_node.image = bpy.data.images.get(f"{texture3.name}_0")

	#set texture wrap mode
	if texture3.wrapModeS == '3':
		tex3_node.extension = 'EXTEND'

	if not tex3_node.image:
		tex3_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	

	#find the shader node
	shader_node = material.node_tree.nodes.get(f'{shader_name}')


	#set shader params
	for prop in mesh.materials[0].properties:
		if prop.name == "NU_blendType":
			shader_node.inputs['blendType'].default_value = prop.values[0]
	

	#set scene framerate to 30
	bpy.context.scene.render.fps = 30
	#set scene frame end to 30
	bpy.context.scene.frame_end = 30
	#play the animation
	bpy.ops.screen.animation_play()
	

	return material


def _01_F00F(self, mesh, xfbin_mat, mesh_flags, shader_name = '1F00F'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/XFBIN_Materials.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]

	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'

	
	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	

	#find the shader node
	shader_node = material.node_tree.nodes.get('XFBIN SHADER')


	#set shadows culling
	material.use_backface_culling_shadow = True

	#set scene framerate to 30
	bpy.context.scene.render.fps = 30
	#set scene frame end to 30
	bpy.context.scene.frame_end = 30
	#play the animation
	bpy.ops.screen.animation_play()
	

	return material


def E002(self, mesh, xfbin_mat, mesh_flags):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(f'{xfbin_mat.name}')
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	meshmat = mesh.materials[0]
	material.use_nodes = True

	material.use_nodes = True
	material.blend_method = 'BLEND'
	material.shadow_method = 'CLIP'
	material.alpha_threshold = 0
	material.use_backface_culling = True
	material.node_tree.nodes.clear()

	#Nodes
	transparent1 = material.node_tree.nodes.new('ShaderNodeBsdfTransparent')

	transparent2 = material.node_tree.nodes.new('ShaderNodeBsdfTransparent')

	mix_shader = material.node_tree.nodes.new('ShaderNodeMixShader')

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')

	invert = material.node_tree.nodes.new('ShaderNodeInvert')
	invert.inputs[0].default_value = 1

	lightpath = material.node_tree.nodes.new('ShaderNodeLightPath')

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')

	#Link nodes
	material.node_tree.links.new(tex1.outputs[1], invert.inputs[1])
	material.node_tree.links.new(invert.outputs[0], transparent1.inputs[0])
	material.node_tree.links.new(lightpath.outputs[0], mix_shader.inputs[0])
	material.node_tree.links.new(transparent1.outputs[0], mix_shader.inputs[1])
	material.node_tree.links.new(transparent2.outputs[0], mix_shader.inputs[2])
	material.node_tree.links.new(mix_shader.outputs[0], output.inputs[0])
	
	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
		tex1.image = bpy.data.images.get(image_name)
		if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')

	return material


def _01_F8_01(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '01F801'):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	#material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	#Remove Unnecessary nodes
	material.node_tree.nodes.clear()

	#remove node groups with the same name to prevent issues with min and max values of some nodes
	if bpy.data.node_groups.get(nodegrp):
		bpy.data.node_groups.remove(bpy.data.node_groups.get(nodegrp))

	#Create a new node tree to be used later
	nodetree = bpy.data.node_groups.new(nodegrp, 'ShaderNodeTree')

	#Create a node group to organize nodes and inputs
	nodegroup = material.node_tree.nodes.new('ShaderNodeGroup')
	nodegroup.name = nodegrp
	nodegroup.location = (409, 182)

	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Le Shader
	normal = nodegroup.node_tree.nodes.new('ShaderNodeNormalMap')
	normal.location = (-682, 125)

	diffuse = nodegroup.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
	diffuse.location = (-430, 256)

	shader_to_rgb = nodegroup.node_tree.nodes.new('ShaderNodeShaderToRGB')
	shader_to_rgb.location = (-200, 245)

	color_ramp = nodegroup.node_tree.nodes.new('ShaderNodeValToRGB')
	color_ramp.color_ramp.elements.new(0.5)
	color_ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1)
	color_ramp.color_ramp.elements[0].position = 0.1
	color_ramp.color_ramp.elements[1].color = (0.1, 0.1, 0.1, 1)
	color_ramp.color_ramp.elements[1].position = 0.15
	color_ramp.color_ramp.elements[2].color = (1, 1, 1, 1)
	color_ramp.color_ramp.elements[2].position = 0.2
	color_ramp.location = (32, 265)

	mix1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix1.blend_type = 'MULTIPLY'
	mix1.inputs[0].default_value = 1
	mix1.location = (381, 248)

	mix2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix2.blend_type = 'MULTIPLY'
	mix2.location = (641, 176)	

	invert = nodegroup.node_tree.nodes.new('ShaderNodeInvert')
	invert.location = (-452, -179)

	fresnel = nodegroup.node_tree.nodes.new('ShaderNodeFresnel')
	fresnel.location = (-280, -346)
	fresnel.inputs[0].default_value = 0.94

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (690, 308)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (977, 50)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-979, -24)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Normals Texture')
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Normals Strength')
	nodegroup.inputs[3].default_value = 2
	nodegroup.node_tree.inputs.new('NodeSocketColor','Outline Color')
	nodegroup.inputs[4].default_value = (0, 0, 0, 1)
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Outline Thickness')
	nodegroup.inputs[5].default_value = 0.05

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (1234, 58)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (38, 356)
	tex1.name = 'Diffuse Texture'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (37, 61)
	tex2.name = 'Normals Texture'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (864, 212)

    #Link nodes
	nodegroup.node_tree.links.new(normal.outputs[0], diffuse.inputs[2])
	nodegroup.node_tree.links.new(normal.outputs[0], fresnel.inputs[1])

	nodegroup.node_tree.links.new(diffuse.outputs[0], shader_to_rgb.inputs[0])

	nodegroup.node_tree.links.new(shader_to_rgb.outputs[0], color_ramp.inputs[0])

	nodegroup.node_tree.links.new(color_ramp.outputs[0], mix1.inputs[1])

	nodegroup.node_tree.links.new(mix1.outputs[0], mix2.inputs[1])

	nodegroup.node_tree.links.new(mix2.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(invert.outputs[0], fresnel.inputs[0])

	nodegroup.node_tree.links.new(fresnel.outputs[0], mix2.inputs[0])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], mix1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[1], mix_shader.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[2], normal.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[3], normal.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[4], mix2.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[5], invert.inputs[1])


	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[2])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])
	
	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		try:
			image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
			tex1.image = bpy.data.images.get(image_name)
			image_name2 = f'{xfbin_mat.texture_groups[0].texture_chunks[1].name}_0'
			tex2.image = bpy.data.images.get(image_name2)
			if tex2.image:
				tex2.image.colorspace_settings.name = 'Non-Color'
		except:
			pass
		if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')

	return material


def _01_F8_00(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '01F801'):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	#material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	#Remove Unnecessary nodes
	material.node_tree.nodes.clear()

	#remove node groups with the same name to prevent issues with min and max values of some nodes
	if bpy.data.node_groups.get(nodegrp):
		bpy.data.node_groups.remove(bpy.data.node_groups.get(nodegrp))

	#Create a new node tree to be used later
	nodetree = bpy.data.node_groups.new(nodegrp, 'ShaderNodeTree')

	#Create a node group to organize nodes and inputs
	nodegroup = material.node_tree.nodes.new('ShaderNodeGroup')
	nodegroup.name = nodegrp
	nodegroup.location = (409, 182)

	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Le Shader
	diffuse = nodegroup.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
	diffuse.location = (-430, 256)

	shader_to_rgb = nodegroup.node_tree.nodes.new('ShaderNodeShaderToRGB')
	shader_to_rgb.location = (-200, 245)

	color_ramp = nodegroup.node_tree.nodes.new('ShaderNodeValToRGB')
	color_ramp.color_ramp.elements.new(0.5)
	color_ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1)
	color_ramp.color_ramp.elements[0].position = 0.1
	color_ramp.color_ramp.elements[1].color = (0.1, 0.1, 0.1, 1)
	color_ramp.color_ramp.elements[1].position = 0.15
	color_ramp.color_ramp.elements[2].color = (1, 1, 1, 1)
	color_ramp.color_ramp.elements[2].position = 0.2
	color_ramp.location = (32, 265)

	mix1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix1.blend_type = 'MULTIPLY'
	mix1.inputs[0].default_value = 1
	mix1.location = (381, 248)

	mix2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix2.blend_type = 'MULTIPLY'
	mix2.location = (641, 176)	

	invert = nodegroup.node_tree.nodes.new('ShaderNodeInvert')
	invert.location = (-452, -179)

	fresnel = nodegroup.node_tree.nodes.new('ShaderNodeFresnel')
	fresnel.location = (-280, -346)
	fresnel.inputs[0].default_value = 0.94

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (690, 308)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (977, 50)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-979, -24)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Outline Color')
	nodegroup.inputs[2].default_value = (0, 0, 0, 1)
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Outline Thickness')
	nodegroup.inputs[3].default_value = 0.05

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (1234, 58)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (38, 356)
	tex1.name = 'Diffuse Texture'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (864, 212)

    #Link nodes
	nodegroup.node_tree.links.new(diffuse.outputs[0], shader_to_rgb.inputs[0])

	nodegroup.node_tree.links.new(shader_to_rgb.outputs[0], color_ramp.inputs[0])

	nodegroup.node_tree.links.new(color_ramp.outputs[0], mix1.inputs[1])

	nodegroup.node_tree.links.new(mix1.outputs[0], mix2.inputs[1])

	nodegroup.node_tree.links.new(mix2.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(invert.outputs[0], fresnel.inputs[0])

	nodegroup.node_tree.links.new(fresnel.outputs[0], mix2.inputs[0])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], mix1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[1], mix_shader.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[2], mix2.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[3], invert.inputs[1])


	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])
	
	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		try:
			image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
			tex1.image = bpy.data.images.get(image_name)
		except:
			pass
		if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')

	return material

def _01_F1_30(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '01F130'):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	#material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	#Remove Unnecessary nodes
	material.node_tree.nodes.clear()

	uv = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv.location = (0, 50)
	uv.uv_map = 'UV_1'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (38, 356)
	tex1.name = 'Diffuse Texture'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (37, 61)
	tex2.name = 'Normals Texture'

	mix1 = material.node_tree.nodes.new('ShaderNodeMixRGB')
	mix1.blend_type = 'MIX'
	mix1.inputs[0].default_value = 1
	mix1.location = (409, 182)

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (864, 212)

    #Link nodes
	material.node_tree.links.new(uv.outputs[0], tex2.inputs[0])

	material.node_tree.links.new(tex1.outputs[0], mix1.inputs[1])

	material.node_tree.links.new(tex2.outputs[0], mix1.inputs[2])
	material.node_tree.links.new(tex2.outputs[1], mix1.inputs[0])

	material.node_tree.links.new(mix1.outputs[0], output.inputs[0])
	
	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
		tex1.image = bpy.data.images.get(image_name)
		image_name2 = f'{xfbin_mat.texture_groups[0].texture_chunks[1].name}_0'
		tex2.image = bpy.data.images.get(image_name2)
	
		if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')

	return material


def _19_F0_0F(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '19F00F'):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	#material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	#Remove Unnecessary nodes
	material.node_tree.nodes.clear()

	#remove node groups with the same name to prevent issues with min and max values of some nodes
	if bpy.data.node_groups.get(nodegrp):
		bpy.data.node_groups.remove(bpy.data.node_groups.get(nodegrp))

	#Create a new node tree to be used later
	nodetree = bpy.data.node_groups.new(nodegrp, 'ShaderNodeTree')

	#Create a node group to organize nodes and inputs
	nodegroup = material.node_tree.nodes.new('ShaderNodeGroup')
	nodegroup.name = nodegrp
	nodegroup.location = (83.41973876953125, -43.020721435546875)

	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Le Shader
	groupnodes = nodegroup.node_tree.nodes

	uv = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv.location = (-1063.779052734375, 155.6358642578125)

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (-725.7741088867188, 254.3086395263672)

	mapping1 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping1.location = Vector((-1048.0135498046875, -48.21296310424805))

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = Vector((-736.3289794921875, -154.64529418945312))

	tex_coords = material.node_tree.nodes.new('ShaderNodeTexCoord')
	tex_coords.location = Vector((-1470.010498046875, -621.0548095703125))

	mapping2 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping2.location = Vector((-1055.4130859375, -510.4031677246094))

	tex3 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex3.location = Vector((-796.4454956054688, -486.6017150878906))

	mapping3 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping3.location = Vector((-1074.871826171875, -922.6276245117188))

	tex4 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex4.location = Vector((-811.4612426757812, -837.7904052734375))


	#node group inputs
	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = Vector((-1356.9105224609375, 143.15475463867188))
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Falloff Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Maplus1')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Maplus2')

	math1 = groupnodes.new('ShaderNodeMath')
	math1.operation = 'SQRT'

	fresnel = groupnodes.new('ShaderNodeFresnel')
	fresnel.location = Vector((-267.765380859375, 293.6260681152344))


	mix1 = groupnodes.new('ShaderNodeMixRGB')
	mix1.blend_type = 'MIX'
	mix1.inputs[0].default_value = 0.5
	mix1.location = Vector((-631.3009033203125, 98.70460510253906))

	mix2 = groupnodes.new('ShaderNodeMixRGB')
	mix2.blend_type = 'MIX'
	mix2.inputs[0].default_value = 0.2
	mix2.location = Vector((-198.2328643798828, 57.780181884765625))

	mix3 = groupnodes.new('ShaderNodeMixRGB')
	mix3.blend_type = 'MIX'
	mix3.inputs[0].default_value = 0.2
	mix3.location = Vector((72.92039489746094, 257.24658203125))

	mix4 = groupnodes.new('ShaderNodeMixRGB')
	mix4.blend_type = 'MULTIPLY'
	mix4.inputs[0].default_value = 1
	mix4.location = Vector((357.3802490234375, 387.3600769042969))

	emission = groupnodes.new('ShaderNodeEmission')
	emission.inputs[1].default_value = 2
	emission.location = Vector((-82.73138427734375, 566.813232421875))

	shader_to_rgb = groupnodes.new('ShaderNodeShaderToRGB')
	shader_to_rgb.location =Vector((103.73695373535156, 538.26416015625))

	transparent = groupnodes.new('ShaderNodeBsdfTransparent')
	transparent.location = Vector((386.8059387207031, 550.951416015625))

	mix_shader = groupnodes.new('ShaderNodeMixShader')
	mix_shader.inputs[0].default_value = 0.85
	mix_shader.location = Vector((608.5802612304688, 339.4270324707031))

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = Vector((1000.0, 0.0))
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')
	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')

	#Link nodes
	nodegroup.node_tree.links.new(group_input.outputs[0], mix2.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[1], math1.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[2], mix1.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[3], mix1.inputs[2])

	nodegroup.node_tree.links.new(mix1.outputs[0], mix2.inputs[2])

	nodegroup.node_tree.links.new(mix2.outputs[0], mix3.inputs[1])

	nodegroup.node_tree.links.new(fresnel.outputs[0], mix3.inputs[2])

	nodegroup.node_tree.links.new(math1.outputs[0], fresnel.inputs[0])

	nodegroup.node_tree.links.new(mix3.outputs[0], mix4.inputs[2])

	nodegroup.node_tree.links.new(mix4.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(emission.outputs[0], shader_to_rgb.inputs[0])

	nodegroup.node_tree.links.new(shader_to_rgb.outputs[0], mix4.inputs[1])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	material.node_tree.links.new(uv.outputs[0], tex1.inputs[0])

	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])

	material.node_tree.links.new(mapping1.outputs[0], tex2.inputs[0])

	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[1])

	material.node_tree.links.new(tex_coords.outputs[4], mapping2.inputs[0])
	material.node_tree.links.new(tex_coords.outputs[4], mapping3.inputs[0])

	material.node_tree.links.new(mapping2.outputs[0], tex3.inputs[0])

	material.node_tree.links.new(tex3.outputs[0], nodegroup.inputs[2])

	material.node_tree.links.new(mapping3.outputs[0], tex4.inputs[0])

	material.node_tree.links.new(tex4.outputs[0], nodegroup.inputs[3])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])


	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
		tex1.image = bpy.data.images.get(image_name)
		image_name2 = f'{xfbin_mat.texture_groups[0].texture_chunks[1].name}_0'
		tex2.image = bpy.data.images.get(image_name2)
		image_name3 = f'{xfbin_mat.texture_groups[0].texture_chunks[2].name}_0'
		tex3.image = bpy.data.images.get(image_name3)
		image_name4 = f'{xfbin_mat.texture_groups[0].texture_chunks[3].name}_0'
		tex4.image = bpy.data.images.get(image_name4)
		if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')

	return material


def _07_F006(self, mesh, xfbin_mat, mesh_flags, shader_name = '7F006'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/7F006.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]
	texture3: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[2]
	texture4: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[3]
	texture5: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[4]


	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	normal1_node = material.node_tree.nodes.get('Normal1')
	normal1_node.image = bpy.data.images.get(f"{texture2.name}_0")
	normal2_node = material.node_tree.nodes.get('Normal2')
	normal2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		normal1_node.extension = 'EXTEND'
		normal2_node.extension = 'EXTEND'
	
	
	if not normal1_node.image:
		normal1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
		normal2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex3_node = material.node_tree.nodes.get('Tex3')
	tex3_node.image = bpy.data.images.get(f"{texture3.name}_0")

	#set texture wrap mode
	if texture3.wrapModeS == '3':
		tex3_node.extension = 'EXTEND'

	if not tex3_node.image:
		tex3_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	#set to non-color
	tex3_node.image.colorspace_settings.name = 'Non-Color'
	

	tex4_node = material.node_tree.nodes.get('Tex4')
	tex4_node.image = bpy.data.images.get(f"{texture4.name}_0")

	#set texture wrap mode
	if texture4.wrapModeS == '3':
		tex4_node.extension = 'EXTEND'
	
	#set filtering to cubic
	tex4_node.interpolation = 'Cubic'

	if not tex4_node.image:
		tex4_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex5_node = material.node_tree.nodes.get('Tex5')
	tex5_node.image = bpy.data.images.get(f"{texture5.name}_0")

	#set texture wrap mode
	if texture5.wrapModeS == '3':
		tex5_node.extension = 'EXTEND'

	if not tex5_node.image:
		tex5_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	#set to non color
	tex5_node.image.colorspace_settings.name = 'Non-Color'
	
	#find the shader node
	shader_node = material.node_tree.nodes.get(f'{shader_name}')

	#set uvOffset and uvScale
	shader_node.inputs['uvOffset0 X'].default_value = mat_data.uvOffset0[0]
	shader_node.inputs['uvOffset0 Y'].default_value = mat_data.uvOffset0[1]
	shader_node.inputs['uvOffset0 Z'].default_value = mat_data.uvOffset0[2]
	shader_node.inputs['uvOffset0 W'].default_value = mat_data.uvOffset0[3]

	shader_node.inputs['uvOffset1 X'].default_value = mat_data.uvOffset1[0]
	shader_node.inputs['uvOffset1 Y'].default_value = mat_data.uvOffset1[1]
	shader_node.inputs['uvOffset1 Z'].default_value = mat_data.uvOffset1[2]
	shader_node.inputs['uvOffset1 W'].default_value = mat_data.uvOffset1[3]

	#set shader params
	for prop in mesh.materials[0].properties:
		if prop.name == "NU_waterParam":
			shader_node.inputs['waterParam X'].default_value = prop.values[0]
			shader_node.inputs['waterParam Y'].default_value = prop.values[1]
			shader_node.inputs['waterParam Z'].default_value = prop.values[2]
			shader_node.inputs['waterParam W'].default_value = prop.values[3]
		elif prop.name == "NU_waterColor":
			shader_node.inputs["waterColor"].default_value = (prop.values[0], prop.values[1], prop.values[2], prop.values[3])
			shader_node.inputs["waterAlpha"].default_value = prop.values[3]

	#set scene framerate to 30
	bpy.context.scene.render.fps = 30
	#set scene frame end to 30
	bpy.context.scene.frame_end = 30
	#play the animation
	bpy.ops.screen.animation_play()
	

	return material


def _07_F00B(self, mesh, xfbin_mat, mesh_flags, shader_name = '7F00B'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.get(f'{shader_name}_Material')
	if not material:
		material_path = f'{path}/7F00B.blend'
		with bpy.data.libraries.load(material_path, link = False) as (data_from, data_to):
			data_to.materials = [f'{shader_name}_Material']
		material = data_to.materials[0]

	material = material.copy()
	material.name = xfbin_mat.name
	
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	
	mat_data: XfbinMaterialPropertyGroup = material.xfbin_material_data
	texture: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[0]
	texture2: XfbinMaterialTexturesPropertyGroup = mat_data.NUTextures[1]



	#find Tex1 node
	tex1_node = material.node_tree.nodes.get('Tex1')
	tex1_node.image = bpy.data.images.get(f"{texture.name}_0")

	#set texture wrap mode
	if texture.wrapModeS == '3':
		tex1_node.extension = 'EXTEND'
	
	if not tex1_node.image:
		tex1_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	
	tex2_node = material.node_tree.nodes.get('Tex2')
	tex2_node.image = bpy.data.images.get(f"{texture2.name}_0")

	#set texture wrap mode
	if texture2.wrapModeS == '3':
		tex2_node.extension = 'EXTEND'

	if not tex2_node.image:
		tex2_node.image = bpy.data.images.load(f"{path}/error64x64.dds")
	

	#shader node
	shader_node = material.node_tree.nodes.get(f'{shader_name}')


	#set shader params
	for prop in mesh.materials[0].properties:
		if prop.name == "NU_waterParam":
			shader_node.inputs['waterParam X'].default_value = prop.values[0]
			shader_node.inputs['waterParam Y'].default_value = prop.values[1]
			shader_node.inputs['waterParam Z'].default_value = prop.values[2]
			shader_node.inputs['waterParam W'].default_value = prop.values[3]
		elif prop.name == "NU_waterColor":
			shader_node.inputs["waterColor"].default_value = (prop.values[0], prop.values[1], prop.values[2], prop.values[3])
			shader_node.inputs["waterAlpha"].default_value = prop.values[3]
	

	return material


def default_mat(self, mesh, xfbin_mat, mesh_flags, nodegrp = 'Default'):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(f'{xfbin_mat.name}')
	material.xfbin_material_data.init_data(xfbin_mat, mesh, mesh_flags)
	if not xfbin_mat.texture_groups:
		return material

	meshmat = mesh.materials[0]
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	#material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	#remove node groups with the same name to prevent issues with min and max values of some nodes
	if bpy.data.node_groups.get(nodegrp):
		bpy.data.node_groups.remove(bpy.data.node_groups.get(nodegrp))

	#clear nodes
	material.node_tree.nodes.clear()

	#add nodes
	#uv node
	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = Vector((-799.7762451171875, -745.7254028320312))
	uv1.uv_map = 'UV_0'
	
	#mapping node
	mapping1 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping1.location = Vector((-523.52191162109375, -561.20159912109375))
	mapping1.vector_type = 'TEXTURE'

	#texture node
	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = Vector((-323.52191162109375, -261.20159912109375))
	tex1.interpolation = 'Cubic'

	#vertex color node
	vcol = material.node_tree.nodes.new('ShaderNodeVertexColor')
	vcol.location = Vector((-799.7762451171875, -745.7254028320312))

	#mix node
	mix = material.node_tree.nodes.new('ShaderNodeMixRGB')
	mix.location = Vector((-99.7762451171875, -745.7254028320312))
	mix.blend_type = 'MULTIPLY'
	mix.inputs[0].default_value = 1.0

	#principled node
	principled = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
	principled.location = Vector((910.05126953125, -49.9783935546875))

	#output node
	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = Vector((910.05126953125, -49.9783935546875))

	#links
	material.node_tree.links.new(uv1.outputs[0], mapping1.inputs[0])
	material.node_tree.links.new(mapping1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], mix.inputs[1])
	material.node_tree.links.new(tex1.outputs[1], principled.inputs[21])
	material.node_tree.links.new(vcol.outputs[0], mix.inputs[2])
	material.node_tree.links.new(mix.outputs[0], principled.inputs[0])
	material.node_tree.links.new(principled.outputs[0], output.inputs[0])

	#set texture
	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
		tex1.image = bpy.data.images.get(image_name)

	if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')

	return material
	

def F001(self, meshmat, xfbin_mat, matname, mesh, nodegrp = 'F001'):
	bpy.context.scene.view_settings.view_transform = 'Standard'
	bpy.context.scene.render.engine = 'BLENDER_EEVEE'
	bpy.context.scene.eevee.use_bloom = True

	if bpy.data.materials.get("Outline Shader"):
		material = bpy.data.materials.get("Outline Shader")
	else:

		material = bpy.data.materials.new("Outline Shader")
		material.use_nodes = True

		# Alpha Mode
		material.blend_method = 'CLIP'
		#material.shadow_method = 'NONE'
		
		# Culling Mode
		material.use_backface_culling = True

		#Remove Unnecessary nodes
		material.node_tree.nodes.remove(material.node_tree.nodes['Principled BSDF'])

		#create a node group
		nodegroup = material.node_tree.nodes.new('ShaderNodeGroup')
		nodegroup.node_tree = bpy.data.node_groups.new("F001", 'ShaderNodeTree')
		nodegroup.location = (0, 0)

		group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
		group_input.location = (-1200, 0)
		
		nodegroup.node_tree.inputs.new('NodeSocketColor', 'Outline Color')
		nodegroup.node_tree.inputs.new('NodeSocketFloat', 'Outline Glow')

		emission = nodegroup.node_tree.nodes.new('ShaderNodeEmission')
		emission.location = (-1000, 0)
		emission.inputs[0].default_value = (0, 0, 0, 1)

		transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
		transparent.location = (-1000, -200)

		geometry = nodegroup.node_tree.nodes.new('ShaderNodeNewGeometry')
		geometry.location = (-1000, -400)

		mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
		mix_shader.location = (-600, -200)

		group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')

		#Link nodes
		nodegroup.node_tree.links.new(group_input.outputs[0], emission.inputs[0])
		nodegroup.node_tree.links.new(group_input.outputs[1], emission.inputs[1])
		nodegroup.node_tree.links.new(emission.outputs[0], mix_shader.inputs[1])
		nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[2])
		nodegroup.node_tree.links.new(geometry.outputs[6], mix_shader.inputs[0])
		nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

		#set default values
		nodegroup.inputs[0].default_value = (0, 0, 0, 1)
		nodegroup.inputs[1].default_value = 0

		#set node group as material output
		material.node_tree.links.new(nodegroup.outputs[0], material.node_tree.nodes['Material Output'].inputs[0])
	
	#try to get geometry nodes group
	if bpy.data.node_groups.get("F001Geometry"):
		gm = mesh.modifiers.new("Outline", 'NODES')
		gm.node_group = bpy.data.node_groups["F001Geometry"]
		#gm.node_group.inputs[2] = bpy.data.materials.get("Outline Shader")
		gm["Input_2"] = bpy.data.materials["Outline Shader"]

	else:
		gn = F001Geometry(mesh)
		gm = mesh.modifiers.new("Outline", 'NODES')
		gm.node_group = gn
		gm["Input_2"] = bpy.data.materials["Outline Shader"]

	return material



def collision_mat(name):
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	material.blend_method = 'BLEND'
	#material.shadow_method = 'NONE'
	material.use_backface_culling = True
	material.node_tree.nodes.clear()

	#Nodes
	transparent = material.node_tree.nodes.new('ShaderNodeBsdfTransparent')

	mix_shader = material.node_tree.nodes.new('ShaderNodeMixShader')

	wireframe = material.node_tree.nodes.new('ShaderNodeWireframe')

	mapping = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping.inputs[2].default_value[1] = 0.785398
	mapping.inputs[3].default_value[1] = -1.0
	mapping.inputs[3].default_value[2] = 1.0

	
	coordinates = material.node_tree.nodes.new('ShaderNodeTexCoord')
	vectormath = material.node_tree.nodes.new('ShaderNodeVectorMath')
	vectormath.operation = 'MULTIPLY'

	value = material.node_tree.nodes.new('ShaderNodeValue')
	value.outputs[0].default_value = 0.01

	rgbnode = material.node_tree.nodes.new('ShaderNodeRGB')
	rgbnode.outputs[0].default_value = (0, 0, 0, 0)

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')

	#Link nodes
	material.node_tree.links.new(coordinates.outputs[4], mapping.inputs[0])
	material.node_tree.links.new(mapping.outputs[0], vectormath.inputs[0])
	material.node_tree.links.new(value.outputs[0], vectormath.inputs[1])
	material.node_tree.links.new(vectormath.outputs[0], wireframe.inputs[0])
	material.node_tree.links.new(wireframe.outputs[0], mix_shader.inputs[0])
	material.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])
	material.node_tree.links.new(rgbnode.outputs[0], mix_shader.inputs[2])
	material.node_tree.links.new(mix_shader.outputs[0], output.inputs[0])

	return material


#Geometry Nodes

def F001Geometry(mesh):
	GeometryNode = bpy.data.node_groups.new('F001Geometry', 'GeometryNodeTree')

	GroupInput = GeometryNode.nodes.new('NodeGroupInput')
	GroupInput.location = (-200, 0)

	GeometryNode.inputs.new('NodeSocketGeometry', 'Geometry')
	GeometryNode.inputs.new('NodeSocketGeometry', 'Outline Scale')

	GeometryToInstance = GeometryNode.nodes.new('GeometryNodeGeometryToInstance')
	GeometryToInstance.location = (0, 0)

	MergeByDistance = GeometryNode.nodes.new('GeometryNodeMergeByDistance')
	MergeByDistance.location = (0, 100)
	MergeByDistance.inputs[2].default_value = 0.00001

	Normal = GeometryNode.nodes.new('GeometryNodeInputNormal')
	Normal.location = (-200, 200)

	VectorMath = GeometryNode.nodes.new('ShaderNodeVectorMath')
	VectorMath.operation = 'MULTIPLY'
	VectorMath.inputs[1].default_value = (0.001, 0.001, 0.001)
	VectorMath.location = (-100, 200)

	VectorMath2 = GeometryNode.nodes.new('ShaderNodeVectorMath')
	VectorMath2.operation = 'SCALE'
	VectorMath2.inputs[1].default_value = (0.2, 0.2, 0.2)
	VectorMath2.location = (0, 200)

	SetPosition = GeometryNode.nodes.new('GeometryNodeSetPosition')
	SetPosition.location = (100, 100)
	
	FlipFaces = GeometryNode.nodes.new('GeometryNodeFlipFaces')
	FlipFaces.location = (200, 100)

	SetMaterial = GeometryNode.nodes.new('GeometryNodeSetMaterial')
	SetMaterial.location = (300, 100)
	SetMaterial.inputs[2].default_value = bpy.data.materials['Outline Shader']

	JoinGeometry = GeometryNode.nodes.new('GeometryNodeJoinGeometry')
	JoinGeometry.location = (400, 100)

	GroupOutput = GeometryNode.nodes.new('NodeGroupOutput')
	GroupOutput.location = (500, 100)

	#Link nodes
	GeometryNode.links.new(GroupInput.outputs[0], GeometryToInstance.inputs[0])
	GeometryNode.links.new(GroupInput.outputs[0], MergeByDistance.inputs[0])
	GeometryNode.links.new(GroupInput.outputs[1], VectorMath2.inputs[1])
	#GeometryNode.links.new(GroupInput.outputs[2], SetMaterial.inputs[2])
	GeometryNode.links.new(MergeByDistance.outputs[0], SetPosition.inputs[0])
	GeometryNode.links.new(GeometryToInstance.outputs[0], JoinGeometry.inputs[0])
	GeometryNode.links.new(Normal.outputs[0], VectorMath.inputs[0])
	GeometryNode.links.new(VectorMath.outputs[0], VectorMath2.inputs[0])
	GeometryNode.links.new(VectorMath2.outputs[0], SetPosition.inputs[3])
	GeometryNode.links.new(SetPosition.outputs[0], FlipFaces.inputs[0])
	GeometryNode.links.new(FlipFaces.outputs[0], SetMaterial.inputs[0])
	GeometryNode.links.new(SetMaterial.outputs[0], JoinGeometry.inputs[0])
	GeometryNode.links.new(JoinGeometry.outputs[0], GroupOutput.inputs[0])

	'''#Assign node group to mesh
	mesh.geometry_nodes = GeometryNode'''


'''shaders_dict = {
				'00 01 F0 0D': _05_F00D,
				'00 07 F0 02': _07_F002,
				'00 07 F0 10': _07_F010,
				'00 03 F0 10': _07_F010,
				'00 07 F0 0D': _07_F00D,
				'00 01 F8 01': _01_F8_01,
				'00 01 F8 02': _01_F8_01,
				'00 02 00 01': _01_F8_01,
				'00 01 F1 30': _01_F1_30,
				'00 00 F0 01': F001,
				'00 19 F0 0F': _19_F0_0F,
				'00 01 F8 00': _01_F8_00,
				'00 01 F8 11': _01_F8_00,
				'default' : default_mat}'''

shaders_dict = {'00 00 F0 00': F00A,
				'00 00 F0 0A': F00A,
				'00 01 F0 0A': F00A,
				'00 06 F0 0A': F00A,
				'00 00 F1 0A': F00A,
				'00 02 F0 0A': _02_F00A,
				'00 02 F0 00': _02_F00A,
				'00 02 F1 0A': _02_F00A,
				'00 16 F0 0A': _02_F00A,
				'00 01 F0 02': _01_F002,
				'00 01 E1 02': _01_F002,
				'00 01 F8 01': _01_F801,
				'00 01 F1 30': _01_F130,
				'00 03 F0 02': _03_F002,
				'00 01 F0 03': _01_F003,
				'00 01 F1 03': _01_F003,
				'00 05 F0 03': _01_F003,
				'00 05 F1 03': _01_F003,
				'00 01 F0 08': _01_F008,
				'00 03 F0 08': _03_F008,
				'00 05 F0 02': _05_F002,
				'00 05 F0 0D': _05_F00D,
				'00 05 F1 0D': _05_F00D,
				'00 01 F1 0D': _05_F00D,
				'00 01 F0 0D': _05_F00D,
				'00 01 F8 06': _05_F00D,
				"00 19 F0 02": _19_F002,
				"00 20 F0 00": _20_F000,
				'00 01 F0 0F': _01_F00F,
				'00 03 F0 0F': _03_F00F,
				'00 07 F0 02': _07_F002,
				'00 07 F0 06': _07_F006,
				'00 07 F0 0B': _07_F00B,
				'00 00 E0 02': E002,
				'default' : default_mat}