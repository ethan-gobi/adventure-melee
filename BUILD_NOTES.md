# Adventure Melee: build notes

Sonic (Sonic Adventure 1, Dreamcast) as a new fighter in Super Smash Bros. Melee NTSC 1.02.
Game files are for personal use only and are never uploaded.

## Builds

No ISO build yet. The first build will be `builds/Melee - Sonic v01.iso`.

## v00: setup and model extraction (2026-11-12)

No game data was changed. Nothing here touches Melee yet.

### Source files (originals in Downloads are untouched; copies live in `source/`)

| File | Check | Result |
|---|---|---|
| `base/Melee NTSC 1.02 clean.iso` (converted from the RVZ copy with DolphinTool) | MD5 `0e63d4223b01d9aba596259dc155a174`, ID GALE01, revision 2 | Matches clean NTSC 1.02 |
| Sonic Adventure (USA) Rev A, Dreamcast bin/cue | IP.BIN: MK-51000, V1.005, 1999-10-05 | US v1.005 |
| `source/sa1_files/1ST_READ.BIN` | MD5 `060cad2ceefc07c7429085f30a356046` | Matches SA Tools' "DC - SA1 (US)" template |

Not used: `Sigma - Copy.iso` (the ISO Slippi Launcher points at). It is GALE01 rev 2 but MD5 `d647b82c...`, so it is modified.

### Tools (all in `tools/`, nothing installed system-wide)

| Tool | Version | Source | Status |
|---|---|---|---|
| Blender (portable, own config in `tools/bl/portable`) | 5.3.0 | blender.org, SHA-256 verified | Runs headless |
| Sonic Adventure I/O add-on | 2.2.2 | github.com/X-Hax/SonicAdventureBlenderIO | Used for the import below |
| SA Tools | build 786 | github.com/X-Hax/sa_tools | `split` and `ArchiveTool` used below |
| Dolphin (for DolphinTool only) | 2609 | dl.dolphin-emu.org | Used for RVZ to ISO |
| HSDRaw | build of 2026-08-25 | github.com/Ploaj/HSDLib | Unpacked, not launched yet |
| MexTool | build of 2024-06-26 | github.com/akaneia/mexTool | Unpacked, not launched yet |

Already present: Slippi Dolphin (Launcher 2.15.2), Python 3.11.9, libmelee 0.47.6, pywin32 312, .NET 8 desktop runtime, .NET Framework 4.8.1.
Not installed: devkitPPC (only needed if custom m-ex C code is approved at decision point 3).

### Steps

1. `scripts/gdrom_extract.py` read the GD-ROM high-density track (Track 3) and extracted 2,832 files to `source/sa1_files`.
2. `split binary 1ST_READ.BIN` with SA Tools' `DC_SA1/1st_read.ini` wrote 543 items to `extract/sa1`.
3. `ArchiveTool -png SONIC.PRS` wrote 28 textures to `extract/sa1_tex/SONIC`.
4. `scripts/preview_sonic.py` imported `figure/sonic/models/s_kihon10_sonic.nja.sa1mdl` into Blender, saved `preview/sonic_sa1_import.blend` and rendered four views to `preview/`.

### Model facts (measured from the import)

- 73 objects: 28 mesh parts on a 45-node hierarchy. There is no armature and no skin weights; each part is rigidly attached to one node.
- 635 vertices, 1,001 triangles, 20 materials, 28 textures (8x8 to 64x64).
- Faces -X in Blender after import. About 10 units tall in SA1 units.
- SA1 animations for Sonic were also split (`s_wait0`, `s_run0`, `s_spin0`, ...) as `.saanim` files; not imported yet.

### Known limits found

- This PC's GPU (Intel HD Graphics 620) cannot run Blender's GPU renderers headless (the Intel driver crashes). Previews use Cycles on the CPU.
- Blender does not start from very long paths; the project must stay at a short path such as `C:\adventure-melee`.

### Not done / unverified

- HSDRaw and MexTool have not been run.
- No Melee-compatible skeleton, skinning or animation work yet.
- No libmelee test harness yet.
- Decision point 1 (slot) is open.

## v01: Sonic slot as a Captain Falcon clone (2026-11-12)

File: `builds/Melee - Sonic v01.iso` (1,439,082,112 bytes). Built by `scripts/build_iso.ps1` from a copy of the clean ISO; the clean ISO's MD5 was re-checked afterwards and is unchanged.

Approved at decision points 1 and 2: new m-ex slot, Captain Falcon as base, up B = Light Speed Dash, moveset table as proposed.

### What changed (no gameplay values changed)

- m-ex 1.1 installed into the copy by MexTool's own code (driven by script, see `scripts/mex_common.ps1`).
- New fighter "Sonic" at internal index 27 (fighters 33 -> 34). He is an exact copy of Captain Falcon: same model, animations, moves, attributes and move code.
- Sonic's own files: `PlSn.dat`, `PlSnAJ.dat`, `PlSnNr/Gy/Wh/Gr/Bu.dat`, `GmRstMSn.dat`, `PlSnDViWaitAJ.dat`, `EfSnData.dat`. Shared with Falcon: sound bank, Kirby hat, ending movies, target stage.
- Falcon's red costume was left out of Sonic (MexTool exported it without its model file). Team colours: red 2 -> 0, blue 5 -> 4, green 4 -> 3.
- Select-screen icons 25 -> 26: a copy of Falcon's icon placed right of Roy (X 24.8, Y -1.2).
- Dialogs MexTool raised and the script answered: "Install m-ex?" -> Yes; "Soundbank captain.ssm already exists, using existing" -> OK.

### Testing (`tests/boot_test.py`, libmelee, Slippi Dolphin from a temp folder, Slippi port 51447)

- PASS: the build boots and reaches the main menu and character select.
- PASS (one run): the bot moved port 1 to the new icon and a character with an ID libmelee does not know was locked in.
- FAIL / not reached: a match has never started. In the first runs port 2 never locked in Fox (libmelee's picker misreads character IDs under m-ex). After switching port 2 to a position-based picker, the last two runs stopped sending frames about 6 seconds in, at character select, and timed out. Cause not yet known: possibly a game freeze, possibly a harness bug.
- The pipe owner check (GetNamedPipeServerProcessId) returned "All pipe instances are busy" and so verified nothing.

### Unverified

- Whether Sonic loads in a match at all, and every move, frame count, damage and knockback value.
- HSDRaw has still not been run. No Sonic model, animation or attribute work has been done on the Melee side.

### v01 known defects (found while testing v02)

- Missing m-ex extra codes: `codes.gct` was only m-ex's base code (MexTool's code paths were not set when driven by script).
- The image ends a few bytes before the end of its last file, so Dolphin can report "The disc could not be read".
- Do not use v01; use v02.

## v02: v01 plus build fixes (2026-11-12)

File: `builds/Melee - Sonic v02.iso` (1,459,978,240 bytes). Same Sonic package as v01 (`work/sonic_package_v01.zip`), so Sonic is still an exact Captain Falcon clone. No gameplay values changed.

### Build changes (`scripts/build_iso.ps1`, `scripts/mex_common.ps1`)

- MexTool's code paths are now set like its own startup does, and `codes.gct` is rebuilt the way its Save button does it (m-ex base code + enabled codes from `lib/codes.ini`). Failed codes: none.
- The finished image is padded from 1,439,089,312 to 1,459,978,240 bytes (standard GameCube disc size).

### Root cause of the stage-select crash

- An m-ex-only build (no Sonic) crashed on entering stage select in Slippi Dolphin ("Invalid read from 0x93e10014, PC = 0x8037c20c"), with or without libmelee's codes.
- Cause: Slippi Dolphin force-enables its `$Required: Slippi Online` code set, which patches the stage select and assumes the vanilla layout that m-ex replaces.
- With that code set disabled in the test's temporary Dolphin settings only, the same build reaches Final Destination and runs normally.
- **Hand testing:** in your normal Slippi Dolphin this code set is forced, so the stage select will crash. Use the bundled mainline Dolphin instead: `tools/Dolphin/Dolphin-x64/Dolphin.exe` (it has `portable.txt`, so it keeps its own settings and does not touch your Dolphin config).

### Test harness changes (`tests/runner.py`, `tests/harness.py`, `tests/mem.py`)

