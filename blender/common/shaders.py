import bpy, os
from mathutils import Vector
from bpy.types import NodeSocket, Node, NodeTree, NodeCustomGroup
path = os.path.dirname(os.path.realpath(__file__))

#Materials
def F00A(self, meshmat, xfbin_mat, matname, mesh, nodegrp = 'F00A'):
	
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	mat_format = xfbin_mat.flags

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
	nodegroup.location = (330, 41)
	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Basic Cel-shader setup
	diffuse_bsdf = nodegroup.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
	diffuse_bsdf.location = (-393, 105)

	shader_rgb = nodegroup.node_tree.nodes.new('ShaderNodeShaderToRGB')
	shader_rgb.location = (-193, 156)

	math_greater = nodegroup.node_tree.nodes.new('ShaderNodeMath')
	math_greater.location = (2, 175)
	math_greater.operation = 'GREATER_THAN'
	math_greater.inputs[1].default_value = 0.15

	lighten = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	lighten.location = (192, 134)
	lighten.blend_type = 'LIGHTEN'
	lighten.inputs[0].default_value = 1

	multiply = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply.location = (407, 118)
	multiply.blend_type = 'MULTIPLY'
	multiply.inputs[0].default_value = 1

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-126, -140)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha')

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (638, 74)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	uvmap = material.node_tree.nodes.new('ShaderNodeUVMap')
	uvmap.location = (-270, -23)

	mapping = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping.location = (-170, -23)
	if xfbin_mat.UV0:
		mapping.inputs[1].default_value[0] = xfbin_mat.UV0[0]
		mapping.inputs[1].default_value[1] = xfbin_mat.UV0[1]
		mapping.inputs[3].default_value[0] = xfbin_mat.UV0[2]
		mapping.inputs[3].default_value[1] = xfbin_mat.UV0[3]

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (-27, -23)
	tex1.name = 'F00A TEX'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (603, 85)

	#Link nodes
	nodegroup.node_tree.links.new(diffuse_bsdf.outputs['BSDF'], shader_rgb.inputs['Shader'])

	nodegroup.node_tree.links.new(shader_rgb.outputs['Color'], math_greater.inputs[0])

	nodegroup.node_tree.links.new(math_greater.outputs[0], lighten.inputs[1])

	nodegroup.node_tree.links.new(lighten.outputs[0], multiply.inputs[1])

	nodegroup.node_tree.links.new(multiply.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], multiply.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs['Alpha'], mix_shader.inputs[0])

	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs['Texture'])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(uvmap.outputs[0], mapping.inputs[0])
	material.node_tree.links.new(mapping.outputs[0], tex1.inputs[0])


	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])
	
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

