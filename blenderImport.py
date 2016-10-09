#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import struct
import random

from collections import OrderedDict
from ctypes import c_short

#path = 'f:/VertMesh/'
path = 'D:/DEVEL_SOFT_L2/umodelGUI/UmodelExport/BG_EffectMeshes/VertMesh/'

def GetBit(val, num):
	return val >> num & 1 > 0


def swapU32(i):
	return struct.unpack('<I', struct.pack('>I', i))[0]


def swap32(i):
	return struct.unpack('<i', struct.pack('>i', i))[0]


def swapU16(i):
	return struct.unpack('<H', struct.pack('>H', i))[0]


def swap16(i):
	return struct.unpack('<h', struct.pack('>h', i))[0]


def readUInt16(f):
	return swapU16(struct.unpack('>H', f.read(2))[0])


def readInt16(f):
	return swap16(struct.unpack('>h', f.read(2))[0])


def readUInt32(f):
	return swapU32(struct.unpack('>I', f.read(4))[0])


def readInt32(f):
	return swap32(struct.unpack('>i', f.read(4))[0])


def readRawByte(f, i):
	return struct.unpack('>B', f.read(i))[0]


def readRawByte2(f, i):
	return f.read(i)

def MakeMaterial(name):
    mat = bpy.data.materials.new(name)
    mat.diffuse_shader = 'MINNAERT'
    mat.diffuse_color = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
    mat.darkness = 0.8
    return mat

class unreal_tri:

	def read(self, f):
		self.mVertex = (readUInt16(f), readUInt16(f), readUInt16(f))

		self.mType = readRawByte(f, 1)
		self.mColor = readRawByte(f, 1)
		self.mTex = [[], [], []]
		self.mTex[0].append(readRawByte(f, 1))
		self.mTex[0].append(readRawByte(f, 1))
		self.mTex[1].append(readRawByte(f, 1))
		self.mTex[1].append(readRawByte(f, 1))
		self.mTex[2].append(readRawByte(f, 1))
		self.mTex[2].append(readRawByte(f, 1))

		self.mTextureNum = readRawByte(f, 1)
		self.mFlags = readRawByte(f, 1)

	def __init__(self, f):
		self.read(f)


def getVector(unreal_vertex):

	px = unreal_vertex & 0x7ff
	py = unreal_vertex >> 11 & 0x7ff
	pz = unreal_vertex >> 22 & 0x3ff

	x = float()
	y = float()
	z = float()

	if GetBit(px, 10):
		x = c_short(0xF800 | unreal_vertex & 0x7ff).value / 8.0
	else:

		x = (unreal_vertex & 0x7ff) / 8.0

	if GetBit(py, 10):
		y = c_short(0xF800 | unreal_vertex >> 11 & 0x7ff).value / 8.0
	else:

		y = (unreal_vertex >> 11 & 0x7ff) / 8.0

	if GetBit(pz, 9):
		z = c_short(0xFC00 | unreal_vertex >> 22 & 0x3ff).value / 4.0
	else:

		z = (unreal_vertex >> 22 & 0x3ff) / 4.0

	return (x, y, z)


flist = os.listdir(path)
print (path)
nlist = []
for i in flist:
	if i[-2:] == '3d':
		nlist.append(i[0:-5])

del flist
nlist = list(OrderedDict.fromkeys(nlist))

import bpy
from mathutils import Vector, Matrix

