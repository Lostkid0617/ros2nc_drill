"""parse_step.py
Utility functions to load a STEP file, perform simple feature recognition (cylindrical holes and large planar faces), and export a mesh (GLB/GLTF) for web viewing.

This is a PoC-level implementation: detection is rule-based and may need improvements for real-world CAD data.
"""
import os
import json
import tempfile
import traceback
from typing import List, Dict, Any

import numpy as np
import trimesh

# pythonocc imports
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.Geom import Geom_CylindricalSurface
from OCC.Core.gp import gp_Ax1, gp_Pnt, gp_Dir
from OCC.Core.BRepTools import breptools_Read


def load_step_to_shape(step_path: str):
    reader = STEPControl_Reader()
    status = reader.ReadFile(step_path)
    if status != IFSelect_RetDone:
        raise RuntimeError(f"STEP read failed with status {status}")
    reader.TransferRoots()
    shape = reader.OneShape()
    return shape


def mesh_shape_to_stl(shape, stl_path: str, linear_deflection: float = 0.5):
    # Create a mesh (BRepMesh) then call STL writer
    BRepMesh_IncrementalMesh(shape, linear_deflection)
    writer = StlAPI_Writer()
    writer.SetASCIIMode(False)
    writer.Write(shape, stl_path)
    return stl_path


def stl_to_glb(stl_path: str, glb_path: str):
    mesh = trimesh.load_mesh(stl_path, force='mesh')
    # Ensure scene with single mesh
    scene = trimesh.Scene(mesh)
    scene.export(glb_path)
    return glb_path


def detect_cylindrical_holes(shape) -> List[Dict[str, Any]]:
    """Simple rule-based detection: find faces whose underlying surface is cylindrical.
    For each cylinder face, report axis (point, dir), radius, and estimate depth by ray-casting in axis direction.
    """
    features = []
    try:
        exp = TopExp_Explorer(shape, TopAbs_FACE)
        idx = 0
        while exp.More():
            face = topods.Face(exp.Current())
            surf = BRep_Tool.Surface(face)
            # Try downcast to cylindrical surface
            try:
                cyl = Geom_CylindricalSurface.DownCast(surf)
            except Exception:
                cyl = None
            if cyl is not None:
                # Extract radius and axis
                radius = cyl.Radius()
                # Cylindrical surface's position gives axis
                pos = cyl.Position()
                ax = pos.Axis()
                pnt = pos.Location()
                center = (pnt.X(), pnt.Y(), pnt.Z())
                axis = (ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z())
                features.append({
                    "id": f"hole_{idx}",
                    "type": "cylindrical_hole",
                    "radius": float(radius),
                    "center": [float(center[0]), float(center[1]), float(center[2])],
                    "axis": [float(axis[0]), float(axis[1]), float(axis[2])],
                    # depth unknown here; placeholder None to be estimated later
                    "depth": None,
                })
                idx += 1
            exp.Next()
    except Exception:
        traceback.print_exc()
    return features


def estimate_depths_via_bbox(shape, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fallback quick depth estimation: use shape bounding box project along hole axis and estimate overlap length.
    This is NOT precise but provides an initial suggested depth for PoC.
    """
    try:
        # export temporary mesh and use trimesh bounding box as a rough method
        with tempfile.TemporaryDirectory() as tmp:
            tmp_stl = os.path.join(tmp, "tmp.stl")
            mesh_shape_to_stl(shape, tmp_stl, linear_deflection=0.5)
            tmesh = trimesh.load_mesh(tmp_stl)
            bbox = tmesh.bounds  # [[minx,miny,minz],[maxx,maxy,maxz]]
            for f in features:
                axis = np.array(f.get('axis', [0, 0, 1]))
                # project bbox corners on axis to get approximate extents
                corners = np.array(np.meshgrid(*[[bbox[0][i], bbox[1][i]] for i in range(3)])).T.reshape(-1,3)
                proj = corners.dot(axis)
                est_len = float(proj.max() - proj.min())
                f['depth'] = round(est_len * 0.9, 3)  # a conservative suggestion
    except Exception:
        traceback.print_exc()
    return features


def parse_step_file(step_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.basename(step_path)
    name, _ = os.path.splitext(base)
    try:
        shape = load_step_to_shape(step_path)
    except Exception as e:
        raise
    # mesh -> stl -> glb
    stl_path = os.path.join(out_dir, name + ".stl")
    glb_path = os.path.join(out_dir, name + ".glb")
    mesh_shape_to_stl(shape, stl_path)
    stl_to_glb(stl_path, glb_path)

    features = detect_cylindrical_holes(shape)
    features = estimate_depths_via_bbox(shape, features)

    meta = {
        "name": name,
        "mesh": os.path.basename(glb_path),
        "features": features,
    }
    meta_path = os.path.join(out_dir, name + ".features.json")
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    return meta, glb_path, stl_path


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_step.py yourfile.step")
        sys.exit(1)
    step = sys.argv[1]
    meta, glb, stl = parse_step_file(step, out_dir='out')
    print('Meta:', meta)
