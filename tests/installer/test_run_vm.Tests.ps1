# tests/installer/test_run_vm.Tests.ps1
BeforeAll {
  . "$PSScriptRoot/../../installer/launcher/run-vm.ps1" -DryRun
}
Describe "Build-QemuArgs" {
  It "dùng accel whpx khi -Accel whpx" {
    $args = Build-QemuArgs -Accel 'whpx' -Disk0 'd0.qcow2' -Disk1 'd1.qcow2' -Port 80 -SeedIso 'seed.iso'
    ($args -join ' ') | Should -Match 'accel=whpx'
  }
  It "fallback tcg khi -Accel tcg" {
    $args = Build-QemuArgs -Accel 'tcg' -Disk0 'd0.qcow2' -Disk1 'd1.qcow2' -Port 80 -SeedIso 'seed.iso'
    ($args -join ' ') | Should -Match 'accel=tcg'
  }
  It "forward host port tới guest 80" {
    $args = Build-QemuArgs -Accel 'whpx' -Disk0 'd0.qcow2' -Disk1 'd1.qcow2' -Port 8080 -SeedIso 'seed.iso'
    ($args -join ' ') | Should -Match 'hostfwd=tcp:127.0.0.1:8080-:80'
  }
  It "gắn cả disk0 và disk1" {
    $args = Build-QemuArgs -Accel 'whpx' -Disk0 'd0.qcow2' -Disk1 'd1.qcow2' -Port 80 -SeedIso 'seed.iso'
    ($args -join ' ') | Should -Match 'd0.qcow2'
    ($args -join ' ') | Should -Match 'd1.qcow2'
  }
}
