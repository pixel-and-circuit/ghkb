"""GHKB case builder: integrated top shell (plate) + bottom lid, both halves.

Run headless:   freecadcmd case/source/ghkb_case.py
Run in the GUI: exec(open("<abs path>/ghkb_case.py").read())

Builds the left half as-drawn in the ergogen frame (x right, y up, z=0 at
the plate top), then rebuilds the right half from mirrored inputs
((x, y, r) -> (-x, y, -r); never Part::Mirroring, which flips STL normals).
Every stage self-checks; any failure exits non-zero under freecadcmd.

ASCII only: freecadcmd runs with an ASCII locale.
"""

import os
import sys
import traceback

import FreeCAD as App
import Part

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # GUI exec() has no __file__
    _HERE = "/Users/gyeongho/workspace/ghkb/case/source"
sys.path.insert(0, _HERE)

import layout
import params

P = params.PARAMS
D = params.derived()
REPO = layout.REPO_ROOT
EXPORTS = os.path.join(REPO, "case", "exports")
REF_STEP = os.path.join(REPO, "case", "reference", "keyboard_pcba.step")

V = App.Vector


def sgn(half):
    return -1.0 if half == "right" else 1.0


def mpoint(half, x, y):
    return (sgn(half) * x, y)


def mrot(half, r):
    return sgn(half) * r


def rect_face(cx, cy, r_deg, w, h, z=0.0):
    """Planar rectangle face centered at (cx, cy), rotated r_deg CCW, at z."""
    pts = []
    for sx, sy in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
        px, py = layout.rot(r_deg, (sx * w, sy * h))
        pts.append(V(cx + px, cy + py, z))
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts))


