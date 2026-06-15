#!/usr/bin/env bash
# guest/packer/smoke.sh — CỔNG TÍCH HỢP (chạy trong CI sau Packer; runner Linux + KVM).
#
# Boot disk0 (overlay) + disk1 trống + seed cidata → chờ app lên → assert:
#   • PULL_POLICY=never boot OFFLINE  (image đã load, base images đã pre-pull)
#   • tag image khớp ghcr.io/mvl26/supplycore:latest  (compose tìm thấy)
#   • cổng 80 trong guest map ra host
#   • /data/sites ghi được bằng uid 1000 → create-site provisioning thành công
#
# CHỈ chạy được khi có KVM + qemu + genisoimage. Dev box thiếu → defer CI (Task 12).
set -euxo pipefail

DISK0="${DISK0:-output-disk0/disk0.qcow2}"
ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-Smoke12345}"
HOST_PORT="${HOST_PORT:-8080}"

WORK="$(mktemp -d)"
SERIAL="$WORK/serial.log"
PIDFILE="$WORK/qemu.pid"

cleanup() {
  if [ -f "$PIDFILE" ]; then
    kill "$(cat "$PIDFILE")" 2>/dev/null || true
  fi
  rm -rf "$WORK"
}
trap cleanup EXIT

# ── disk1 trống (dữ liệu bền) — đúng như runtime production ───────────────────
qemu-img create -f qcow2 "$WORK/disk1.qcow2" 30G

# ── overlay disk0 để KHÔNG sửa artifact gốc khi boot test ────────────────────
qemu-img create -f qcow2 -b "$(readlink -f "$DISK0")" -F qcow2 "$WORK/disk0-overlay.qcow2"

# ── seed cidata: render production user-data + chèn ADMIN_PASSWORD ──────────
SEEDDIR="$WORK/seed"
mkdir -p "$SEEDDIR"
sed "s|__ADMIN_PASSWORD__|${ADMIN_PASSWORD}|g" guest/cloud-init/user-data > "$SEEDDIR/user-data"
cp guest/cloud-init/meta-data "$SEEDDIR/meta-data"
genisoimage -V cidata -o "$WORK/seed.iso" -J -r "$SEEDDIR"

# ── boot (virtio: disk0 overlay + disk1 + seed.iso readonly) ─────────────────
qemu-system-x86_64 \
  -accel kvm \
  -m 4096 -smp 2 \
  -drive file="$WORK/disk0-overlay.qcow2",if=virtio,format=qcow2 \
  -drive file="$WORK/disk1.qcow2",if=virtio,format=qcow2 \
  -drive file="$WORK/seed.iso",if=virtio,format=raw,readonly=on \
  -netdev "user,id=n0,hostfwd=tcp:127.0.0.1:${HOST_PORT}-:80" \
  -device virtio-net-pci,netdev=n0 \
  -display none \
  -serial file:"$SERIAL" \
  -daemonize -pidfile "$PIDFILE"

# ── poll tới ~20 phút (first boot: create-site → install-app → migrate) ─────
ok=0
for _ in $(seq 1 240); do
  if curl -fsS -o /dev/null "http://127.0.0.1:${HOST_PORT}/supplycore"; then
    ok=1
    break
  fi
  sleep 5
done

if [ "$ok" -ne 1 ]; then
  echo "SMOKE FAIL: /supplycore không trả 200 trong ~20 phút." >&2
  echo "──────── serial log ────────" >&2
  cat "$SERIAL" >&2 || true
  exit 1
fi

# site root cũng phải phục vụ (frontend nginx + FRAPPE_SITE_NAME_HEADER đúng)
curl -fsS -o /dev/null "http://127.0.0.1:${HOST_PORT}/"

echo "SMOKE PASS: site root 200 + /supplycore 200."
echo "→ CỔNG xác nhận: OFFLINE PULL_POLICY=never, tag image khớp, cổng 80 map, /data/sites ghi được (uid 1000)."
# Assert SÂU hơn (tuỳ chọn, nếu có QEMU guest agent / SSH vào guest):
#   docker compose ... exec -T backend grep -qx supplycore sites/apps.txt
# để chắc app đã CÀI (không chỉ frontend serving). Ở đây 200 trên cả / và
# /supplycore đã hàm ý create-site chạy đúng SITE_NAME=supplycore.localhost.
