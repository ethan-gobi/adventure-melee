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

## v54-v56: move swaps, Peel-Out aim, down B jump cancel, movement feel, crouch, Sonic Adventure sounds (2026-11-20/22)

Files: v54, v55 and v56 were built in turn (only the newest ISO is kept). Package `work/sonic_package_v56.zip` (model `work/v19/PlSnNr_v54.dat`).

User: "fix the cd upb", "make fsmash boomerang", "add endlag to neutral special", "make down b jump cancelable after two seconds", "up b looks super weird", "increase his speed a little bit and his friction, his wavedash is a tadbit too strong and he feels super slippery", "make the downtilt the forward tilt and make the new down tilt the somersault", "fix the mouth animations and add sound effects from sonic adventure", "make his crouch animation look like this" (reference picture), "the figure 8 running animation looks kinda goofy and really really bugged".

- Forward tilt: the old down tilt (Chaos Emerald thrown out like a boomerang) moves here. From -> to: old forward tilt (28 frames, kick 8-10, 8-9%) -> 32 frames, gem out f6-13 8% (angle 70), gem back f14-25 5% (angle 80).
- Down tilt: new SA2 Somersault. 26 frames: ball roll f4-10 4% (set KB 22, size 4.0), kick f12-14 5% (angle 85). Old down tilt (34 frames) moved to forward tilt.
- Forward smash: the gem now flies out and back like a boomerang. From -> to: 44 -> 50 frames, IASA 42 -> 46; gem 18% f15-18 size 3.0 -> 17% f15-24 size 2.8 (BKB 35, KBG 102 -> 100); new return hit f25-38 8%; forearm hit 12% removed. Test v56: 17% at f16 face to face, then 7.3% on the return; 16% at 24 units.
- Neutral air: early hit size 4.7 -> 5.8 with the SA1-era Insta-Shield crescent (new model part 25, shown f4-10).
- Neutral B (Homing Attack, `fighter_code/sonic.c`), from -> to: end lag 24 -> 32 frames, hit lag 12 -> 20 frames, landing during the move normal landing (4 frames) -> special landing 14 frames. Test v56: hit 8%; miss ends in LANDING_SPECIAL.
- Down B (Spin Dash): rev can be held 60 -> 180 frames before it releases by itself. New: jump cancels the move once 120 frames (2 seconds) have passed since down B started (rev + roll); before that, jump does nothing. Test v56: jump at frame 124 -> KNEE_BEND, jump; jump at frame 40 -> no jump, Spin Dash continued (10%).
- Up B (Super Peel-Out, Sonic CD): rev 6 -> 8 frames, total 22 -> 30 frames. v55 aims at the end of the rev (v54 used the stick at the B press). The figure-8 leg blur was removed from up B and from the run in v56 (user: "goofy and bugged"); legs alternate between two running poses every 2 frames instead.
- Attributes (`patch_attributes.ps1`), from -> to: InitialDashSpeed 1.9 -> 2.1, InitialRunSpeed 3.1 -> 3.3, StopTurnInitialSpeedA 0.15 -> 0.2, MaxWalkSpeed 1.3 -> 1.45, WalkAcceleration 0.08 -> 0.11, Friction 0.045 -> 0.08 (shorter wavedash, less slippery). Gravity 0.13, air speed 1.2 and air acceleration 0.06 unchanged.
- Crouch (v56): rebuilt from the user's reference: low on the heels, curled forward, head bowed, right glove over the top of the head (two-bone arm IK `reach()` and `head_point()` in `sonic_anim_lib.py`). Seen in `test_logs/v56_big_crouch_30.png`.
- Sounds (v56): Sonic's own sound bank `sonic.ssm` (bank index 56, IDs 560000+), 14 sounds taken from the user's Sonic Adventure (Dreamcast) files: homing attack, Light Dash hold/launch/attack, Spin Dash charge/release, swipe, 5 short voice grunts and 2 hurt voices (`scripts/extract_sa1_sounds.py` decodes the MLT/ADPCM banks, `scripts/make_sonic_soundbank.py` picks and resamples, `build_iso.ps1 -SoundBank` adds the bank). Move cues added in `sonic_moves.py` (SFX table); 25 voice IDs in kept Falcon scripts were remapped from Falcon's voice bank to Sonic's grunts/hurt sounds.
- Tests v56: load test Sonic P1 + Fox P2 OK (150 frames, no crash). Move test (`test_logs/v56_big.out`) results as above.

