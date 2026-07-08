# installer/launcher/make-data.ps1
# Tạo dữ liệu BỀN cho SupplyCore VM:
#   1) disk1.qcow2 (30G) — KHÔNG ghi đè nếu đã có (giữ DB/files khi cài lại/cập nhật).
#   2) seed.iso (cidata) — render cloud-init user-data, thay __ADMIN_PASSWORD__ bằng mật khẩu wizard.
#
# Chạy bởi installer (Inno [Code] CurStepChanged ssPostInstall) với:
#   make-data.ps1 -DataDir "C:\ProgramData\SupplyCore" -AdminPassword "<pw>"
# qemu-img.exe nằm trong bundle QEMU portable ({app}\launcher\qemu, = $PSScriptRoot\qemu) — forward dep Task 13.
# seed.iso được tạo bằng IMAPI2FS (COM Windows sẵn có) — KHÔNG cần oscdimg/ADK/mkisofs (không phụ thuộc binary ngoài).
# KHÔNG in/log mật khẩu plaintext.

param(
  [Parameter(Mandatory = $true)][string]$DataDir,
  [Parameter(Mandatory = $true)][string]$AdminPassword,
  [string]$SiteName = 'supplycore.localhost'   # khớp spec §4b (cloud-init dùng supplycore.localhost)
)

$ErrorActionPreference = 'Stop'

$qemuImg = Join-Path $PSScriptRoot 'qemu\qemu-img.exe'
$ciSrc   = Join-Path $PSScriptRoot 'cloud-init'

# --- Helper: tạo ISO cidata (ISO9660 + Joliet) bằng IMAPI2FS (COM Windows sẵn có) ----------
# cloud-init NoCloud cần: nhãn volume = 'cidata', chứa user-data + meta-data (tên thường).
# Joliet giữ tên file thường (oscdimg -j2 / genisoimage -J tương đương). KHÔNG cần binary ngoài.
function New-CidataIso {
  param(
    [Parameter(Mandatory = $true)][string]$SourceDir,
    [Parameter(Mandatory = $true)][string]$IsoPath
  )

  $fsi = New-Object -ComObject IMAPI2FS.MsftFileSystemImage
  try {
    # FileSystemsToCreate: 1 = ISO9660, 2 = Joliet -> 3 = cả hai (Joliet giữ user-data/meta-data thường).
    $fsi.FileSystemsToCreate = 3
    $fsi.VolumeName = 'cidata'
    # AddTree(dir, $false): thêm NỘI DUNG thư mục vào gốc ISO, không lồng thêm thư mục gốc thừa.
    $fsi.Root.AddTree($SourceDir, $false)

    $resultImage = $fsi.CreateResultImage()
    # ImageStream là COM IStream — cast sang ComTypes.IStream để đọc Stat/Read theo block.
    $istream = [System.Runtime.InteropServices.ComTypes.IStream]$resultImage.ImageStream

    # Stat -> cbSize (kích thước ảnh). STATFLAG_NONAME = 1 (không cấp phát tên -> không leak BSTR).
    $stat = New-Object System.Runtime.InteropServices.ComTypes.STATSTG
    $istream.Stat([ref]$stat, 1)
    $size = [int64]$stat.cbSize
    if ($size -le 0) {
      throw "IMAPI2FS trả ảnh rỗng (cbSize=$size) — hủy tạo seed.iso (tránh ISO 0 byte)."
    }

    # ISO9660 sector = 2048 byte; ImageStream của IMAPI2 luôn là bội số của block này.
    $blockSize = 2048
    $buffer = New-Object byte[] $blockSize
    # pcbRead nhận số byte thực đọc mỗi lần Read (ULONG). Cấp phát rồi giải phóng ở finally.
    $pcbRead = [System.Runtime.InteropServices.Marshal]::AllocHGlobal([System.IntPtr]::Size)
    $out = [System.IO.File]::Open($IsoPath, [System.IO.FileMode]::Create,
                                  [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    try {
      $remaining = $size
      while ($remaining -gt 0) {
        $toRead = [int][System.Math]::Min([int64]$blockSize, $remaining)
        $istream.Read($buffer, $toRead, $pcbRead)
        $read = [System.Runtime.InteropServices.Marshal]::ReadInt32($pcbRead)
        if ($read -le 0) { break }   # EOF sớm bất thường -> dừng (assert non-empty bên dưới sẽ bắt).
        $out.Write($buffer, 0, $read)
        $remaining -= $read
      }
      $out.Flush()
    }
    finally {
      $out.Dispose()
      [System.Runtime.InteropServices.Marshal]::FreeHGlobal($pcbRead)
    }
  }
  finally {
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($fsi) | Out-Null
  }

  # Assert: file tồn tại và non-empty (COM lỗi mà nuốt -> 0 byte ISO sẽ làm cloud-init treo).
  $isoFile = Get-Item -LiteralPath $IsoPath -ErrorAction Stop
  if ($isoFile.Length -le 0) {
    throw "seed.iso rỗng (0 byte) sau khi tạo bằng IMAPI2FS — hủy (cloud-init sẽ không boot)."
  }
}

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
  Write-Host "Tạo seed.iso (nhãn cidata) bằng IMAPI2FS (COM Windows)..."
  New-CidataIso -SourceDir $tmp -IsoPath $seed

  Write-Host "Hoàn tất khởi tạo dữ liệu."
}
finally {
  # Xóa thư mục tạm chứa user-data đã render (có mật khẩu plaintext).
  if (Test-Path -LiteralPath $tmp) {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
  }
}