def fuse_all(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out


def outline_faces(half):
    """PCB outline face and its offsets: (pcb, cavity, outer, rebate, lid)."""
    rects = [rect_face(*mpoint(half, cx, cy), mrot(half, r), w, h)
             for cx, cy, r, w, h in layout.OUTLINE_RECTS]
    # coplanar face fusion leaves boolean fragments; fuse thin solids and
    # slice instead, which yields the union footprint as clean wires
    thin = fuse_all([f.extrude(V(0, 0, 1.0)) for f in rects]).removeSplitter()
    wires = thin.slice(V(0, 0, 1), 0.5)
    # the tile union produces the outer boundary plus the PCB's two interior
    # holes (hex + sliver near the thumb fan; they exist on Edge.Cuts too).
    # The case only follows the outer boundary -- the plate stays solid over
    # the PCB holes.
    wires.sort(key=lambda w: Part.Face(w).Area, reverse=True)
    outer_wire = wires[0]
    outer_wire.translate(V(0, 0, -0.5))
    base = Part.Face(outer_wire)
    bb = base.BoundBox
    exp = layout.outline_bbox()
    ex0, ex1 = (-exp[2], -exp[0]) if half == "right" else (exp[0], exp[2])
    for got, want in ((bb.XMin, ex0), (bb.XMax, ex1), (bb.YMin, exp[1]), (bb.YMax, exp[3])):
        if abs(got - want) > 1e-3:
            raise AssertionError(f"outer wire bbox {got:.4f} != layout {want:.4f}")

    def off(amount):
        if amount == 0.0:
            return base
        res = outer_wire.makeOffset2D(amount, 0, False, False)  # join=0: arcs
        cands = []
        for w in (res.Wires or [res]):
            if not w.isClosed():
                continue
            try:
                cands.append((Part.Face(w).Area, w))
            except Exception:
                continue  # degenerate artifact loop
        if not cands:
            raise AssertionError(f"offset {amount} produced no usable wire")
        cands.sort(key=lambda t: t[0], reverse=True)
        return Part.Face(cands[0][1])

    return {
        "pcb": base,
        "cavity": off(D["cavity_offset"]),
        "outer": off(D["outer_offset"]),
        "rebate": off(P["pcb_gap"] + P["lid_ledge"]),
        "lid": off(P["pcb_gap"] + P["lid_ledge"] - P["lid_fit"]),
    }


def prism(face, z0, z1):
    f = face.translated(V(0, 0, z0 - face.BoundBox.ZMin))
    return f.extrude(V(0, 0, z1 - z0))


def box(cx, cy, r_deg, w, h, z0, z1):
    return prism(rect_face(cx, cy, r_deg, w, h), z0, z1)


def cyl(cx, cy, d, z0, z1):
    return Part.makeCylinder(d / 2.0, z1 - z0, V(cx, cy, z0))


def rect_clear(pt, center, r_deg, half_w, half_h, margin):
    """Distance-style check: is pt at least margin away from the rotated rect?"""
    dx, dy = pt[0] - center[0], pt[1] - center[1]
    lx, ly = layout.rot(-r_deg, (dx, dy))
    lx, ly = abs(lx), abs(ly)
    if lx >= half_w + margin or ly >= half_h + margin:
        return True
    if lx > half_w and ly > half_h:
        return ((lx - half_w) ** 2 + (ly - half_h) ** 2) >= margin ** 2
    return False


def usable_mount_holes(half, keys, enc):
    """Board mounting holes that the CASE can actually use for a post+tower.

    The PCB drill itself only needs copper/edge clearance (validated when the
    holes were placed); the case-side features have stricter needs, checked
    here in the ergogen frame with exact rotation handling:
      - insert hole (r 1.6) and post (r 2.8) clear of every plate cutout
      - lid tower corridor (r 3.0) clear of the encoder leg envelope
    Holes that fail are skipped (logged), not fatal: the lid rebate lip
    carries the uncovered span.
    """
    post_m = P["post_shoulder_d"] / 2.0
    corr = P["tower_d"] / 2.0 + 0.5
    ew, eh, _ = P["env_encoder_legs"]
    out, skipped = [], []
    for hx, hy in [mpoint(half, x, y) for x, y in layout.MOUNT_HOLES]:
        ok = all(rect_clear((hx, hy), (x, y), r,
                            P["plate_cutout"] / 2.0, P["plate_cutout"] / 2.0, post_m)
                 for x, y, r in keys)
        ok = ok and rect_clear((hx, hy), enc[:2], enc[2],
                               P["enc_cutout_w"] / 2.0, P["enc_cutout_h"] / 2.0, post_m)
        ok = ok and rect_clear((hx, hy), enc[:2], enc[2],
                               ew / 2.0, eh / 2.0, corr)
        (out if ok else skipped).append((hx, hy))
    for hx, hy in skipped:
        print(f"  note: mount hole ({hx:.2f}, {hy:.2f}) skipped by the case "
              f"(too close to the encoder cutout/legs); PCB hole stays")
    if len(out) < 5:
        raise AssertionError(f"only {len(out)} usable mount holes")
    return out


def anchors(half):
    """All layout anchors, mirrored for the requested half."""
    keys = [(mpoint(half, x, y) + (mrot(half, r),)) for _, x, y, r in layout.KEYS]
    enc = mpoint(half, layout.ENCODER[0], layout.ENCODER[1]) + \
        (mrot(half, layout.ENCODER[2]),)
    return {
        "keys": keys,
        "enc": enc,
        "mcu": mpoint(half, *layout.MCU),
        "battery": mpoint(half, *layout.BATTERY),
        "power": mpoint(half, *layout.POWER),
        "reset": mpoint(half, *layout.RESET),
        "holes": usable_mount_holes(half, keys, enc),
        "ctrl_center": mpoint(half, *layout.CONTROLLER_RECT["center"]),
        "usb_x": sgn(half) * layout.MCU[0],
        "ctrl_top_y": layout.CONTROLLER_RECT["center"][1]
                      + layout.CONTROLLER_RECT["h"] / 2.0,  # 51.075
        "ctrl_east_x": sgn(half) * (layout.CONTROLLER_RECT["center"][0]
                                    + layout.CONTROLLER_RECT["w"] / 2.0),
    }


def build_shell(half, faces, a):
    z_bot = D["z_outer_bottom"]
    shell = prism(faces["outer"], z_bot, 0.0)

    # main cavity: everything under the plate down to the lid seat
    shell = shell.cut(prism(faces["cavity"], D["z_lid_top"], -P["plate_t"]))
    # lid rebate
    shell = shell.cut(prism(faces["rebate"], z_bot, D["z_lid_top"]))

    # plate cutouts: 21 switches + encoder, cut through the plate
    cuts = [box(x, y, r, P["plate_cutout"], P["plate_cutout"], -P["plate_t"] - 0.1, 0.1)
            for x, y, r in a["keys"]]
    ex, ey, er = a["enc"]
    cuts.append(box(ex, ey, er, P["enc_cutout_w"], P["enc_cutout_h"],
                    -P["plate_t"] - 0.1, 0.1))
    shell = shell.cut(fuse_all(cuts))

    # posts: seat on the PCB top face, heat-set insert from below
    for hx, hy in a["holes"]:
        shell = shell.fuse(cyl(hx, hy, P["post_shoulder_d"],
                               D["z_pcb_top"], -P["plate_t"] + 0.05))
    shell = shell.removeSplitter()
    for hx, hy in a["holes"]:
        shell = shell.cut(cyl(hx, hy, P["insert_hole_d"],
                              D["z_pcb_top"], D["z_pcb_top"] + P["insert_depth"]))

    # USB opening in the north wall
    usb_y0 = a["ctrl_top_y"] - 0.5
    shell = shell.cut(box(a["usb_x"], usb_y0 + (D["outer_offset"] + 1.5) / 2.0, 0,
                          P["usb_w"], D["outer_offset"] + 2.5,
                          P["usb_z_center"] - P["usb_h"] / 2.0,
                          P["usb_z_center"] + P["usb_h"] / 2.0))

    # power switch notch through the east wall (west wall on the right half)
    pwx, pwy = a["power"]
    wall_out = a["ctrl_east_x"] + sgn(half) * (D["outer_offset"] + 1.0)
    x0, x1 = sorted((a["ctrl_east_x"] - sgn(half) * 0.3, wall_out))
    notch = Part.makeBox(x1 - x0, P["power_notch_w"],
                         abs(P["power_z_top"] - D["z_lid_top"]),
                         V(x0, pwy - P["power_notch_w"] / 2.0, D["z_lid_top"]))
    shell = shell.cut(notch)

    return shell.removeSplitter()


def build_lid(half, faces, a):
    z0, z1 = D["z_outer_bottom"], D["z_lid_top"]
    lid = prism(faces["lid"], z0, z1)

    # towers up to the PCB bottom face
    for hx, hy in a["holes"]:
        lid = lid.fuse(cyl(hx, hy, P["tower_d"], z1 - 0.05, D["z_pcb_bottom"]))
    lid = lid.removeSplitter()

    # battery retention ribs (across the pocket's short edges)
    bx, by = a["battery_center"] if "battery_center" in a else mpoint(half, *P["battery_center"])
    for dx in (-(P["battery_w"] / 2.0 + 0.5), P["battery_w"] / 2.0 + 0.5):
        lid = lid.fuse(box(bx + sgn(half) * dx, by, 0, 1.2, P["battery_h"],
                           z1, z1 + P["battery_rib_h"]))
    lid = lid.removeSplitter()

    # screw holes + countersinks
    for hx, hy in a["holes"]:
        lid = lid.cut(cyl(hx, hy, P["screw_clear_d"], z0 - 0.1, D["z_pcb_bottom"] + 0.1))
        cs = Part.makeCone(P["countersink_d"] / 2.0, P["screw_clear_d"] / 2.0,
                           (P["countersink_d"] - P["screw_clear_d"]) / 2.0,
                           V(hx, hy, z0))
        lid = lid.cut(cs)

    # reset access hole
    rx, ry = a["reset"]
    lid = lid.cut(cyl(rx, ry, P["reset_hole_d"], z0 - 0.1, z1 + 0.1))

    # bumpon recesses: grid-sample spots fully on the lid, clear of screws
    # and the reset hole, then greedily pick the most spread-out five
    lid_face = faces["lid"]
    bb = lid_face.BoundBox
    min_feat = P["bumpon_d"] / 2.0 + P["countersink_d"]
    spots = []
    step = 6.0
    y = bb.YMin + 8.0
    while y <= bb.YMax - 8.0:
        x = bb.XMin + 8.0
        while x <= bb.XMax - 8.0:
            probe = Part.Face(Part.Wire(Part.makeCircle(
                P["bumpon_d"] / 2.0 + 1.5, V(x, y, bb.ZMin))))
            if probe.cut(lid_face).Area < 1e-6 and \
               all((x - fx) ** 2 + (y - fy) ** 2 >= min_feat ** 2
                   for fx, fy in a["holes"] + [a["reset"]]):
                spots.append((x, y))
            x += step
        y += step
    keep = []
    if spots:
        keep.append(min(spots, key=lambda p: (p[0] - bb.XMin) ** 2 + (p[1] - bb.YMin) ** 2))
        while len(keep) < 5 and len(keep) < len(spots):
            far = max(spots, key=lambda p: min((p[0] - k[0]) ** 2 + (p[1] - k[1]) ** 2
                                               for k in keep))
            if far in keep:
                break
            keep.append(far)
    for cx, cy in keep:
        lid = lid.cut(cyl(cx, cy, P["bumpon_d"], z0 - 0.01, z0 + P["bumpon_depth"]))

    return lid.removeSplitter(), len(keep)


def envelopes(half, a):
    """Phantom component solids on the lid side + clip tabs above the PCB."""
    zt = D["z_pcb_bottom"]
    out = []

    def down(cx, cy, r, w, h, t):
        out.append(box(cx, cy, r, w, h, zt - t, zt))

    nw, nh, nt = P["env_nano"]
    down(a["mcu"][0], a["mcu"][1], 0, nw, nh, nt)
    jw, jh, jt = P["env_jst"]
    down(a["battery"][0], a["battery"][1], 0, jw, jh, jt)
    rw, rh, rt = P["env_reset"]
    down(a["reset"][0], a["reset"][1], 0, rw, rh, rt)
    pw, ph, pt = P["env_power"]
    down(a["power"][0], a["power"][1], mrot(half, -90.0), pw, ph, pt)
    ew, eh, et = P["env_encoder_legs"]
    down(a["enc"][0], a["enc"][1], a["enc"][2], ew, eh, et)
    sw, sh, st = P["env_socket_strip"]
    dy = P["env_socket_strip_dy"]
    for x, y, r in a["keys"]:
        for s in (-1.0, 1.0):
            ox, oy = layout.rot(r, (0.0, s * dy))
            down(x + ox, y + oy, r, sw, sh, st)
    # battery body itself
    bx, by = mpoint(half, *P["battery_center"])
    out.append(box(bx, by, 0, P["battery_w"], P["battery_h"],
                   D["z_lid_top"] + P["battery_rib_h"],
                   D["z_lid_top"] + P["battery_rib_h"] + P["battery_t"]))
    # switch clip tabs under the plate at the N/S cutout edges
    cw, creach, cdepth = P["env_clip"]
    for x, y, r in a["keys"]:
        for s in (-1.0, 1.0):
            ox, oy = layout.rot(r, (0.0, s * (P["plate_cutout"] + creach) / 2.0))
            out.append(box(x + ox, y + oy, r, cw, creach, -P["plate_t"] - cdepth,
                           -P["plate_t"]))
    return out


def load_pcb_step(half):
    """Import the kicad STEP, measure, and snap it into the case frame."""
    shape = Part.Shape()
    shape.read(REF_STEP)
    bb = shape.BoundBox
    exp = layout.outline_bbox()  # ergogen frame (x0, y0, x1, y1)
    dx = abs((bb.XMax - bb.XMin) - (exp[2] - exp[0]))
    dy = abs((bb.YMax - bb.YMin) - (exp[3] - exp[1]))
    if dx > 0.2 or dy > 0.2:
        raise AssertionError(f"PCB STEP footprint {bb.XLength:.3f}x{bb.YLength:.3f} "
                             f"does not match layout bbox")
    # kicad STEP is y-up like ergogen; translate so outline min corner and
    # the PCB top face land exactly on the layout frame
    m = App.Matrix()
    if half == "right":
        m.scale(V(-1, 1, 1))  # mirror about x=0 (right half is the flip)
    shape = shape.transformGeometry(m)
    bb = shape.BoundBox
    x0 = -exp[2] if half == "right" else exp[0]
    tr = V(x0 - bb.XMin, exp[1] - bb.YMin, D["z_pcb_top"] - bb.ZMax)
    shape.translate(tr)
    return shape


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"  ok: {msg}")