def _02_F00A(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '02F00A'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False

	mat_format = xfbin_mat.flags
	#Remove Unnecessary nodes
	material.node_tree.nodes.clear()

	#remove node groups with the same name to prevent issues with min and max values of some nodes
	#for node in bpy.data.node_groups:
	if bpy.data.node_groups.get(nodegrp):
		bpy.data.node_groups.remove(bpy.data.node_groups.get(nodegrp))

	#Create a new node tree to be used later
	nodetree = bpy.data.node_groups.new(nodegrp, 'ShaderNodeTree')

	#Create a node group to organize nodes and inputs
	nodegroup = material.node_tree.nodes.new('ShaderNodeGroup')
	nodegroup.name = nodegrp
	nodegroup.location = (330, 41)
	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Basic Cel-shader setup
	diffuse_bsdf = nodegroup.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
	diffuse_bsdf.location = (-393, 105)

	shader_rgb = nodegroup.node_tree.nodes.new('ShaderNodeShaderToRGB')
	shader_rgb.location = (-193, 156)

	math_greater = nodegroup.node_tree.nodes.new('ShaderNodeMath')
	math_greater.location = (2, 175)
	math_greater.operation = 'GREATER_THAN'
	math_greater.inputs[1].default_value = 0.15

	lighten = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	lighten.location = (192, 134)
	lighten.blend_type = 'LIGHTEN'
	lighten.inputs[0].default_value = 1

	multiply1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply1.location = (407, 118)
	multiply1.blend_type = 'MULTIPLY'
	multiply1.inputs[0].default_value = 1

	mix1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix1.location = (407, 158)
	mix1.blend_type = 'MIX'
	mix1.inputs[0].default_value = 1

	#This will be used for texture 2 visibility
	mix2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix2.location = (407, 0)
	mix2.blend_type = 'MIX'
	mix2.inputs[1].default_value = (0, 0, 0, 1)

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-126, -140)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Texture1')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Texture2')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha1')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha2')
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Texture2 Visibility')
	bpy.data.node_groups[nodegroup.name].inputs[4].min_value = 0.0
	bpy.data.node_groups[nodegroup.name].inputs[4].max_value = 1.0

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (638, 74)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-77, -23)
	uv1.uv_map = 'UV_0'

	mapping1 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping1.location = (-77, -43)
	mapping1.name = 'UV_0_Mapping'
	
	mapping2 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping2.location = (-77, -63)
	mapping2.name = 'UV_1_Mapping'

	if xfbin_mat.UV0:
		mapping1.inputs[1].default_value[0] = xfbin_mat.UV0[0]
		mapping1.inputs[1].default_value[1] = xfbin_mat.UV0[1]
		mapping1.inputs[3].default_value[0] = xfbin_mat.UV0[2]
		mapping1.inputs[3].default_value[1] = xfbin_mat.UV0[3]
	if xfbin_mat.UV1:
		mapping2.inputs[1].default_value[0] = xfbin_mat.UV1[0]
		mapping2.inputs[1].default_value[1] = xfbin_mat.UV1[0]
		mapping2.inputs[3].default_value[0] = xfbin_mat.UV1[0]
		mapping2.inputs[3].default_value[1] = xfbin_mat.UV1[0]
	if xfbin_mat.BlendRate:
		nodegroup.inputs[4].default_value = xfbin_mat.BlendRate


	uv2 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv2.location = (-77, -23)
	uv2.uv_map = 'UV_1'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (-27, -23)
	tex1.name = 'Texture1'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (-27, -43)
	tex2.name = 'Texture2'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (603, 85)

	#Link nodes
	nodegroup.node_tree.links.new(diffuse_bsdf.outputs['BSDF'], shader_rgb.inputs['Shader'])

	nodegroup.node_tree.links.new(shader_rgb.outputs['Color'], math_greater.inputs[0])

	nodegroup.node_tree.links.new(math_greater.outputs[0], lighten.inputs[1])

	nodegroup.node_tree.links.new(lighten.outputs[0], multiply1.inputs[1])

	nodegroup.node_tree.links.new(mix1.outputs[0], multiply1.inputs[2])

	nodegroup.node_tree.links.new(group_input.outputs[0], mix1.inputs[1])

	nodegroup.node_tree.links.new(group_input.outputs[1], mix1.inputs[2])

	nodegroup.node_tree.links.new(group_input.outputs[2], mix_shader.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[3], mix2.inputs[2])

	nodegroup.node_tree.links.new(group_input.outputs[4], mix2.inputs[0])

	nodegroup.node_tree.links.new(mix2.outputs[0], mix1.inputs[0])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(multiply1.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	material.node_tree.links.new(uv1.outputs[0], mapping1.inputs[0])
	material.node_tree.links.new(mapping1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs['Texture1'])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs['Alpha1'])

	material.node_tree.links.new(uv2.outputs[0], mapping2.inputs[0])
	material.node_tree.links.new(mapping2.outputs[0], tex2.inputs[0])
	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs['Texture2'])
	material.node_tree.links.new(tex2.outputs[1], nodegroup.inputs['Alpha2'])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])
	
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

def _01_F002(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '01F002'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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
	multiply1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply1.location = (256, 131)
	multiply1.blend_type = 'MULTIPLY'
	multiply1.inputs[0].default_value = 1

	emission = nodegroup.node_tree.nodes.new('ShaderNodeEmission')

	multiply2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply2.location = (256, 131)
	multiply2.blend_type = 'MULTIPLY'
	multiply2.inputs[0].default_value = 1

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (264, -261)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (696, -113)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-56, -112)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Light Strength')
	nodegroup.inputs[2].default_value = 2
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Colors')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Alpha')

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (886, 4)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	vcol = material.node_tree.nodes.new('ShaderNodeVertexColor')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-84, -552)
	uv1.uv_map = 'UV_0'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (174, 720)
	tex1.name = 'Diffuse'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (1091, 520)

	#Link nodes
	nodegroup.node_tree.links.new(multiply1.outputs[0], emission.inputs[0])

	nodegroup.node_tree.links.new(emission.outputs[0], mix_shader.inputs[2])
	
	nodegroup.node_tree.links.new(multiply2.outputs[0], mix_shader.inputs[0])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], multiply1.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[1], multiply2.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[2], emission.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[3], multiply1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[4], multiply2.inputs[2])

	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(vcol.outputs[0], nodegroup.inputs[3])
	material.node_tree.links.new(vcol.outputs[1], nodegroup.inputs[4])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

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

