# installer/whpx-check.ps1
# Trả exit 0 nếu WHPX sẵn sàng; bật nếu thiếu (cần admin); exit 2 nếu cần reboot.
$feature = Get-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -ErrorAction SilentlyContinue
if ($null -eq $feature) { Write-Warning "Không có WHPX trên máy này — sẽ fallback TCG (chậm)."; exit 3 }
if ($feature.State -eq 'Enabled') { Write-Host "WHPX đã bật."; exit 0 }
Write-Host "Đang bật Windows Hypervisor Platform..."
$r = Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -NoRestart
if ($r.RestartNeeded) { Write-Host "Cần khởi động lại để hoàn tất WHPX."; exit 2 }
exit 0
