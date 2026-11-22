# Builds a new versioned ISO: clean Melee copy + m-ex + the Sonic fighter package.
# Usage: powershell -File build_iso.ps1 -Version v01 -Package C:\adventure-melee\work\sonic_package_v01.zip
# Never overwrites an existing build and never touches base\Melee NTSC 1.02 clean.iso.
param([Parameter(Mandatory)][string]$Version, [string]$Package, [switch]$NoFighter, [switch]$NoIcon, [string]$SoundBank)
. C:\adventure-melee\scripts\mex_common.ps1
$out = "C:\adventure-melee\builds\Melee - Sonic $Version.iso"
if (Test-Path $out) { throw "Build already exists, refusing to overwrite: $out" }
$log = "C:\adventure-melee\work\dialogs_$Version.log"
Remove-Item $log -ErrorAction SilentlyContinue
$w = Start-DialogWatcher $log
try {
    Copy-Item 'C:\adventure-melee\base\Melee NTSC 1.02 clean.iso' 'C:\adventure-melee\work\work.iso' -Force
    Set-ItemProperty 'C:\adventure-melee\work\work.iso' -Name IsReadOnly -Value $false
    if (-not (Mex-Static 'InitFromISO' @('C:\adventure-melee\work\work.iso'))) { throw 'InitFromISO failed' }
    $fighters = Mex-Field 'Fighters'
    "fighters before: $($fighters.Count)"

    if (-not $NoFighter) {
    $ft = $MexAsm.GetType('mexTool.Core.MEXFighter')
    $ft.GetMethod('InstallFighterFromFile', $BF).Invoke($null, @($Package))
    "fighters after: $($fighters.Count)"
    $sonic = $fighters | Where-Object { $_.NameText -eq 'Sonic' } | Select-Object -First 1
    if (-not $sonic) { throw 'Sonic was not installed' }
    "Sonic internal index: " + $fighters.IndexOf($sonic) + "  files: $($sonic.FighterDataPath), $($sonic.AnimFile)  mex=$($sonic.IsMEXFighter)"
    # Kirby hat: the exported package has no Kirby costume entries, so copy Captain Falcon's (same hat file).
    $falconF = $fighters | Where-Object { $_.NameText -eq 'C. Falcon' } | Select-Object -First 1
    $kf = $sonic.GetType().GetField('KirbyCostumes', $BF)
    $srcK = $kf.GetValue($falconF.PSObject.BaseObject); $dstK = $kf.GetValue($sonic.PSObject.BaseObject)
    "Kirby hat entries: Falcon $($srcK.Count), Sonic $($dstK.Count)"
    if ($dstK.Count -eq 0 -and $srcK.Count -gt 0) {
        $oeK = $MexAsm.GetType('System.ObjectExtensions')
        foreach ($kc in $srcK) {
            $o = $kc.PSObject.BaseObject
            $cp = ($oeK.GetMethods($BF) | Where-Object { $_.Name -eq 'Copy' -and $_.IsGenericMethod } | Select-Object -First 1).MakeGenericMethod($o.GetType()).Invoke($null, [object[]]@($o))
            $dstK.Add($cp)
        }
        "Kirby hat entries copied to Sonic: $($dstK.Count)"
    }
    $i = 0; foreach ($x in $fighters) { if ($i -ge 24) { "  {0,2} {1}" -f $i, $x.NameText }; $i++ }

    if ($SoundBank) {
        # Sonic's own sound bank, built from a manifest of WAV files (index order = sound ID - 560000). A new bank, so Falcon's
        # captain.ssm is left as it is. Script settings are copied from Falcon's bank.
        $man = Get-Content $SoundBank -Raw | ConvertFrom-Json
        $banks = Mex-Field 'SoundBanks'
        $cap = $banks | Where-Object { $_.SoundBank.Name -eq 'captain.ssm' } | Select-Object -First 1
        $mm = [AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.GetName().Name -eq 'MeleeMedia' } | Select-Object -First 1
        $ssm = [Activator]::CreateInstance($mm.GetType('MeleeMedia.Audio.SSM'))
        $ssm.Name = 'sonic.ssm'
        $scripts = New-Object System.Collections.ArrayList
        $codeT = $mm.GetType('MeleeMedia.Audio.SEMCode'); $enumT = $mm.GetType('MeleeMedia.Audio.SEM_CODE')
        foreach ($e in $man) {
            $dsp = [Activator]::CreateInstance($mm.GetType('MeleeMedia.Audio.DSP'))
            $dsp.FromFormat([IO.File]::ReadAllBytes($e.wav), 'wav')
            $ssm.AddSound($dsp)
            $sc = [Activator]::CreateInstance($mm.GetType('MeleeMedia.Audio.SEMBankScript'))
            $sc.Name = 'SONIC_' + $e.name.ToUpper()
            foreach ($cv in @(@('SET_SFXID', [int]$e.index), @('SET_REVERB1', 1), @('SET_PRIORITY', 15), @('PLAY', 200), @('END_PLAYBACK', 0))) {
                $c = [Activator]::CreateInstance($codeT, [object[]]@([Enum]::Parse($enumT, $cv[0])))
                $c.Value = $cv[1]
                $sc.Codes.Add($c)
            }
            [void]$scripts.Add($sc)
        }
        $sem = [Activator]::CreateInstance($mm.GetType('MeleeMedia.Audio.SEMBank'))
        $arr = [Array]::CreateInstance($mm.GetType('MeleeMedia.Audio.SEMBankScript'), $scripts.Count)
        for ($k = 0; $k -lt $scripts.Count; $k++) { $arr[$k] = $scripts[$k] }
        $sem.Scripts = $arr
        $bankT = $MexAsm.GetType('mexTool.Core.MEXSoundBank')
        $nb = [Activator]::CreateInstance($bankT, [object[]]@($sem, $ssm))
        $nb.Group = $cap.Group; $nb.Flags = $cap.Flags; $nb.GroupFlags = $cap.GroupFlags
        $banks.Add($nb)
        $sonic.SoundBank = $nb
        $bi = $banks.IndexOf($nb)
        "Sonic sound bank: sonic.ssm, $($man.Count) sounds, bank index $bi (script IDs ${bi}0000+)"
        if ($bi -ne 56) { throw "sound bank index is $bi, but Sonic's scripts were built for 56" }
    }

    if (-not $NoIcon) {
    # Character-select icon: clone Captain Falcon's icon and place it in the gap right of Roy.
    $icons = Mex-Field 'FighterIcons'
    $src = $icons | Where-Object { $_.Fighter.NameText -eq 'C. Falcon' } | Select-Object -First 1
    # same steps as MexTool's own "add icon" button: copy an icon without its image, then copy the image
    $oe = $MexAsm.GetType('System.ObjectExtensions')
    function Copy-Obj($o) { $o = $o.PSObject.BaseObject; ($oe.GetMethods($BF) | Where-Object { $_.Name -eq 'Copy' -and $_.IsGenericMethod } | Select-Object -First 1).MakeGenericMethod($o.GetType()).Invoke($null, [object[]]@($o)) }
    $img = $src.Image; $src.Image = $null
    $icon = Copy-Obj $src
    $icon.Image = Copy-Obj $img
    $src.Image = $img
    $icon.Fighter = $sonic
    $roy = $icons | Where-Object { $_.Fighter.NameText -eq 'Roy' } | Select-Object -First 1
    "Roy icon at X=$($roy.X) Y=$($roy.Y) W=$($roy.Width);  Falcon icon at X=$($src.X) Y=$($src.Y)"
    $icon.X = $roy.X + 7.0; $icon.Y = $roy.Y
    $icon.StartX = $icon.X; $icon.StartY = $icon.Y
    $icons.Add($icon.PSObject.BaseObject)
    "icons: $($icons.Count); Sonic icon at X=$($icon.X) Y=$($icon.Y)"

    }
    }
    $progress = [System.ComponentModel.ProgressChangedEventHandler] { param($s, $e) }
    Mex-Static 'PrepareSave' @($progress)
    # Same as MexTool's Save button: rebuild codes.gct from m-ex's base code plus the enabled codes in lib\codes.ini.
    $cpType = $MexAsm.GetType('mexTool.GUI.Pages.CodesPage')
    $codesPage = [Activator]::CreateInstance($cpType)
    $saveCodes = $cpType.GetMethod('SaveCodes', $BF)
    $codeArgs = [object[]]@($null)
    [void]$saveCodes.Invoke($codesPage, $codeArgs)
    $failed = $codeArgs[0]
    "codes.gct rebuilt; failed codes: " + $(if ($failed -and $failed.Length) { $failed -join ', ' } else { 'none' })
    $res = Mex-Prop 'ImageResource'
    $save = $res.GetType().GetMethod('Save', $BF)
    $save.Invoke($res, @($progress, $out, $true))
    # MexTool's rebuild can end the image a few bytes short of the last file, which Dolphin reports as a
    # disc read error. Pad to the standard GameCube disc size.
    $discSize = 1459978240
    $len = (Get-Item $out).Length
    if ($len -lt $discSize) {
        $fs = [IO.File]::Open($out, 'Open', 'Write'); $fs.SetLength($discSize); $fs.Close()
        "padded $len -> $discSize bytes"
    }
    "saved: $out  " + (Get-Item $out).Length + " bytes"
    Mex-Static 'Close'
} catch { "ERROR: " + $_.Exception.ToString(); if (Test-Path $out) { "partial output left at $out" } }
finally { Stop-Process -Id $w.Id -Force -ErrorAction SilentlyContinue; "--- dialogs answered ---"; if (Test-Path $log) { Get-Content $log } }
