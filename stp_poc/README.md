# STEP PoC - README

This PoC provides a minimal pipeline to upload a STEP file, run simple feature recognition (cylindrical holes), allow manual adjustment in a web UI, and generate simple drill trajectories as Cartesian points.

Files added under stp_poc/:
- requirements.txt -- Python dependencies
- backend/parse_step.py -- STEP parsing, feature recognition, mesh export
- backend/api.py -- FastAPI app to upload STEP, serve mesh/features, and generate trajectories
- frontend/index.html -- minimal web UI using three.js for preview and controls
- data/ (created at runtime) -- uploaded files and generated meshes/features
- stp_examples/ -- placeholder directory for user STEP examples

Quick start (local)
1. Create a virtualenv and install dependencies:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r stp_poc/requirements.txt

2. Run the API server (from repository root):
   uvicorn stp_poc.backend.api:app --reload --host 0.0.0.0 --port 8000

3. Open the UI by visiting:
   http://localhost:8000/

Usage
- Use the file input to upload a .step/.stp file. The server will parse it and return detected features and a GLB mesh to preview.
- Edit depth/feed for each detected feature in the panel, then click "Generate Trajectory" to get a simple Cartesian drill trajectory JSON.

How to upload STEP files to the repository (optional)
- For the PoC you can upload STEP files via the web UI (they will be stored under stp_poc/backend/data/<token>/).
- If you prefer to add example STEP files into the repository under stp_examples/, you can:
  1) Add the files locally and push via git:
     git add stp_examples/your_model.step
     git commit -m "add example STEP"
     git push
  2) Or upload via GitHub web UI into the stp_examples/ folder.

Notes & Limitations
- Feature detection is a conservative PoC and focuses on cylindrical holes. Real-world STEP models may require more robust heuristics and user-guided corrections.
- Collision detection, tool definitions, and machine kinematics are outside the scope of this initial PoC.

Next steps after PoC
- Improve feature recognition rules and add ability to merge/split features
- Implement robust depth detection and hole-type classification (through/blind/counterbore)
- Integrate trajectory output with ROS2/motion executor
- Add collision checks and tool/fixture models

