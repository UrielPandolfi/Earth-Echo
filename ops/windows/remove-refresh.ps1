[CmdletBinding(SupportsShouldProcess)]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$pythonPath = Join-Path $projectRoot 'services/api/.venv/Scripts/pythonw.exe'
$taskName = 'Earth Echo - Public Data Refresh'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $existing) { Write-Output 'La tarea no está instalada.'; return }
if ($existing.Actions.Execute -ne $pythonPath -or $existing.Actions.Arguments -ne '-m earth_echo.tools.refresh --watch') { throw 'La tarea pertenece a otra acción; no se modificó.' }
if ($PSCmdlet.ShouldProcess($taskName, 'Detener y quitar la tarea de actualización de este proyecto')) {
    Stop-ScheduledTask -TaskName $taskName
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}
