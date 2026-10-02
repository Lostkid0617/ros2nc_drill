@@
-    response = {
-        'token': token,
-        'mesh_url': f'/static/{token}/{meta["mesh"]}',
-        'features_url': f'/static/{token}/{meta["name"]}.features.json',
-        'meta': meta,
-    }
+    response = {
+        'token': token,
+        'mesh_url': f'/static/{token}/{meta["mesh"]}',
+        'features_url': f'/static/{token}/{meta["name"]}.features.json',
+        'meta': meta,
+    }
     return response
@@
 @app.post('/generate_trajectory')
 def generate_trajectory(req: GenerateRequest):
@@
     traj = []
     for sel in req.selections:
         feat = features.get(sel.feature_id)
         if feat is None:
             continue
         center = feat.get('center', [0,0,0])
         axis = feat.get('axis', [0,0,1])
         # compute approach: retract point above by retract mm
-        approach = [center[0] - axis[0]*sel.retract, center[1] - axis[1]*sel.retract, center[2] - axis[2]*sel.retract]
-        plunge = [center[0], center[1], center[2] - sel.depth]
+        # normalize axis
+        import math
+        ax = np.array(axis, dtype=float)
+        norm = np.linalg.norm(ax)
+        if norm < 1e-6:
+            ax = np.array([0,0,1], dtype=float)
+        else:
+            ax = ax / norm
+        approach = [center[0] - ax[0]*sel.retract, center[1] - ax[1]*sel.retract, center[2] - ax[2]*sel.retract]
+        # plunge along axis by depth (depth is positive length)
+        plunge = [center[0] + ax[0]*(-sel.depth), center[1] + ax[1]*(-sel.depth), center[2] + ax[2]*(-sel.depth)]
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
