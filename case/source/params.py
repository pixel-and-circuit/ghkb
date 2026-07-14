"""GHKB case parameters. All lengths in millimetres, ergogen frame (y-up).

Vertical datum: z = 0 at the plate/shell top face, +z up. The stack:
    0            shell/plate top (keycaps live above the case)
    0 .. -1.5    integrated switch plate
   -1.5 .. -5.0  under-plate air (MX plate-top -> PCB-top = 5.0)
   -5.0 .. -6.6  PCB (hangs on switches; clamped at the mount posts)
   -6.6 .. -13.1 under-PCB cavity (JST 6.0 governs) / lid towers
  -13.1 .. -15.5 lid, flush-inset into the wall rebate
"""

PARAMS = {
    # plate
    "plate_t": 1.5,
    "plate_cutout": 14.0,          # square, rotated with each key
    "include_clip_reliefs": False,  # optional 5x1x0.75 notches, N/S edges
    "enc_cutout_w": 13.6,          # EC11 body passes through the plate
    "enc_cutout_h": 14.6,

    # stack
    "plate_to_pcb": 5.0,
    "pcb_t": 1.6,
    "pcb_gap": 0.25,               # radial fit gap around the PCB outline
    "under_pcb": 6.5,              # >= JST-PH 6.0 + margin

    # shell
    "wall_t": 3.0,                 # cavity wall; inner face = outline + pcb_gap
    "lid_t": 2.4,
    "lid_fit": 0.15,               # per side, lid vs rebate
    "lid_ledge": 1.6,              # rebate depth into the wall

    # fastening (M2 through the PCB mounting holes; see layout.MOUNT_HOLES)
    "post_shoulder_d": 5.6,        # shell post, seats on the PCB top face
    "insert_hole_d": 3.2,          # M2 heat-set insert, blind hole in the post
    "insert_depth": 4.4,
    "tower_d": 6.0,                # lid tower, seats on the PCB bottom face
    "screw_clear_d": 2.3,          # M2 clearance through lid + tower
    "countersink_d": 4.2,          # 90 deg flat-head countersink in the lid
    # screw: M2x14 flat head -- lid 2.4 + tower 6.5 + PCB 1.6 = 10.5 mm of
    # travel before the insert, leaving ~3.5 mm of thread engagement

    # openings (positions derive from layout.MCU / layout.POWER / layout.RESET)
    "usb_w": 10.4,
    "usb_h": 4.4,
    "usb_z_center": -8.45,
    "usb_chamfer": 1.0,
    "power_notch_w": 11.0,
    # notch reaches above the PCB top: the side-switch pads overhang the
    # board edge by ~2.1 mm on both faces (reversible), so the wall must be
    # open across the whole PCB seam, not just below it
    "power_z_top": -4.9,
    "reset_hole_d": 3.6,

    # battery pocket (301230-class LiPo, one per half)
    "battery_w": 32.0,
    "battery_h": 14.0,
    "battery_t": 3.2,
    "battery_center": (95.25, 8.0),
    "battery_rib_h": 1.0,

    # cosmetics / print
    "bumpon_d": 8.2,
    "bumpon_depth": 0.5,
    "fillet_outer_r": 2.0,         # degrade gracefully if OCC refuses
    "rim_chamfer": 0.6,
    "lid_chamfer": 0.5,
    "usb_shelves": False,          # posts clamp the PCB; shelves off by default

    # phantom envelopes for interference checks only (never printed)
    # (w, h, t) footprints in the ergogen frame; anchored in ghkb_case.py
    "env_nano": (18.2, 33.6, 5.3),
    "env_jst": (8.0, 6.5, 6.2),
    "env_reset": (7.0, 7.0, 4.5),
    "env_power": (7.5, 3.2, 1.7),
    # hotswap socket: two strips per key (reversible board), footprint-local
    # y in [2.0, 8.2] both signs, x within +-5.5, 1.9 tall below the PCB
    "env_socket_strip": (11.0, 6.2, 1.9),
    "env_socket_strip_dy": 5.1,
    "env_encoder_legs": (14.0, 15.0, 2.2),
    # switch clip tabs: 5 wide, reach 0.8 past the N/S cutout edge, ~2 deep
    "env_clip": (5.0, 0.8, 2.0),
}


def derived(p=PARAMS):
    """Values computed from the base parameters (single place for the stack)."""
    z_plate_bottom = -p["plate_t"]
    z_pcb_top = -p["plate_to_pcb"]
    z_pcb_bottom = z_pcb_top - p["pcb_t"]
    z_lid_top = z_pcb_bottom - p["under_pcb"]
    z_outer_bottom = z_lid_top - p["lid_t"]
    return {
        "z_plate_bottom": z_plate_bottom,   # -1.5
        "z_pcb_top": z_pcb_top,             # -5.0
        "z_pcb_bottom": z_pcb_bottom,       # -6.6
        "z_lid_top": z_lid_top,             # -13.1
        "z_outer_bottom": z_outer_bottom,   # -15.5
        "post_len": z_plate_bottom - z_pcb_top,      # 3.5
        "tower_len": z_pcb_bottom - z_lid_top,       # 6.5
        "cavity_offset": p["pcb_gap"],               # 0.25
        "outer_offset": p["pcb_gap"] + p["wall_t"],  # 3.25
    }
