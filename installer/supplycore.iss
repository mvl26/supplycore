; installer/supplycore.iss
; SupplyCore (Frappe v15) — Windows one-file installer.
; Compiles to SupplyCore-Setup-<ver>.exe via ISCC (defers to CI / Windows; Task 12).
;
; File layout produced by this installer:
;   {app}\disk0.qcow2                  (shipped, read-only base image; = WinSW %BASE%\disk0.qcow2)
;   {app}\SupplyCore-service.exe       (WinSW; %BASE%)
;   {app}\SupplyCore-service.xml       (WinSW service def; reads %SC_ACCEL%/%SC_DATA%/%SC_PORT%)
;   {app}\whpx-check.ps1
;   {app}\launcher\run-vm.ps1, wait-healthy.ps1, make-data.ps1
;   {app}\launcher\qemu\*              (QEMU portable incl. qemu-system-x86_64.exe + qemu-img.exe)
;   {app}\launcher\cloud-init\*        (user-data template + meta-data; consumed by make-data.ps1)
; Data (NEVER touched by uninstall), created at runtime by make-data.ps1:
;   {commonappdata}\SupplyCore\disk1.qcow2   (= %SC_DATA%\disk1.qcow2, persistent DB/files)
;   {commonappdata}\SupplyCore\seed.iso      (= %SC_DATA%\seed.iso, cloud-init cidata w/ admin pw)
;   {commonappdata}\SupplyCore\supplycore-vm.log (service workingdirectory)

#define AppName "SupplyCore"
#ifndef SC_VERSION
  #define SC_VERSION GetEnv("SC_VERSION")
#endif
#if SC_VERSION == ""
  #define SC_VERSION "0.0.0-dev"
