# FastAPI backend for STEP PoC
# Provides endpoints to upload STEP files, run parsing/feature recognition, serve mesh and features, and generate simple trajectories.
import os
import shutil
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any

from stp_poc.backend.parse_step import parse_step_file

app = FastAPI(title='STEP PoC API')

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
WORK_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(WORK_DIR, exist_ok=True)

# mount static to serve meshes and meta
app.mount('/static', StaticFiles(directory=WORK_DIR), name='static')


class TrajectoryPoint(BaseModel):
    x: float
    y: float
    z: float
    speed: float = 100.0


class DrillFeatureSelection(BaseModel):
    feature_id: str
    depth: float
    retract: float = 2.0
    feed: float = 200.0


class GenerateRequest(BaseModel):
    file_token: str
    selections: List[DrillFeatureSelection]


@app.post('/upload')
async def upload_step(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.step', '.stp')):
        raise HTTPException(status_code=400, detail='Only STEP (.step/.stp) files are accepted')
    token = str(uuid.uuid4())
    token_dir = os.path.join(WORK_DIR, token)
    os.makedirs(token_dir, exist_ok=True)
    file_path = os.path.join(token_dir, file.filename)
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    # parse
    try:
        meta, glb_path, stl_path = parse_step_file(file_path, token_dir)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})

    response = {
        'token': token,
        'mesh_url': f'/static/{token}/{meta["mesh"]}',
        'features_url': f'/static/{token}/{meta["name"]}.features.json',
        'meta': meta,
    }
    return response


@app.get('/features/{token}')
def get_features(token: str):
    path = os.path.join(WORK_DIR, token)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='token not found')
    # find features json
    for f in os.listdir(path):
        if f.endswith('.features.json'):
            return FileResponse(os.path.join(path, f), media_type='application/json')
    raise HTTPException(status_code=404, detail='features not found')


@app.post('/generate_trajectory')
def generate_trajectory(req: GenerateRequest):
    # For each selected feature, make a simple vertical drill trajectory in Cartesian points
    token_dir = os.path.join(WORK_DIR, req.file_token)
    if not os.path.exists(token_dir):
        raise HTTPException(status_code=404, detail='token not found')
    # load features
    features_file = None
    for f in os.listdir(token_dir):
        if f.endswith('.features.json'):
            features_file = os.path.join(token_dir, f)
    if features_file is None:
        raise HTTPException(status_code=404, detail='features json missing')
    import json
    with open(features_file) as fh:
        meta = json.load(fh)
    features = {f['id']: f for f in meta.get('features', [])}

    traj = []
    for sel in req.selections:
        feat = features.get(sel.feature_id)
        if feat is None:
            continue
        center = feat.get('center', [0,0,0])
        axis = feat.get('axis', [0,0,1])
        # compute approach: retract point above by retract mm
        approach = [center[0] - axis[0]*sel.retract, center[1] - axis[1]*sel.retract, center[2] - axis[2]*sel.retract]
        plunge = [center[0], center[1], center[2] - sel.depth]
        retract = approach
        traj.append({
            'feature_id': sel.feature_id,
            'points': [
                {'x': approach[0], 'y': approach[1], 'z': approach[2], 'speed': 300},
                {'x': plunge[0], 'y': plunge[1], 'z': plunge[2], 'speed': sel.feed},
                {'x': retract[0], 'y': retract[1], 'z': retract[2], 'speed': 300},
            ]
        })
    return {'trajectories': traj}


@app.get('/')
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html'))
