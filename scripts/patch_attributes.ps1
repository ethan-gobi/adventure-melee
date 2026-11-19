# Patches common attributes of a fighter DAT in place (same bytes, same length; nothing else in the file moves).
# Usage: patch_attributes.ps1 -Src in.dat -Dst out.dat -Set "Weight=85;InitialRunSpeed=2.4"
param([Parameter(Mandatory)][string]$Src, [Parameter(Mandatory)][string]$Dst, [Parameter(Mandatory)][string]$Set)
$ErrorActionPreference = 'Stop'
if ((Resolve-Path $Src).Path -eq [IO.Path]::GetFullPath($Dst)) { throw 'Dst must differ from Src' }
[void][Reflection.Assembly]::LoadFrom('C:\adventure-melee\tools\mexTool\lib\HSDRaw.dll')
$f = New-Object HSDRaw.HSDRawFile((Resolve-Path $Src).Path)
$attr = ($f.Roots | Where-Object { $_.Name -like 'ftData*' } | Select-Object -First 1).Data.Attributes
$before = [byte[]]$attr._s.GetData().Clone()
foreach ($kv in ($Set -split "[;,]" | Where-Object { $_ })) {
    $name, $val = $kv.Split('=', 2)
    $p = $attr.GetType().GetProperty($name)
    if (-not $p) { throw "No attribute named $name" }
    $old = $p.GetValue($attr)
    $p.SetValue($attr, [Convert]::ChangeType($val, $p.PropertyType, [Globalization.CultureInfo]::InvariantCulture))
    "{0}: {1} -> {2}" -f $name, $old, $p.GetValue($attr)
}
$after = $attr._s.GetData()
$file = [IO.File]::ReadAllBytes((Resolve-Path $Src).Path)
# locate the attribute block in the file (must be exactly one match)
$hits = @()
for ($i = 0; $i -le $file.Length - $before.Length; $i += 4) {
    $ok = $true
    for ($j = 0; $j -lt $before.Length; $j++) { if ($file[$i + $j] -ne $before[$j]) { $ok = $false; break } }
    if ($ok) { $hits += $i }
}
if ($hits.Count -ne 1) { throw "Attribute block found $($hits.Count) times; refusing to patch" }
$at = $hits[0]
$changed = @()
for ($j = 0; $j -lt $after.Length; $j++) { if ($file[$at + $j] -ne $after[$j]) { $file[$at + $j] = $after[$j]; $changed += $j } }
[IO.File]::WriteAllBytes([IO.Path]::GetFullPath($Dst), $file)
"attribute block at file offset 0x{0:X}; {1} bytes changed at struct offsets: {2}" -f $at, $changed.Count, (($changed | ForEach-Object { '0x{0:X}' -f $_ }) -join ' ')
