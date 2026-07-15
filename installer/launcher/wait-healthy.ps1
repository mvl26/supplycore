# installer/launcher/wait-healthy.ps1
param([int]$Port = 80, [int]$TimeoutSec = 600)
$deadline = (Get-Date).AddSeconds($TimeoutSec)
$url = "http://127.0.0.1:$Port/supplycore"
while ((Get-Date) -lt $deadline) {
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -eq 200) { Write-Host "SupplyCore sẵn sàng."; exit 0 }
  } catch { Start-Sleep -Seconds 5 }
}
Write-Error "Hết thời gian chờ SupplyCore khởi động."
exit 1
