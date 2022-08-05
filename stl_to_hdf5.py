from stl import mesh
import numpy as np
import h5py
import stltovoxel
import argparse
import os

def file_choices(parser, choices, fname):
    filename, ext = os.path.splitext(fname)
    if ext == '' or ext.lower() not in choices:
        if len(choices) == 1:
            parser.error('%s doesn\'t end with %s' % (fname, choices))
        else:
            parser.error('%s doesn\'t end with one of %s' % (fname, choices))
    return fname

parser = argparse.ArgumentParser()
parser.add_argument('input', nargs='+', type=lambda s: file_choices(parser, ('.stl'), s), help='Input STL files')
parser.add_argument("-r", "--res", help="dx_dy_dz in mm", default=1, type=float)
parser.add_argument('-n', '--name', help='name of h5 file', default='model')


args = parser.parse_args()

files = args.input
meshes = []
for input_file_path in files:
    mesh_obj = mesh.Mesh.from_file(input_file_path)
    org_mesh = np.hstack((mesh_obj.v0[:, np.newaxis], mesh_obj.v1[:, np.newaxis], mesh_obj.v2[:, np.newaxis]))
    meshes.append(np.round(org_mesh))

mesh_min = meshes[0].min(axis=(0, 1))
mesh_max = meshes[0].max(axis=(0, 1))

#print(mesh_min)
#print(mesh_max)
for mesh in meshes[1:]:    
    mesh_min = np.minimum(mesh_min, mesh.min(axis=(0, 1)))
    mesh_max = np.maximum(mesh_max, mesh.max(axis=(0, 1)))
    #print(mesh_min)
    #print(mesh_max)

bounding_box = mesh_max - mesh_min
#print('box:',bounding_box)

resolution = int(round(bounding_box[2]/args.res))
#print('resolution:', resolution)
if isinstance(resolution, int):
    resolution = resolution * bounding_box / bounding_box[2]
else:
    resolution = np.array(resolution)

scale = (resolution - 1) / bounding_box
new_resolution = np.floor(resolution).astype(int) + 1

vol = np.zeros(new_resolution[::-1], dtype=np.int8)
vol, scale, shift = stltovoxel.convert_meshes(meshes, resolution, parallel=False)
vol = np.array(vol.T, dtype=np.int16) - 1

hdf5file = args.name + '.h5'
with h5py.File(hdf5file, 'w') as fout:
    fout.attrs['dx_dy_dz'] = tuple([args.res/1000, ]*3)#dx_dy_dz
    fout.create_dataset('data', data=vol)

print("")
print('Created file', '"'+args.name + '.h5"')
print('Voxelized files:', files)
print("dx_dy_dz =",tuple([args.res/1000, ]*3))
print("Material ranges:", np.min(vol), 'to', np.max(vol))