def _01_F003(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '01F003'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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

	multiply2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply2.location = (256, 131)
	multiply2.blend_type = 'MULTIPLY'
	multiply2.inputs[0].default_value = 1

	multiply3 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply3.location = (256, 131)
	multiply3.blend_type = 'MULTIPLY'
	multiply3.inputs[0].default_value = 1

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (264, -261)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (696, -113)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-56, -112)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Colors')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Alpha')

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (886, 4)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	vcol = material.node_tree.nodes.new('ShaderNodeVertexColor')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-84, -552)
	uv1.uv_map = 'UV_0'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (174, 720)
	tex1.name = 'Diffuse'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (1091, 520)

	#Link nodes
	nodegroup.node_tree.links.new(diffuse_bsdf.outputs['BSDF'], shader_rgb.inputs['Shader'])

	nodegroup.node_tree.links.new(shader_rgb.outputs['Color'], math_greater.inputs[0])

	nodegroup.node_tree.links.new(math_greater.outputs[0], lighten.inputs[1])

	nodegroup.node_tree.links.new(lighten.outputs[0], multiply1.inputs[1])

	nodegroup.node_tree.links.new(multiply1.outputs[0], multiply2.inputs[1])

	nodegroup.node_tree.links.new(multiply2.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(multiply3.outputs[0], mix_shader.inputs[0])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], multiply1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[1], multiply3.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[2], multiply2.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[3], multiply3.inputs[2])

	material.node_tree.links.new(vcol.outputs[0], nodegroup.inputs[2])
	material.node_tree.links.new(vcol.outputs[1], nodegroup.inputs[3])

	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

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

def _01_F008(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '01F008'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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
	mix1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix1.location = (256, 131)
	mix1.blend_type = 'MIX'
	mix1.inputs[0].default_value = 1

	multiply1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply1.location = (256, 131)
	multiply1.blend_type = 'MULTIPLY'
	multiply1.inputs[0].default_value = 1

	emission = nodegroup.node_tree.nodes.new('ShaderNodeEmission')

	multiply2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply2.location = (256, 131)
	multiply2.blend_type = 'MULTIPLY'
	multiply2.inputs[0].default_value = 1

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (264, -261)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (696, -113)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-56, -112)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Falloff Texture')
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Light Strength')
	nodegroup.inputs[3].default_value = 2
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Light Limit')
	bpy.data.node_groups[nodegroup.name].inputs[4].min_value = 0
	bpy.data.node_groups[nodegroup.name].inputs[4].max_value = 1
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Colors')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Alpha')

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (886, 4)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	vcol = material.node_tree.nodes.new('ShaderNodeVertexColor')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-84, -552)
	uv1.uv_map = 'UV_0'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (174, 720)
	tex1.name = 'Diffuse'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (174, 720)
	tex2.name = 'Falloff'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (1091, 520)

	#Link nodes
	nodegroup.node_tree.links.new(mix1.outputs[0], multiply1.inputs[1])

	nodegroup.node_tree.links.new(multiply1.outputs[0], emission.inputs[0])

	nodegroup.node_tree.links.new(emission.outputs[0], mix_shader.inputs[2])
	
	nodegroup.node_tree.links.new(multiply2.outputs[0], mix_shader.inputs[0])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], mix1.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[1], multiply2.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[2], mix1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[3], emission.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[4], mix1.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[5], multiply1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[6], multiply2.inputs[2])

	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(uv1.outputs[0], tex2.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])
	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[2])

	material.node_tree.links.new(vcol.outputs[0], nodegroup.inputs[5])
	material.node_tree.links.new(vcol.outputs[1], nodegroup.inputs[6])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

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

