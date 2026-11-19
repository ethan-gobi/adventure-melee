# Prints every common-attribute value of a fighter DAT, using HSDRaw (MexTool's copy).
param([Parameter(Mandatory)][string]$Dat)
$ErrorActionPreference = 'Stop'
[void][Reflection.Assembly]::LoadFrom('C:\adventure-melee\tools\mexTool\lib\HSDRaw.dll')
$f = New-Object HSDRaw.HSDRawFile($Dat)
foreach ($r in $f.Roots) { "root: $($r.Name) : $($r.Data.GetType().FullName)" }
$root = $f.Roots | Where-Object { $_.Name -like 'ftData*' } | Select-Object -First 1
$fd = $root.Data
$attr = $fd.Attributes
"attributes type: $($attr.GetType().FullName)"
$attr.GetType().GetProperties() | Where-Object { $_.DeclaringType -eq $attr.GetType() } | ForEach-Object { "{0} = {1}" -f $_.Name, $_.GetValue($attr) }