- Menus are driven by reading emulated memory (scene, main-menu selection, cursor positions). Every A press is gated on what is highlighted, so the bot can never confirm "Online Play" (an earlier button-mashing script opened Slippi login pages in the browser).
- The m-ex stage-select cursor is found each run by diffing RAM while nudging the stick.
- A separate thread watches for a Dolphin crash dialog, screenshots it and stops the test Dolphin (only the one the harness started).

### Test results (Slippi Dolphin 3.6.4, temp user folder, port 51447, `--disable=$Required: Slippi Online`)

| Build | P1 vs P2 | Result |
|---|---|---|
| Clean ISO | Falcon vs Fox, FD | PASS: 480 frames |
| m-ex only (no Sonic), Slippi Online on | Falcon vs Fox | FAIL: crash on stage select |
| m-ex only (no Sonic), Slippi Online off | Falcon vs Fox, FD | PASS: 480 frames |
| **v02** | **Sonic vs Fox, FD** | **PASS: 480 frames; P1 internal fighter 27 (Sonic slot); dash moved P1 from x=-60 to x=38.5** |

### Unverified

- Jab and neutral air were scripted, but the 80-frame samples did not land on them; per-move checks have not been done.
- Sonic still uses Falcon's model, animations, moves and attributes.
- The pipe-owner check still reports "All pipe instances are busy" and so verifies nothing.
- Hand test in the bundled Dolphin not done by me.

## v03: Sonic's approved movement attributes (2026-11-12)

File: `builds/Melee - Sonic v03.iso` (1,459,978,240 bytes). Package: `work/sonic_package_v03.zip`.
Only Sonic's own `PlSn.dat` changed (`scripts/patch_attributes.ps1`): 16 bytes patched in place in the attribute block at file offset 0x3774; file size unchanged. Falcon's `PlCa.dat` is untouched. Sonic still has Falcon's model, animations and moves.

### Values (read from the file first, then patched)

| Attribute (HSDRaw name) | From -> to | Measured in game (v03 Sonic, Final Destination) |
|---|---|---|
| Weight | 104 -> 85 | not measurable without being hit; confirmed by reading the file back |
| InitialRunSpeed (run speed) | 2.3 -> 2.4 | 2.4 |
| InitialDashSpeed | 2.0 -> 2.0 (unchanged) | 2.0 |
| Friction (traction) | 0.08 -> 0.06 | 0.06 per frame |
| MaxAerialHorizontalSpeed (air speed) | 1.12 -> 1.0 | 1.0 |
| TerminalVelocity (fall speed) | 2.9 -> 2.5 | 2.5 |
| Gravity | 0.13 -> 0.15 | 0.15 |
| JumpStartupLag (jump squat) | 4 -> 4 (unchanged) | 4 frames |
| FastFallTerminalVelocity | 3.5 (not in the approved table, unchanged) | not measured |

### Tests (`tests/measure_attributes.py`)

- Sonic on v03, Final Destination: all values above as measured. PASS.
- Sonic on v02 and Falcon on v03: Falcon's values (dash 2.0, run 2.3, traction 0.08, jump squat 4, air speed 1.12, gravity 0.13). So Falcon is unchanged in v03. These two runs ended up on a stage other than Final Destination (floor at y=33.7) because the stage-cursor search failed; flat-ground movement does not depend on the stage.
- Falcon's fall speed measured 2.73, not 2.9, only because a full jump lands before reaching top fall speed.

### Known test-harness issue

- On the m-ex stage select the harness finds the cursor by nudging the stick and diffing memory. A wrong match makes the cursor wander or jitter on screen (test Dolphin only). When no match is found it picks whatever stage is under the cursor.

### Unverified

- Weight in game, fast-fall speed, short-hop and double-jump heights.
- Frame data of any move (still Falcon's).

## v04: Sonic Adventure 1 model in game (2026-11-12)

File: `builds/Melee - Sonic v04.iso` (1,459,978,240 bytes). Package: `work/sonic_package_v04.zip`. Attributes as in v03.

### How the model was made

1. `scripts/export_sonic_parts.py` (Blender) exports the 28 SA1 mesh parts (1,001 triangles) with UVs and material settings.
2. `scripts/build_sonic_costume.py` (Python + HSDRaw via pythonnet) binds every part rigidly to one of Captain Falcon's 63 bones. The skeleton is not changed, so all of Falcon's animations still apply. Placement:
   - Body and tail -> Falcon's chest and hip bones (scaled to span hip to neck).
   - Head, eyes and pupils -> head bone, scaled 1.5x.
   - Upper arm, forearm and hand -> shoulder, elbow and hand bones; arm and leg segments are stretched to Falcon's bone lengths (thickness x2.2).
   - Thigh, shin and shoe -> leg, knee and foot bones; the shoe is scaled so its sole sits on the floor.
3. Textures: SA1's 28 textures, multiplied by each SA1 material colour (as SA1 does), encoded RGB565 (opaque). 18 material groups -> 18 model parts.
4. `scripts/make_v04_package.py` puts the same model in all 5 costume files (root names kept) and repoints Sonic's part-visibility tables in `PlSn.dat`:
   - High poly: 44 Falcon parts -> parts 0-17.
   - Low poly: 35 -> 0-17.
   - Metal main model: 10 -> 0-17.
   - Metal model: 7 -> 0-17.

   `PlSn.dat` is re-saved by HSDRaw (not an in-place patch this time). The attributes were re-read afterwards and match v03.

### Test (`tests/runner.py --capture`, Slippi Online codes disabled in the temp folder)

- PASS: Sonic vs Fox on Final Destination, 480 frames, no crash. P1 = fighter 27.
- Captures: `test_logs/v04_run_shot_100.png` (standing), `_275.png` (running), `_345.png` (jump/aerial). Sonic renders with his SA1 textures and follows Falcon's animations.

### Known issues / unverified

- Proportions follow Falcon's skeleton: Sonic looks taller and lankier than in SA1, with long, thin arms and legs.
- Character select portraits, stock icons and the HUD icon are still Falcon's.
- Low-poly and metal-box appearance use the same parts; the metal box has not been tested.
- Texture alpha is ignored (one small buckle texture has transparency).
- Hurtboxes, moves and sounds are still Falcon's.
- The off-screen window setting was ignored by Slippi Dolphin: the test game window appeared on screen at (114, 114) during this run.

## v05 and v06: defective, do not use (2026-11-13)

Both were attempts at the proportion fix below and both fail at match start.
- v05: the animation offsets written to `PlSn.dat` were all -1 (read from the wrong object after rebuilding the animation file). The match loads but never starts.
- v06: offsets correct, but `PlSn.dat` was re-saved through HSDRaw after re-assigning its action and hurtbox tables. Crash at match start: "Invalid read from 0x3f800014, PC = 0x8035ddb8". An isolation build with no animation changes crashed the same way, which pinned it on that re-save.

## v07: Sonic's own proportions (2026-11-13)

File: `builds/Melee - Sonic v07.iso` (1,459,978,240 bytes). Package: `work/sonic_package_v07.zip`. Movement attributes as in v03.

### What changed (Sonic's files only: costume files, `PlSnAJ.dat`, `PlSn.dat`)

1. **Skeleton lengths** (`scripts/sonic_proportions.py`, applied in `scripts/build_sonic_costume.py`): bone directions and rotations are unchanged, only rest lengths. SA1 Sonic is scaled 1.7x (10.08 SA1 units -> 17.1 Melee units; Falcon is about 21). Main bones, from -> to:
   - Hip height (bone 2): 13.86 -> 9.63 (the floor reference bone 61 gets the same factor)
   - Thigh (bones 8, 14): 5.09 -> 2.13
   - Shin (bones 9, 15): 5.66 -> 3.51
   - Upper arm (bones 24, 46): 3.15 -> 1.34
   - Forearm (bones 25, 47): 3.56 -> 2.70
   - Shoulder offset (bones 22, 44): 1.90 -> 0.93
   - Neck (bone 38): 3.12 -> 0.88
   - Fingers and toes: x0.6. All factors are saved in `work/v05/PlSnNr_sonic_bone_factors.json`.
2. **Model parts** are now placed at uniform 1.7x scale on those bones (no more stretched limbs).
3. **Animations** (`scripts/scale_animations.py`): in all 213 animations, the translation keys of the resized bones are multiplied by the same factors (2,488 tracks; maximum re-encoding error 0.0001). Rotations are untouched. `PlSnAJ.dat` 1,633,440 -> 1,672,896 bytes.
4. **`PlSn.dat`, patched in place** (file size unchanged, 163,198 bytes):
   - Animation offset/size of 275 of 318 actions updated to the rebuilt animation file; each offset is verified against the animation's bytes.
   - Hurtboxes (bone, end points, radius), from -> to:

| # | Bone | From | To |
|---|---|---|---|
| 0 | 4 hip | (0,0,1)-(0,0,0) r2.40 | (0,0,1)-(0,0,0) r2.00 |
| 1 | 19 chest | (0,0.7,0)-(0,1.5,0) r3.30 | (0,0.3,0)-(0,0.9,0) r2.40 |
| 2 | 39 head | (0,1.2,0)-(0,1.2,0.5) r1.68 | (0,2.2,0)-(0,3.6,-0.5) r2.80 |
| 3, 4 | 45, 23 upper arms | (0,0,0)-(2.3,0,0) r1.44 | (0,0,0)-(1.0,0,0) r0.90 |
| 5, 6 | 46, 24 forearms | (0,0,0)-(3.5,0,0) r1.32 | (0,0,0)-(2.6,0,0) r0.90 |
| 7, 8 | 13, 7 thighs | (0,0,0)-(4.5,0,0) r1.80 | (0,0,0)-(1.9,0,0) r1.30 |
| 9, 10 | 14, 8 shins | (0,0,0)-(4.9,0,0) r1.44 | (0,0,0)-(3.3,0,0) r1.10 |

### Test (`tests/runner.py --capture`)

- PASS: Sonic vs Fox on Final Destination, 480 frames, no crash.
- Captures `test_logs/v07_run_shot_100.png` (standing), `_204.png` (jab), `_275.png` (running): Sonic has SA1 proportions, his feet are on the floor, and he animates.

### Known issues / unverified

- Hurtbox sizes are my estimates from the model; they have not been checked visually in game.
- Hitboxes of all moves are still Falcon's, at Falcon's reach, although Sonic's limbs are now shorter.
- Not checked: ledge grab, grabs and throws, shield size, Falcon's specials with the new skeleton, every animation by eye.
- Icons, portraits and sounds are still Falcon's.
- Test window: a fully off-screen window renders black, so the test window is now kept on screen behind all other windows and never activated.

## Decision point 3 (2026-11-13)

Approved by the user: custom m-ex C code for Sonic's four specials (Homing Attack, Spin Dash, Light Speed Dash, Bounce Attack), because Melee runs each special through fixed built-in code and data alone cannot add homing or a floor bounce. Toolchain: devkitPPC + MexTK. No code written yet.

### Toolchain status (2026-11-13)

- m-ex repository cloned to `tools/m-ex` (commit c9f25da, 2026-06-07). It contains MexTK.exe, the headers and a full C Mario fighter example (`examples/mario`) used as the template for Sonic's specials.
- devkitPro installer v3.0.3 downloaded to `tools/_dl` (signature valid: David Murphy, devkitPro). Its silent mode (`/S`) exits 0 without installing anything, and pkg.devkitpro.org blocks scripted downloads with a Cloudflare check. devkitPPC must be installed through the installer's GUI by the user.

## v08: incomplete, deleted

A first moveset pass that missed scripts shared between actions; replaced by v09 before testing. The ISO was deleted.

## v09: hitbox refit + approved damage values (2026-11-13)

`scripts/patch_moveset_v08.py`, byte-patched in place.
- 190 hitboxes refit to Sonic's size: offsets scaled per bone, sizes x0.75.
- 75 value changes, listed from -> to in `work/v08/changes_v09.md`.
- Moves were still Falcon's animations and timings, so v09 was not measured (testing was stopped at the user's request).