def _05_F00D(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '05F00D'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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
	math_greater.inputs[1].default_value = 0.06

	lighten = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	lighten.location = (47, 300)
	lighten.blend_type = 'LIGHTEN'
	lighten.inputs[0].default_value = 1
	lighten.inputs[2].default_value = (0.2,0.2,0.2,1)

	multiply1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply1.location = (256, 131)
	multiply1.blend_type = 'MULTIPLY'
	multiply1.inputs[0].default_value = 1

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
	nodegroup.node_tree.inputs.new('NodeSocketColor','Shadow Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha')
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
	tex1.name = 'Diffuse'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (178, 420)
	tex2.name = 'Shadow'

	vcol = material.node_tree.nodes.new('ShaderNodeVertexColor')


	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (1091, 520)

	#Link nodes
	nodegroup.node_tree.links.new(normal.outputs[0], diffuse_bsdf.inputs[2])

	nodegroup.node_tree.links.new(diffuse_bsdf.outputs['BSDF'], shader_rgb.inputs['Shader'])

	nodegroup.node_tree.links.new(shader_rgb.outputs['Color'], math_greater.inputs[0])

	nodegroup.node_tree.links.new(math_greater.outputs[0], lighten.inputs[1])

	nodegroup.node_tree.links.new(lighten.outputs[0], multiply1.inputs[1])

	nodegroup.node_tree.links.new(multiply1.outputs[0], multiply2.inputs[1])

	nodegroup.node_tree.links.new(multiply2.outputs[0], multiply3.inputs[1])

	nodegroup.node_tree.links.new(multiply3.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], multiply1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[1], multiply2.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[2], multiply4.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[3], multiply3.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[4], multiply4.inputs[2])
	nodegroup.node_tree.links.new(multiply4.outputs[0], mix_shader.inputs[0])



	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[2])

	material.node_tree.links.new(uv2.outputs[0], tex2.inputs[0])
	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[1])

	material.node_tree.links.new(vcol.outputs[0], nodegroup.inputs[3])
	material.node_tree.links.new(vcol.outputs[1], nodegroup.inputs[4])



	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

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

def _07_F00D(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '07F00D'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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

def _05_F002(self, meshmat,  xfbin_mat, matname, mesh, nodegrp = '05F002'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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

	multiply1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply1.location = (256, 131)
	multiply1.blend_type = 'MULTIPLY'
	multiply1.inputs[0].default_value = 1

	multiply2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply2.location = (256, 131)
	multiply2.blend_type = 'MULTIPLY'
	multiply2.inputs[0].default_value = 1


	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (264, -261)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (696, -113)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-56, -112)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Colors')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Vertex Alpha')

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (886, 4)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	vcol = material.node_tree.nodes.new('ShaderNodeVertexColor')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-84, -552)
	uv1.uv_map = 'UV_0'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (174, 720)
	tex1.name = 'Diffuse'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (1091, 520)

	#Link nodes
	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], multiply1.inputs[1])

	nodegroup.node_tree.links.new(group_input.outputs[1], multiply2.inputs[1])

	nodegroup.node_tree.links.new(group_input.outputs[2], multiply1.inputs[2])

	nodegroup.node_tree.links.new(group_input.outputs[3], multiply2.inputs[2])

	nodegroup.node_tree.links.new(multiply1.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(multiply2.outputs[0], mix_shader.inputs[0])

	material.node_tree.links.new(vcol.outputs[0], nodegroup.inputs[2])
	material.node_tree.links.new(vcol.outputs[1], nodegroup.inputs[3])

	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

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

def _07_F002(self, meshmat,  xfbin_mat, matname, mesh, nodegrp = '07F002'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True
	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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

	multiply1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply1.location = (256, 131)
	multiply1.blend_type = 'MULTIPLY'
	multiply1.inputs[0].default_value = 1

	multiply2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	multiply2.location = (256, 131)
	multiply2.blend_type = 'MULTIPLY'
	multiply2.inputs[0].default_value = 1


	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (264, -261)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (696, -113)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-56, -112)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Shadow Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Tweak Colors')
	material.node_tree.nodes[nodegrp].inputs['Tweak Colors'].default_value = (1,1,1,1)

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (886, 4)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-84, -552)
	uv1.uv_map = 'UV_0'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (174, 720)
	tex1.name = 'Diffuse'

	uv2 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv2.location = (-84, -552)
	uv2.uv_map = 'UV_1'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (174, 720)
	tex2.name = 'Diffuse'


	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (1091, 520)

	#Link nodes
	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], multiply1.inputs[1])

	nodegroup.node_tree.links.new(group_input.outputs[1], multiply1.inputs[2])

	nodegroup.node_tree.links.new(group_input.outputs[2], mix_shader.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[3], multiply2.inputs[2])

	nodegroup.node_tree.links.new(multiply1.outputs[0], multiply2.inputs[1])

	nodegroup.node_tree.links.new(multiply2.outputs[0], mix_shader.inputs[2])

	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[2])

	material.node_tree.links.new(uv2.outputs[0], tex2.inputs[0])
	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[1])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[0].name}_0'
		tex1.image = bpy.data.images.get(image_name)
		image_name = xfbin_mat.texture_groups[0].texture_chunks[1].name
		tex2.image = bpy.data.images.get(image_name)
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
	material.shadow_method = 'NONE'
	
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

