#!/usr/bin/env bash
# SupplyCore one-command installer for Ubuntu / Linux.
#   curl-less usage:  cd deploy && ./install.sh
#
# Optional environment variables (otherwise prompted / defaulted):
#   GHCR_USER, GHCR_TOKEN   GitHub username + PAT (read:packages) to pull the private image
#   SITE_NAME, ADMIN_PASSWORD, DB_PASSWORD, HTTP_PORT, IMAGE_TAG
set -euo pipefail

cd "$(dirname "$0")"

say()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!! \033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mxx \033[0m %s\n' "$*" >&2; exit 1; }

# --- 1. Docker -------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  say "Docker not found — installing via get.docker.com (needs sudo)…"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
  warn "Added $USER to the 'docker' group. If the next step fails on permissions, log out/in and re-run."
fi
if ! docker compose version >/dev/null 2>&1; then
  die "Docker Compose v2 plugin not found. Install Docker Engine >= 20.10 with the compose plugin."
fi
DOCKER="docker"; docker info >/dev/null 2>&1 || DOCKER="sudo docker"

# --- 2. .env ---------------------------------------------------------------
gen() { openssl rand -hex 16 2>/dev/null || head -c16 /dev/urandom | od -An -tx1 | tr -d ' \n'; }
if [ ! -f .env ]; then
  say "Creating .env…"
  cp .env.example .env
  sed -i "s|^SITE_NAME=.*|SITE_NAME=${SITE_NAME:-supplycore.localhost}|" .env
  sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${ADMIN_PASSWORD:-$(gen)}|" .env
  sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=${DB_PASSWORD:-$(gen)}|" .env
  sed -i "s|^HTTP_PORT=.*|HTTP_PORT=${HTTP_PORT:-8080}|" .env
  [ -n "${IMAGE_TAG:-}" ] && sed -i "s|^IMAGE_TAG=.*|IMAGE_TAG=${IMAGE_TAG}|" .env
else
  warn ".env already exists — reusing it."
fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

# --- 3. GHCR login (private image) ----------------------------------------
if [ "${PULL_POLICY:-always}" = "never" ]; then
  warn "PULL_POLICY=never — dùng image local ${IMAGE}:${IMAGE_TAG} (không pull GHCR)."
elif ! $DOCKER pull "${IMAGE}:${IMAGE_TAG}" >/dev/null 2>&1; then
  say "Logging in to GitHub Container Registry to pull the private image…"
  if [ -z "${GHCR_USER:-}" ]; then
    read -rp 'GitHub username: ' GHCR_USER
  fi
  if [ -z "${GHCR_TOKEN:-}" ]; then
    read -rsp 'GitHub PAT (read:packages): ' GHCR_TOKEN; echo
  fi
  echo "$GHCR_TOKEN" | $DOCKER login ghcr.io -u "$GHCR_USER" --password-stdin
  $DOCKER pull "${IMAGE}:${IMAGE_TAG}"
fi

# --- 4. Up -----------------------------------------------------------------
say "Starting the SupplyCore stack…"
$DOCKER compose up -d

say "Waiting for first-run site creation (installs SupplyCore)…"
for i in $(seq 1 90); do
  line=$($DOCKER compose ps -a --format '{{.Service}} {{.State}} {{.ExitCode}}' | awk '$1=="create-site"{print $2" "$3}')
  case "$line" in
    "exited 0") say "Site ready."; break ;;
    "exited "*) $DOCKER compose logs create-site; die "Site creation failed." ;;
    *) printf '\r    still working… (%s/90)   ' "$i"; sleep 10 ;;
  esac
done
echo

# --- 5. Done ---------------------------------------------------------------
IP=$(hostname -I 2>/dev/null | awk '{print $1}'); IP=${IP:-localhost}
printf '\n\033[1;32mSupplyCore is up.\033[0m\n'
cat <<EOF
  URL:       http://${IP}:${HTTP_PORT}      (or http://localhost:${HTTP_PORT})
  Login:     Administrator
  Password:  ${ADMIN_PASSWORD}

  Logs:      docker compose logs -f backend
  Stop:      docker compose down
  Update:    edit IMAGE_TAG in .env, then ./install.sh   (run 'bench migrate' after — see README)
EOF