## v10: user-reported visual fixes + Sonic's own idle/walk/run (2026-11-13)

File: `builds/Melee - Sonic v10.iso`. Package `work/sonic_package_v10.zip`.

Reported by the user from hand testing (v07/v09):
1. In the idle, the head tipped forward, the face was hidden and the hands covered it.
2. In falling/tumble, the shoes and legs looked detached.
3. The shield bubble did not cover his head.

Diagnosis (`scripts/pose_preview.py` renders any animation frame offline): Falcon's animations tilt the head bone forward by a median of 23° (idle 26°, fall 41°). That is invisible on Falcon but buries Sonic's big head, and Falcon's boxing-guard idle puts the fists at Sonic's face height.

Changes:
- **Head:** geometry pre-tilted back 20° about the neck (`HEAD_TILT` in `build_sonic_costume.py`).
- **Shield:** in the Guard animations the bubble bone (61) translation factor is 0.695 -> 0.85, so the bubble centre is about 1.6 units higher and covers the head. Throws are untouched.
- **Sonic's own animations from SA1**, retargeted with `scripts/retarget_sa1.py`: each SA1 joint's world rotation change is applied to the matching Melee bone, corrected for the part placement.
  - Wait1 <- s_wait0, Wait2 <- s_wait_a0, Wait3 <- s_wait_b0
  - WalkSlow/Middle/Fast <- s_walk0
  - Run <- s_run1, Dash <- s_run0
- **v09's hitbox/damage pass** re-applied.

Tests:
- PASS: Sonic vs Fox on Final Destination, 480 frames, no crash.
- Captures `test_logs/v10_run_shot_100.png` (idle) and `_275.png` (run).

Not yet fixed / unverified:
- Tumble, fall, jump, shield, damage and every attack still use Falcon's animations (with the head tilt). Item 2 (legs/shoes in tumble) is therefore only improved by the head change, not fixed.
- The shield fix has not been seen in game yet.
- SA1 animation speed in Melee (playback rate) has not been checked against Sonic's run speed.

### Specials toolchain working (2026-11-13)

devkitPPC could not be installed (the installer run left no files, and its package server blocks scripted downloads). Replacement:
- Zig 0.17.1 from PyPI (`python -m ziglang`) provides clang and lld for the GameCube CPU.
- A wrapper installed as `C:\devkitpro\devkitPPC\bin\powerpc-eabi-gcc.exe` / `-g++.exe` (source `tools/ppc-shim/src/gccwrap.c`) translates MexTK's GCC calls. Every call is logged to `tools/ppc-shim/calls.log`.
- Verified: m-ex's Mario example compiles and packs into `PlMr.dat` with all function-table entries filled and no unresolved symbols.
- Not verified: that code built with clang runs correctly in game. This will be tested with Sonic's first special.

## v11: defective (crash at match start)

MexTK injected the code by re-saving all of `PlSn.dat` through HSDRaw. That causes the same crash as v06 ("Invalid read ... PC = 0x8035ddb8") before any custom code runs. Do not let HSDRaw re-save `PlSn.dat`.

## v12: first custom code in game, Homing Attack prototype v0 (2026-11-13)

File: `builds/Melee - Sonic v12.iso`. Package `work/sonic_package_v12.zip`. Everything else is as in v10.

- Code: `fighter_code/sonic.c` (neutral B and aerial neutral B). It finds the nearest fighter within 70 units (centre to centre), sets Sonic airborne, faces him at the target and launches him at 3.2 units/frame along that line. With no target it does a forward dash (2.8, 0.6). The move uses the common neutral-air state, so it has the neutral air's spin hitbox for now.
- Build:
  - `MexTK -ff -i sonic.c -s ftFunction -o ftFunction_sonic.dat` through the Zig wrapper.
  - Then `scripts/append_dat_root.py` appends the code as a new `ftFunction` root. Sonic's existing data, pointers and roots stay byte-identical (163,198 -> 165,981 bytes).
- Compiler fixes found on the way:
  - Helpers must be force-inlined, and the wrapper now adds `-ffunction-sections -fdata-sections`. Without that, clang resolved calls inside one section and MexTK dropped the called code (the output had branches into nothing).
- Test (`tests/runner.py --special`, Sonic vs Fox on Final Destination):
  - PASS, 480 frames, no crash.
  - B on frame 200 -> NAIR state on the next frame. Sonic moved x -60 -> -8 (Fox 120 units away, so this was the no-target dash).
  - This proves Zig/clang-built m-ex code runs in Melee.
- Not yet tested: homing onto a target in range, hitting Fox, once-per-airtime limit (not implemented), Sonic's own spin animation and frame data from the moveset table.

## v13, v14, v15-diag: Homing Attack debugging (2026-11-13)