def _01_F00F(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '01F00F'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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
	nodegroup.location = (226, 326)

	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Le Shader
	fresnel = nodegroup.node_tree.nodes.new('ShaderNodeFresnel')
	fresnel.location = (-280, -346)
	fresnel.inputs[0].default_value = 0.9

	mix1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix1.inputs[0].default_value = 0
	mix1.location = (-280, -142)

	mix2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix2.location = (162, -61)

	emission = nodegroup.node_tree.nodes.new('ShaderNodeEmission')
	emission.inputs[1].default_value = 1.35
	emission.location = (399, -24)

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (326, 181)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (619, 96)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-668, 8)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Falloff Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Falloff Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Rim Light')
	nodegroup.inputs[4].default_value = 0.9
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Light Strength')
	nodegroup.inputs[5].default_value = 1.35


	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (862, 84)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (-394, 443)
	tex1.name = 'Diffuse Texture'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (-399, 141)
	tex2.name = 'Falloff Texture'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (772, 331)

	#Link nodes
	nodegroup.node_tree.links.new(mix1.outputs[0], mix2.inputs[2])

	nodegroup.node_tree.links.new(fresnel.outputs[0], mix2.inputs[0])

	nodegroup.node_tree.links.new(mix2.outputs[0], emission.inputs[0])

	nodegroup.node_tree.links.new(emission.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], mix2.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[1], mix_shader.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[2], mix1.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[3], mix1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[4], fresnel.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[5], emission.inputs[1])

	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[2])
	material.node_tree.links.new(tex2.outputs[1], nodegroup.inputs[3])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])
	
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


def _03_F00F(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '03F00F'):

	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
	# Culling Mode
	if meshmat.cullMode == 1028 or meshmat.cullMode == 1029:
		material.use_backface_culling = True
	else:
		material.use_backface_culling = False
	
	mat_format = xfbin_mat.flags
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
	nodegroup.location = (226, 326)

	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Le Shader
	fresnel = nodegroup.node_tree.nodes.new('ShaderNodeFresnel')
	fresnel.location = (-280, -346)
	fresnel.inputs[0].default_value = 0.9

	mix1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix1.location = (-280, -142)

	mix2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix2.inputs[0].default_value = 0
	mix2.location = (162, -61)

	mix3 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mix3.location = (162, -61)

	emission = nodegroup.node_tree.nodes.new('ShaderNodeEmission')
	emission.inputs[1].default_value = 1.35
	emission.location = (399, -24)

	transparent = nodegroup.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.location = (326, 181)

	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = (619, 96)

	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = (-668, 8)
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse2 Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Diffuse2 Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Falloff Texture')
	nodegroup.node_tree.inputs.new('NodeSocketColor','Falloff Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Rim Light')
	nodegroup.inputs[6].default_value = 0.9
	nodegroup.node_tree.inputs.new('NodeSocketFloat','Light Strength')
	nodegroup.inputs[7].default_value = 1.35


	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = (862, 84)
	nodegroup.node_tree.outputs.new('NodeSocketShader','Out')

	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = (-84, -552)
	uv1.uv_map = 'UV_0'

	mapping1 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping1.location = (-84, -552)

	uv2 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv2.location = (-84, -552)
	uv2.uv_map = 'UV_1'

	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = (-394, 443)
	tex1.name = 'Diffuse Texture'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = (-399, 141)
	tex2.name = 'Diffuse2 Texture'

	tex3 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex3.location = (-399, 141)
	tex3.name = 'Falloff Texture'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = (772, 331)

    #Link nodes
	nodegroup.node_tree.links.new(mix1.outputs[0], mix3.inputs[1])

	nodegroup.node_tree.links.new(mix2.outputs[0], mix3.inputs[2])

	nodegroup.node_tree.links.new(fresnel.outputs[0], mix3.inputs[0])

	nodegroup.node_tree.links.new(mix3.outputs[0], emission.inputs[0])

	nodegroup.node_tree.links.new(emission.outputs[0], mix_shader.inputs[2])

	nodegroup.node_tree.links.new(transparent.outputs[0], mix_shader.inputs[1])

	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])

	nodegroup.node_tree.links.new(group_input.outputs[0], mix1.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[1], mix_shader.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[2], mix1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[3], mix1.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[4], mix2.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[5], mix2.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[6], fresnel.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[7], emission.inputs[1])

	material.node_tree.links.new(uv1.outputs[0], tex1.inputs[0])

	material.node_tree.links.new(uv2.outputs[0], tex2.inputs[0])

	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex1.outputs[1], nodegroup.inputs[1])

	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[2])
	material.node_tree.links.new(tex2.outputs[1], nodegroup.inputs[3])

	material.node_tree.links.new(tex3.outputs[0], nodegroup.inputs[4])
	material.node_tree.links.new(tex3.outputs[1], nodegroup.inputs[5])

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


