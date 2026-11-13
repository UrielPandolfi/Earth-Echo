[CmdletBinding(SupportsShouldProcess)]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$pythonPath = Join-Path $projectRoot 'services/api/.venv/Scripts/pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) { throw "Falta el entorno Python: $pythonPath" }
$taskName = 'Earth Echo - Public Data Refresh'
$arguments = '-m earth_echo.tools.refresh --watch'
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and ($existing.Actions.Execute -ne $pythonPath -or $existing.Actions.Arguments -ne $arguments)) {
    throw 'Existe una tarea con el mismo nombre y otra acción. No se reemplazó.'
}
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $arguments -WorkingDirectory $projectRoot -ErrorAction Stop
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity -ErrorAction Stop
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited -ErrorAction Stop
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -ErrorAction Stop
if ($PSCmdlet.ShouldProcess($taskName, 'Registrar e iniciar actualización pública local al iniciar sesión')) {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Actualiza productos públicos Earth Echo; usa .env local, cuotas, lock y estado persistido. Sin credenciales en argumentos.' -Force -ErrorAction Stop | Out-Null
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    Get-ScheduledTask -TaskName $taskName -ErrorAction Stop | Select-Object TaskName,State
}