All are v10 plus `fighter_code/sonic.c` variants, appended with `append_dat_root.py`. Test: `tests/runner.py --homing`, where the bot walks to 40 units from Fox and presses B.

| Build | Change | Result |
|---|---|---|
| v12 | prototype | Fox out of range: forward dash works. Fox in range on FD floor: **game freezes the frame B is pressed** (Dolphin window "FPS: 0, VPS: 59", so game code is stuck in a loop) |
| v13 | plain-C square root instead of the game's `sqrtf` | still freezes |
| v14 | minimum upward launch 1.0 from the ground | still freezes |
| v15-diag | invalid distance -> fly left (diagnostic) | different stage picked (Fox on a platform at y 27.2): **no freeze, homing launched toward Fox**, arc fell short below him, no hit |

Open: the freeze happens with a target level with Sonic on the floor. Not caused by sqrt, by a zero vertical launch or by an invalid distance. Next ideas:
- Read emulated memory after the freeze for P1's position and velocity (NaN check).
- Test without `Fighter_SetAirborne`.
- Test with the launch aimed slightly up.

Also: the homing aims only once at launch, so gravity makes it fall short; it needs steering each frame (its own action state). The user reported the run still looks wrong (screenshot); details still to be clarified.
The test harness's stage-cursor check now verifies both down and right movement.

## Crash investigation: Sonic on port 2 / vs Kirby (2026-11-13, unresolved)

User report: the game crashes with Kirby. Reproduced automatically with `tests/kirby_test.py <iso> <prefix> <P1> <P2>`, which only checks that the match loads.

Facts established:
- The crash is at match load, not at the swallow. Dolphin reports "Invalid read ... PC = 0x8035ddb8". That address is the entry of `DOBJ_SetFlags` (m-ex symbol list): the game sets flags on a model part through a garbage pointer.
- The garbage values look like floats or texture pixels, so the game is reading past the end of the fighter's part list. Whether a match crashes depends on what happens to be in memory, which is why it varies with port order and opponent.
- The plain Falcon-clone Sonic (package v03) never crashes: Fox vs Sonic OK, Sonic vs Kirby OK.
- Sonic's model alone on the clean clone crashes. So the cause is the model plus Sonic's tables. It is not the animations, attributes, hitboxes or custom code.
- The only fighter code that calls `DOBJ_SetFlags` is `Fighter_SetVisGroupCurrent` (0x80074c40) and `Fighter_UpdateDObjFlags2` (0x80074dfc), found by scanning the DOL.
- v10-v16 "worked" on port 1 vs Fox only by luck. v12's Homing Attack freeze may be related.

Tried, did not fix it:
- Rebuilding `PlSn.dat` from the pristine clone with in-place patches only (`scripts/patch_lookup.py`), with no HSDRaw re-save.
- Attaching parts directly to bones instead of envelopes on the root (new `build_sonic_costume.py`; the old one is `work/v17/build_sonic_costume_envelope_version.py`). This made the crash happen every time.
- Moving head and shoe parts to child bones; max 4 parts per bone.
- Setting the three model-part entries (hand/face swaps) to Count 0 (`scripts/patch_modelparts.py`).

Variant results (Sonic P1 vs Fox, bone-attached model):

| Variant | Parts | Result |
|---|---|---|
| Body and tail only | 3 | loads |
| Body + arms | 12 | loads |
| Body + head | 9 | crash |
| Body + legs | 21 | crash |

Next step (do this before more guessing): disassemble `Fighter_SetVisGroupCurrent` and `Fighter_UpdateDObjFlags2` from the DOL to see exactly which table and index they read. Alternatively, break in Dolphin's debugger at 0x8035ddb8 and read LR and r3.

Builds: v16, v17 and v18 are crash-investigation builds; none is good. v10 remains the last build that plays (Sonic on port 1 vs Fox, by luck of memory layout). Kirby hat entries: Falcon has none, so nothing needed copying.

## v19: Sonic's own moves and animations (2026-11-16)

File: `builds/Melee - Sonic v19.iso`. Package `work/sonic_package_v19.zip`. Base: v10's model, attributes and SA1 idle/walk/run. No custom code (the v12 Homing Attack prototype is left out because it freezes). All older ISOs were deleted at the user's request; v19 is the only build.

The match-load crash (Sonic on port 2 / vs Kirby) is NOT fixed: the user chose to stop that work. Use Sonic as player 1.

New tools:
- `scripts/sonic_anim_lib.py`: hand-keyed animation solver (poses in body space, rotations only, so limbs cannot detach), a hitbox-script assembler, and a flat-shaded preview renderer.
- `scripts/sonic_moves.py`: every pose, animation, hitbox and timing. `preview <dir>` draws sheets, `build ...` writes `PlSnAJ.dat` and `PlSn.dat`.
- New attack scripts are appended to the end of `PlSn.dat`'s data and the action table is repointed; existing bytes are not re-serialised (166,006 bytes, was 163,198).

Animations replaced (76 actions): JumpF/B, JumpAerialF/B (spin ball), all Fall variants, Landing and the five aerial landings, Squat/SquatWait/SquatRv, RunBrake, DamageN/Hi/Lw/Air 1-3, DamageFly*, DamageFall (tumble), EscapeF/B (ball roll), every jab/tilt/smash/aerial/dash attack, and the specials' animations.

Attacks, from Falcon's values (v10) to Sonic's. Full table with angles, knockback and sizes: `work/v19/changes_v19.md`.

| Move | Was (v10: hit frames, total, damage) | Now (hit frames, total, IASA, damage) |
|---|---|---|
| Jab 1 (palm) | 3-5, 22, 3 | 3-4, 16, 14, 3 |
| Jab 2 (punch) | 4-6, 20, 3 | 3-5, 18, 16, 3 |
| Jab 3 (side kick) | 5-11, 32, 5 | 6-8, 28, 24, 5 foot / 4 shin |
| Dash attack (Spin Dash roll) | 7-16, 40, 9/6 | 6-9 then 10-16, 38, 36, 9/6 |
| Forward tilt (thrust kick) | 9-11, 30, 9 | 8-10, 28, 26, 9/8 |
| Up tilt (high kick) | 17-21, 40, 8 | 6-10, 28, 24, 8/7 |
| Down tilt (sweep) | 10-15, 36, 7 | 5-8, 22, 20, 7/6 |
| Forward smash (spinning kick) | 18-, 65, 15 | 15-17, 44, 42, 15/14 |
| Up smash (spin jump in place) | 21-28, 55, 5+8 | 4 hits of 2 (8-18) + 5 (20-22), 48, 44 |
| Down smash (split kick) | 19-32, 50, 13 | 8-10, 44, 40, 13 front / 11 back |
| Neutral air (spin) | 7-29, 45, 4/5 | 4-9 then 10-27, 39, 36, 9/5 |
| Forward air (axe kick) | 14-30, 40, 12/7 | sourspot 12-14 (7, sends forward); heel sweetspot 15-17 (12, angle 270 meteor), 42, 38 |
| Back air | 10-17, 36, 12/8 | 5-7 then 8-11, 34, 30, 12/8 |
| Up air (flip kick) | 6-12, 34, 10/8/6 | 5-7 then 8-10, 30, 28, 10/8 |
| Down air (drill) | 16-20, 45, 13 | 5 hits of 2 (6-23) + 3 (24-26), 44, 40 |

Specials: still Captain Falcon's behaviour and timing (data only). Sonic's animations are swapped in (spin charge, rolling ball, dash pose), Falcon's graphics and voice commands are removed from the scripts, fire element 1 -> 0, and damage is lowered: neutral B 27/25/23 -> 13, down B ground 15/12/9 -> 10/8/6, down B air 15/13/11 -> 10/9/8. The ball hitboxes sit on the body centre. Grab and throws are Falcon's.

Tests (`tests/move_test.py`, Sonic P1 vs standing Fox, Final Destination, memory-read percent):
- PASS: match loads, 15 moves run, no crash. Screenshots `test_logs/v19_shots_*.png`.
- First hit frame and damage as designed: jab 1 f3 3%, jab 2 f3 3%, jab 3 f6 5%, forward tilt f8 9%, up tilt f6 7% (shin), down tilt f5 7%, forward smash f15 15%, down smash f8 13%, dash attack f6 9%, down air f6 2%, grab works.
- Up smash: only the first hit (f8, 2%) and the last (f20) connected on a standing Fox. The hits do not link yet.
- Neutral air hit only with the late hitbox (f27, 5%) from a short hop next to Fox.
- Forward, back and up air did NOT hit in this test: the short hop carries Sonic over a standing Fox. Their hitboxes are untested in game, including the axe kick sweetspot/sourspot.