def verify(half, shell, lid, faces, a):
    print(f"[{half}] verifying...")
    check(shell.isValid(), "shell isValid")
    check(lid.isValid(), "lid isValid")

    # plate section: outer boundary + 22 cutouts + one insert hole per post
    n_holes = len(a["holes"])
    section = shell.slice(V(0, 0, 1), -P["plate_t"] / 2.0)
    wires = sum((s.Wires for s in section), [])
    check(len(wires) == 1 + 22 + n_holes,
          f"plate section wires = {len(wires)} (1 outer + 22 cutouts + {n_holes} inserts)")

    # posts concentric with the board mounting holes
    for hx, hy in a["holes"]:
        c = shell.common(cyl(hx, hy, P["insert_hole_d"] - 0.1,
                             D["z_pcb_top"] + 0.2, D["z_pcb_top"] + 1.0))
        check(c.Volume < 1e-9, f"insert hole open at ({hx:.2f}, {hy:.2f})")

    # PCB fits: no intersection with shell or lid
    pcb = load_pcb_step(half)
    for name, solid in (("shell", shell), ("lid", lid)):
        inter = solid.common(pcb)
        if inter.Volume >= 1e-6:
            ib = inter.BoundBox
            print(f"  DEBUG {name} x pcb: vol {inter.Volume:.4g} at "
                  f"({ib.XMin:.2f},{ib.YMin:.2f},{ib.ZMin:.2f})-"
                  f"({ib.XMax:.2f},{ib.YMax:.2f},{ib.ZMax:.2f})")
        check(inter.Volume < 1e-6, f"pcb vs {name}: intersection {inter.Volume:.4g}")

    # phantom envelopes: no intersection
    envs = envelopes(half, a)
    blob = fuse_all([shell, lid])
    for i, env in enumerate(envs):
        inter = blob.common(env)
        check(inter.Volume < 1e-6, f"envelope {i}: intersection {inter.Volume:.4g}")

    # clearances (sampled, cheap): JST vs lid top, nano vs lid top
    jz = D["z_pcb_bottom"] - P["env_jst"][2]
    check(jz - D["z_lid_top"] >= 0.3 - 1e-9, f"JST-to-lid {jz - D['z_lid_top']:.2f} >= 0.3")
    nz = D["z_pcb_bottom"] - P["env_nano"][2]
    check(nz - D["z_lid_top"] >= 1.0 - 1e-9, f"nano-to-lid {nz - D['z_lid_top']:.2f} >= 1.0")

    # geometry check() must stay silent
    for name, solid in (("shell", shell), ("lid", lid)):
        try:
            bad = solid.check(True)
        except Exception as e:  # check(True) raises on defects
            raise AssertionError(f"{name} geometry check: {e}")
    print(f"[{half}] all checks passed")
    return pcb


