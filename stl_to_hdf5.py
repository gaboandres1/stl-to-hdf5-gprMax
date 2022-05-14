import pyvoxsurf
import trimesh
import numpy as np
from glob import glob
import os
import sys
import h5py

try:
    step = float(sys.argv[1])

    files = glob("*/*.stl")
    folders = glob("*/")
    n_materials = len(folders)
    materials = np.arange(1, n_materials+1, 1).astype(np.int16)

    mesh_models = {0:trimesh.load(files[0])}
    volumes = {}
    mesh_min_corner = [np.min(mesh_models[0].vertices[:,0]), np.min(mesh_models[0].vertices[:,1]), np.min(mesh_models[0].vertices[:,2])]
    mesh_max_corner = [np.max(mesh_models[0].vertices[:,0]), np.max(mesh_models[0].vertices[:,1]), np.max(mesh_models[0].vertices[:,2])]

    for i, file in enumerate(files, 1):
        mesh_models[i] = trimesh.load(file)
        for j in range(3):
            mesh_min_corner[j] = np.min([mesh_min_corner[j], np.min(mesh_models[i].vertices[:,j])])
            mesh_max_corner[j] = np.max([mesh_max_corner[j], np.max(mesh_models[i].vertices[:,j])])

    bounds = np.stack((mesh_min_corner, mesh_max_corner))

    max_len = np.max(np.array(mesh_max_corner) - np.array(mesh_min_corner))
    resolution = int(round(max_len/step))
    dx_dy_dz = tuple([step/1000, ]*3)
    print("Real [dx', dy', dz'] =", [max_len/resolution/1000, ]*3)
    print("hdf5 file resolution [dx, dy, dz] =", dx_dy_dz)
    print("")
    print("Bounds [mm]:")
    print("[x0, y0, z0] =", bounds[0])
    print("[xe, ye, ze] =", bounds[1])
    print("")

    for i, file in enumerate(files):
        mesh = trimesh.load(file)
        volumes[i] = (int(file.split("\\")[0]) + 1)*pyvoxsurf.voxelize(mesh.vertices, mesh.faces, bounds, resolution, "Inside").astype(np.int16)
        #print(file)
        #print(i)

    volume = np.copy(volumes[0])
    for i in range(1, len(files)):
        volume += volumes[i]
    volume -= 1

    print("#materials:", list(range(n_materials)))

    if len(sys.argv) > 2:
        print("Reflected")
        for j in range(volume.shape[1]):
            for k in range(volume.shape[2]):
                volume[:,j,k] = volume[-1::-1,j,k]

    hdf5file = 'model.h5'
    with h5py.File(hdf5file, 'w') as fout:
        fout.attrs['dx_dy_dz'] = dx_dy_dz
        fout.create_dataset('data', data=volume)

    print(hdf5file, 'created!')
except:
    print("Usage: python stl-to-hdf5.py <dx_dy_dz> <optional>")