Not tested: knockback and launch on any character, other characters and percents, DI, IASA frames, landing lag, the specials, rolls, damage/tumble animations in game, the shield.
Known gaps: no swing sounds on the new attacks; Guard, Turn, ledge, throws, item and taunt animations are still Falcon's; portraits, icons and voice are Falcon's.

## v20: aerial fixes (2026-11-16)

File: `builds/Melee - Sonic v20.iso`. Package `work/sonic_package_v20.zip`. v19 deleted (user wants only the newest build kept). Animations unchanged from v19. Full table: `work/v19/changes_v20.md`.

Aerial sweep on v19 (`tests/move_test.py --air`, several input timings per aerial, standing Fox):
- Neutral air hit only with the late hitbox (5%).
- Forward air: the 7% sourspot always landed on its last frame (f14) and the heel never got to hit.
- Back air 8% (late hit), up air 10% (launch mostly upward), down air 2% per hit: all connect.

Changes (from -> to):
- Forward air sourspot frames 12-14 -> 11-13; heel sweetspot frames 15-17 -> 14-17, size 2.2 -> 2.6, offset (0.8,-0.5,0) -> (1.2,-0.5,0); the shin hitbox during the sweetspot 1.9 -> 1.6 and moved toward the knee.
- Spin-ball hitbox size (neutral air, dash attack, up smash) 4.2 -> 4.7; late neutral air 3.7 -> 4.1; late dash attack 3.6 -> 4.0.
- Up smash weak hits: angle 95 -> 88, set knockback 35 -> 18; final hit size 4.8 -> 5.4.

Tests on v20 (Sonic P1 vs standing Fox):
- PASS: forward air heel hits on f14 for 12% (fresh), 10.9% and 10% when staled. Late input still gives the sourspot (5.3% staled, sends forward and up).
- Up smash: 3 of 5 hits connect now (f8, f18, f22), was 2.
- Neutral air 5% late hit at f21. Dash attack f6 9%; it sends Fox behind Sonic because the ball passes through him.

Not tested: the heel's meteor on an airborne target (on a grounded Fox it only causes a flinch), the early 9% neutral air, the strong 12% back air, knockback at higher percents, other characters, DI.

## v21-v23: crash fixed, four real specials (2026-11-16)

File: `builds/Melee - Sonic v23.iso` (the only build kept; v20-v22 deleted). Package `work/sonic_package_v23.zip`. v21 = specials code, untested; v22 = v21 + crash fix; v23 = v22 + two changes below.

### Match-load crash: FIXED (v22)
- Cause, found by disassembling the game's part-visibility routines (0x80074B6C, 0x80074CA0, 0x80074D7C in the DOL): they walk `ftData -> model lookup -> costume 0 -> table -> group -> set` and use each byte of a set as an index into the fighter's model-part array. In Sonic's `PlSn.dat` the HighPoly and LowPoly lists had been shortened to 18 bytes (parts 0-17) when the model was first installed (v04, HSDRaw save), but their counts still said 44 and 35. The game read 26 and 17 bytes past the lists into the next structures (values 44, 127, 60, 80...) and set flags through whatever was in memory there. Which match crashed depended on that memory.
- Fix: `scripts/patch_lookup_all.py <in> <out> 18` sets the two counts in place: HighPoly 44 -> 18, LowPoly 35 -> 18. Metal tables (7 and 10 entries, all < 18) are untouched. Costumes 1-5 have no tables.
- Tests on v22 (`tests/kirby_test.py`, 150 frames each): Fox P1 + Sonic P2 OK, Kirby P1 + Sonic P2 OK, Sonic P1 + Kirby P2 OK, Sonic P1 + Fox P2 OK. Full Kirby test (inhale, swallow, use copied B): 572 frames, no crash. v23: Kirby+Sonic and Fox+Sonic OK.
- Not tested: 3-4 players, other stages, Sonic's other four colours in a match, metal box.

### Specials (custom code, `fighter_code/sonic.c`, built with MexTK + Zig, appended with `append_dat_root.py`)
Sonic now has his own action states 341-345 (m-ex `move_logic` table) instead of Falcon's. The old Homing Attack freeze is gone with the rewrite (own state, target re-found every frame, guarded distance).

| Special | State | Behaviour | Hitbox (game frames) |
|---|---|---|---|
| Neutral B: Homing Attack | 341 | From ground or air: flies at 3.4/frame at the nearest fighter within 75 units, steering each frame for up to 24 frames. On hit: pops up and back (2.4 up) into a normal fall. No target: 12-frame forward air dash (2.8). | ball 1-40: 8%, angle 60, BKB 40, KBG 70 |
| Side B: Spin Dash | 342 charge, 343 roll | Ground: hold B to rev (8 to 45 frames, auto-release at 60), release to roll at 2.4 to 4.2/frame, slowing 2.5% per frame, 34 frames. Rolling off a ledge drops into a fall. In the air: the plain forward air dash. | roll 1-32: 10%, angle 50, BKB 35, KBG 75 |
| Up B: Light Speed Dash | 344 | Straight dash in the stick direction (up and slightly forward by default) at 3.3/frame for 12 frames, then helpless fall. Grabs ledges. | body 2-16: 6%, angle 70, BKB 30, KBG 60 |
| Down B: Bounce Attack | 345 | Ground: small hop (2.4) then plunge. Air: plunge at once, accelerating 0.45/frame to 4.6. Rebounds 3.0 off the floor into a normal fall; on hit a 2.2 rebound. | ball 3-60: 9%, angle 70, BKB 30, KBG 80 |

v23 changes after the first test:
- Neutral B miss: helpless fall -> normal fall (user request). To stop endless air dashing, a miss sets the jump counter to max+1, which blocks another Homing Attack and the double jump until landing (the game clears it on landing). A hit does not set it.
- Up B: speed 3.6 -> 3.3, straight phase 14 -> 12 frames, end 24 -> 22 (height measured 67.6 -> 55.1 units).

Tests on v23 (`tests/move_test.py --specials`, Sonic P1 vs standing Fox):
- Homing Attack from 40 units: hits for 8% and bounces to y 18.8, then lands. No freeze.
- Homing miss: ends in FALLING (not DEAD_FALL).
- Spin Dash: tap travels 69 units and hits for 10%; 40-frame charge travels 105 units.
- Light Speed Dash straight up: 55 units, then helpless fall and landing.
- Bounce Attack from ground and air: hits for 9% and rebounds (y up to 21).

Not tested: Homing Attack in the air after a miss (the block), against moving or airborne targets; Spin Dash off a ledge; Light Speed Dash directions other than up, and its ledge grab; Bounce on platforms; any special on other characters; shield interactions. Up B with a diagonal stick came out as side B in the test (input overlap), not a code fault.
Known: specials have no sound or effects; the side B travel when fully charged (105 units) is probably too long.

## v24 (in progress, paused by the user 2026-11-17): spin-ball model

File: `builds/Melee - Sonic v24.iso`, package `work/sonic_package_v24.zip`. Built but NOT yet verified in game (the capture test was stopped when the user paused). v23 is kept until v24 is checked.

User feedback on v23: "spin dash doesnt look like spin dash". The capture showed a curled-up Sonic tumbling with his shoes out, not a ball.

Changes:
- `scripts/build_sonic_costume_ball.py`: same body as v10 (18 parts, bound data identical) plus part 18, a sphere (radius 4.5, centred on the curl pivot of bone 2) textured with SA1's own spin sprite `stx_newspin`. Same model in all five costume files.
- `scripts/patch_ball_sets.py`: HighPoly and LowPoly visibility groups get two sets: set 0 = body parts 0-17 (default), set 1 = the ball. Appended data plus two new relocation entries.
- `scripts/sonic_moves.py`: the script command "Change Model State (group 0, set 1)" shows the ball and hides the body during the jumps, neutral air, dash attack, up smash, Homing Attack, Spin Dash charge and roll, and Bounce Attack; set 0 is restored on the listed frame or left to the action change. Ground ball height: hip offset -5.3 -> -7.1 so the ball rests on its radius.

