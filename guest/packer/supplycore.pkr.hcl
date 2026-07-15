# guest/packer/supplycore.pkr.hcl — build disk0.qcow2 cho appliance SupplyCore.
#
# disk0 = Ubuntu 22.04 cloud image + Docker Engine + image SupplyCore (đã load,
#         retag đúng hợp đồng) + compose + first-boot/backup systemd units.
#         KHÔNG chứa dữ liệu — dữ liệu nằm trên disk1 (mount /data trong guest).
#
# Đường dẫn file provisioner là TƯƠNG ĐỐI so với thư mục chạy Packer → CI phải
# chạy từ GỐC REPO:  packer build guest/packer/supplycore.pkr.hcl
#
# CHỈ chạy được trên runner Linux CÓ KVM. Dev box không KVM → `packer validate`
# và `packer build` defer sang CI (Task 12).

packer {
  required_plugins {
    qemu = {
      source  = "github.com/hashicorp/qemu"
      version = "~> 1.1"
    }
  }
}

variable "ubuntu_image" {
  type        = string
  default     = "jammy-server-cloudimg-amd64.img"
  description = "Đường dẫn local tới Ubuntu 22.04 cloud image (.img qcow2). CI tải + verify checksum trước khi build."
}

variable "ubuntu_image_sha256" {
  type        = string
  default     = ""
  description = "SHA256 đã PIN của cloud image. CI BẮT BUỘC truyền giá trị này (-var). Để rỗng → iso_checksum 'sha256:' → Packer fail (đúng ý: không build từ image chưa verify)."
}

source "qemu" "disk0" {
  iso_url      = var.ubuntu_image
  iso_checksum = "sha256:${var.ubuntu_image_sha256}"
  disk_image   = true # base là cloud image qcow2, KHÔNG phải installer ISO

  output_directory = "output-disk0"
  vm_name          = "disk0.qcow2"
  format           = "qcow2"
  disk_size        = "20000M"
  disk_compression = true

  accelerator = "kvm"
  headless    = true
  cpus        = 2
  memory      = 4096

  # cloud-init NoCloud: ISO nhãn "cidata" để build VM tự cấu hình + mở SSH.
  # DÙNG cloud-init RIÊNG cho build (guest/packer/cloud-init), KHÔNG dùng seed
  # production (guest/cloud-init): seed prod tắt SSH (Packer không vào được) và
  # bật first-boot.service ngay (chạy trước khi Docker/image tồn tại).
  # Seed THẬT do make-data.ps1 (Task 11) sinh mỗi lần cài.
  cd_files = [
    "guest/packer/cloud-init/user-data",
    "guest/packer/cloud-init/meta-data",
  ]
  cd_label = "cidata"

  # Khớp user trong guest/packer/cloud-init/user-data.
  communicator = "ssh"
  ssh_username = "packer"
  ssh_password = "packer"
  ssh_timeout  = "20m"

  # Gỡ user build NGAY trong shutdown: sudo elevate khi sudoers còn hiệu lực →
  # root xoá user packer + drop-in (sudoers/sshd ssh_pwauth) → shutdown. Nhờ vậy
  # build vẫn halt sạch mà user build KHÔNG lọt vào disk0 ship cho bệnh viện.
  shutdown_command = "sudo bash -c 'userdel -f -r packer; rm -f /etc/sudoers.d/90-cloud-init-users /etc/ssh/sshd_config.d/50-cloud-init.conf; shutdown -P now'"
}

build {
  sources = ["source.qemu.disk0"]

  # Stage artifact vào /tmp build VM. destination "/tmp/" (có dấu /) → mỗi source
  # giữ basename: /tmp/compose.yml, /tmp/bench, /tmp/supplycore-image.tar, ...
  provisioner "file" {
    sources = [
      "deploy/compose.yml",
      "guest/compose.override.yml",
      "guest/ensure-data.sh",
      "guest/first-boot.sh",
      "guest/backup.sh",
      "guest/bin/bench",
      "guest/ensure-data.service",
      "guest/first-boot.service",
      "guest/backup.service",
      "guest/backup.timer",
      "supplycore-image.tar", # do Task 12 build & save ở gốc repo (tag ghcr.io/mvl26/supplycore:latest)
    ]
    destination = "/tmp/"
  }

  provisioner "shell" {
    script          = "guest/packer/install.sh"
    execute_command = "sudo -E bash '{{ .Path }}'"
  }
}
