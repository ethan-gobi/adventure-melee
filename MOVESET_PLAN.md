# Sonic moveset plan (from v09)

Goal: every move is Sonic's own move (animation, timing, hitboxes) from the approved moveset table, and each is tested only after it is built.

## Where things stand

- Latest good build: `builds/Melee - Sonic v09.iso`, but its moves are still Falcon's. Only damage numbers changed in v09 (`work/v08/changes_v09.md`), and hitboxes were shrunk to Sonic's size.
- Sonic's files are in the package `work/sonic_package_v09.zip`:
  - `PlSn.dat`: fighter data (attributes, action table, hitbox scripts, hurtboxes)
  - `PlSnAJ.dat`: animations
  - `PlSnNr.dat` etc.: model and skeleton (Falcon's 63 bones, Sonic's lengths)
- Tools already written:
  - `scripts/subactions.py`: decode and edit hitbox scripts in place
  - `scripts/scale_animations.py`: animation file rebuild + offsets
  - `scripts/build_iso.ps1 -Version vNN -Package <zip>`: never overwrites a build
  - `tests/runner.py`: menus and matches, with `--capture` screenshots
  - `tests/move_test.py`: per-move hit frames and damage on a standing Fox
- Rules (from the brief):
  - New version number for every build.
  - Tell the user "from -> to" before changing any value.
  - Never touch Falcon's own files or any other character.
  - Update BUILD_NOTES.md after every build.
  - Any custom game code needs the user's OK first (decision point 3).

## Hard lessons (do not repeat)

- Never re-save `PlSn.dat` through HSDRaw after re-assigning its tables: it crashes the game. Patch bytes in place, as `scale_animations.py` and `patch_moveset_v08.py` do.
- Read animation offsets from the same `FighterAJManager` that called `RebuildAJFile`.
- Find each move's script through the action table pointer (`0x20 + script ptr`), not by searching for its bytes: variants share identical scripts.
- Slippi Dolphin's `$Required: Slippi Online` code set crashes the m-ex stage select. Tests disable it in the temp folder only.

## Steps

### 1. Animation pipeline (data only)

Retarget SA1 animations onto Sonic's Melee skeleton, writing new figatrees into `PlSnAJ.dat`.

- Map the SA1 node hierarchy to the 63 Melee bones. The node to bone mapping is already in `scripts/build_sonic_costume.py`.
- Convert rotations from SA1 rest pose to the Melee rest pose per bone.
- Done when: Sonic's idle (`s_wait0`), walk (`s_walk0`), run (`s_run0`/`s_run1`) and dash play in game, checked with screenshots, and his feet stay on the floor.

### 2. Spin-ball model swap (data only)

- Add the SA1 spin-ball mesh (`s_spinball`) as extra model parts, hidden by default.
- Show it, hiding the body, through the subaction script's model-visibility command during spin moves.
- Done when: a test script can toggle ball and body in game.

### 3. Spin moves (data only)

New animations plus new hitbox scripts with the approved frame data:

| Move | First active | Active | Total | Damage | Source |
|---|---|---|---|---|---|
| Neutral air (spin jump) | 4 | 4-27 | 39 | 9 early / 5 late | ball |
| Dash attack (Spin Dash roll) | 6 | 6-16 | 38 | 9 / 6 | ball |
| Up smash (spin jump in place) | 8 | multi-hit 8-22 | 48 | 13 total | ball |
| Down air (drill spin) | 6 | 5 hits to f26 | 44 | 2x5 + 3 | ball |

- Done when: `tests/move_test.py` (extended for aerials) measures each first active frame, total frames and damage within 1 frame / 1% of the table.

### 4. Kicks and strikes (hand-made keyframes in Blender, data only)

- Jab 1/2/3, forward tilt, up tilt, down tilt (Somersault), forward smash, down smash (sweep), back air, up air.
- Forward air axe kick: sourspot frames 12-14 sends forward at 7%; heel sweetspot frames 15-17 meteor at 12%.
- Grab, pummel and the four throws.
- Done when: each move matches its table row, the axe kick spikes on the sweetspot and not on the sourspot, and the user has looked at each animation.

### 5. Specials: decision point 3 APPROVED by the user on 2026-11-13

- Homing Attack, Spin Dash (side B), Light Speed Dash (up B), Bounce Attack (down B) need m-ex C code plus devkitPPC.
- Approved: custom m-ex C code for the four specials. Toolchain: devkitPPC + MexTK.

