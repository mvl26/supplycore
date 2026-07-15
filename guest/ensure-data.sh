#!/usr/bin/env bash
# guest/ensure-data.sh — format (chỉ lần đầu) + mount disk1 (/dev/vdb) vào /data.
# Chạy bởi ensure-data.service TRƯỚC first-boot.service. KHÔNG format lại nếu đã có fs
# (→ dữ liệu sống qua update khi disk0 bị thay).
set -euo pipefail
DEV="${DATA_DEV:-/dev/vdb}"
MNT="${DATA_MNT:-/data}"
LABEL=supplycore-data

if [ ! -b "$DEV" ]; then
  echo "ensure-data: ERROR thiết bị $DEV không tồn tại" >&2
  exit 1
fi
if ! blkid "$DEV" >/dev/null 2>&1; then
  echo "ensure-data: $DEV trống — tạo ext4 ($LABEL)"
  mkfs.ext4 -F -L "$LABEL" "$DEV"
fi
mkdir -p "$MNT"
if ! mountpoint -q "$MNT"; then
  mount "$DEV" "$MNT"
fi
grep -q "$LABEL" /etc/fstab || echo "LABEL=$LABEL $MNT ext4 defaults 0 2" >> /etc/fstab
echo "ensure-data: mounted $DEV at $MNT"