#endif
#define AppVersion SC_VERSION

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=SupplyCore
; SourceDir = repo root ({#SourcePath} là thư mục chứa .iss = installer\). Nhờ vậy các
; path trong [Files] (dist\, installer\, guest\) phân giải từ gốc repo, không bị lặp
; thành installer\installer\... (Task 12 review).
SourceDir={#SourcePath}\..
DefaultDirName={commonpf}\SupplyCore
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputBaseFilename=SupplyCore-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
; --- QEMU portable (CI-produced under dist\qemu by Task 13 fetch-deps; incl. qemu-system-x86_64.exe + qemu-img.exe) ---
Source: "dist\qemu\*";                              DestDir: "{app}\launcher\qemu";       Flags: recursesubdirs ignoreversion
; --- Launcher scripts (run-vm.ps1, wait-healthy.ps1, make-data.ps1) ---
Source: "installer\launcher\*";                     DestDir: "{app}\launcher";            Flags: recursesubdirs ignoreversion
; --- Production cloud-init (template user-data + meta-data) — make-data.ps1 reads $PSScriptRoot\cloud-init\user-data ---
Source: "guest\cloud-init\*";                       DestDir: "{app}\launcher\cloud-init"; Flags: recursesubdirs ignoreversion
; (cidata seed.iso do make-data.ps1 tạo runtime bằng IMAPI2FS — COM Windows sẵn có — nên KHÔNG ship ISO builder nào.)
; --- WinSW service host (CI-produced under dist by Task 13) ---
Source: "dist\WinSW.exe";                           DestDir: "{app}"; DestName: "SupplyCore-service.exe"; Flags: ignoreversion
Source: "installer\winsw\supplycore-service.xml";   DestDir: "{app}"; DestName: "SupplyCore-service.xml"; Flags: ignoreversion
; --- Base disk image (CI-produced by Packer under dist\disk0.qcow2; Task 9) ---
Source: "dist\disk0.qcow2";                         DestDir: "{app}";                     Flags: ignoreversion
; --- WHPX enablement/check ---
Source: "installer\whpx-check.ps1";                 DestDir: "{app}";                     Flags: ignoreversion

[Icons]
; Start Menu shortcuts cho IT bệnh viện: sao lưu / phục hồi dữ liệu (mức file disk1.qcow2, §5.3).
; DisableProgramGroupPage=yes chỉ bỏ TRANG chọn group trong wizard — Inno vẫn tạo được icon dưới
; nhóm {autoprograms}\SupplyCore. Cả 2 script tự kiểm tra quyền Administrator và TỰ NÂNG QUYỀN
; (UAC qua Start-Process -Verb RunAs) khi cần — nên [Icons] không cần ép elevation. Nếu UAC bị chặn,
; IT có thể bấm chuột phải shortcut > "Run as administrator".
; - "Sao lưu": chạy không tham số → backup-export.ps1 mặc định DestDir = {commonappdata}\SupplyCore\exports.
; - "Phục hồi": chạy không tham số → restore.ps1 mở hộp thoại chọn file .qcow2.
Name: "{autoprograms}\SupplyCore\Sao lưu SupplyCore"; \
  Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\launcher\backup-export.ps1"""; \
  Comment: "Sao lưu dữ liệu SupplyCore ra {commonappdata}\SupplyCore\exports"
Name: "{autoprograms}\SupplyCore\Phục hồi SupplyCore (chọn file)"; \
  Filename: "powershell.exe"; \
  Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\launcher\restore.ps1"""; \
  Comment: "Phục hồi dữ liệu SupplyCore từ file sao lưu .qcow2"

[UninstallRun]
; Stop + uninstall the WinSW service. NOTE: we intentionally do NOT delete
; {commonappdata}\SupplyCore (disk1.qcow2 + DB + backups) — data is preserved on uninstall/update.
Filename: "{app}\SupplyCore-service.exe"; Parameters: "stop";      Flags: runhidden; RunOnceId: "scStopSvc"
Filename: "{app}\SupplyCore-service.exe"; Parameters: "uninstall"; Flags: runhidden; RunOnceId: "scRmSvc"

[Code]
var
  AdminPwPage: TInputQueryWizardPage;
  PortPage: TInputQueryWizardPage;
  NeedReboot: Boolean;

procedure InitializeWizard;
begin
  NeedReboot := False;
  AdminPwPage := CreateInputQueryPage(wpSelectDir, 'Mật khẩu Administrator',
    'Đặt mật khẩu cho tài khoản Administrator của SupplyCore',
    'Mật khẩu này dùng để đăng nhập SupplyCore lần đầu. Tránh các ký tự: " ` '' \');
  AdminPwPage.Add('Mật khẩu:', True);
  // Prefill từ tham số dòng lệnh /ADMINPW= (rỗng nếu không truyền). Cho phép cài im lặng
  // (/SILENT /ADMINPW=xxx) — bắt buộc cho CI smoke + IT deploy hàng loạt. Ở chế độ silent,
  // trang wizard bị bỏ qua nhưng Values[0] vẫn giữ giá trị param này.
  AdminPwPage.Values[0] := ExpandConstant('{param:ADMINPW|}');
  PortPage := CreateInputQueryPage(AdminPwPage.ID, 'Cổng truy cập',
    'Cổng localhost để mở SupplyCore (mặc định 80)', '');
  PortPage.Add('Cổng:', False);
  PortPage.Values[0] := ExpandConstant('{param:PORT|80}');
end;

// Lý do từ chối ký tự (rỗng = hợp lệ). Dùng cho cả wizard lẫn đường silent.
function PwRejectReason(const pw: String): String;
begin
  Result := '';
  if pw = '' then
    Result := 'Mật khẩu Administrator trống. Cài im lặng phải truyền /ADMINPW=...'
  else if (Pos('"', pw) > 0) or (Pos(#96, pw) > 0) or (Pos('''', pw) > 0) or (Pos('\', pw) > 0) then
    Result := 'Mật khẩu không được chứa các ký tự: " `  '' \';
end;

function IsAllDigits(const S: String): Boolean;
var i: Integer;
begin
  Result := (Length(S) > 0);
  for i := 1 to Length(S) do
    if (S[i] < '0') or (S[i] > '9') then
    begin
      Result := False;
      Exit;
    end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var port, reason: String;
begin
  Result := True;
  if CurPageID = AdminPwPage.ID then
  begin
    // Charset reject (xem PwRejectReason): bảo vệ command line PowerShell của make-data.ps1
    // (" và `) và systemd EnvironmentFile trong guest (' và \). Đảm bảo mật khẩu tới
    // cloud-init + create-site đúng hệt người dùng gõ (Correction C + Task 11 review M3).
    reason := PwRejectReason(AdminPwPage.Values[0]);
    if reason <> '' then
    begin
      MsgBox(reason, mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
  if CurPageID = PortPage.ID then
  begin
    port := Trim(PortPage.Values[0]);
    if port = '' then
      PortPage.Values[0] := '80'
    else if not IsAllDigits(port) then
    begin
      MsgBox('Cổng phải là số (ví dụ 80).', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

// Set a MACHINE-scope (HKLM) environment variable. Belt-and-suspenders only: it lets a MANUAL
// run-vm.ps1 invocation (outside the service) inherit SC_*. The WinSW service no longer depends
// on this — it gets SC_ACCEL/SC_DATA/SC_PORT from its own <env> block (see SubstituteServiceXml),
// which is immune to the SCM system-environment cache. setx /M writes
// HKLM\...\Session Manager\Environment AND broadcasts WM_SETTINGCHANGE.
function SetMachineEnv(const Name, Value: String): Boolean;
var rc: Integer;
begin
  Result := Exec(ExpandConstant('{sys}\setx.exe'), Name + ' "' + Value + '" /M',
                 '', SW_HIDE, ewWaitUntilTerminated, rc) and (rc = 0);
end;

// Bake the resolved SC_ACCEL/SC_DATA/SC_PORT into the WinSW service XML's own <env> block by
// replacing the @@...@@ markers in the shipped template ({app}\SupplyCore-service.xml). WinSW
// expands %SC_ACCEL%/%SC_DATA%/%SC_PORT% in <arguments> from this <env> — so the service is
// self-contained and does NOT race the SCM system-environment cache. Must run BEFORE
// "SupplyCore-service.exe install".
function SubstituteServiceXml(const Accel, DataDir, Port: String): Boolean;
var
  raw: AnsiString;
  xml, path: String;
begin
  Result := False;
  path := ExpandConstant('{app}\SupplyCore-service.xml');
  if not LoadStringFromFile(path, raw) then
    Exit;
  xml := raw;
  StringChangeEx(xml, '@@SC_ACCEL@@', Accel, True);
  StringChangeEx(xml, '@@SC_DATA@@', DataDir, True);
  StringChangeEx(xml, '@@SC_PORT@@', Port, True);
  raw := xml;
  Result := SaveStringToFile(path, raw, False);
end;

function PSFile(const ScriptPath: String): String;
begin
  Result := '-NoProfile -ExecutionPolicy Bypass -File "' + ScriptPath + '"';
end;

procedure RegisterPostRebootBrowser(const Port: String);
var cmd: String;
begin
  // After a reboot the Automatic service starts QEMU with fresh machine env; open the browser
  // at next logon once it is healthy. Best-effort (RunOnce, deleted after it runs).
  cmd := 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& ''' +
         ExpandConstant('{app}\launcher\wait-healthy.ps1') + ''' -Port ' + Port +
         ' -TimeoutSec 900; Start-Process ''http://127.0.0.1:' + Port + '/supplycore''"';
  RegWriteStringValue(HKEY_LOCAL_MACHINE,
    'SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce', 'SupplyCoreOpen', cmd);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  rc: Integer;
  dataDir, port, pw, accel, reason: String;
  waitTimeout: Integer;
  serviceStarted: Boolean;
begin
  if CurStep <> ssPostInstall then
    Exit;

  dataDir := ExpandConstant('{commonappdata}\SupplyCore');
  port := Trim(PortPage.Values[0]);
  if port = '' then port := '80';
  // pw đã prefill từ /ADMINPW= (silent) hoặc người dùng gõ (wizard). Validate LẠI ở đây
  // vì cài im lặng KHÔNG chạy NextButtonClick — nếu không sẽ provision với mật khẩu rỗng/sai.
  pw := AdminPwPage.Values[0];
  reason := PwRejectReason(pw);
  if reason <> '' then
  begin
    MsgBox(reason + #13#10 + 'Cài im lặng: thêm /ADMINPW="<mật khẩu hợp lệ>".', mbError, MB_OK);
    Exit; // không provision với mật khẩu rỗng/sai → dịch vụ không được cài → CI test-install fail rõ ràng.
  end;
  ForceDirectories(dataDir);

  // 1) WHPX: enable/check accelerator. Exit codes (whpx-check.ps1):
  //    0 = WHPX ready, 2 = enabled but reboot required, 3 = WHPX unavailable -> TCG fallback.
  accel := 'whpx';
  waitTimeout := 600;
  if not Exec('powershell.exe', PSFile(ExpandConstant('{app}\whpx-check.ps1')),
              '', SW_HIDE, ewWaitUntilTerminated, rc) then
    rc := 3; // could not even run the check -> treat as no WHPX
  if rc = 3 then
  begin
    accel := 'tcg';
    waitTimeout := 1800; // TCG (software emulation) first boot is much slower
    MsgBox('Máy này không hỗ trợ Windows Hypervisor Platform (WHPX). SupplyCore sẽ chạy ở chế độ '
      + 'mô phỏng phần mềm (TCG) — hiệu năng sẽ CHẬM. Khuyến nghị bật ảo hóa trong BIOS/UEFI.',
      mbInformation, MB_OK);
  end
  else if rc = 2 then
    NeedReboot := True; // WHPX just enabled — needs reboot before it actually works.

  // 2) Belt-and-suspenders: persist machine-scope env vars so a MANUAL run-vm.ps1 inherits SC_*.
  //    The service itself does NOT rely on these (see step 3b) — failures here are non-fatal.
  if not SetMachineEnv('SC_ACCEL', accel) then
    MsgBox('Không thể đặt biến môi trường SC_ACCEL.', mbError, MB_OK);
  if not SetMachineEnv('SC_DATA', dataDir) then
    MsgBox('Không thể đặt biến môi trường SC_DATA.', mbError, MB_OK);
  if not SetMachineEnv('SC_PORT', port) then
    MsgBox('Không thể đặt biến môi trường SC_PORT.', mbError, MB_OK);

  // 3) Create persistent disk1 (if absent) + render cloud-init seed.iso with the admin password.
  if not Exec('powershell.exe',
       PSFile(ExpandConstant('{app}\launcher\make-data.ps1')) +
       ' -DataDir "' + dataDir + '" -AdminPassword "' + pw + '"',
       '', SW_HIDE, ewWaitUntilTerminated, rc) or (rc <> 0) then
  begin
    MsgBox('Khởi tạo dữ liệu (disk1/seed.iso) thất bại (mã ' + IntToStr(rc) + '). '
      + 'Cài đặt sẽ dừng phần khởi động dịch vụ; xem nhật ký để xử lý.', mbError, MB_OK);
    Exit;
  end;

  // 3b) Bake resolved SC_ACCEL/SC_DATA/SC_PORT into the WinSW service XML's own <env> block.
  //     This makes the service self-contained: WinSW expands %SC_*% in <arguments> from its <env>,
  //     immune to the SCM system-environment cache — so it can start immediately, no reboot needed
  //     (except the genuine WHPX rc=2 case). MUST happen before the service is installed.
  if not SubstituteServiceXml(accel, dataDir, port) then
  begin
    MsgBox('Không thể ghi cấu hình dịch vụ (SupplyCore-service.xml). Cài đặt sẽ dừng.', mbError, MB_OK);
    Exit;
  end;

  // 4) Install the WinSW service (startmode Automatic per supplycore-service.xml).
  if not Exec(ExpandConstant('{app}\SupplyCore-service.exe'), 'install',
              '', SW_HIDE, ewWaitUntilTerminated, rc) or (rc <> 0) then
  begin
    MsgBox('Cài đặt dịch vụ SupplyCore thất bại (mã ' + IntToStr(rc) + ').', mbError, MB_OK);
    Exit;
  end;

  if NeedReboot then
  begin
    // WHPX needs a reboot: do NOT start now. The Automatic service starts on next boot with a
    // fresh machine environment. Open the browser at next logon once healthy.
    RegisterPostRebootBrowser(port);
    MsgBox('Đã cài đặt xong. Cần KHỞI ĐỘNG LẠI máy để hoàn tất bật ảo hóa (WHPX). '
      + 'Sau khi khởi động lại, SupplyCore sẽ tự chạy và mở trong trình duyệt.', mbInformation, MB_OK);
    Exit;
  end;

  // 5) Start the service and wait until healthy, then open the browser.
  serviceStarted := Exec(ExpandConstant('{app}\SupplyCore-service.exe'), 'start',
                         '', SW_HIDE, ewWaitUntilTerminated, rc) and (rc = 0);
  if serviceStarted then
    Exec('powershell.exe',
      PSFile(ExpandConstant('{app}\launcher\wait-healthy.ps1')) + ' -Port ' + port +
      ' -TimeoutSec ' + IntToStr(waitTimeout),
      '', SW_HIDE, ewWaitUntilTerminated, rc)
  else
    rc := 1;

  if rc = 0 then
    ShellExec('open', 'http://127.0.0.1:' + port + '/supplycore', '', '', SW_SHOW, ewNoWait, rc)
  else
  begin
    // Graceful fallback: not an env-cache race anymore (the service reads SC_* from its own <env>),
    // but a TCG first boot (or slow disk) can still exceed the wait timeout. Defer to a reboot:
    // the Automatic service restarts and we open the browser once healthy.
    NeedReboot := True;
    RegisterPostRebootBrowser(port);
    MsgBox('SupplyCore chưa phản hồi trong thời gian chờ. Vui lòng KHỞI ĐỘNG LẠI máy để hoàn tất; '
      + 'dịch vụ sẽ tự chạy lại sau khi khởi động và mở trong trình duyệt.', mbInformation, MB_OK);
  end;
end;

function NeedRestart(): Boolean;
begin
  Result := NeedReboot;
end;
