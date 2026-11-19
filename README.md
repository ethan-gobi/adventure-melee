# Adventure Melee: Sonic for Super Smash Bros. Melee (m-ex)

Scripts, fighter code and notes for a personal mod that adds Sonic the Hedgehog (Sonic Adventure look) to Melee NTSC 1.02 as a new m-ex fighter slot.

**No game files are in this repository.** Nothing from Melee (Nintendo) or Sonic Adventure (Sega) is included: no ISO, no .dat files, no models, textures or animations. To build the mod you need your own legal copies of both games; the scripts read them from local folders that are excluded here.

## What is here

- `scripts/` - Python/PowerShell build pipeline
  - `sonic_anim_lib.py`, `sonic_moves.py`: hand-keyed animations and hitbox scripts for every move
  - `build_sonic_costume_ball.py`: builds Sonic's model from the SA1 parts on the Melee skeleton (plus spin ball, Chaos Emerald, mouth, speed trail)
  - `retarget_sa1.py`, `export_sa1_anim.py`: SA1 animations onto the Melee skeleton (Blender + SA Tools add-on)
  - `patch_*.py`, `append_dat_root.py`: in-place binary patches of the fighter file (visibility tables, attributes, custom code)
  - `build_iso.ps1`: drives MexTool to make a versioned ISO (never overwrites the source ISO)
- `fighter_code/sonic.c`: m-ex C code for the specials (Homing Attack, Light Dash, Light Speed Dash, Spin Dash, Bounce Attack)
- `tools/ppc-shim/src/gccwrap.c`: wrapper that lets MexTK compile with Zig's clang instead of devkitPPC (set `ZIG_EXE` to your zig.exe)
- `tests/`: libmelee test harness (menus, per-move hit frame/damage measurement, load tests)
- `BUILD_NOTES.md`: every build, what changed (values from -> to), how it was tested, what is unverified

## Third-party tools used (not included)

m-ex / MexTool / MexTK, HSDRaw, SA Tools and the Sonic Adventure Blender add-on, Blender, Dolphin / Slippi Dolphin, libmelee, Zig. See each project for its own license.
