# Opens a fresh working copy of the clean ISO, installs m-ex into the copy (in memory)
# and lists what MexTool sees. Writes no ISO.
. C:\adventure-melee\scripts\mex_common.ps1
$log = 'C:\adventure-melee\work\dialogs.log'
$w = Start-DialogWatcher $log
try {
    Copy-Item 'C:\adventure-melee\base\Melee NTSC 1.02 clean.iso' 'C:\adventure-melee\work\work.iso' -Force
    Set-ItemProperty 'C:\adventure-melee\work\work.iso' -Name IsReadOnly -Value $false
    "InitFromISO = " + (Mex-Static 'InitFromISO' @('C:\adventure-melee\work\work.iso'))
    "Initialized = " + (Mex-Prop 'Initialized') + "  m-ex version " + (Mex-Prop 'VersionMajor') + "." + (Mex-Prop 'VersionMinor')
    $f = Mex-Field 'Fighters'
    "Fighters: $($f.Count)"
    $i = 0; foreach ($x in $f) { "{0,2} {1,-18} {2,-12} anim={3} mex={4}" -f $i, $x.NameText, $x.FighterDataPath, $x.AnimFile, $x.IsMEXFighter; $i++ }
    "FighterIcons: " + (Mex-Field 'FighterIcons').Count
    $falcon = $f | Where-Object { $_.FighterDataPath -eq 'PlCa.dat' } | Select-Object -First 1
    "--- Falcon properties ---"
    $falcon.GetType().GetProperties($BF) | ForEach-Object { "  {0} = {1}" -f $_.Name, $_.GetValue($falcon) }
    "--- Falcon fields ---"
    $falcon.GetType().GetFields($BF) | ForEach-Object { "  {0} : {1}" -f $_.Name, $_.FieldType.Name }
} catch { "ERROR: " + $_.Exception.ToString() }
finally { Stop-Process -Id $w.Id -Force -ErrorAction SilentlyContinue; "--- dialogs answered ---"; if (Test-Path $log) { Get-Content $log } }
