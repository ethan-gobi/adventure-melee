# Loads MexTool's own code into this PowerShell session so builds can be scripted.
# Dot-source it:  . C:\adventure-melee\scripts\mex_common.ps1
$ErrorActionPreference = 'Stop'
$script:MexDir = 'C:\adventure-melee\tools\mexTool'

# MexTool looks for lib\dol.patch, lib\codes.gct etc. relative to the application base.
[AppDomain]::CurrentDomain.SetData('APPBASE', $MexDir + '\')
[Environment]::CurrentDirectory = $MexDir
New-Item -ItemType Directory -Force "$MexDir\temp" | Out-Null
Get-ChildItem "$MexDir\lib\*.dll" | ForEach-Object { [void][Reflection.Assembly]::LoadFrom($_.FullName) }
$script:MexAsm = [Reflection.Assembly]::LoadFrom("$MexDir\mexTool.exe")
$script:BF = [Reflection.BindingFlags]'Public,NonPublic,Static,Instance'
$script:MEX = $MexAsm.GetType('mexTool.Core.MEX')

# What MexTool's Program.Main -> ApplicationSettings.Init() would set (Init itself expects to be the entry program).
$appSet = $MexAsm.GetType('mexTool.ApplicationSettings')
$appSet.GetProperty('ExecutablePath', $BF).SetValue($null, $MexDir)
$appSet.GetProperty('MexCodePath', $BF).SetValue($null, (Join-Path $MexDir 'lib/codes.gct'))
$appSet.GetProperty('MexAddCodePath', $BF).SetValue($null, (Join-Path $MexDir 'lib/codes.ini'))

function Mex-Static($name, [object[]]$mexArgs = @()) { $MEX.GetMethod($name, $BF).Invoke($null, $mexArgs) }
# the leading comma stops PowerShell from copying live lists into a snapshot array
function Mex-Field($name) { ,($MEX.GetField($name, $BF).GetValue($null)) }
function Mex-Prop($name) { $MEX.GetProperty($name, $BF).GetValue($null) }
function Obj-Call($obj, $name, [object[]]$callArgs = @()) {
    $m = $obj.GetType().GetMethods($BF) | Where-Object { $_.Name -eq $name -and $_.GetParameters().Count -eq $callArgs.Count } | Select-Object -First 1
    $m.Invoke($obj, $callArgs)
}

# MexTool asks questions in message boxes. This watcher answers them for this process only
# and logs every dialog it answered, so nothing is accepted silently.
function Start-DialogWatcher($logPath) {
    $code = @'
param($targetPid, $logPath)
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public class DW { public delegate bool CB(IntPtr h, IntPtr l);
[DllImport("user32.dll")] public static extern bool EnumWindows(CB cb, IntPtr l);
[DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr p, CB cb, IntPtr l);
[DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
[DllImport("user32.dll")] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
[DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
[DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
public static List<string> Go(uint target){ var r=new List<string>(); EnumWindows((h,l)=>{ if(!IsWindowVisible(h)) return true; uint pid; GetWindowThreadProcessId(h,out pid); var c=new StringBuilder(64); GetClassName(h,c,64); if(c.ToString()=="#32770" && pid==target){ var t=new StringBuilder(256); GetWindowText(h,t,256); var texts=new List<string>(); IntPtr yes=IntPtr.Zero, ok=IntPtr.Zero; EnumChildWindows(h,(ch,l2)=>{ var ct=new StringBuilder(512); GetWindowText(ch,ct,512); var s=ct.ToString(); if(s.Length>0) texts.Add(s); if(s=="&Yes") yes=ch; if(s=="OK") ok=ch; return true;},IntPtr.Zero); IntPtr b = yes!=IntPtr.Zero?yes:ok; r.Add("["+t+"] "+String.Join(" | ",texts)+" -> "+(b==IntPtr.Zero?"NO BUTTON":(b==yes?"Yes":"OK"))); if(b!=IntPtr.Zero) PostMessage(b,0x00F5,IntPtr.Zero,IntPtr.Zero);} return true;},IntPtr.Zero); return r; } }
"@
while ($true) { foreach ($l in [DW]::Go([uint32]$targetPid)) { Add-Content -Path $logPath -Value ((Get-Date -Format 'HH:mm:ss') + ' ' + ($l -replace "`r?`n",' ')) }; Start-Sleep -Milliseconds 700 }
'@
    $f = Join-Path $env:TEMP "mex_dialog_watcher_$PID.ps1"
    Set-Content -Path $f -Value $code -Encoding utf8
    Start-Process powershell -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$f`"",$PID,"`"$logPath`""
}

