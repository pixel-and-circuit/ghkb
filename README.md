GHKB

GHKB is an open-source split mechanical keyboard project focused on custom hardware, modern firmware, and long-term experimentation.

The goal of this project is to build a fully custom wireless split keyboard from the ground up, including both the hardware and firmware stack. Rather than assembling an existing design, GHKB documents the complete engineering process—from PCB and enclosure design to firmware development.

Goals

Phase 1: Build a Reliable Daily Driver

Develop a fully functional wireless split keyboard featuring:

* Custom PCB designed with KiCad
* Custom 3D-printed enclosure
* MX-compatible mechanical switches
* Battery-powered operation
* Bluetooth Low Energy (BLE)
* ZMK firmware
* Comfortable ergonomic layout

Controller strategy: the first prototype targets an off-the-shelf nRF52840
controller module (e.g. Nice!Nano) socketed onto the PCB. Designing a fully
custom controller—placing the nRF52840 QFN/BGA package directly on the board—is
a later, optional goal once the socketed design is validated.

Phase 2: Develop a TinyGo Firmware

Create a native TinyGo firmware targeting the same hardware platform. The
long-term objective is not simply to recreate existing keyboard firmware, but to
explore whether a modern Go-based embedded ecosystem can become a practical
alternative for custom keyboard development.

Because the wireless BLE stack is by far the highest-risk part of this effort,
Phase 2 is split into two independent milestones:

Phase 2a: USB-wired TinyGo firmware (high feasibility)

Bring up a wired, single-board or wired-split TinyGo build using USB HID, which
is well supported in the TinyGo ecosystem and has existing precedent. This
establishes the matrix scanning, keymap, and feature layer in Go without
depending on wireless.

Phase 2b: BLE-wireless TinyGo firmware (research / uncertain)

Extend the firmware to full wireless operation. This is genuinely exploratory
and may not be achievable: TinyGo's BLE support (`tinygo.org/x/bluetooth`) has
historically centered on the central/scanner role and relies on Nordic's
SoftDevice, whereas a keyboard needs a BLE peripheral with HID-over-GATT,
pairing/bonding, and a wireless split link. ZMK gets these for free from
Zephyr's mature BLE stack; in TinyGo much of it would have to be built from
scratch. Treat Phase 2b as an open question, not a scheduled deliverable.

Planned Features

* Wireless split architecture
* Bluetooth Low Energy (BLE)
* Multi-device pairing
* Battery management
* USB-C charging
* Layer support
* Mod-Tap / Hold-Tap
* Combo keys
* Rotary encoder support
* OLED display support
* Optional RGB lighting
* Firmware updates via bootloader

Repository Structure

Note: this is the planned/target layout for the completed project. The
repository currently contains only this README while the project is in the
planning and hardware design phase; directories below are created as work
progresses.

```
.
├── README.md
├── LICENSE
├── .gitignore
├── firmware/
│   ├── zmk/
│   └── tinygo/
├── pcb/
│   ├── keyboard.kicad_pro
│   ├── keyboard.kicad_sch
│   ├── keyboard.kicad_pcb
│   └── libraries/
├── case/
│   ├── source/
│   │   ├── left.FCStd
│   │   └── right.FCStd
│   └── exports/
│       ├── left.step
│       ├── right.step
│       ├── left.stl
│       └── right.stl
├── plate/
├── docs/
│   ├── assembly.md
│   ├── wiring.md
│   └── images/
└── bom/
    └── bom.csv
```

Directory Overview

Directory	Description
firmware/zmk	Production firmware based on ZMK.
firmware/tinygo	Experimental TinyGo firmware implementation.
pcb	KiCad project files, schematics, PCB layout, and custom libraries.
case/source	Source CAD models for the enclosure.
case/exports	Exported manufacturing files (STEP/STL).
plate	Switch plate designs.
docs	Assembly guide, wiring documentation, and project images.
bom	Bill of Materials used to build the keyboard.

Roadmap

* Finalize the keyboard layout
* Design the PCB
* Design the enclosure
* Build the first prototype
* Bring up ZMK firmware
* Validate the hardware
* Use as a daily driver
* Develop USB-wired TinyGo firmware (Phase 2a)
* Investigate BLE-wireless TinyGo firmware (Phase 2b, research)
* Document the complete development process

Status

This project is currently in the planning and hardware design phase.

Contributing

Contributions are welcome.

Whether you are interested in mechanical keyboards, embedded systems, TinyGo, ZMK, PCB design, or 3D modeling, feel free to open an issue or submit a pull request.

License

This project is licensed under the MIT License. See the LICENSE file for details.
