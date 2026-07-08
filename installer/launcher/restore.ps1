# installer/launcher/restore.ps1
# Phục hồi (restore) dữ liệu SupplyCore từ một file sao lưu `.qcow2` đã export trước đó.
#
# Bản chất: dừng dịch vụ "SupplyCore", đổi tên ổ dữ liệu hiện tại `disk1.qcow2` thành
# `disk1.qcow2.bak-<thời-gian>` (KHÔNG xoá — để IT tự dọn sau khi đã kiểm chứng), copy file
# backup vào thay thế `disk1.qcow2`, rồi khởi động lại dịch vụ. KHÔNG cần shell vào VM.
#
# Chạy từ Start Menu ("Phục hồi SupplyCore (chọn file)") không cần tham số: nếu thiếu -BackupFile
# sẽ mở hộp thoại chọn file `.qcow2`. Cần quyền Administrator — script tự nâng quyền (UAC) nếu chưa.
#
#   restore.ps1 [-BackupFile <file.qcow2>] [-Force]
#   -Force: bỏ qua câu hỏi xác nhận (dùng cho kịch bản tự động).

param(
  [string]$BackupFile,
  [switch]$Force
)

$ErrorActionPreference = 'Stop'

# --- 0) Tự nâng quyền Administrator (UAC) nếu chưa có ---
$identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Host "Cần quyền Administrator — đang yêu cầu nâng quyền (UAC)..."
  $relaunch = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath)
  if ($PSBoundParameters.ContainsKey('BackupFile')) { $relaunch += @('-BackupFile', $BackupFile) }
  if ($Force) { $relaunch += '-Force' }
  Start-Process -FilePath 'powershell.exe' -ArgumentList $relaunch -Verb RunAs
  exit
}

# MessageBox + OpenFileDialog: shortcut Start Menu tự nâng quyền → mở cửa sổ powershell MỚI rồi
# tự đóng khi script kết thúc, nên Write-Host sẽ biến mất. Nạp một lần ở đây để cả hộp thoại chọn
# file lẫn MsgBox kết quả/lỗi đều dùng được (kể cả đường -BackupFile bỏ qua hộp thoại).
Add-Type -AssemblyName System.Windows.Forms

# --- 1) Chọn file backup: nếu thiếu -BackupFile → mở hộp thoại OpenFileDialog ---
if (-not $BackupFile) {
  $dlg = New-Object System.Windows.Forms.OpenFileDialog
  $dlg.Title  = 'Chọn file sao lưu SupplyCore (.qcow2)'
  $dlg.Filter = 'SupplyCore backup (*.qcow2)|*.qcow2'
  $startDir   = Join-Path (if ($env:SC_DATA) { $env:SC_DATA } else { 'C:\ProgramData\SupplyCore' }) 'exports'
  if (Test-Path -LiteralPath $startDir) { $dlg.InitialDirectory = $startDir }
  if ($dlg.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
    Write-Host "Đã huỷ — không chọn file nào."
    exit
  }
  $BackupFile = $dlg.FileName
}

# --- 2) Kiểm tra file backup hợp lệ ---
if (-not (Test-Path -LiteralPath $BackupFile)) {
  throw "Không tìm thấy file sao lưu: $BackupFile"
}
if (-not $BackupFile.ToLower().EndsWith('.qcow2')) {
  throw "File sao lưu phải có đuôi .qcow2: $BackupFile"
}

# --- 3) Phân giải thư mục dữ liệu + disk1 ---
$dataDir = if ($env:SC_DATA) { $env:SC_DATA } else { 'C:\ProgramData\SupplyCore' }
$disk1   = Join-Path $dataDir 'disk1.qcow2'

# --- 4) CẢNH BÁO + xác nhận (trừ khi -Force) ---
Write-Host ""
Write-Host "==================== CẢNH BÁO ===================="
Write-Host " Phục hồi sẽ GHI ĐÈ toàn bộ dữ liệu hiện tại của SupplyCore."
Write-Host "   Nguồn  : $BackupFile"
Write-Host "   Đích   : $disk1"
Write-Host " Dữ liệu hiện tại sẽ được đổi tên thành disk1.qcow2.bak-<thời-gian> (giữ lại để dự phòng)."
Write-Host "=================================================="
if (-not $Force) {
  $answer = Read-Host "Gõ 'yes' để tiếp tục phục hồi (mọi câu trả lời khác sẽ huỷ)"
  if ($answer -ne 'yes') {
    Write-Host "Đã huỷ phục hồi."
    exit
  }
}

