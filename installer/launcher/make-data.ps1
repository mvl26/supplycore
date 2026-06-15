# installer/launcher/make-data.ps1
# Tạo dữ liệu BỀN cho SupplyCore VM:
#   1) disk1.qcow2 (30G) — KHÔNG ghi đè nếu đã có (giữ DB/files khi cài lại/cập nhật).
#   2) seed.iso (cidata) — render cloud-init user-data, thay __ADMIN_PASSWORD__ bằng mật khẩu wizard.
#
# Chạy bởi installer (Inno [Code] CurStepChanged ssPostInstall) với:
#   make-data.ps1 -DataDir "C:\ProgramData\SupplyCore" -AdminPassword "<pw>"
# qemu-img.exe nằm trong bundle QEMU portable ({app}\launcher\qemu, = $PSScriptRoot\qemu) — forward dep Task 13.
# oscdimg.exe là công cụ tạo ISO đã chọn ({app}\launcher\oscdimg.exe, = $PSScriptRoot\oscdimg.exe) — forward dep Task 13.
# KHÔNG in/log mật khẩu plaintext.

param(
  [Parameter(Mandatory = $true)][string]$DataDir,
  [Parameter(Mandatory = $true)][string]$AdminPassword,
  [string]$SiteName = 'supplycore.localhost'   # khớp spec §4b (cloud-init dùng supplycore.localhost)
)

$ErrorActionPreference = 'Stop'

$qemuImg = Join-Path $PSScriptRoot 'qemu\qemu-img.exe'
$oscdimg = Join-Path $PSScriptRoot 'oscdimg.exe'
$ciSrc   = Join-Path $PSScriptRoot 'cloud-init'

# --- 0) DataDir ---
if (-not (Test-Path -LiteralPath $DataDir)) {
  New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
}

# --- 1) disk1.qcow2 (no-clobber: chỉ tạo khi CHƯA có, để giữ dữ liệu) ---
$disk1 = Join-Path $DataDir 'disk1.qcow2'
if (-not (Test-Path -LiteralPath $disk1)) {
  Write-Host "Tạo ổ dữ liệu bền disk1.qcow2 (30G)..."
  & $qemuImg create -f qcow2 $disk1 30G
  if ($LASTEXITCODE -ne 0) { throw "qemu-img create disk1.qcow2 thất bại (exit $LASTEXITCODE)." }
} else {
  Write-Host "disk1.qcow2 đã tồn tại — giữ nguyên (không tạo lại)."
}

# --- 2) seed.iso (cidata) với mật khẩu admin ---
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("sc-cidata-" + [System.Guid]::NewGuid().ToString('N'))
try {
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null

  $tplPath = Join-Path $ciSrc 'user-data'
  if (-not (Test-Path -LiteralPath $tplPath)) { throw "Không tìm thấy template cloud-init: $tplPath" }
  $tpl = Get-Content -LiteralPath $tplPath -Raw

  if ($tpl -notmatch '__ADMIN_PASSWORD__') {
    throw "Template cloud-init thiếu placeholder __ADMIN_PASSWORD__ — không an toàn để build seed.iso."
  }

  $rendered = $tpl.Replace('__ADMIN_PASSWORD__', $AdminPassword)

  # ASSERT (Correction C): placeholder PHẢI biến mất. Nếu còn -> thay thế thất bại,
  # nếu không chặn thì chuỗi literal "__ADMIN_PASSWORD__" sẽ thành mật khẩu admin thật.
  if ($rendered -match '__ADMIN_PASSWORD__') {
    throw "Thay thế __ADMIN_PASSWORD__ THẤT BẠI — hủy build seed.iso (tránh mật khẩu sai)."
  }

  # Ghi không thêm newline thừa (UTF-8 không BOM, LF cho cloud-init).
  $renderedLf = $rendered -replace "`r`n", "`n"
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText((Join-Path $tmp 'user-data'), $renderedLf, $utf8NoBom)

  $metaSrc = Join-Path $ciSrc 'meta-data'
  if (-not (Test-Path -LiteralPath $metaSrc)) { throw "Không tìm thấy meta-data: $metaSrc" }
  Copy-Item -LiteralPath $metaSrc -Destination (Join-Path $tmp 'meta-data') -Force

  $seed = Join-Path $DataDir 'seed.iso'
  Write-Host "Tạo seed.iso (nhãn cidata)..."
  # oscdimg: -lcidata = volume label 'cidata'; -j2 = Joliet+ISO9660. (Windows ADK redistributable.)
  & $oscdimg "-lcidata" "-j2" $tmp $seed
  if ($LASTEXITCODE -ne 0) { throw "oscdimg tạo seed.iso thất bại (exit $LASTEXITCODE)." }

  Write-Host "Hoàn tất khởi tạo dữ liệu."
}
finally {
  # Xóa thư mục tạm chứa user-data đã render (có mật khẩu plaintext).
  if (Test-Path -LiteralPath $tmp) {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
  }
}