def E002(self, meshmat, xfbin_mat, matname, mesh, nodegrp = 'E002'):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
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
	material.shadow_method = 'NONE'
	
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
	material.shadow_method = 'NONE'
	
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
	material.shadow_method = 'NONE'
	
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
	material.shadow_method = 'NONE'
	
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


def _07_F0_06(self, meshmat, xfbin_mat, matname, mesh, nodegrp = '19F00F'):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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
	nodegroup.location = Vector((376.1145935058594, -6.813720703125))

	#use the node tree we made earlier for our node group
	nodegroup.node_tree = nodetree

	#Le Shader
	group_input = nodegroup.node_tree.nodes.new('NodeGroupInput')
	group_input.location = Vector((-1325.369384765625, 64.7136459350586))
	
	nodegroup.node_tree.inputs.new('NodeSocketColor', 'Normal')
	nodegroup.node_tree.inputs.new('NodeSocketColor', 'Shadow')
	nodegroup.node_tree.inputs.new('NodeSocketColor', 'Water Color')
	nodegroup.node_tree.inputs.new('NodeSocketFloat', 'Alpha')
	nodegroup.node_tree.inputs.new('NodeSocketColor', 'Floor')
	nodegroup.node_tree.inputs.new('NodeSocketFloat', 'Floor Height')
	nodegroup.node_tree.inputs.new('NodeSocketFloat', 'Water Normal Strength')

	group_output = nodegroup.node_tree.nodes.new('NodeGroupOutput')
	group_output.location = Vector((1155.974609375, -39.84018325805664))

	nodegroup.node_tree.outputs.new('NodeSocketShader', 'Shader')
	nodegroup.node_tree.outputs.new('NodeSocketColor', 'Normal')

	#Normal Map
	normal_map = nodegroup.node_tree.nodes.new('ShaderNodeNormalMap')
	normal_map.location = Vector((-781.5745849609375, 453.59375))

	#Glossy BSDF
	glossy_bsdf = nodegroup.node_tree.nodes.new('ShaderNodeBsdfGlossy')
	glossy_bsdf.location = Vector((-298.35662841796875, 384.85284423828125))
	glossy_bsdf.inputs[0].default_value = (0.8, 0.8, 0.8, 1)
	glossy_bsdf.inputs[1].default_value = 0.2

	#Shader to RGB
	shader_to_rgb = nodegroup.node_tree.nodes.new('ShaderNodeShaderToRGB')
	shader_to_rgb.location = Vector((135.53338623046875, 413.5357360839844))

	#Math Add
	math_add = nodegroup.node_tree.nodes.new('ShaderNodeMath')
	math_add.location = Vector((626.6395874023438, 364.9391174316406))
	math_add.operation = 'ADD'
	math_add.inputs[1].default_value = -0.5

	#mixRGB multiply
	mixrgb1 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mixrgb1.location = Vector((-170.1310577392578, -16.47406005859375))
	mixrgb1.blend_type = 'MULTIPLY'
	mixrgb1.inputs[0].default_value = 1

	#mixRGB multiply
	mixrgb2 = nodegroup.node_tree.nodes.new('ShaderNodeMixRGB')
	mixrgb2.location = Vector((147.2736053466797, 198.53411865234375))
	mixrgb2.blend_type = 'MULTIPLY'
	mixrgb2.inputs[0].default_value = 1

	#bump
	bump = nodegroup.node_tree.nodes.new('ShaderNodeBump')
	bump.location = Vector((242.3257293701172, -277.94189453125))

	#vertex color
	vertex_color = nodegroup.node_tree.nodes.new('ShaderNodeVertexColor')
	vertex_color.location = Vector((472.6097106933594, 11.021947860717773))
	
	#mix shader
	mix_shader = nodegroup.node_tree.nodes.new('ShaderNodeMixShader')
	mix_shader.location = Vector((917.1795654296875, 180.4666748046875))

	#links
	nodegroup.node_tree.links.new(group_input.outputs[0], normal_map.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[1], mixrgb2.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[2], mixrgb1.inputs[1])
	nodegroup.node_tree.links.new(group_input.outputs[3], mixrgb1.inputs[0])
	nodegroup.node_tree.links.new(group_input.outputs[4], mixrgb1.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[5], bump.inputs[2])
	nodegroup.node_tree.links.new(group_input.outputs[6], normal_map.inputs[0])

	nodegroup.node_tree.links.new(normal_map.outputs[0], glossy_bsdf.inputs[2])
	nodegroup.node_tree.links.new(glossy_bsdf.outputs[0], shader_to_rgb.inputs[0])
	nodegroup.node_tree.links.new(shader_to_rgb.outputs[0], math_add.inputs[0])
	nodegroup.node_tree.links.new(math_add.outputs[0], mix_shader.inputs[0])
	nodegroup.node_tree.links.new(mixrgb1.outputs[0], mixrgb2.inputs[2])
	nodegroup.node_tree.links.new(mixrgb2.outputs[0], mix_shader.inputs[1])
	nodegroup.node_tree.links.new(vertex_color.outputs[0], mix_shader.inputs[2])
	nodegroup.node_tree.links.new(mix_shader.outputs[0], group_output.inputs[0])
	nodegroup.node_tree.links.new(bump.outputs[0], group_output.inputs[1])

	#set water props
	nodegroup.inputs[2].default_value = Vector(meshmat.properties[0].values)
	nodegroup.inputs[3].default_value = meshmat.properties[0].values[3]
	nodegroup.inputs[6].default_value = meshmat.properties[1].values[2]

	#material nodes
	uv1 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv1.location = Vector((-866.95458984375, 242.65982055664062))
	uv1.uv_map = 'UV_0'

	mapping1 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping1.location = Vector((-613.7636108398438, 369.87762451171875))
	
	tex1 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex1.location = Vector((-354.9815979003906, 571.17236328125))
	tex1.interpolation = 'Cubic'

	uv2 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv2.location = Vector((-594.8995971679688, -40.25141525268555))
	uv2.uv_map = 'UV_1'

	tex2 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex2.location = Vector((-365.3246154785156, 149.91421508789062))
	tex2.interpolation = 'Cubic'

	uv3 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv3.location = Vector((-878.4056396484375, -297.788818359375))
	uv3.uv_map = 'UV_0'

	mapping2 = material.node_tree.nodes.new('ShaderNodeMapping')
	mapping2.location = Vector((-591.8324584960938, -216.53134155273438))

	if xfbin_mat.flags == 0x43:
		mapping1.inputs[3].default_value[0] = xfbin_mat.floats[6]
		mapping1.inputs[3].default_value[1] = xfbin_mat.floats[7]

		mapping2.inputs[3].default_value[0] = xfbin_mat.floats[6]
		mapping2.inputs[3].default_value[1] = xfbin_mat.floats[7]

	tex3 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex3.location = Vector((-323.52191162109375, -261.20159912109375))
	tex3.interpolation = 'Cubic'

	uv4 = material.node_tree.nodes.new('ShaderNodeUVMap')
	uv4.location = Vector((-799.7762451171875, -745.7254028320312))
	uv4.uv_map = 'UV_1'

	tex4 = material.node_tree.nodes.new('ShaderNodeTexImage')
	tex4.location = Vector((-339.1034851074219, -640.7785034179688))
	tex4.interpolation = 'Cubic'

	output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
	output.location = Vector((910.05126953125, -49.9783935546875))

	#links
	material.node_tree.links.new(uv1.outputs[0], mapping1.inputs[0])
	material.node_tree.links.new(mapping1.outputs[0], tex1.inputs[0])
	material.node_tree.links.new(uv2.outputs[0], tex2.inputs[0])
	material.node_tree.links.new(uv3.outputs[0], mapping2.inputs[0])
	material.node_tree.links.new(mapping2.outputs[0], tex3.inputs[0])
	material.node_tree.links.new(uv4.outputs[0], tex4.inputs[0])
	
	material.node_tree.links.new(tex1.outputs[0], nodegroup.inputs[0])
	material.node_tree.links.new(tex2.outputs[0], nodegroup.inputs[1])
	material.node_tree.links.new(tex3.outputs[0], nodegroup.inputs[4])
	material.node_tree.links.new(tex4.outputs[0], nodegroup.inputs[5])

	material.node_tree.links.new(nodegroup.outputs[0], output.inputs[0])

	material.node_tree.links.new(nodegroup.outputs[1], output.inputs[2])


	if xfbin_mat.texture_groups and xfbin_mat.texture_groups[0].texture_chunks:
		image_name = f'{xfbin_mat.texture_groups[0].texture_chunks[1].name}_0'
		tex1.image = bpy.data.images.get(image_name)
		image_name2 = f'{xfbin_mat.texture_groups[0].texture_chunks[2].name}_0'
		tex2.image = bpy.data.images.get(image_name2)
		image_name3 = f'{xfbin_mat.texture_groups[0].texture_chunks[3].name}_0'
		tex3.image = bpy.data.images.get(image_name3)
		image_name4 = f'{xfbin_mat.texture_groups[0].texture_chunks[4].name}_0'
		tex4.image = bpy.data.images.get(image_name4)

	if not tex1.image:
			#load error64x64.dds
			if bpy.data.images.get('error64x64.dds'):
				tex1.image = bpy.data.images.get('error64x64.dds')
			else:
				tex1.image = bpy.data.images.load(f'{path}/error64x64.dds')
	


	return material


