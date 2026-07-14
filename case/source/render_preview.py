"""GHKB case README preview renderer (docs/images/case-preview*.png).

Arranges the built left/right FCStd halves as a split pair (thumbs inward,
18 mm apart at the inner edges), takes a front-top product shot on a
transparent background, and writes light- and dark-mode PNGs cropped to
content for the README's <picture> block.

Requires the FreeCAD GUI for View3D.saveImage -- freecadcmd cannot render.
Run it from the GUI Python console:
    exec(open("/Users/gyeongho/workspace/ghkb/case/source/render_preview.py").read())
or through freecad-mcp's execute_code.

ASCII only: freecadcmd runs with an ASCII locale.
"""

import os

import FreeCAD as App
import FreeCADGui as Gui
import matplotlib.image as mpimg
import numpy as np

_FALLBACK = "/Users/gyeongho/workspace/ghkb/case/source"
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # GUI console exec() has no __file__
    _HERE = _FALLBACK
if not os.path.isfile(os.path.join(_HERE, "ghkb_case.py")):
    # exec() through freecad-mcp inherits the addon's __file__
    _HERE = _FALLBACK
REPO = os.path.dirname(os.path.dirname(_HERE))
OUT_DIR = os.path.join(REPO, "docs", "images")

GAP = 18.0  # clearance between the halves' inner edges (mm)
IMG_W, IMG_H = 2400, 1400
MARGIN = 48  # transparent border kept after cropping (px)

# (shell, lid, edge line) RGB per README color-scheme variant
COLORWAYS = {
    "case-preview.png": (
        (0.16, 0.17, 0.20), (0.45, 0.48, 0.53), (0.04, 0.04, 0.05)),
    "case-preview-dark.png": (
        (0.80, 0.81, 0.84), (0.33, 0.35, 0.40), (0.10, 0.10, 0.12)),
}


def open_half(half):
    path = os.path.join(REPO, "case", "source", half + ".FCStd")
    for doc in App.listDocuments().values():
        if doc.FileName == path:
            return doc
    return App.openDocument(path)


def build_scene():
    if "ghkb_render" in App.listDocuments():
        App.closeDocument("ghkb_render")
    doc = App.newDocument("ghkb_render")
    for half in ("left", "right"):
        src = open_half(half)
        shell_bb = src.getObject("top_shell").Shape.BoundBox
        # place the pair symmetrically: inner edges GAP apart at x=0
        if half == "left":
            dx = -GAP / 2.0 - shell_bb.XMax
        else:
            dx = GAP / 2.0 - shell_bb.XMin
        for name in ("top_shell", "bottom_lid"):
            o = doc.addObject("Part::Feature", half + "_" + name)
            o.Shape = src.getObject(name).Shape
            o.Placement = App.Placement(App.Vector(dx, 0, 0), App.Rotation())
    doc.recompute()
    return doc


def crop_to_content(path):
    img = mpimg.imread(path)
    ys, xs = np.where(img[:, :, 3] > 0.01)
    y0 = max(0, ys.min() - MARGIN)
    x0 = max(0, xs.min() - MARGIN)
    crop = img[y0:ys.max() + MARGIN, x0:xs.max() + MARGIN]
    mpimg.imsave(path, crop)
    return crop.shape


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    doc = build_scene()
    Gui.setActiveDocument(doc.Name)
    view = Gui.getDocument(doc.Name).activeView()
    view.setCameraType("Perspective")
    view.setViewDirection((0.0, 0.5, -1.0))
    view.fitAll()
    for fname, (shell_c, lid_c, line_c) in COLORWAYS.items():
        for o in doc.Objects:
            vo = o.ViewObject
            vo.ShapeColor = shell_c if o.Name.endswith("top_shell") else lid_c
            vo.LineColor = line_c
            vo.LineWidth = 1.0
            vo.DisplayMode = "Flat Lines"
        path = os.path.join(OUT_DIR, fname)
        view.saveImage(path, IMG_W, IMG_H, "Transparent")
        shape = crop_to_content(path)
        print("wrote %s (%dx%d)" % (os.path.relpath(path, REPO), shape[1], shape[0]))


main()
