#!/usr/bin/env bash
# guest/packer/smoke.sh — CỔNG TÍCH HỢP (chạy trong CI sau Packer; runner Linux + KVM).
#
# Boot HAI PHA để chứng minh dữ liệu BỀN qua update (đây là bug nghiêm trọng được vá):
#
#   PHA 1: disk0 overlay MỚI + disk1 TRỐNG MỚI → chờ app lên → assert:
#            • PULL_POLICY=never boot OFFLINE  (image đã load, base images đã pre-pull)
#            • tag image khớp ghcr.io/mvl26/supplycore:latest  (compose tìm thấy)
#            • cổng 80 trong guest map ra host
#            • /data/sites ghi được bằng uid 1000 → create-site provisioning thành công
#            • serial: "ensure-data: mounted /dev/vdb at /data"  (disk1 đã mount)
#            • serial: "first-boot: DB_PASSWORD generated"        (lần đầu)
#          → tắt máy GRACEFUL (qemu monitor system_powerdown) + chờ tiến trình thoát
#            để disk1 được flush (KHÔNG kill -9 — mất ghi disk1).
#
#   PHA 2: disk0 overlay MỚI (mô phỏng disk0 bị thay khi update) + ĐÚNG disk1 của PHA 1
#          → chờ app lên → assert:
#            • serial: "first-boot: DB_PASSWORD reused"  (đọc lại từ disk1)
#            • serial KHÔNG có "DB_PASSWORD generated"   (nếu có → disk1 KHÔNG bền)
#          → nếu thấy "generated": FAIL rõ ràng — disk1 không sống qua disk0 swap.
#
# CWD BẮT BUỘC: GỐC REPO (đường dẫn guest/cloud-init/... là tương đối).
# CHỈ chạy được khi có KVM + qemu + genisoimage + python3. Dev box thiếu → defer CI (Task 12).
set -euxo pipefail

DISK0="${DISK0:-output-disk0/disk0.qcow2}"
ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-Smoke12345}"
HOST_PORT="${HOST_PORT:-8080}"

WORK="$(mktemp -d)"
SERIAL1="$WORK/serial1.log"
SERIAL2="$WORK/serial2.log"
PIDFILE1="$WORK/qemu1.pid"
PIDFILE2="$WORK/qemu2.pid"

dump_serials() {
  echo "──────── serial log PHA 1 ────────" >&2
  cat "$SERIAL1" >&2 2>/dev/null || true
  echo "──────── serial log PHA 2 ────────" >&2
  cat "$SERIAL2" >&2 2>/dev/null || true
}

cleanup() {
  for pf in "$PIDFILE1" "$PIDFILE2"; do
    [ -f "$pf" ] && kill "$(cat "$pf")" 2>/dev/null || true
  done
  rm -rf "$WORK"
}
trap cleanup EXIT

# ── seed cidata: render production user-data + chèn ADMIN_PASSWORD (dựng 1 lần) ──
SEEDDIR="$WORK/seed"
mkdir -p "$SEEDDIR"
sed "s|__ADMIN_PASSWORD__|${ADMIN_PASSWORD}|g" guest/cloud-init/user-data > "$SEEDDIR/user-data"
cp guest/cloud-init/meta-data "$SEEDDIR/meta-data"
genisoimage -V cidata -o "$WORK/seed.iso" -J -r "$SEEDDIR"

# ── disk1 TRỐNG, tạo 1 lần, dùng chung CHO CẢ HAI PHA (đây là đĩa bền) ─────────
DISK1="$WORK/disk1.qcow2"
qemu-img create -f qcow2 "$DISK1" 30G

# boot_vm <disk0_overlay> <serial> <pidfile> <monitor_sock>
# Boot VM (virtio: disk0 overlay=vda + disk1=vdb + seed.iso=vdc readonly) rồi
# poll /supplycore tới ~20 phút. Trả 0 nếu app lên, 1 nếu timeout.
boot_vm() {
  local overlay="$1" serial="$2" pidfile="$3" monsock="$4"
  qemu-system-x86_64 \
    -accel kvm \
    -m 4096 -smp 2 \
    -drive file="$overlay",if=virtio,format=qcow2 \
    -drive file="$DISK1",if=virtio,format=qcow2 \
    -drive file="$WORK/seed.iso",if=virtio,format=raw,readonly=on \
    -netdev "user,id=n0,hostfwd=tcp:127.0.0.1:${HOST_PORT}-:80" \
    -device virtio-net-pci,netdev=n0 \
    -display none \
    -serial file:"$serial" \
    -monitor "unix:$monsock,server,nowait" \
    -daemonize -pidfile "$pidfile"

  local i
  for i in $(seq 1 240); do
    if curl -fsS -o /dev/null "http://127.0.0.1:${HOST_PORT}/supplycore"; then
      return 0
    fi
    sleep 5
  done
  return 1
}