for file_3d in nlist:
	fd3d = open(path + file_3d + '_d.3d', 'rb')

	NumPolygons = readUInt16(fd3d)
	NumVertices = readUInt16(fd3d)
	BogusRot = readUInt16(fd3d)
	BogusFrame = readUInt16(fd3d)

	BogusNormX = readUInt32(fd3d)
	BogusNormY = readUInt32(fd3d)
	BogusNormZ = readUInt32(fd3d)
	FixScale = readUInt32(fd3d)
	UnUsed = readRawByte2(fd3d, 12)
	Unknown = readRawByte2(fd3d, 12)

	faces = []
	uv = []
	temp_tex_num = []
	tex_num = 0
	color = []


	for noused in range(0, NumPolygons):
		tri = unreal_tri(fd3d)
		faces.append(tri.mVertex)
		uv.append((tri.mTex[0][0] / 255, tri.mTex[0][1] / 255))
		uv.append((tri.mTex[1][0] / 255, tri.mTex[1][1] / 255))
		uv.append((tri.mTex[2][0] / 255, tri.mTex[2][1] / 255))

		temp_tex_num.append(tri.mTextureNum)
		color.append(tri.mColor)

		del tri

	tex_num = max(temp_tex_num) + 1

	fa3d = open(path + file_3d + '_a.3d', 'rb')

	verts_list = []

	if file_3d != '':

		me = bpy.data.meshes.new(file_3d)
		ob = bpy.data.objects.new(file_3d, me)

		scn = bpy.context.scene
		scn.objects.link(ob)
		scn.objects.active = ob
		ob.select = True

		unreal_vertex = 0
		num_of_frame = readUInt16(fa3d)
		frame_size = readUInt16(fa3d)

		for s in range(0, NumVertices):
			unreal_vertex = readUInt32(fa3d)
			verts_list.append(getVector(unreal_vertex))

		me.from_pydata(verts_list, [], faces)
		me.update(calc_edges=True)

		uv_lay = []
		uv_tex = me.uv_textures.new('UV_Scheme')
		for i_uv in range(0, tex_num):
			uv_lay.append([])

		for i in range(0, len(temp_tex_num)):
			for vector_count in range(0, 3):
				me.uv_layers[0].data[i * 3 + vector_count].uv = (uv[i * 3 + vector_count][0], 1 - uv[i * 3 + vector_count][1])  # coord
				uv_lay[temp_tex_num[i]].append( faces[i][vector_count] )
		obj = bpy.context.object
		for i_uv in range(0, tex_num):
			obj.vertex_groups.new('MyVertexGroup'+str(i_uv)).add(uv_lay[i_uv], 1.0, 'ADD')
			bpy.ops.object.vertex_group_set_active(group='MyVertexGroup'+str(i_uv))
			bpy.ops.object.material_slot_add()
			obj.material_slots[obj.material_slots.__len__() - 1].material = MakeMaterial('NewMat')
			bpy.ops.object.editmode_toggle()
			bpy.ops.mesh.select_all(action='DESELECT')
			bpy.ops.object.vertex_group_select()
			bpy.ops.object.material_slot_assign()
			bpy.ops.object.editmode_toggle()  # Toggle to object mode
			
		ob.select = True
		bpy.ops.object.shape_key_add(from_mix=False)
		basis = ob.active_shape_key

		verts_list = []

		for n in range(1, num_of_frame):
			bpy.ops.object.shape_key_add(from_mix=False)
			shkey = ob.active_shape_key
			shkey.name = 'key_' + str(n)
			shkey.value = 1.0

			for s in range(0, NumVertices):
				unreal_vertex = readUInt32(fa3d)
				v = getVector(unreal_vertex)
				verts_list.append(v)
				me.vertices[s].co = Vector(v)

			me.update(calc_edges=True)

		scn.objects.active = ob
		bpy.data.objects[file_3d].show_only_shape_key = True
		bpy.context.object.active_shape_key_index = 0
		del uv_lay

		print ( path + file_3d + '.blend' )

		bpy.ops.wm.save_as_mainfile(filepath=path + file_3d + '.blend')

	del faces
	del uv
	del verts_list
	del temp_tex_num

	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_by_type(type='MESH')
	bpy.ops.object.delete(use_global=False)
	for item in bpy.data.meshes:
		bpy.data.meshes.remove(item)

	fa3d.close()
	fd3d.close()


			