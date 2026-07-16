# Copyright (c) 2026 GyeongHo Kim
# SPDX-License-Identifier: GPL-3.0-or-later

"""GHKB key/feature layout, recomputed from the ergogen parameters.

Single source of geometry for the case build. Every anchor this module
computes is asserted against the routed board (pcb/keyboard.kicad_pcb) at
load time, so any drift between pcb/ergogen/config.yaml, the routed board,
and this file fails loudly instead of producing a case that doesn't fit.

Frames: ergogen frame is x-right / y-up / degrees CCW-positive; the KiCad
board file is the same except y is negated (kicad = (x, -y), angle equal).
All public data below is in the ergogen frame, millimetres.

No FreeCAD imports here -- runs under plain python3 and freecadcmd alike.
"""

import math
import os
import re

KX = 19.05
KY = 19.05
PX = KX + 3.6  # padded board tile used for the outline
PY = KY + 3.6

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BOARD_PATH = os.path.join(REPO_ROOT, "pcb", "keyboard.kicad_pcb")

TOL = 1e-3


def rot(deg, v):
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _matrix_points():
    """18 matrix keys: (name, x, y, r). Cumulative stagger per config.yaml."""
    stagger = {"outer": 0.0, "pinky": 0.0, "ring": 6.0, "middle": 3.0,
               "index": -3.0, "inner": -1.5}
    cols = ["outer", "pinky", "ring", "middle", "index", "inner"]
    rows = {"bottom": 0.0, "home": KY, "top": 2 * KY}
    pts = []
    base = 0.0
    for i, col in enumerate(cols):
        base += stagger[col]
        for row, dy in rows.items():
            pts.append((f"matrix_{col}_{row}", i * KX, base + dy, 0.0))
    return pts


def _thumb_points():
    """3 thumb keys with cumulative -15 deg splay about [-0.5kx, -0.5ky]."""
    mid_bottom = (3 * KX, 9.0)  # matrix_middle_bottom (cumulative stagger 0+0+6+3)
    near = add(mid_bottom, (0.25 * KX, -1.15 * KY))
    pts = [("thumbs_near_thumb", near[0], near[1], 0.0)]
    prev, r = near, 0.0
    for name in ("thumbs_home_thumb", "thumbs_far_thumb"):
        candidate = add(prev, rot(r, (KX, 0.0)))
        center = add(candidate, rot(r, (-0.5 * KX, -0.5 * KY)))
        rel = (candidate[0] - center[0], candidate[1] - center[1])
        point = add(center, rot(-15.0, rel))
        r -= 15.0
        pts.append((name, point[0], point[1], r))
        prev = point
    return pts


MATRIX = _matrix_points()
THUMBS = _thumb_points()
KEYS = MATRIX + THUMBS  # 21 switches

_far = THUMBS[-1]
ENCODER = add((_far[1], _far[2]), rot(_far[3], (1.1 * KX, 0.15 * KY))) + (_far[3],)
ENCODER = (ENCODER[0], ENCODER[1], _far[3])  # (x, y, r=-30)

_inner_top = (5 * KX, 4.5 + 2 * KY)  # matrix_inner_top
MCU = add(_inner_top, (1.05 * KX + 3.0, -0.5 * KY))  # (118.2525, 33.075)
CONTROLLER_RECT = {  # 26 x 64 centered at mcu + (0, -14)
    "center": add(MCU, (0.0, -14.0)),
    "w": 26.0,
    "h": 64.0,
}
BATTERY = add(MCU, (0.0, -25.0))
POWER = add(MCU, (11.0, -25.0))
RESET = add(MCU, (-8.5, -25.0))

# outline input: 22 padded tiles (keys + encoder, rotated) + controller rect
OUTLINE_RECTS = (
    [(x, y, r, PX, PY) for _, x, y, r in KEYS]
    + [(ENCODER[0], ENCODER[1], ENCODER[2], PX, PY)]
    + [(CONTROLLER_RECT["center"][0], CONTROLLER_RECT["center"][1], 0.0,
        CONTROLLER_RECT["w"], CONTROLLER_RECT["h"])]
)


def outline_bbox():
    xs, ys = [], []
    for cx, cy, r, w, h in OUTLINE_RECTS:
        for sx in (-0.5, 0.5):
            for sy in (-0.5, 0.5):
                px, py = rot(r, (sx * w, sy * h))
                xs.append(cx + px)
                ys.append(cy + py)
    return min(xs), min(ys), max(xs), max(ys)


def _diode_points():
    """SOD-123 diodes: key + Rot(r)*(0, -5); encoder diode: enc + Rot(r)*(8, 0)."""
    pts = [add((x, y), rot(r, (0.0, -5.0))) for _, x, y, r in KEYS]
    pts.append(add((ENCODER[0], ENCODER[1]), rot(ENCODER[2], (8.0, 0.0))))
    return pts