$serviceName = 'SupplyCore'
$svc = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if (-not $svc) { throw "Không tìm thấy dịch vụ Windows '$serviceName' — chưa cài SupplyCore?" }

$stamp   = Get-Date -Format 'yyyyMMdd-HHmmss'
$bakPath = "$disk1.bak-$stamp"
$movedCurrent = $false

try {
  # --- 5) Dừng dịch vụ + chờ Stopped (nhả khoá qcow2) ---
  if ($svc.Status -ne 'Stopped') {
    Write-Host "Dừng dịch vụ $serviceName..."
    Stop-Service -Name $serviceName -Force -ErrorAction Stop
    $deadline = (Get-Date).AddSeconds(120)
    do {
      Start-Sleep -Seconds 2
      $svc.Refresh()
    } while ($svc.Status -ne 'Stopped' -and (Get-Date) -lt $deadline)
    if ($svc.Status -ne 'Stopped') {
      throw "Dịch vụ $serviceName không dừng được trong 120 giây (trạng thái: $($svc.Status))."
    }
  }

  # --- 6) An toàn: đổi tên disk1 hiện tại thành .bak-<thời-gian> trước khi ghi đè ---
  if (Test-Path -LiteralPath $disk1) {
    Write-Host "Sao lưu dự phòng dữ liệu hiện tại -> $bakPath"
    Rename-Item -LiteralPath $disk1 -NewName (Split-Path -Leaf $bakPath) -ErrorAction Stop
    $movedCurrent = $true
  }

  # --- 7) Copy file backup vào thay thế disk1.qcow2 ---
  Write-Host "Đang phục hồi $BackupFile -> $disk1 (có thể mất vài phút)..."
  Copy-Item -LiteralPath $BackupFile -Destination $disk1 -Force
  if (-not (Test-Path -LiteralPath $disk1)) {
    throw "Phục hồi thất bại — không thấy $disk1 sau khi copy."
  }

  Write-Host ""
  Write-Host "Phục hồi thành công. SupplyCore đang khởi động lại với dữ liệu vừa phục hồi."
  Write-Host "Sau khi kiểm tra dữ liệu OK, có thể xoá file dự phòng:"
  Write-Host "  $bakPath"
  if (-not $Force) {
    [System.Windows.Forms.MessageBox]::Show(
      "Phục hồi thành công. SupplyCore đang khởi động lại với dữ liệu vừa phục hồi.`n`n" +
      "Dữ liệu cũ được giữ tại:`n$bakPath`n`nSau khi kiểm tra OK, có thể xoá file này.",
      'SupplyCore - Phục hồi', 'OK', 'Information') | Out-Null
  }
}
catch {
  # --- 9) Rollback: nếu đã đổi tên dữ liệu cũ nhưng disk1 mới chưa có (copy lỗi giữa chừng) → trả lại ---
  if ($movedCurrent -and -not (Test-Path -LiteralPath $disk1) -and (Test-Path -LiteralPath $bakPath)) {
    Write-Host "Có lỗi xảy ra — đang khôi phục dữ liệu cũ ($bakPath -> disk1.qcow2)..."
    Rename-Item -LiteralPath $bakPath -NewName 'disk1.qcow2' -ErrorAction SilentlyContinue
  }
  if (-not $Force) {
    [System.Windows.Forms.MessageBox]::Show(
      "Phục hồi THẤT BẠI:`n`n$($_.Exception.Message)`n`n" +
      "Dữ liệu cũ đã được giữ/khôi phục (xem disk1.qcow2 / *.bak-* trong thư mục dữ liệu).",
      'SupplyCore - Phục hồi', 'OK', 'Error') | Out-Null
  }
  throw
}
finally {
  # --- 8) LUÔN khởi động lại dịch vụ (kể cả khi lỗi + rollback) để SupplyCore không bị treo ở
  #         trạng thái dừng. Start-Service idempotent khi đang chạy → an toàn ở đường thành công. ---
  Write-Host "Khởi động lại dịch vụ $serviceName..."
  Start-Service -Name $serviceName -ErrorAction SilentlyContinue
}
