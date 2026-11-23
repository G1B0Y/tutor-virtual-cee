# Crea las dos tareas del Programador de tareas que mantienen el tutor encendido en la PC del CEE,
# la regla del firewall y copia vigilar.ps1 a C:\TutorCEE. Correr UNA vez, en PowerShell como administrador:
#   powershell -ExecutionPolicy Bypass -File C:\TutorCEE\instalar-tareas.ps1
# Pide la contrasena de la cuenta de Windows donde se instalo Ubuntu (WSL es por usuario).
param(
    [string]$Distro = "Ubuntu-24.04",
    [int]$Puerto = 8090,
    [string]$Carpeta = "C:\TutorCEE"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $Carpeta, "$Carpeta\registros", "$Carpeta\respaldos" | Out-Null
if ($PSScriptRoot -ne $Carpeta) { Copy-Item (Join-Path $PSScriptRoot "vigilar.ps1") $Carpeta -Force }

$cuenta = Get-Credential -UserName "$env:USERDOMAIN\$env:USERNAME" -Message "Cuenta de Windows donde esta instalado Ubuntu (WSL)"
$usuario = $cuenta.UserName
$clave = $cuenta.GetNetworkCredential().Password

$ajustes = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew -StartWhenAvailable

# Tarea 1: enciende WSL al arrancar Windows (sin iniciar sesion) y lo mantiene vivo.
# Dentro de WSL, systemd arranca Docker y el servicio tutor-cee (docker compose up -d).
$accionWsl = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d $Distro --exec /bin/sleep infinity"
$alArrancar = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "Tutor CEE - WSL" -Action $accionWsl -Trigger $alArrancar -Settings $ajustes `
    -User $usuario -Password $clave -RunLevel Highest -Force | Out-Null

# Tarea 2: vigilar.ps1 a los 2 minutos de arrancar y luego cada 5 minutos.
$accionVigilar = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Carpeta\vigilar.ps1`" -Distro $Distro -Puerto $Puerto -Carpeta `"$Carpeta`""
$inicio = New-ScheduledTaskTrigger -AtStartup
$inicio.Delay = "PT2M"
$cada5 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
$ajustesVigilar = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 4) -MultipleInstances IgnoreNew -StartWhenAvailable
Register-ScheduledTask -TaskName "Tutor CEE - vigilar" -Action $accionVigilar -Trigger @($inicio, $cada5) `
    -Settings $ajustesVigilar -User $usuario -Password $clave -RunLevel Highest -Force | Out-Null

# Firewall: solo el puerto del chat y solo desde la red local.
if (-not (Get-NetFirewallRule -DisplayName "Tutor CEE (web)" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "Tutor CEE (web)" -Direction Inbound -Protocol TCP -LocalPort $Puerto `
        -RemoteAddress LocalSubnet -Action Allow -Profile Any | Out-Null
}

Write-Host "Listo. Tareas creadas: 'Tutor CEE - WSL' y 'Tutor CEE - vigilar'. Firewall abierto en el puerto $Puerto (solo red local)."
Write-Host "Prueba ahora: Start-ScheduledTask 'Tutor CEE - WSL'; Start-Sleep 60; Start-ScheduledTask 'Tutor CEE - vigilar'"
Write-Host "y revisa $Carpeta\registros\salud.csv"