Not verified: the voice clips were chosen by length only (nobody has listened to them yet); the sounds' volume against Melee's.

## v57: mouth wraps round the muzzle, Peel-Out hitbox covers the whole dash (2026-11-22)

File: `builds/Melee - Sonic v57.iso`. Package `work/sonic_package_v57.zip`, model `work/v19/PlSnNr_v57.dat`.

- Mouth: a close-up renderer (`scripts/face_preview.py`, software render of the model's `_bound.json`) showed that the v49-v56 mouth, cast straight back onto the muzzle front, was only a dot from the side, and the open mouth a red smudge. Melee shows Sonic side-on almost all the time. v57 casts the mouth radially around the muzzle axis, so it wraps round the muzzle from -60 to +60 degrees with the corners turning up 0.5 at the sides (the Adventure-era side smirk). Line half-thickness 0.075 -> 0.06 at the front, 0.11 at the corners. The open mouth is deepest at the front (0.75) and closes toward the corners, with a pink tongue (same part 23, two-colour texture). Preview: `test_logs/v57_face_preview.png` (rows: smile, open, open from 3 angles).
- Up B (Peel-Out) hitbox, from -> to: active frames 9-22 -> 9-29. In v56 the sideways dash reached a target 60 units away after the hitbox had ended (NO HIT). Damage 6% unchanged.
- Tests v57: load test Sonic P1 + Fox P2 OK (150 frames, no crash). Move test (`test_logs/v57_big.out`): up B sideways now hits Fox at 60 units on f25 for 6% (v56: no hit); every other move unchanged from v56 (forward smash 17% + 7.3% return, forward tilt 8% + 4.5%, Somersault 4% + 4.5%, homing 8% / miss -> special landing, down B jump cancel at 2 s works and is blocked at f40).

Not verified on v57: the new mouth in game at close range (the in-game test camera is too far out to see it; checked only in the offline render).

## v58-v63: Homing Attack lag, real shield fix, knockdown/grab/item animations, smaller mouth (2026-11-23)

File: `builds/Melee - Sonic v63.iso` (only build kept; v62 + the shield pose fix). v57, v60, v61, v62 deleted. Packages `work/sonic_package_v62.zip` / `v63.zip`, model `work/v19/PlSnNr_v61.dat`, fighter code `work/v19/ftFunction_v61.dat`.

User: "add more endlag to neutral b", "fix his model when shielding ... something to do with falcons limbs being sonics", "fix his ledge getup and tech animations also the game js straight up crashes", "fix his mouth animations his mouth is wayy too big", "fix the model its still broken and add other moves and references keep adding stuff".

- Crash (v58, v59 froze on match load): PlSnAJ.dat had grown to 1,353,664 bytes; every build up to 1,342,912 loaded. `write_anims` now keeps only the keys needed (`thin()`), v60 974,464 bytes, v62 624,000 bytes. Loads every time.
- Neutral B (Homing Attack, `fighter_code/sonic.c`), from -> to: end lag after a miss 32 (v57, only about 16 played) -> 44 (v58) -> 60; lag after a hit 20 -> 26 -> 34; landing lag after a miss 14 -> 20 -> 28, and a miss that lands now takes its remaining end lag as landing lag, capped 36 -> 48; landing lag after a hit 14 -> 20 (unchanged in v61+). Animation 40 -> 70 -> 90 frames, hitbox f1-40 -> f1-24. Test v62: miss from the ground = 27 frames + 45 landing, actionable frame 73 (v60: 57, v57: 40); hit = 47 frames + 20 landing, actionable frame 68 (v60: 60), 8%.
- Shield, the real cause (found v62 with `tests/bone_probe.py`, which reads bone positions from game memory): while a shield is held the game does not use the Guard animations at all. It copies a guard pose skeleton stored in PlSn.dat (ftData + 0x20), and that still held Captain Falcon's pose with Falcon's full-size bone offsets (hips 13.85 vs Sonic 9.62, shin 4.68 vs 2.13, forearm 2.77 vs 1.34), which pulled Sonic's parts apart. v58-v60's Guard animation edits only ever showed while raising/dropping the shield. v63 writes Sonic's own pose into that block (`sonic_anim_lib.write_shield_pose`, `scripts/patch_shield_pose.py`; the moves build does it too).
- Shield look: Sonic guards curled into his spin ball (Sonic 1-3). The game ignores model changes in guard scripts, so the ball model is switched on by a per-frame hook (`OnFrame` in sonic.c, states 178/179/181/182). Bubble bone height 9.4 -> 6.6 (v58) -> 4.6 (ball centre). v62 test: ball shows but sat at the top of the bubble (Falcon pose block). v63 test (`test_logs/v63_sh_shield_hit_*.png`): ball centred in the bubble on the floor through the whole held shield (98 frames), drops back to standing cleanly.
- Rolls, spot dodge, air dodge, techs, get-up rolls, ledge roll/jump, grab-release jump now show the spin-ball model (model commands merged into the game's own scripts, `show_ball` / INJECT in `sonic_moves.py`; intangibility frames untouched). Spot dodge also flashes the Insta-Shield crescent (Sonic 3). Seen in game v62.
- New Sonic animations replacing Falcon's (same lengths, scripts untouched): spot dodge, air dodge, dizzy (v58); ledge climb/attack/roll/jump, tech in place and tech rolls (v60, seen in game on v60: hang, attack, roll, jump OK); knockdown bounce/lie/hit/stand both ways, get-up rolls, get-up attack from the back = breakdance windmill (legs hit both sides on Falcon's f19-20 and f28-29), from the front = mule kick then front kick (f20-21, f26-27), grabbed/pummeled/released, asleep (sits and nods off), clank recoil, platform drop, wall/ceiling techs and bumps, wall splat, slip (v61). Lying poses rest on the floor by the lowest point of the body (`floor` in the pose solver); before, he sank into the floor. Seen in game v61: grabbed, bounce, lying on his back. Not seen in game: face-down set, get-up attacks, sleep, wall ones.
- About 45 item animations (pick up, throw, swing, shoot, crate carry, hammer, parasol, scope) re-posed from Falcon's limb directions with Sonic's solver (`retarget()`), feet planted. Screw Attack item = spin jump. Only checked offline.
- Down tilt kick (Somersault), from -> to: Element 0 (normal) -> 1 (fire): SA2's Fire Somersault. Damage and frames unchanged.
- Mouth, from -> to (`build_sonic_costume_ball.py`): wraps 60 -> 30 degrees each side, corner upturn 0.5 -> 0.22, line half-thickness 0.06/0.11 -> 0.045/0.06, open depth 0.75 -> 0.32. Seen in game with the pause camera (`tests/face_test.py`, `test_logs/v62_mouth_ingame.png`): thin smile at rest, small open mouth on attacks.
- New tools: `scripts/anim_sheet.py` (contact sheet of any stored animation), `scripts/package_build.py`, `tests/ledge_test.py`, `tests/knock_test.py`, `tests/face_test.py`, `tests/bone_probe.py`. Test inputs are now flushed every frame (un-flushed inputs arrived late).

Tests v63: loads, shield/dodge/roll/Homing test OK (same Homing numbers as v62). Not verified / to do next: get-up attack and roll options in `knock_test.py` (v61 run only stood up, inputs were not flushed then); item animations in game; sleep; the on-hit Homing Attack total may now be too slow at low percent.

## v64: blinking eyes, higher consecutive bounces, get-ups verified (2026-11-23)

File: `builds/Melee - Sonic v64.iso` (only build kept; v63 deleted). Package `work/sonic_package_v64.zip`, model `work/v19/PlSnNr_v64.dat` (27 parts), fighter code `work/v19/ftFunction_v64.dat`. Animations unchanged from v62/v63 (`PlSnAJ_v62.dat`).

- Verified on v63 first (`tests/knock_test.py`, `test_logs/v63_kn_*.png`): get-up attack from his back (the windmill, GROUND_ATTACK_UP 49 frames), get-up roll back (spin ball, 35 frames), knockdown bounce and lying, grabbed pose. The earlier runs only ever stood up because the test's inputs were sent while it was still catching up after a capture; the option is now pressed 45 frames into lying.
- Eyelids (new model part 26, visibility group 4; `build_sonic_costume_ball.py`, `patch_ball_sets.py` now writes 5 groups): the eye whites copied 0.16 in front, fur blue with a dark lash line. Fighter code (`OnFrame`): a 5-frame blink every 170 frames; eyes shut while asleep (states 297-299), dizzy (211), flinching (75-91) and knocked down (183-185, 191-193); never while the spin ball is showing. Seen in game v64 (`test_logs/v64_kn_lie*.png`: shut while lying and on the hit pose, open while grabbed and standing). The idle blink itself was not caught on a capture.
- Down B in the air (Bounce Attack, SA2 Bounce Bracelet), from -> to: rebound speed 3.0 every time -> 3.0, then 3.45, then 3.9 for each further bounce in a row without landing (the count clears when he stands on the floor). Test v64 (`tests/bounce_test.py`): rebound peaks 28.4, 36.5, 44.6, 44.6 units.
- Tests v64: knockdown/grab test and bounce test ran full matches without a crash. The shield/dodge run landed on another stage because the test's stage picker missed (its captures still show the ball centred in the bubble, the spot dodge ball with the Insta-Shield and the roll ball); Homing Attack numbers were not re-measured on v64 (code for it unchanged since v62).

Not verified: face-down knockdown set and its get-up attack, get-up roll forward, sleep, item animations, wall techs (offline previews only); the blink timing by eye.

## v65: new up tilt and down smash (2026-11-23)

File: `builds/Melee - Sonic v65.iso` (only build kept; v64 deleted). Package `work/sonic_package_v65.zip`, animations `work/v19/PlSnAJ_v65.dat` (622,912 bytes), model `PlSnNr_v64.dat`, fighter code `ftFunction_v64.dat` (unchanged). First full `sonic_moves.py build` since the shield-pose writer went in: log shows "shield pose written: 63 joints".

User picked "New attacks". Forward tilt, forward smash, down tilt, neutral air and the specials were left alone (user-specified moves).

- Up tilt: flip kick (the same animation as the up air) -> Insta-Shield flash overhead (Sonic 3): he rises onto his toes and pirouettes once with his right arm up while the white crescent (part 25) whirls over his head (frames 5-12). Hitboxes, from -> to: right foot 8% size 2.6, left foot 8% size 2.6, right shin 7% size 2.0 -> one sphere on the hips bone 7.0 above it (over his head) 8% size 4.4 and one 3.0 up / 5.5 forward (in front of his chest) 7% size 3.0. Unchanged: hit frames 6-10, angle 92, BKB 35, KBG 95, 28 frames, IASA 24.
- Down smash: split kick -> breakdance windmill, a full turn on his shoulders with the legs in a flat split (left foot 6.7 in front, right foot 4.2 behind at hip height on the early hit). Early hit unchanged: f8-10, 13/12/11/10% (left foot, left shin, right foot, right shin), angle 30, BKB 30, KBG 90. New late hit f11-17: 8% feet, 7% shins, angle 30, BKB 20, KBG 80; it follows straight on from the early hit, so it cannot hit someone the early hit already hit. Unchanged: 44 frames, charge frame 5, IASA 40.
- Test v65 (`tests/move_test.py ... --only=utilt,dsmash --big`, new `--only=` filter, FD, Fox standing in front): up tilt hits f6 for 8.0%, knockback (-0.06, 1.74); down smash hits f8 for 13.0%, knockback (1.79, 1.03). Captures `test_logs/v65_na_*.png`, `v65_ut_utilt_4.png`: windmill seen spinning low with the hit spark; up tilt pose seen (arm up, turning).

Checked offline on the final `PlSn_v65.dat`: the stored shield pose reads back identical to v64's on all 63 joints (in v65 it came from the moves build instead of `patch_shield_pose.py`); the up tilt script switches the crescent on at f5 and off at f12.

Not verified: the crescent on the up tilt was not seen on a capture (commands confirmed in the file only); the down smash's rear hit and its late hit (Fox only stood in front); shield, blink and bounce were not re-run in game on v65.

## v66: quicker forward smash, Insta-Shield up smash, old up tilt back, slower down smash, ball throws, new crouch/grabs, eyes (2026-11-24)

File: `builds/Melee - Sonic v66.iso` (only build kept; v65 deleted). Package `work/sonic_package_v66.zip`, model `work/v19/PlSnNr_v66.dat`, animations `PlSnAJ_v66.dat` (625,856 bytes), fighter code unchanged (`ftFunction_v64.dat`). Build log shows "shield pose written: 63 joints".

User: "fix down air, down tilt teleports back, the crouch looks super weird, give fsmash less range, make down smash animation slightly slower, make his eyes slightly more viewable from the side, give him his old up tilt, make his new uptilt his upsmash, make it kill early, make tails pick him up for his recovery, better dash grab and grab animation, make his fsmash quicker with a lot less range and less damage, use his spikes more in his grabs, do more attacks".

- Forward smash, from -> to: 50 -> 40 frames, charge f7 -> f5, IASA 46 -> 36; gem out f15-24 -> f11-17, 17% -> 13%, size 2.8 -> 2.6, flies 27 -> 15 units; return f25-38 -> f18-26, 8% -> 4%, size 2.4 -> 2.2. Knockback unchanged. No longer ends 3.5 units forward (it snapped back).
- Up smash, from -> to: ball spin (4 x 2% + 5%, 48 frames) -> Insta-Shield flash (the v65 up tilt, Sonic 3): one hit f10-14, 17% overhead (size 4.6, angle 88, BKB 40, KBG 112) and 14% in front (size 3.2, KBG 105); 46 frames, charge f6, IASA 42.
- Up tilt: back to the v64 flip kick and its values.
- Down smash, from -> to: 44 -> 50 frames, charge f5 -> f6, IASA 40 -> 46, hits f8-10 -> f10-12 and f11-17 -> f13-21. Damage and knockback unchanged.
- Down tilt: the Somersault now rolls in place (it rolled 7.5 units forward and snapped back at the end). Hitboxes unchanged.
- Down air: the drill now spins three turns. Hitboxes unchanged.
- Crouch: the v56 glove-over-the-head pose -> a plain Sonic 1 duck, hands on his knees.
- Grab and dash grab: new lunge poses (hands pulled back, then a lunge with the front foot out). Grab frames unchanged.
- Throws use the spin ball (model shown through the game's own scripts): forward = spin-ball ram (was a punch), up = spin-ball launch upward (was an uppercut), down = spin-ball grind on the floor (was a slam). Release frames and hitboxes unchanged.
- Eyes: irises turned 0 -> 14 degrees toward each side and 12% larger.
- Test v66 (`--only=utilt,usmash,fsmash,dsmash,dtilt,grab --big`, FD, Fox in front): up smash f10 17%, knockback (0.13, 3.85); forward smash f11 13% then f18 3.6% on the return; down smash f10 13%; up tilt f6 7%; grab catches Fox on f6. Down tilt: the test's input did not register (he stayed STANDING), so the new roll was not seen in game.

Not done: Tails carrying him as the recovery. Tails' SA1 model is in the user's files (`extract/sa1/figure/miles/models/m_kihon3_miles.nja.sa1mdl`, plus tail models and animations); it needs the model brought in as a new part and a new up B. Not verified in game: down tilt, down air, crouch, the throws, the new eyes.

## v67: Sonic's own select-screen icon, portrait and stock icon (2026-11-24)

File: `builds/Melee - Sonic v67.iso` (v66 kept until chat Claude checks v67). Package `work/sonic_package_v67.zip` = v66 with new pictures; gameplay identical to v66.
User (via chat Claude): "give sonic his own icon". From -> to, all five costumes: select-screen grid icon Captain Falcon's face -> Sonic's head (the slot's image is 64x56; written as RGB5A3, was CI8; `build_iso.ps1 -IconPng`); portrait `csp.png` (136x188) and stock icon `stc.png` (24x24) Falcon's -> Sonic renders from his own model (`scripts/make_icons.py`, transparent background).
Not verified in game yet (asked chat Claude in `.bridge/messages.md`). The 128x128 render is stretched to 64x56, so the head may look slightly squashed.

Open from chat Claude's v66 report: an out-of-memory crash (HSD heap assert, memory.c line 52) after about 8 minutes in Training; jumping did not leave the ground for chat Claude (works in the test harness); down air and throws still unchecked. Down tilt stays in place (confirmed); crouch fine; eyes still show only a thin iris sliver from the side and the user finds them odd from the front.

## v68: eyes reverted, head portrait (2026-11-24)

File: `builds/Melee - Sonic v68.iso` (only build kept; v66, v67 deleted). Package `work/sonic_package_v68.zip`: v66 gameplay files, model `work/v19/PlSnNr_v68.dat`, pictures `work/icons_v68/`.
- v67 checked by chat Claude: grid icon and stock icons show Sonic; portrait showed the T-pose arms; jumping works (its earlier report was its own input); user found the v66 eyes "super duper creepy" from the front and asked to revert.
- Eyes, from -> to: iris turn 14 -> 0 degrees, iris size 1.12 -> 1.0 (back to v64/v65; model file byte-identical to `PlSnNr_v64.dat`).
- Portrait, from -> to: head and shoulders with T-pose arms -> head-only close-up, three-quarter view. The series emblem (Falcon's) behind it is unchanged.
- Test v68: loads into a match; up smash f10 17%, grab catches on f6.
Still open: out-of-memory crash after ~8 min in Training (needs a soak test); down air and throws unchecked in game; Tails-carry recovery not started; Falcon emblem on the portrait panel.

## v69: Tails carries Sonic (air up B) (2026-11-24)

File: `builds/Melee - Sonic v69.iso` (only build kept; v68 deleted). Package `work/sonic_package_v69.zip`, model `work/v19/PlSnNr_v69.dat` (43 parts, 918,861 bytes, was 845,293), animations `PlSnAJ_v69.dat`, fighter code `ftFunction_v69.dat`.
User: "make tails pick him up for his recovery", "wheres tails carry on on your own".

- Air up B, from -> to: Super Peel-Out in the air (rev 8 frames, dash 3.3 for 12 frames, 6% hitbox f9-29, then helpless) -> Tails carry (Sonic 3): Tails holds Sonic's hands and flies him up for 60 frames (no rise for 8 frames while Tails grabs him, rise speed 1.0 for frames 8-40, fading to 0.2 by frame 60), steerable sideways (stick x 0.08 per frame, max 0.9), then Tails lets go and Sonic falls helpless (same helpless fall and 15-frame landing lag as the Peel-Out). No hitbox. Can grab ledges. Ground up B is still the Peel-Out.
- New fighter state 351 (`fighter_code/sonic.c`, `Tails_Anim`/`Tails_Phys`, animation SpecialHiCatch = 309, unused by Sonic before). OnFrame shows visibility group 5 (Tails) only in this state.
- Tails model: his SA1 Dreamcast model from the user's files (`extract/sa1/figure/miles/models/m_kihon3_miles.nja.sa1mdl`, textures unpacked from `MILES.PRS` with ArchiveTool to `extract/sa1_tex/MILES`), posed on frame 4 of his SA1 fly-up animation in Blender (`scripts/export_tails_pose.py`, preview `scripts/preview_parts.py`), placed so his hands are at (0, 15.2, 0.6) above Sonic's head. 13 body parts on bone 1, 3 tail parts on bone 62 spun round their base (47 degrees per frame) by the animation. Textures resized to 64x64 or smaller.
- Sonic's pose: hanging, both arms IK-reached to Tails' hands (checked: hands land exactly on the targets), legs swinging every 12 frames.
- Test v69 (`tests/tails_test.py`): jump, up B at frame 22: rises from 35.9 to 80.3 (44 units) over 60 frames, then fall special and landing; captures `test_logs/v69_tails_*.png` show Tails above him holding his hands.

Not verified: the tail spin is hard to see in the captures; ledge grab during the carry; how it looks from the front; memory use with the bigger model (the 8-minute out-of-memory crash is still open).

## v70-v72: up B recovers further + shield cancel, neutral B fixes and reticle, attack face, bigger irises, sounds (2026-11-26)

File: `builds/Melee - Sonic v72.iso` (only build kept; v69-v71 deleted). Package `work/sonic_package_v72.zip`: PlSn/PlSnAJ from v71 (`PlSn_v71.dat`, `PlSnAJ_v71.dat`, fighter code `ftFunction_v71.dat`), model `PlSnNr_v72.dat` (45 parts).
User: "make the up b recover a bit more and polished", "make the up b cancelable with shield", "make the neutral b have less end lag", "acts really weird when you miss cuz of an airdodge", "if you use it off stage ur dead", "add the homing attack reticle", "make his eyes more visible from side view without moving them", "facial expressions more akin to the ones in game", "the neutral special sound effect sounds bad and activates when you airdodge", "improve other moves, add nods".

- Air up B (Tails carry), from -> to: 60 -> 70 frames; rise 1.0 for f8-40 fading to 0.2 -> 1.15 for f8-45 fading to 0.35; steering max 0.9 -> 1.1, 0.08 -> 0.10 per frame. New: L or R after frame 8 cancels it (Tails lets go, normal fall, can air dodge; no second up B until he lands or grabs a ledge). Animation: arms reach up as Tails arrives (f0-6), whoosh sound at f1. Test v71: rises 35.9 -> 97.6 (62 units, was 44). Shield cancel not tested in game.
- Neutral B (Homing Attack), from -> to: end lag after a miss 60 -> 52 frames, lag after a hit 34 -> 30, landing lag after a miss 28 -> 24 (cap 48 -> 40). Steers at the target only for the first 6 frames, then flies straight (it chased air-dodging targets every frame). A miss no longer uses up the double jump (own flag instead of jumps used; cleared on landing or ledge grab). During the end lag he can drift (0.06 per frame, max 1.0) and falls slower (gravity 0.15 -> 0.10, max fall 1.8). Sound: SA1 homing clip + grunt -> Melee medium whoosh (165), no voice. Test v71: hit 8% at f10; miss on the ground actionable at frame 65 (v62: 73).
- Reticle (SA1/SA2 lock-on): green ring with four yellow pointers (model part 43, visibility group 6) drawn on the nearest opponent within 75 units while he jumps or falls and the Homing Attack is available. Fighter code moves bone 62 onto the target each frame. Seen in game on v70 (`test_logs/v70_ret_8.png`).
- Dodge sounds: air dodge and spot dodge no longer play a voice (they played grunt 560007, the same clip as neutral B, carried over from Falcon's scripts).
- Eyes, from -> to: iris size 1.0 -> 1.18 and 0.06 -> 0.09 out from the eye, same place, not turned. Attack face: new half eyelids (part 44, group 4 set 2) over the top of the eyes whenever the mouth is open on an attack (fighter code). v71 had them behind the eye whites; v72 places them out past the eye bulge. Seen in game on v72 (`test_logs/v72_face_sheet.png`: forward smash narrowed eyes, idle normal).
- Nods/animation: taunt ends on a thumbs-up (Sonic CD / SA1 goal pose); pummel is a quill headbutt (was a knee; damage unchanged); leaning bank turns on Turn and TurnRun (Falcon's timing and root motion kept).

Not verified: shield cancel of the up B, ledge grab during the carry, the off-stage miss recovery, bank turns and taunt in game; memory with the bigger model (the 8-minute crash is still open).

## v73: Sonic Adventure lives icon for stocks and the select screen; recovery and soak tests (2026-11-26)

File: `builds/Melee - Sonic v73.iso` (only build kept; v72 deleted). Package `work/sonic_package_v73.zip` = v72 with new pictures (`work/icons_v73`). Gameplay identical to v72.
User: "put a proper icon, take like a sonic adventure asset for it and just use the lives systems from the game like maybe the genesis 16 bit head as the stock icon"; "do all this on your own, no chat Claude" (bridge request closed).
- Stock icon, from -> to: render of his model -> SA1's own lives icon `hyoji_zanki_s` (32x32, from `CON_REGULAR.PRS`, unpacked to `extract/sa1_ui/`), scaled to 24x24. Seen in game: four of them in the HUD (`test_logs/v73_hud.png`).
- Select-screen grid icon, from -> to: model render -> the same lives icon, 56x56 (pixel-doubled) in the 64x56 slot. Portrait unchanged (v68 head render). There is no 16-bit Genesis head in the SA1 files; the SA1 lives icon is the game's own.
- Recovery tests on v72 (`tests/recovery_test.py`, FD left edge): shield cancel of the Tails carry -> normal fall and no second carry (a later up input gave a double jump instead); Tails from 27 below the stage -> rose past the ledge and landed on stage (no ledge grab on the way up); neutral B miss off stage -> he still double jumped, used Tails and got back on stage.
- Soak test (`tests/soak_test.py`): both runs ended when the match ended (stocks ran out at 59-89 s; screen back on the character select), so the 8-minute out-of-memory crash is still not reproduced.
Still open: Captain Falcon's series emblem behind the damage percent and portrait; the memory crash.

## v74-v76: own emblem, cover-art portrait and icon, Sonic 2 stock icon, Tails flies off, release window, new down tilt (2026-11-26)

File: `builds/Melee - Sonic v76.iso` (only build kept; v73-v75 deleted). Package `work/sonic_package_v75.zip` (model `PlSnNr_v75.dat`, `PlSn_v75.dat`, `PlSnAJ_v75.dat`, fighter code `ftFunction_v75.dat`); v76 differs from v75 only in where the select-screen icon sits.
User: emblem; "make his down tilt better"; reticle only during the homing ball; Sonic 2 sprite head as the stock icon; Adventure art for the select screen; "tails flys off screen and fades", "a window of half a second, then free fall"; "you can't jump after up b"; "his pupils stick through the cover"; "it's cropped in the character select screen".

- Series emblem, from -> to: Captain Falcon's -> Sonic's own, a white silhouette of his head in profile rendered from his model (`make_icons.py`, `build_iso.ps1 -EmblemPng`). Added as a new emblem slot (index 16); Falcon's emblem is untouched (the build checks its image bytes; v74's first attempt shared the image with Falcon's slot and was discarded before use). Seen in game behind his damage percent; Fox's emblem unchanged.
- Stock icon, from -> to: SA1 lives icon -> the Sonic 2 sprite's head from the user's sprite sheet (`work/sprites/sonic_sprites.png`, body removed, background keyed out, `scripts/make_sprite_icon.py`), 24x24.
- Select-screen portrait, from -> to: model head render -> the Sonic Adventure cover-art Sonic (`work/sprites/sa_icon.png`, from the user's Downloads). Select-screen grid icon, from -> to: SA1 lives icon -> his head from that cover art inside Melee's own icon frame and name plate (taken from Fox's icon), "SONIC" name. Icon position, from -> to: right of Roy (past the grid's edge, the screen frame cut it off) -> the empty slot at the left end of the bottom row, left of Pichu. `tests/harness.py` SONIC_CSS 27.2 -> -29.0. Seen on the select screen (`test_logs/v76_css_crop.png`).
- Reticle, from -> to: shown whenever he jumped or fell with neutral B available -> only during the Homing Attack dash with a target, before it hits.
- Air up B (Tails), from -> to: at the end Sonic went straight into helpless fall -> Tails lets go and flies up and forward, shrinking away over 30 frames; Sonic falls normally for 30 frames (can air dodge or attack, no double jump, no second carry), then free fall (same 15-frame landing lag). The shield cancel also blocks the double jump now. Tails is one piece on bone 62 (was body on bone 1, tails spinning on bone 62; the tail spin is gone). Test v75/v76: carry to frame 72, FALLING 72-101, free fall from 102.
- Eyelids, from -> to: closed lids 0.16 -> 0.30 in front of the eye; half lids 0.2 -> 0.34 past the eye bulge (the 1.18x irises poked through). Seen in game: shut eyes fully covered while lying (`test_logs/v76_lids.png`).
- Down tilt (animation only; hit frames, damage, fire kick unchanged): roll in place + upright kick -> rolls 5 forward as a ball (f4-10), low slide kick leaning back on his hands with the front leg along the floor (f12-14), hips slide back to the start by f21 (no snap back). Not seen in game yet.
Still open: the 8-minute memory crash (not reproduced; test matches end when stocks run out); down tilt in game; the fly-off seen in game (camera crops it).

