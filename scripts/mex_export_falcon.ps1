# Exports Captain Falcon as a MexTool fighter package (zip) from a working copy. Writes no ISO.
. C:\adventure-melee\scripts\mex_common.ps1
$log = 'C:\adventure-melee\work\dialogs.log'
$w = Start-DialogWatcher $log
try {
    Copy-Item 'C:\adventure-melee\base\Melee NTSC 1.02 clean.iso' 'C:\adventure-melee\work\work.iso' -Force
    Set-ItemProperty 'C:\adventure-melee\work\work.iso' -Name IsReadOnly -Value $false
    [void](Mex-Static 'InitFromISO' @('C:\adventure-melee\work\work.iso'))
    $falcon = (Mex-Field 'Fighters') | Where-Object { $_.FighterDataPath -eq 'PlCa.dat' } | Select-Object -First 1
    $out = 'C:\adventure-melee\work\falcon_package.zip'
    Remove-Item $out -ErrorAction SilentlyContinue
    Obj-Call $falcon 'SaveFighterToPackage' @($out)
    "exported: " + (Get-Item $out).Length + " bytes"
    "--- icons ---"
    $icons = Mex-Field 'FighterIcons'
    $ic = $icons[0]
    $ic.GetType().GetProperties($BF) | ForEach-Object { "  prop {0} : {1} = {2}" -f $_.Name, $_.PropertyType.Name, $_.GetValue($ic) }
    $ic.GetType().GetFields($BF) | ForEach-Object { "  field {0} : {1}" -f $_.Name, $_.FieldType.Name }
    $ic.GetType().GetConstructors($BF) | ForEach-Object { "  ctor " + $_.ToString() }
    $i = 0; foreach ($x in $icons) { "  {0,2} {1}" -f $i, $x.ToString(); $i++ }
    "--- functions ---"
    $fn = $falcon.GetType().GetField('Functions', $BF).GetValue($falcon)
    $fn.GetType().GetFields($BF) + $fn.GetType().GetProperties($BF) | ForEach-Object { "  {0} = {1}" -f $_.Name, $(try { '0x{0:X8}' -f $_.GetValue($fn) } catch { $_.GetValue($fn) }) }
} catch { "ERROR: " + $_.Exception.ToString() }
finally { Stop-Process -Id $w.Id -Force -ErrorAction SilentlyContinue; "--- dialogs answered ---"; if (Test-Path $log) { Get-Content $log | Select-Object -Last 3 } }