### 6. Full measurement pass

- Every move tested on Fox, Falco, Captain Falcon, Marth and Jigglypuff at 0%, 60% and 120%, with and without DI away.
- Multi-hits checked for linking.
- Final tables and the balance opinion.

## Resume here (paused 2026-11-13)

- Latest build: `builds/Melee - Sonic v10.iso` (package `work/sonic_package_v10.zip`). Details are in BUILD_NOTES.md under v10.
- Step 1 is partly done: Wait1-3, Walk and Run/Dash use retargeted SA1 animations (`scripts/retarget_sa1.py`; SA1 samples in `work/sa1anim`). Still to do:
  - Fall, jump and tumble/damage poses: the user reported legs and shoes coming apart in tumble.
  - Check the shield bubble in game.
  - Check the playback speed of the SA1 animations.
- Offline check: `scripts/pose_preview.py <bound.json> <AJ> <anim> <frames> <out>`, then `scripts/_render_pose.py` in Blender.
- Specials toolchain:
  - Zig (`python -m ziglang cc -target powerpc-freestanding-eabihf -mcpu=750 ...`) compiles m-ex C to PowerPC objects.
  - MexTK needs a stand-in at `devkitpro/devkitPPC/bin/powerpc-eabi-gcc.exe` and `powerpc-eabi-g++.exe`, relative to the working folder (copies in `tools/ppc-shim`). The next check is to pack the Mario example objects (`work/zigtest`) with MexTK.
  - devkitPPC itself is not installed: the user's installer run left no files.
- 2026-11-13 follow-up: with both stand-ins in place, MexTK passes its compiler check, then fails starting another devkitPPC program ("cannot find the file", from Process.Start inside Compile). It is probably the linker or objcopy, even for `.o` inputs. Next: find which program it runs (Process Monitor, or read MexTK's Compiling class with a .NET decompiler), then provide it via Zig (`zig ld.lld` / `zig objcopy`) or get devkitPPC installed properly.
- 2026-11-13 FIXED: the specials toolchain works.
  - `C:\devkitpro\devkitPPC\bin\powerpc-eabi-gcc.exe` and `powerpc-eabi-g++.exe` are a small wrapper (`tools/ppc-shim/src/gccwrap.c`). It forwards MexTK's compile calls to Zig's clang (target powerpc-freestanding-eabihf, -mcpu=750, GCC-only flags dropped) and its `-r` link calls to Zig's lld.
  - Test: m-ex's Mario example (`work/zigtest`, two stale declarations removed from the example header) builds from C source with MexTK: "Sucessfully Compiled and Converted to DAT!". onload, move_logic and all 8 special entries are filled, with no unresolved symbols or unsupported relocations.
  - Not yet tested in game.

## Resume here (2026-11-16, v19)

- Only build: `builds/Melee - Sonic v19.iso`. All moves are defined in `scripts/sonic_moves.py` (poses, key frames, hitboxes); rebuild with `python scripts/sonic_moves.py build work/v10/PlSnAJ_v10r.dat work/v10/PlSn_v10.dat <AJ out> <PlSn out> <changes.md>`, swap both files into a copy of `work/sonic_package_v10.zip`, then `scripts/build_iso.ps1`.
- Preview poses without the game: `python scripts/sonic_moves.py preview <dir> [Label,Label]`.
- Next: make up smash and down air hits link; test the aerials (axe kick) against a jumping or platform target; swing sounds; real specials in C (Homing Attack freeze is unsolved); Guard/Turn/throw animations.
- The user stopped the crash fix (Sonic must be player 1).

## Resume here (2026-11-16, v23)

- Only build: `builds/Melee - Sonic v23.iso`. Crash fixed (`scripts/patch_lookup_all.py`), four specials in `fighter_code/sonic.c`.
- Build chain: `sonic_moves.py build` -> `MexTK -ff -i sonic.c -s ftFunction -o ft.dat` (run in `fighter_code`) -> `append_dat_root.py` -> `patch_lookup_all.py <in> <out> 18` -> swap PlSn.dat/PlSnAJ.dat into a copy of `work/sonic_package_v10.zip` -> `build_iso.ps1`.
- Next: tune specials (side B distance), sounds/effects, up smash links, remaining Falcon animations (shield, turn, ledge, throws), portraits/icons/voice, full measurement pass.