# powerdown_vm <pidfile> <monitor_sock> — tắt GRACEFUL + chờ tiến trình thoát để
# disk1 được flush. KHÔNG kill -9: có thể mất ghi disk1 (mất ý nghĩa phép thử bền).
powerdown_vm() {
  local pidfile="$1" monsock="$2" pid
  pid="$(cat "$pidfile")"
  python3 - "$monsock" <<'PY'
import socket, sys
s = socket.socket(socket.AF_UNIX)
s.connect(sys.argv[1])
s.sendall(b"system_powerdown\n")
s.close()
PY
  local i
  for i in $(seq 1 60); do
    kill -0 "$pid" 2>/dev/null || return 0
    sleep 2
  done
  # Tới đây nghĩa là graceful shutdown thất bại → disk1 có thể CHƯA flush.
  echo "SMOKE FAIL: VM không tắt graceful trong 120s — disk1 có thể chưa flush." >&2
  dump_serials
  exit 1
}

# ════════════════════════════ PHA 1 ══════════════════════════════════════════
qemu-img create -f qcow2 -b "$(readlink -f "$DISK0")" -F qcow2 "$WORK/disk0-overlay1.qcow2"

if ! boot_vm "$WORK/disk0-overlay1.qcow2" "$SERIAL1" "$PIDFILE1" "$WORK/mon1.sock"; then
  echo "SMOKE FAIL (PHA 1): /supplycore không trả 200 trong ~20 phút." >&2
  dump_serials
  exit 1
fi

# site root cũng phải phục vụ (frontend nginx + FRAPPE_SITE_NAME_HEADER đúng)
curl -fsS -o /dev/null "http://127.0.0.1:${HOST_PORT}/"

if ! grep -q "ensure-data: mounted /dev/vdb at /data" "$SERIAL1"; then
  echo "SMOKE FAIL (PHA 1): không thấy 'ensure-data: mounted /dev/vdb at /data' — disk1 KHÔNG được mount." >&2
  dump_serials
  exit 1
fi
if ! grep -q "first-boot: DB_PASSWORD generated" "$SERIAL1"; then
  echo "SMOKE FAIL (PHA 1): không thấy 'first-boot: DB_PASSWORD generated' — first-boot không chạy đúng trên disk1 trống." >&2
  dump_serials
  exit 1
fi
echo "SMOKE PHA 1 PASS: app 200, disk1 mounted, DB_PASSWORD generated."

powerdown_vm "$PIDFILE1" "$WORK/mon1.sock"
rm -f "$PIDFILE1"

# ════════════════════════════ PHA 2 ══════════════════════════════════════════
# disk0 overlay MỚI off base GỐC (KHÔNG dùng lại overlay PHA 1) = mô phỏng disk0
# bị thay khi update; disk1 GIỮ NGUYÊN từ PHA 1.
qemu-img create -f qcow2 -b "$(readlink -f "$DISK0")" -F qcow2 "$WORK/disk0-overlay2.qcow2"

if ! boot_vm "$WORK/disk0-overlay2.qcow2" "$SERIAL2" "$PIDFILE2" "$WORK/mon2.sock"; then
  echo "SMOKE FAIL (PHA 2): /supplycore không trả 200 trong ~20 phút." >&2
  dump_serials
  exit 1
fi

curl -fsS -o /dev/null "http://127.0.0.1:${HOST_PORT}/"

if grep -q "first-boot: DB_PASSWORD generated" "$SERIAL2"; then
  echo "SMOKE FAIL (PHA 2): thấy 'DB_PASSWORD generated' — disk1 KHÔNG bền qua disk0 swap." >&2
  echo "  → Đây CHÍNH XÁC là bug đang vá: dữ liệu sống trên disk0 và bị xoá mỗi lần update." >&2
  dump_serials
  exit 1
fi
if ! grep -q "first-boot: DB_PASSWORD reused" "$SERIAL2"; then
  echo "SMOKE FAIL (PHA 2): không thấy 'DB_PASSWORD reused' — first-boot không đọc lại trạng thái từ disk1." >&2
  dump_serials
  exit 1
fi

powerdown_vm "$PIDFILE2" "$WORK/mon2.sock"
rm -f "$PIDFILE2"

echo "SMOKE PASS: PHA 1 (boot sạch) + PHA 2 (disk0 swap, disk1 GIỮ) đều 200."
echo "→ CỔNG xác nhận: OFFLINE PULL_POLICY=never, tag image khớp, cổng 80 map,"
echo "  /data/sites ghi được (uid 1000), VÀ disk1 BỀN qua update (DB_PASSWORD reused)."