To check next: that the ball shows and the body hides, that the body comes back when the action ends (if not, add an explicit revert), ball size/texture look, and that matches still load on port 2 and with Kirby. Then: shield, turn, ledge and grab/throw animations.

## v25-v31: textures, eyes, spin ball, speed, reworked animations (2026-11-17/18)

File: `builds/Melee - Sonic v31.iso` (the only build kept; v23-v30 deleted). Package `work/sonic_package_v31.zip`. v24's spin ball is confirmed working (below). v25-v30 were eye/texture iterations.

User reports: wrong textures and no pupils ("creepy"), Spin Dash did not look like a Spin Dash, wanted more speed and better forward/back/down air, up tilt and up B animations, and a sharper ball texture.

### Model (`scripts/build_sonic_costume_ball.py`, all five costume files)
- Texture colour: the SA1 material colour is no longer multiplied into the textures. That had turned the iris black and tinted the skin orange and the soles dark red.
- Quill textures (`stx_btest1`, `stx_head`) x1.35 brightness.
- Material colours: diffuse 179 -> 255, ambient 179 -> 200. The user sent a dark screenshot afterwards; I started reverting this and was told to ignore that shot, so it stays. If Sonic looks too dark on normal stages, this is the first thing to revert.
- Pupils: the irises sit on the very front of the eyes, so Melee's side-on camera only saw their edge. Each iris is now turned 42 degrees toward its own side about a point inside the head, lifted 0.6 off the surface and drawn double-sided. Confirmed in game (`test_logs/v31_heads.png`): green iris and pupil visible from the side and mid-turn.
- Tried and removed: lifting the eye whites (v27-v30) let more of the blue brow cover them. A thin blue brow line across the eye remains.
- Spin ball: part 18, a sphere (radius 4.5, 10x18 segments) with SA1's spin sprite upscaled 64 -> 256 and sharpened. `scripts/patch_ball_sets.py` adds a second visibility set; the script command Change Model State (group 0, set 1) shows it. Confirmed in game on v25: ball during Spin Dash charge/roll and neutral air, body back on landing. Used in jumps, neutral air, dash attack, up smash, Homing Attack, Spin Dash, Bounce Attack.
- `scripts/make_spin_texture.py` (a generated ball texture) gave a poor result and is not used.

### Speed (from -> to, `patch_attributes.ps1`)
InitialDashSpeed 2.0 -> 2.3; InitialRunSpeed 2.4 -> 2.9; MaxWalkSpeed 0.85 -> 1.3; WalkAcceleration 0.1 -> 0.15; MaxAerialHorizontalSpeed 1.0 -> 1.2; AerialSpeed 0.04 -> 0.06.

### Animations reworked (`scripts/sonic_moves.py`; hit frames and damage unchanged unless listed)
- Up tilt: standing high kick -> backflip kick on the spot (both feet, frames 6-10, 8%).
- Forward air: bigger wind-up (curl, leg overhead, body leaning back) and a forward chop with the whole body.
- Back air: one-leg back kick -> both legs thrust straight back with the body horizontal; hitboxes on both feet (12% early, 8% late).
- Down air: both feet together pointing down, arms overhead, 5 turns; foot hitbox 2.4 -> 2.6, last hit 2.6 -> 2.8.
- Up B: curl, then a straight arrow pose with arms swept back, somersault out.
- Ground ball height: hip offset -5.3 -> -7.1 for ball moves.

### Tests on v31 (Sonic P1 vs standing Fox)
- Hit frame and damage as before: jab 1/2/3 (f3 3%, f3 3%, f6 5%), forward tilt f8 9%, up tilt f6 7%, down tilt f5 7%, forward smash f15 15%, down smash f8 13%, grab works, neutral air f26 5%, down air f6 2%.
- Up smash connected only with its last hit (f20, 5%) this run.
- Dash attack did NOT hit: with the faster dash Sonic runs past Fox before the attack starts (travelled 65.7 units from 30 away). The test distance needs raising; the move itself may also travel too far now.
- Forward, back and up air did not hit at this test's timing (same as v19; they hit in the v20/v23 timing sweeps, which were not rerun).

Not tested on v31: the specials, the reworked aerial animations' look in game, the new speed values measured, port 2 / Kirby load (unchanged files since v23 except the costume and visibility sets), other colours.
Test harness: `tests/harness.py` can open a larger window at 3x internal resolution (`move_test.py --big --faceshot`) for close-ups.

## v32-v34: solid model, new kicks, up smash links, back air, up B, shield, ledge, throws (2026-11-18)

File: `builds/Melee - Sonic v34.iso` (only build kept). Package `work/sonic_package_v34.zip`.

User reports on v31: model see-through (no face from the front, soles visible through the shoes); forward smash and kicks "don't look proper"; up smash should connect; back air should make sense; much better up B; add shield, ledge and throws; then "eyes look off still".

### Model
- See-through fixed: every part had the generator's CULLFRONT flag, which with these polygon windings drew only the far side of each part. Flags are now ENVELOPE only (both sides drawn). Confirmed by the user's own screenshot (face, shoes solid).
- Eyes (v34): iris turn 42 -> 16 degrees, lift 0.6 -> 0.2, each iris 1.2x larger. The 42-degree turn dated from when the face was not rendering and looked wall-eyed once it did.

### Moves (`scripts/sonic_moves.py`; damage and hit frames unchanged unless listed)
- Jab 3, forward tilt, forward smash: thrust kick -> side kick with the left leg (body turns chest-to-camera and leans away, sole first). Forward smash spins once into it. Hitboxes moved from the right leg to the left.
- Up smash: the ball now spins on the floor for the four weak hits and leaps only for the last. Weak hits angle 88 -> 90, set knockback 18 -> 14; last hit size 5.4 -> 5.6. Test: all five hits connect on Fox (f8, 11, 14, 17, 20).
- Back air: both-legs thrust -> turn toward the camera and side-kick straight back with the right leg (12% early, 8% late, right leg hitboxes).
- Up B: 4-frame ball flash, then one of two poses picked by the code (`fighter_code/sonic.c`, new state 346): mostly upward = rising corkscrew with one fist up (3 turns); mostly sideways = head-first flying pose. Somersault out. Body hitbox size 3.6 -> 3.8.
- Shield: new guard pose (GuardOn, Guard, GuardOff, GuardDamage); the bubble bone is held 9.4 units above the floor (8.3 in v33 left the head out).
- Ledge: CliffCatch, CliffWait1/2 hanging pose, hands placed where Falcon's scaled animation had them. Climb, attack, roll and jump from the ledge are still Falcon's.
- Grab and throws: new Catch, CatchDash, CatchWait, CatchAttack (knee), CatchCut, ThrowF (punch), ThrowB (turn and side kick), ThrowHi (uppercut), ThrowLw (slam). Falcon's scripts, damage and timings are unchanged.

### Tests
- v32: forward smash f15 15%; up smash 5/5 hits; up B rises 55 units.
- v33: shield comes up; grab connects (f6); forward throw 4%, back throw 5% + 4%, up throw 7%, down throw 7%; Fox P1 + Sonic P2 and Kirby P1 + Sonic P2 load without a crash.
- v34: face and shield captured (`test_logs/v34_sheet.png`); irises visible near the front of the eye, shield covers most of the head.

Not tested: ledge hang in game, sideways up B pose, back air and the other aerials' hits after the rework, dash attack distance with the faster dash, the look of each throw on the victim, other colours.

## v35: quick pass under a 20-minute limit (2026-11-18)

File: `builds/Melee - Sonic v35.iso` (only build kept). Package `work/sonic_package_v35.zip`.

User reports on v34: ledge hang broken; eyes cross-eyed and creepy when not side-on; animations still buggy; shield distorts the limbs; wants more end lag on neutral B and down B, classic-Sonic movement feel and crouch, slightly more range, sharper textures, fixed up B and down air. Also asked for side B more like SSF2, animations based on Ultimate or free online ones, and more references to games up to SA2: NOT done (see below).

