# Vigila el tutor en la PC del CEE. Lo corre el Programador de tareas al arrancar y cada 5 minutos
# (tarea "Tutor CEE - vigilar", la crea instalar-tareas.ps1). Ver docs/DESPLIEGUE.md.
#  1. Si WSL no esta corriendo, lanza la tarea "Tutor CEE - WSL".
#  2. Mantiene el portproxy de Windows apuntando a la IP actual de WSL (cambia en cada reinicio).
#  3. Revisa /api/salud y anota una linea en C:\TutorCEE\registros\salud.csv.
#  4. Si la API no responde 3 veces seguidas (15 min), reinicia Docker dentro de WSL.
param(
    [string]$Distro = "Ubuntu-24.04",
    [int]$Puerto = 8090,
    [string]$Carpeta = "C:\TutorCEE"
)
$ErrorActionPreference = "Continue"
$registro = Join-Path $Carpeta "registros\salud.csv"
New-Item -ItemType Directory -Force -Path (Split-Path $registro) | Out-Null
if (-not (Test-Path $registro)) { "fecha,estado,detalle,ram_libre_mb,ip_wsl" | Set-Content -Encoding UTF8 $registro }

function Limpiar([object]$texto) { return (($texto | Out-String) -replace "`0", "").Trim() }

# 1. WSL encendido
$corriendo = (Limpiar (wsl.exe -l --running -q)) -split "\r?\n" | ForEach-Object { $_.Trim() }
if ($corriendo -notcontains $Distro) {
    Start-ScheduledTask -TaskName "Tutor CEE - WSL" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 45
}

# 2. Portproxy: 0.0.0.0:$Puerto (Windows) -> IP de WSL:$Puerto
$ip = ((Limpiar (wsl.exe -d $Distro -- hostname -I)) -split "\s+")[0]
if ($ip -match '^\d+\.\d+\.\d+\.\d+$') {
    $regla = netsh interface portproxy show v4tov4 | Select-String "0\.0\.0\.0\s+$Puerto\s+(\S+)\s+$Puerto"
    if (-not $regla -or $regla.Matches[0].Groups[1].Value -ne $ip) {
        netsh interface portproxy delete v4tov4 listenport=$Puerto listenaddress=0.0.0.0 | Out-Null
        netsh interface portproxy add v4tov4 listenport=$Puerto listenaddress=0.0.0.0 connectport=$Puerto connectaddress=$ip | Out-Null
    }
}

# 3. Salud (directo a la IP de WSL; si no se pudo leer, por localhost, que WSL reenvia a Windows)
$destino = if ($ip -match '^\d+\.\d+\.\d+\.\d+$') { $ip } else { "127.0.0.1" }
$estado = "sin_respuesta"; $detalle = ""
try {
    $r = Invoke-RestMethod -Uri "http://${destino}:$Puerto/api/salud" -TimeoutSec 20
    $estado = $r.estado
    if ($estado -ne "ok") {
        $detalle = ($r.servicios.PSObject.Properties | Where-Object { $_.Value.estado -ne "ok" } |
            ForEach-Object { "$($_.Name): $($_.Value.detalle)" }) -join " | "
    }
} catch { $detalle = $_.Exception.Message -replace ",", ";" }
$ramLibre = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
$fecha = Get-Date -Format "dd/MM/yyyy HH:mm"
"$fecha,$estado,""$detalle"",$ramLibre,$ip" | Add-Content -Encoding UTF8 $registro

# 4. Tres fallos seguidos: reiniciar Docker (los contenedores vuelven solos; el modelo tarda unos minutos en cargar)
$ultimas = Get-Content $registro -Tail 3
if (@($ultimas | Where-Object { $_ -match ",sin_respuesta," }).Count -eq 3) {
    wsl.exe -d $Distro -u root -- systemctl restart docker
    "$fecha,reinicio_docker,""3 fallos seguidos"",$ramLibre,$ip" | Add-Content -Encoding UTF8 $registro
}
