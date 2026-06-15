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
;   {app}\launcher\oscdimg.exe         (ISO builder; consumed by make-data.ps1)
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
; --- ISO builder (CI-produced under dist by Task 13 fetch-deps) — make-data.ps1 calls $PSScriptRoot\oscdimg.exe ---
Source: "dist\oscdimg.exe";                         DestDir: "{app}\launcher";            Flags: ignoreversion
; --- WinSW service host (CI-produced under dist by Task 13) ---
Source: "dist\WinSW.exe";                           DestDir: "{app}"; DestName: "SupplyCore-service.exe"; Flags: ignoreversion
Source: "installer\winsw\supplycore-service.xml";   DestDir: "{app}"; DestName: "SupplyCore-service.xml"; Flags: ignoreversion
; --- Base disk image (CI-produced by Packer under dist\disk0.qcow2; Task 9) ---
Source: "dist\disk0.qcow2";                         DestDir: "{app}";                     Flags: ignoreversion
; --- WHPX enablement/check ---
Source: "installer\whpx-check.ps1";                 DestDir: "{app}";                     Flags: ignoreversion

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
    'Mật khẩu này dùng để đăng nhập SupplyCore lần đầu. Tránh các ký tự " và `.');
  AdminPwPage.Add('Mật khẩu:', True);
  PortPage := CreateInputQueryPage(AdminPwPage.ID, 'Cổng truy cập',
    'Cổng localhost để mở SupplyCore (mặc định 80)', '');
  PortPage.Add('Cổng:', False);
  PortPage.Values[0] := '80';
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
var pw, port: String;
begin
  Result := True;
  if CurPageID = AdminPwPage.ID then
  begin
    pw := AdminPwPage.Values[0];
    if pw = '' then
    begin
      MsgBox('Vui lòng nhập mật khẩu Administrator.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    // Reject characters that would break the PowerShell command line used to pass the
    // password to make-data.ps1 (double quote breaks out of the quoted arg; backtick is
    // PowerShell's escape char). This guarantees the value substituted into cloud-init is
    // exactly what the user typed (Correction C — no silent wrong-password substitution).
    if (Pos('"', pw) > 0) or (Pos(#96, pw) > 0) then
    begin
      MsgBox('Mật khẩu không được chứa ký tự " hoặc `.', mbError, MB_OK);
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

// Set a MACHINE-scope (HKLM) environment variable. The WinSW service runs as LocalSystem and
// reads %SC_ACCEL%/%SC_DATA%/%SC_PORT% from the machine environment — these MUST be machine scope.
// setx /M writes HKLM\...\Session Manager\Environment AND broadcasts WM_SETTINGCHANGE.
function SetMachineEnv(const Name, Value: String): Boolean;
var rc: Integer;
begin
  Result := Exec(ExpandConstant('{sys}\setx.exe'), Name + ' "' + Value + '" /M',
                 '', SW_HIDE, ewWaitUntilTerminated, rc) and (rc = 0);
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
  dataDir, port, pw, accel: String;
  waitTimeout: Integer;
  serviceStarted: Boolean;
begin
  if CurStep <> ssPostInstall then
    Exit;

  dataDir := ExpandConstant('{commonappdata}\SupplyCore');
  port := Trim(PortPage.Values[0]);
  if port = '' then port := '80';
  pw := AdminPwPage.Values[0];
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

  // 2) Persist machine-scope env vars for the LocalSystem WinSW service.
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
    // Graceful fallback: the service may have launched before SCM picked up the freshly-set
    // machine env (SCM caches the system environment), or a TCG first boot is still slow.
    // Defer to a reboot: the Automatic service restarts with fresh env, then we open the browser.
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