Changes:
- Eyes: irises back at SA1's own position (turn 16 -> 0 degrees, scale 1.2 -> 1.0, lift 0.2 -> 0.06). The outward turn was a workaround from before the model was drawn solid.
- Textures: every texture under 128 px is upscaled 4x (Lanczos) before encoding. Costume file 221 KB -> 826 KB.
- Shield: crossed-arm guard pose -> plain braced stance with arms low in front.
- Ledge: my CliffCatch/CliffWait1/CliffWait2 removed; the game's (Falcon's scaled) hang is back.
- Crouch: tucked right down with knees up and head lowered (classic Sonic duck). Also used by landings and move wind-ups.
- Full-body yaw spins removed (likely source of flicker): forward smash goes straight into the side kick, up B (up) holds the fist-up pose, down air holds a both-feet stomp with a small bob instead of spinning.
- Range: every authored hitbox size x1.12 (`RANGE` in `sonic_anim_lib.py`).
- End lag (`fighter_code/sonic.c`): Homing Attack stays in its state 14 more frames after the dash (slows and falls, cannot act); a hit still releases at once. Bounce Attack: 18 frames after the rebound (or after a hit) before he can act; a second floor contact lands normally.
- Movement (from -> to, vs v34): InitialDashSpeed 2.3 -> 1.9, InitialRunSpeed 2.9 -> 3.1, WalkAcceleration 0.15 -> 0.08, Friction 0.06 -> 0.045, Gravity 0.15 -> 0.13. Slow start, high top speed, slidier stops, floatier jump.

Test (v35, `move_test.py --specials`): match loads; Homing Attack 8%, Spin Dash 10% (tap now travels 75 units, charged 116: longer because of the lower friction/top speed), Light Speed Dash rises 55, Bounce Attack 9% from ground and air and still rebounds.
Not tested: how the eyes, shield, crouch, up B and down air look in game; the end lag lengths measured; normal attacks after the range change; port 2 / Kirby load on this build.

Not done, and why:
- Ultimate / online animations: Ultimate's animation files are Nintendo's assets on a different skeleton; using rips conflicts with the project's copyright rule and needs a converter that does not exist here. No time to look for free-licensed motion data.
- Side B "like SSF2": the original brief says not to copy SSF2 files or values; a look-alike (hop on release, charge dust) needs new code and effects.
- More references to Sonic 1-SA2, per-move: not started.

## v36 (2026-11-18)

File: `builds/Melee - Sonic v36.iso` (only build kept). v35 checked in game first (`test_logs/v35_sheet.png`): side-kick forward smash, shield, crouch and up B pose all render correctly.
- Spin Dash roll: base speed 2.4 -> 2.2, charge bonus 1.8 -> 1.5, per-frame slowdown 2.5% -> 5%. Measured travel: tap 75 -> 41 units, 40-frame charge 116 -> 60. Still hits for 10%.
- Taunt (AppealR/AppealL): Sonic turns to the camera and wags his finger (Sonic 1 title screen / Sonic CD / SA1 reference). Not yet looked at in game.

## v37 (2026-11-18)

File: `builds/Melee - Sonic v37.iso` (only build kept).
- Aerial sweep on v36: neutral air early hit 9%, forward air heel 12% (f14), back air 12%, up air 10%, down air 2% all connect on a standing Fox with the right timing. The hop is higher now (gravity 0.13, peak 14.9), so aerials must be done later in the jump.
- Bug found and fixed: back air hit twice (12% at f7, then 7.3% at f9) because the script cleared the hitboxes before creating the weaker late ones, which let them hit again. `make_script` now skips the clear when a hit decays straight into a weaker one with the same IDs (back air, neutral air, dash attack, up air). v37 test: back air hits once (12%, 10.9%, 10% staled).
- Also measured on v36: up smash 5/5 hits, dash attack f6 9%.
- v37 load tests: Fox P1 + Sonic P2 and Kirby P1 + Sonic P2 checked (see test_logs/v37_*.out).

## v38: classic references, Sonic 1 to SA2 only (2026-11-18)

File: `builds/Melee - Sonic v38.iso` (only build kept). Animations only; no values changed.
- Taunt (AppealR/L): turns to the player and wags a finger (Sonic 1 title screen / Sonic CD / SA1). Confirmed in game (`test_logs/v38_sheet.png`); the eyes also look right from the front there.
- Idle 3 (Wait3): impatient foot tap, hands on hips, looking out at the player (Sonic 1/2/3). Not seen in game yet (plays at random).
- Edge teeter (Ottotto, OttottoWait): leaning over the edge with arms windmilling (Sonic 1/2/3). Not seen in game yet.
- Launched upward (DamageFlyTop): arms and legs flung out, facing the player (Sonic 1 hit sprite). Not seen in game yet.
- Helpless fall after up B (FallSpecial*): spring-jump pose, arms straight up. Confirmed in game.
Already in from earlier builds: SA1 idle/walk/run animations and spin sprite, Spin Dash (Sonic 2), Homing Attack and Light Speed Dash (SA1), Bounce Attack (SA2), classic crouch, skid.

## v39-v40: Sonic 1 crouch (2026-11-18)

File: `builds/Melee - Sonic v40.iso` (only build kept). Animation only.
- Squat / SquatWait / SquatRv use a dedicated `DUCK` pose (Sonic 1 duck): sitting down on the heels, knees up, body curled over them, arms round the shins. Landings and attack wind-ups keep the older `CROUCH` pose.
- v39 tucked the head so far that the face was hidden (`test_logs/v39_crouch.png`); v40 lifts it (chest 62 -> 50, head 28 -> -22) so he looks down and forward as in the sprite. Confirmed in game: `test_logs/v40_crouch.png`. Down tilt still comes out of the crouch and hits f5 for 7% (v39 test).

## v41-v44: Chaos Emerald forward tilt, ledge hang, Spin Dash hop (2026-11-18)

File: `builds/Melee - Sonic v44.iso` (only build kept). v41 and v43 were defective and are deleted (see below).

- Chaos Emerald (SA1/SA2 reference): new model part 19, a cut green gem (own mesh and texture) on the right-hand bone, anchored to the glove tip and pointing outward. Hidden unless a script shows it.
- Visibility: `scripts/patch_ball_sets.py` now makes two groups. Group 0: set 0 body, set 1 spin ball. Group 1: set 0 nothing, set 1 emerald. Lookup count 1 -> 2 and all four tables get 2-entry arrays.
  - v41 defect: I first added a third set "body + emerald" to group 0. The game hides every part named by a non-selected set, so the body list in set 2 hid Sonic's whole body while standing. A part must be in one set only.
  - v43 defect: a Windows path with `\a`/`\v` escapes in `sonic_moves.py` broke the build step and an ISO was made from an incomplete package.
- Forward tilt (all five angles) is now the emerald thrust, replacing the side kick (jab 3 and forward smash keep the side kick). From -> to: hit frames 8-10 -> 8-11; damage 9 foot / 8 shin -> 10 on the gem / 7 on the forearm; angle 361; BKB 12 -> 15 (gem); KBG 95. Gem hitbox radius 2.4 (x1.12 range) centred 1.4 units past the glove tip, where Sonic has no hurtbox (disjoint).
  - Test v44: hits f8 for 10% at 10.2 units; misses at 13.6 and 14.5. Capture `test_logs/v44_emerald.png` shows the gem beyond the hand. The gem texture is rather dark.
- Ledge hang (CliffCatch, CliffWait1/2) redone: bones 1-3 keep the game's own tracks so the body sits where the game expects, and only Sonic's limbs are keyed (arms up, legs dangling). Not seen in game.
- Spin Dash roll: small hop as the roll is released (hip offset -7.1 -> -4.8 at frame 4, back by frame 9). Roll still hits for 10% and travels 41 units on a tap.

## v45-v46: kill forward tilt, emerald boomerang, SSF2-style Light Dash (2026-11-18)

File: `builds/Melee - Sonic v46.iso` (only build kept).

User: "just copy the move as a whole" (side B, after SSF2), "make f-tilt a kill move", "make down tilt throw out a chaos emerald like a boomerang". The user's instruction to copy SSF2's move overrides the original brief's "no SSF2" rule for this one move. No SSF2 files were used; the behaviour was rebuilt from public descriptions (McLeodGaming and Miraheze wikis): pause, fast forward dash, angle up/down diagonally, sweetspot and weak hit (16% / 5%), helpless in the air.

