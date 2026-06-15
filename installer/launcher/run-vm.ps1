# installer/launcher/run-vm.ps1
param(
  [string]$Accel = 'whpx',
  [string]$Disk0,
  [string]$Disk1,
  [int]$Port = 80,
  [string]$SeedIso,
  [string]$QemuExe = "$PSScriptRoot\qemu\qemu-system-x86_64.exe",
  [switch]$DryRun
)

function Build-QemuArgs {
  param($Accel, $Disk0, $Disk1, $Port, $SeedIso)
  return @(
    '-machine', "type=q35,accel=$Accel"
    '-cpu', 'max'
    '-smp', '2'
    '-m', '4096'
    '-drive', "file=$Disk0,if=virtio,format=qcow2"
    '-drive', "file=$Disk1,if=virtio,format=qcow2"
    '-drive', "file=$SeedIso,if=virtio,format=raw,readonly=on"
    '-netdev', "user,id=n0,hostfwd=tcp:127.0.0.1:$Port-:80"
    '-device', 'virtio-net-pci,netdev=n0'
    '-display', 'none'
    '-serial', 'file:supplycore-vm.log'
  )
}

if ($DryRun) { return }

$qemuArgs = Build-QemuArgs -Accel $Accel -Disk0 $Disk0 -Disk1 $Disk1 -Port $Port -SeedIso $SeedIso
& $QemuExe @qemuArgs
