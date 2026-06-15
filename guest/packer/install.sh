#!/usr/bin/env bash
# guest/packer/install.sh — provisioner chạy TRONG build VM (Packer: sudo -E bash).
# Cài Docker Engine, dàn compose + systemd units + bench wrapper vào /opt/supplycore,
# load image SupplyCore, retag về ĐÚNG tag hợp đồng, pre-pull base images để boot
# OFFLINE (PULL_POLICY=never), rồi trim + cloud-init clean cho first boot thật.
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

# ── Docker Engine từ apt repo chính thức của Docker ───────────────────────────
apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y \
  docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker

# ── Dàn file vào /opt/supplycore (Packer file-provisioner đã stage vào /tmp) ──
mkdir -p /opt/supplycore /opt/supplycore/bin
cp /tmp/compose.yml          /opt/supplycore/compose.yml
cp /tmp/compose.override.yml /opt/supplycore/compose.override.yml
cp /tmp/ensure-data.sh       /opt/supplycore/ensure-data.sh
cp /tmp/first-boot.sh        /opt/supplycore/first-boot.sh
cp /tmp/backup.sh            /opt/supplycore/backup.sh
cp /tmp/bench                /opt/supplycore/bin/bench
chmod +x /opt/supplycore/ensure-data.sh /opt/supplycore/first-boot.sh /opt/supplycore/backup.sh /opt/supplycore/bin/bench

cp /tmp/ensure-data.service /etc/systemd/system/ensure-data.service
cp /tmp/first-boot.service  /etc/systemd/system/first-boot.service
cp /tmp/backup.service      /etc/systemd/system/backup.service
cp /tmp/backup.timer        /etc/systemd/system/backup.timer
systemctl daemon-reload
systemctl enable ensure-data.service first-boot.service backup.timer

# ── Load image SupplyCore + retag về ĐÚNG hợp đồng ───────────────────────────
# compose resolve `ghcr.io/mvl26/supplycore:latest`; runtime đặt PULL_POLICY=never
# nên tag PHẢI khớp, nếu không VM không tìm thấy image → không lên.
# Capture output TRƯỚC rồi mới parse (tránh SIGPIPE 141 dưới `set -o pipefail`
# nếu pipe vào `head`).
target="ghcr.io/mvl26/supplycore:latest"
load_out="$(docker load -i /tmp/supplycore-image.tar)"
echo "$load_out"
loaded="$(printf '%s\n' "$load_out" | sed -n 's/^Loaded image: //p' | head -1)"
if [ -z "$loaded" ]; then
  echo "ERROR: không phân giải được tag từ 'docker load'." >&2
  echo "       Task 12 PHẢI lưu tar có tag (vd 'docker save ${target}' — KHÔNG save theo digest)." >&2
  exit 1
fi
if [ "$loaded" != "$target" ]; then
  docker tag "$loaded" "$target"
fi
docker image inspect "$target" >/dev/null

# ── Pre-pull base images để boot OFFLINE (build có internet, runtime không) ──
# KHÔNG dùng `docker compose pull` vì image supplycore là load, không pull được.
docker pull mariadb:10.6
docker pull redis:6.2-alpine

# ── Cho phép disk0 re-provision ở first boot THẬT (seed production khác) ─────
# Xoá build state để first boot dùng seed cidata do make-data.ps1 (Task 11) sinh.
# LƯU Ý: cloud-init clean KHÔNG gỡ user/sudoers/sshd đã được áp dụng — phải gỡ tay
# (xem bước HARDEN ở cuối).
cloud-init clean --logs || true

# ── Gỡ user build (Packer SSH) + drop-in ─────────────────────────────────────
# KHÔNG gỡ ở đây: Packer chạy shutdown_command BẰNG user packer + sudo SAU khi
# install.sh xong; nếu xoá user/sudoers ngay thì `sudo shutdown` fail → build treo.
# Việc gỡ được thực hiện trong shutdown_command (xem supplycore.pkr.hcl): sudo
# elevate khi sudoers còn hiệu lực → root xoá user/drop-in → shutdown. User build
# KHÔNG lọt vào disk0 ship cho bệnh viện.

# ── Trim để disk0 nhỏ ────────────────────────────────────────────────────────
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/*
fstrim -av || true
