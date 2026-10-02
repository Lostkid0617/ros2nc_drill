"""parse_step.py - improved for hole pattern detection and depth estimation using mesh vertices.
PoC-level: detects cylindrical surfaces, estimates depths via mesh vertex projection onto hole axis,
clusters features into pattern groups by rounding centers.
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
from OCC.Core.gp import gp_Pnt


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
    """Detect cylindrical surfaces and extract basic parameters (id,type,radius,axis_point,axis_dir).
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
                radius = cyl.Radius()
                pos = cyl.Position()
                loc = pos.Location()
                ax = pos.Axis()
                axis_point = (float(loc.X()), float(loc.Y()), float(loc.Z()))
                axis_dir = (float(ax.Direction().X()), float(ax.Direction().Y()), float(ax.Direction().Z()))
                # Use the axis point as center proxy
                center = list(axis_point)
                features.append({
                    "id": f"hole_{idx}",
                    "type": "cylindrical_hole",
                    "radius": float(radius),
                    "center": center,
                    "axis": list(axis_dir),
                    "depth": None,
                    "pattern_group": None,
                })
                idx += 1
            exp.Next()
    except Exception:
        traceback.print_exc()
    return features


def estimate_depths_via_mesh_vertices(stl_path: str, features: List[Dict[str, Any]], tol_rad: float = 0.5):
    """Estimate axial extents of features by analysing mesh vertices close to the cylinder axis.
    stl_path: path to the mesh representing the solid
    For each feature, we project mesh vertices onto the axis and select those within radius+tol_rad.
    The depth is estimated as the spread (max-min) of projected coordinates in axis direction.
    """
    try:
        mesh = trimesh.load_mesh(stl_path, process=False)
        verts = np.asarray(mesh.vertices)
        if verts.size == 0:
            return features

        for f in features:
            center = np.array(f.get('center', [0.0, 0.0, 0.0]), dtype=float)
            axis = np.array(f.get('axis', [0.0, 0.0, 1.0]), dtype=float)
            radius = float(f.get('radius', 1.0))
            if np.linalg.norm(axis) < 1e-6:
                axis = np.array([0.0, 0.0, 1.0])
            axis = axis / np.linalg.norm(axis)
            # vector from axis point to verts
            rel = verts - center
            # projection length along axis
            proj = rel.dot(axis)
            # closest point on axis for each vertex
            closest = center + np.outer(proj, axis)
            # radial distances
            radial = np.linalg.norm(verts - closest, axis=1)
            # select vertices near cylinder radius (allow tolerance)
            mask = radial < (radius + tol_rad)
            if np.any(mask):
                proj_sel = proj[mask]
                # depth is extent of selected projections
                depth = float(np.max(proj_sel) - np.min(proj_sel))
                # Depth might be negative depending on orientation; take absolute
                f['depth'] = round(abs(depth), 4)
            else:
                f['depth'] = None
    except Exception:
        traceback.print_exc()
    return features


def group_features_into_patterns(features: List[Dict[str, Any]], position_tol: float = 1.0, radius_tol: float = 0.5) -> List[Dict[str, Any]]:
    """Group features into pattern groups based on rounded center positions and similar radii.
    Simple approach: quantize center coordinates with position_tol and radius with radius_tol.
    Assign pattern_group strings like "group_0", "group_1".
    """
    groups = {}
    group_ids = []
    for f in features:
        center = np.array(f.get('center', [0.0,0.0,0.0]), dtype=float)
        radius = float(f.get('radius', 0.0))
        # quantize
        key_pos = tuple(np.round(center / position_tol).astype(int).tolist())
        key_rad = int(round(radius / radius_tol))
        key = (key_rad, key_pos)
        if key not in groups:
            groups[key] = []
        groups[key].append(f)
    # assign ids
    for idx, (k, items) in enumerate(groups.items()):
        gid = f'pattern_{idx}'
        for it in items:
            it['pattern_group'] = gid
        group_ids.append({'group_id': gid, 'count': len(items), 'radius_approx': float(k[0]*radius_tol)})
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
    features = estimate_depths_via_mesh_vertices(stl_path, features, tol_rad=0.8)
    features = group_features_into_patterns(features, position_tol=2.0, radius_tol=0.5)

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