def default_mat(self, meshmat, xfbin_mat, material, nodegrp = 'Default'):
	bpy.context.scene.view_settings.view_transform = 'Standard'

	#material = bpy.data.materials.new(matname)
	material.use_nodes = True

	# Alpha Mode
	if meshmat.sourceFactor == 2:
		material.blend_method = 'CLIP'
	elif meshmat.sourceFactor == 1 or meshmat.sourceFactor == 5:
		material.blend_method = 'BLEND'
	material.shadow_method = 'NONE'
	
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
		material.shadow_method = 'NONE'
		
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
	material.shadow_method = 'NONE'
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


shaders_dict = {'00 00 F0 00': F00A, '00 00 F0 0A': F00A, '00 01 F0 0A': F00A, '00 02 F0 0A': _02_F00A, '00 02 F0 00': _02_F00A,
				'00 01 F0 0D': _05_F00D, '00 01 F0 03': _01_F003, '00 05 F0 03': _01_F003, '00 05 F0 02': _05_F002,
				'00 07 F0 02': _07_F002,'00 00 E0 02': E002, '00 07 F0 10': _07_F010, '00 03 F0 10': _07_F010,
				'00 07 F0 0D': _07_F00D, '00 01 F0 02': _01_F002, '00 01 F0 08': _01_F008, '00 01 F0 0F': _01_F00F,
				'00 03 F0 0F': _03_F00F, '00 20 F0 00': _01_F00F,'00 01 F8 01': _01_F8_01, '00 01 F8 02': _01_F8_01,
				'00 02 00 01': _01_F8_01, '00 01 F1 30':_01_F1_30,  '00 05 F0 0D': _05_F00D, '00 00 F0 01': F001,
				'00 19 F0 0F': _19_F0_0F, '00 01 F8 00': _01_F8_00,'00 01 F8 11': _01_F8_00, '00 07 F0 06':_07_F0_06,
				'00 01 F8 06': _05_F00D, 'default' : default_mat}

