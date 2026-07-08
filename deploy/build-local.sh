#!/usr/bin/env bash
# Build the SupplyCore image LOCALLY (no GHCR/CI needed), then bring up the stack.
# Run inside WSL2 / Linux / macOS where `docker` (Docker Desktop) is available.
#
#   cd deploy && ./build-local.sh
#
# Optional env vars:
#   GH_TOKEN     GitHub PAT with read access to the private app repo (else prompted)
#   APP_BRANCH   branch of mvl26/supplycore to package   (default: feat/docker-packaging)
#   IMAGE_TAG    local tag                                (default: local)
set -euo pipefail
cd "$(dirname "$0")"

say()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mxx \033[0m %s\n' "$*" >&2; exit 1; }

APP_REPO="${APP_REPO:-github.com/mvl26/supplycore}"
APP_BRANCH="${APP_BRANCH:-feat/docker-packaging}"
FD_REF="1e3d40fa65347209418e70a451d5b266e1a75b92"   # pinned frappe_docker
IMAGE_LOCAL="${IMAGE_LOCAL:-supplycore}"
IMAGE_TAG="${IMAGE_TAG:-local}"
WORK="${WORK:-${TMPDIR:-/tmp}/supplycore-build}"

command -v docker >/dev/null 2>&1 || die "docker not found. Bật Docker Desktop + WSL integration."
docker buildx version >/dev/null 2>&1 || die "docker buildx không khả dụng (cần BuildKit / Docker Desktop)."

if [ -z "${GH_TOKEN:-}" ]; then read -rsp "GitHub PAT (read repo): " GH_TOKEN; echo; fi

say "Chuẩn bị build context (frappe_docker @ ${FD_REF:0:7})…"
rm -rf "$WORK"; mkdir -p "$WORK"
git clone -q https://github.com/frappe/frappe_docker "$WORK/frappe_docker"
git -C "$WORK/frappe_docker" checkout -q "$FD_REF"
cp ../docker/Containerfile "$WORK/frappe_docker/images/custom/Containerfile"

# apps.json with token — written to a temp file, used only as a buildx secret.
printf '[{"url":"https://%s@%s","branch":"%s"}]\n' "$GH_TOKEN" "$APP_REPO" "$APP_BRANCH" > "$WORK/apps.json"
trap 'rm -f "$WORK/apps.json"' EXIT

say "Building ${IMAGE_LOCAL}:${IMAGE_TAG} (15–20 phút, vài GB)…"
docker buildx build \
  --file "$WORK/frappe_docker/images/custom/Containerfile" \
  --secret id=apps_json,src="$WORK/apps.json" \
  --build-arg FRAPPE_BRANCH=version-15 \
  --build-arg PYTHON_VERSION=3.11.9 \
  --build-arg NODE_VERSION=18.20.4 \
  --build-arg INSTALL_CHROMIUM=false \
  --tag "${IMAGE_LOCAL}:${IMAGE_TAG}" \
  --load \
  "$WORK/frappe_docker"
rm -f "$WORK/apps.json"; trap - EXIT

# --- .env for the local image ---------------------------------------------
gen() { openssl rand -hex 16 2>/dev/null || head -c16 /dev/urandom | od -An -tx1 | tr -d ' \n'; }
if [ ! -f .env ]; then
  cp .env.example .env
  sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=$(gen)|" .env
  sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=$(gen)|" .env
fi
sed -i "s|^IMAGE=.*|IMAGE=${IMAGE_LOCAL}|"       .env
sed -i "s|^IMAGE_TAG=.*|IMAGE_TAG=${IMAGE_TAG}|" .env
sed -i "s|^PULL_POLICY=.*|PULL_POLICY=never|"    .env

say "Image xong. Khởi động stack…"
exec ./install.sh
