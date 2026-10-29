---
"mesh-avatar": minor
---

Add optional rig fields for stronger, cleaner head and face motion: `face.brow.pair`, `lift` and `tilt` (faces that show both brows tilt each brow about its own centre, mirrored, instead of see-sawing the pair), `head.parallax` (scales per-feature turn depth) and `face.jaw.drop` (chin drop with an open mouth). Overlay entries may set `rigid: true` so glasses move as one piece. Rigs and overlays without these fields render exactly as before.