def _parse_board(path=BOARD_PATH):
    """Return {lib_name: [(x, y, r_deg), ...]} in KICAD frame (y-down)."""
    text = open(path, encoding="utf-8").read()  # explicit: freecadcmd locale is ASCII
    out = {}
    for m in re.finditer(r'\(footprint "([^"]+)"', text):
        lib = m.group(1)
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)",
                       text[m.end():m.end() + 600])
        if not at:
            raise AssertionError(f"no (at ...) found for footprint {lib}")
        x, y = float(at.group(1)), float(at.group(2))
        r = float(at.group(3)) if at.group(3) else 0.0
        out.setdefault(lib, []).append((x, y, r))
    return out


def _match(expected, actual, label, check_angle=False):
    """Greedy nearest matching of expected ergogen points to kicad footprints."""
    if len(expected) != len(actual):
        raise AssertionError(
            f"{label}: expected {len(expected)} footprints, board has {len(actual)}")
    remaining = list(actual)
    for e in expected:
        ex, ey = e[0], -e[1]  # ergogen -> kicad
        best = min(remaining, key=lambda a: (a[0] - ex) ** 2 + (a[1] - ey) ** 2)
        d = math.hypot(best[0] - ex, best[1] - ey)
        if d > TOL:
            raise AssertionError(f"{label}: no board footprint within {TOL} of "
                                 f"ergogen ({e[0]:.4f}, {e[1]:.4f}); nearest off by {d:.4f}")
        if check_angle:
            er = e[2] % 360.0
            ar = best[2] % 360.0
            if min(abs(er - ar), 360.0 - abs(er - ar)) > TOL:
                raise AssertionError(f"{label}: angle mismatch at ({e[0]:.3f}, {e[1]:.3f}): "
                                     f"expected {er}, board {ar}")
        remaining.remove(best)


def mount_holes(board=None):
    """Mounting holes read FROM the board (authoritative; do not hardcode).

    Returns [(x, y), ...] in the ergogen frame.
    """
    board = board or _parse_board()
    mh = board.get("MountingHole:MountingHole_2.2mm", [])
    if len(mh) != 6:
        raise AssertionError(f"expected 6 mounting holes on board, found {len(mh)}")
    return sorted((x, -y) for x, y, _ in mh)


def assert_against_board(path=BOARD_PATH, verbose=False):
    board = _parse_board(path)
    _match([(x, y, r) for _, x, y, r in KEYS],
           board.get("ceoloide:switch_mx", []), "switch_mx", check_angle=True)
    _match([ENCODER], board.get("ceoloide:rotary_encoder_ec11_ec12", []),
           "rotary_encoder", check_angle=True)
    _match([_diode_points()[i] + (0,) for i in range(22)],
           board.get("ceoloide:diode_tht_sod123", []), "diode_tht_sod123")
    _match([MCU + (0,)], board.get("ceoloide:mcu_nice_nano", []), "mcu_nice_nano")
    _match([BATTERY + (0,)], board.get("ceoloide:battery_connector_jst_ph_2", []),
           "battery_connector")
    _match([POWER + (0,)], board.get("ceoloide:power_switch_smd_side", []),
           "power_switch")
    _match([RESET + (0,)], board.get("ceoloide:reset_switch_tht_top", []),
           "reset_switch")
    holes = mount_holes(board)

    x0, y0, x1, y1 = outline_bbox()
    exp = (-11.325, -47.3497, 137.8963, 58.425)
    for got, want, tag in zip((x0, y0, x1, y1), exp, "x0 y0 x1 y1".split()):
        if abs(got - want) > 5e-4:
            raise AssertionError(f"outline bbox {tag}: {got:.4f} != {want:.4f}")

    n = 21 + 1 + 22 + 1 + 1 + 1 + 1
    if verbose:
        print(f"layout OK: {n} footprints + {len(holes)} mounting holes match "
              f"{os.path.relpath(path, REPO_ROOT)} (tol {TOL} mm)")
        print(f"outline bbox: ({x0:.4f}, {y0:.4f}) - ({x1:.4f}, {y1:.4f}) "
              f"[{x1 - x0:.3f} x {y1 - y0:.3f}]")
        for i, (hx, hy) in enumerate(holes, 1):
            print(f"mount hole {i}: ergogen ({hx:.2f}, {hy:.2f})")
    return holes


MOUNT_HOLES = assert_against_board()

# freecadcmd runs scripts with __name__ == "layout" (not "__main__")
if __name__ in ("__main__", "layout"):
    assert_against_board(verbose=True)
