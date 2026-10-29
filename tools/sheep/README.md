# Sheep avatar helpers

Project-specific scripts for `projects/sheep` (the project folder itself is not committed).
Run from the repository root after **Save and rebuild layers**, in this order:

```sh
uv run --with numpy --with pillow --with opencv-python-headless tools/sheep/wool-mask.py      # smooth wool + ear sway mask
uv run --with numpy --with pillow --with opencv-python-headless tools/sheep/fix-base-eyes.py  # clean eye sockets in base.png
uv run --with pillow tools/sheep/glasses.py                                                   # rigid glasses overlay
uv run --with numpy --with pillow --with opencv-python-headless tools/sheep/draw-variants.py  # drawn eyes and mouths
uv run --with numpy --with pillow --with opencv-python-headless tools/build-sprites.py projects/sheep
```