def export_half(half, shell, lid):
    doc = App.newDocument(f"ghkb_{half}")
    o1 = doc.addObject("Part::Feature", "top_shell")
    o1.Shape = shell
    o2 = doc.addObject("Part::Feature", "bottom_lid")
    o2.Shape = lid
    doc.recompute()
    fcstd = os.path.join(REPO, "case", "source", f"{half}.FCStd")
    doc.saveAs(fcstd)

    os.makedirs(EXPORTS, exist_ok=True)
    step_path = os.path.join(EXPORTS, f"{half}.step")
    Part.export([o1, o2], step_path)

    import Mesh
    import MeshPart
    for tag, solid in (("top", shell), ("bottom", lid)):
        mesh = MeshPart.meshFromShape(Shape=solid, LinearDeflection=0.1,
                                      AngularDeflection=0.5, Relative=False)
        stl = os.path.join(EXPORTS, f"{half}_{tag}.stl")
        mesh.write(stl)
        if not mesh.isSolid() or mesh.hasNonManifolds():
            raise AssertionError(f"{stl}: mesh not watertight/manifold")
        dv = abs(mesh.Volume - solid.Volume) / solid.Volume
        if dv > 0.01:
            raise AssertionError(f"{stl}: mesh volume off by {dv * 100:.2f}%")
        print(f"  exported {os.path.relpath(stl, REPO)} "
              f"({mesh.CountFacets} facets, dV {dv * 100:.2f}%)")
    print(f"  exported {os.path.relpath(step_path, REPO)} and {half}.FCStd")
    return doc


def build_half(half):
    print(f"[{half}] building...")
    faces = outline_faces(half)
    a = anchors(half)
    a["battery_center"] = mpoint(half, *P["battery_center"])
    shell = build_shell(half, faces, a)
    lid, n_bumpons = build_lid(half, faces, a)
    print(f"[{half}] shell vol {shell.Volume / 1000.0:.1f} cm3, "
          f"lid vol {lid.Volume / 1000.0:.1f} cm3, bumpons {n_bumpons}")
    verify(half, shell, lid, faces, a)
    export_half(half, shell, lid)
    return shell, lid


def main():
    left = build_half("left")
    right = build_half("right")
    lb, rb = left[0].BoundBox, right[0].BoundBox
    check(abs(lb.XMin + rb.XMax) < 1e-6 and abs(lb.XMax + rb.XMin) < 1e-6
          and abs(lb.YMin - rb.YMin) < 1e-6,
          "right bbox is the exact mirror of left")
    print("BUILD COMPLETE")


# freecadcmd runs scripts with __name__ == "ghkb_case" (not "__main__");
# accept both so python3, freecadcmd, and GUI exec() all enter main().
if __name__ in ("__main__", "ghkb_case"):
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    if not App.GuiUp:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