- Chaos Emerald now rides an otherwise unused bone (62, child of the root) that animations can place anywhere (`prop=` in `sonic_anim_lib.py`). Brighter facet texture.
- Forward tilt (emerald thrust), from -> to: damage 10 -> 13, BKB 15 -> 40, KBG 95 -> 110, hitbox now on the emerald bone. Test: f8, 13%; launch speed at 0% (1.66, 1.60) vs (0.89, 0.86) before.
- Down tilt: side sweep -> emerald boomerang. Total 22 -> 34 frames, IASA 20 -> 31. The emerald leaves the hand at f6, spins out to 17 units along the floor by f13 and returns by f25. Hits: out f6-13 6% (angle 70, BKB 25, KBG 60, radius 2.2); return f14-25 4% (angle 80, BKB 15, KBG 50). It is a hitbox carried by the move, not a separate projectile: it stops if Sonic is interrupted. Test: at 9 units both hits connect (6% f6, 3.6% f15); at 18 units the outward hit connects (f9).
- Side B = Light Dash (`fighter_code/sonic.c` states 347-350): 18-frame pause, then 3.9 units/frame for 12 frames. On the floor it runs along the ground and skids to a stop (30 frames total). In the air, or with the stick held up/down as it starts, it goes straight or 30 degrees up/down and ends in helpless fall. Hitbox: sweetspot f1-4 16% (BKB 40, KBG 100), then f5-14 5% (BKB 20, KBG 60). v45 used 4.4 x 14 frames and travelled 83 (ground) / 105 (air) units; v46 travels 66 / 84.
  Test v46: from 12 units the sweetspot hits (14.6% staled, launch (1.86, 1.80)); from 48 units the weak hit (5%); air version ends in DEAD_FALL. Captures `test_logs/v46_sheet.png`.
- Down B on the ground is now the Spin Dash (hold B to rev, release to roll), as in SSF2; in the air it is still the Bounce Attack. Test v45: Spin Dash 9.1% (staled), 48 units with a 20-frame hold; Bounce 9%.
- The forward air-dash that side B did in the air before is gone.

Not tested: Light Dash diagonals, Light Dash off a ledge, emerald moves against shields, port 2 / Kirby load on v46, how the kill power of forward tilt scales at high percent.

## v47-v48: smash/tilt swap, gem damage and glint, Light Dash trail, mouth (2026-11-18)

File: `builds/Melee - Sonic v48.iso` (only build kept).

Model parts now (`scripts/build_sonic_costume_ball.py`): 0-17 body, 18 mouth, 19 spin ball, 20 Chaos Emerald, 21 emerald glint, 22 light-speed trail. `scripts/patch_ball_sets.py <in> <out> 19` builds three visibility groups: group 0 body(0-18) | ball; group 1 nothing | emerald + glint; group 2 nothing | trail. Lookup count 1 -> 3.

- Swap: forward smash is now the Chaos Emerald thrust; forward tilt is the side kick again.
  - Forward smash, from (side kick) -> to (emerald): hit frames 15-17 -> 15-18; damage 15 foot / 14 shin -> 18 gem / 12 forearm; BKB 30 -> 35 (gem); KBG 98 -> 104; charge from f7 as before; total 44. Test: f15, 18%, launch at 0% (1.81, 1.74). Misses at 16 units.
  - Forward tilt, from (emerald, v46) -> to (side kick): 13% BKB 40 KBG 110 -> 9% foot / 8% shin, BKB 12, KBG 95, frames 8-10. Test: f8, 9%.
- Gem damage: down tilt boomerang 6% out / 4% back -> 8% / 5%. Test: 8% (f6) and 4.5% staled (f16).
- Glint: a white four-point star (two in the camera plane, one across) fixed on the emerald, shown with it. Visible in `test_logs/v47_sheet.png`.
- Light Dash trail: a tapering pale-blue-to-white streak 20 units long behind Sonic during side B frames 1-16 (prop bone 62 follows the hips). Seen in game in v47 (looked grey-blue; brightened in v48, not re-captured mid-dash).
- Mouth: SA1 keeps the mouth on a separate head model, so a thin dark smile is added on the muzzle (arc on a sphere fitted to the cheek polygons). v47 put it too low and wide (a line under the chin); v48: centre elevation -34 -> -17 degrees, half-width 62 -> 36 degrees, thinner. Confirmed from the front in `test_logs/v48_face.png`. It is part of the body set, so it hides with the body during ball moves.

Not tested on v48: port 2 / Kirby load, the trail's new colour mid-dash, the mouth from a pure side view up close, emerald hits on shield.

## v49-v51: mouth on the face, open mouth on attacks, forward smash rework (2026-11-19)

File: `builds/Melee - Sonic v51.iso` (only build kept). Package `work/sonic_package_v51.zip`.

User on v48: "the mouth isn't even in the right spot", "fix the mouth animations and fsmash animation", "make his fsmash do more damage when it hits the chaos emerald".

- Mouth position: v47/v48 placed the smile on a sphere fitted to the cheek polygons, which put it about 1.5 units in front of and below the muzzle. A face map by ray-casting showed the muzzle front at height 11.4-12.2 just under the nose (y 12.7). v49 casts every mouth point straight onto the head's skin triangles (`onface()` in `build_sonic_costume_ball.py`) at height 11.6 (corners up 0.24), lifted 0.13 off the skin.
- Mouth animation: new part 23, an open D-shaped mouth (dark red), lifted 0.19 so it covers the smile. Visibility group 3: set 0 nothing, set 1 open mouth. Every authored attack that is not a ball move opens it 3 frames before its first hit and closes it 5 frames after its last (`make_script`).
  - v49/v50 had the smile as the default set of its own group; the game did not draw it (captures showed no smile). v51 puts the smile in the body set (group 0, set 0 = parts 0-18), which also hides it during ball moves.
  - Confirmed in game (`test_logs/v51_faces.png`): smile under the nose from the front; open mouth during forward smash.
- Forward smash: wind-up now peaks on the charge frame (7) with the gem raised back over the shoulder and knees bent, then a lunge (3.5 units forward travel) driving the gem out at chest height, with follow-through. Gem hit, from -> to: damage 18 -> 22, size 2.6 -> 2.7, KBG 104 -> 102 (BKB 35); forearm hit unchanged (12%). Emerald shown frames 3-28. Test v49: f15, 22%, launch at 0% (2.08, 2.01) (was (1.81, 1.74)).

Not tested on v51: port 2 / Kirby load (only the model and visibility tables changed since v46's test), the open mouth on every move.

## v52-v53: neutral B end lag, Sonic CD up B, faster Spin Dash, forward smash gem boomerang (2026-11-19)

File: `builds/Melee - Sonic v53.iso` (only build kept). v52 = all changes; v53 = v52 with the speed trail removed from the rising up B (it pointed sideways).

- Neutral B (Homing Attack), `fighter_code/sonic.c`, from -> to: end lag after a miss 14 -> 24 frames; after a hit Sonic popped up and could act at once -> stays in the move for 12 frames (pops up and back, slowing) before he can act. Test: homing hit 8%, miss lands without acting.
- Up B (Light Speed Dash), Sonic CD reference: the ball flash is replaced by the Super Peel-Out. He revs his legs into the figure-8 blur in place for 6 frames, then rises (fist up) or flies (head first) with the legs still spinning like wheels (100 degrees per frame, left/right half a turn apart). Sideways version keeps the light-speed trail; rising version has none. Hitbox unchanged. Test: rises 55 units, ends helpless.
- Spin Dash (ground down B), from -> to: base roll speed 2.2 -> 3.0, charge bonus 1.5 -> 1.6, slowdown 5% -> 3% per frame. Test: tap reached Fox at 40 units on f11 (was f20) and travelled 84 units (was 41); 40-frame charge 116 units. Still 10% (9.1% staled).
- Forward smash gem, from -> to: damage 22 -> 18, hitbox size 2.7 -> 3.0, and the gem now leaves the hand on the thrust and spins out 4.5 units (and 0.4 up) like a small boomerang, back by frame 24. Test: hits at 10.2, 15.0 and 17.1 units (v49 missed at 16-18); 18% fresh, launch at 0% (1.79, 1.72).
- Glint: star 2.6 -> 3.8 units long, 0.32 -> 0.5 wide, two diagonal rays added, full ambient (always lit white). Visible in `test_logs/v52_sheet.png`.
- Load test v53: Fox P1 + Sonic P2 and Kirby P1 + Sonic P2 OK.

Not tested: the exact homing hit end lag in frames, Spin Dash off a ledge at the new speed (it may fly further off stage), forward smash charged damage.
