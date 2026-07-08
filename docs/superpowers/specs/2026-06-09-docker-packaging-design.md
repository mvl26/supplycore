# SupplyCore — Đóng gói Docker (Frappe Docker) — Design Spec

**Ngày:** 2026-06-09
**Mục tiêu:** Đóng gói SupplyCore thành Docker image chạy trên Frappe Docker, cài được trên **Ubuntu cloud server** và **Windows (Docker Desktop)** bằng 1 lệnh / 1 click.

---

## 1. Bối cảnh & ràng buộc (đã xác minh trong repo)

- SupplyCore là **Frappe-only app** (không cần ERPNext kể từ v0.2). `required_apps = ["frappe/frappe"]`.
- Frappe **version-15** (local `v15.107.2`). Toolchain local: Python 3.12, Node **18.20.8**, yarn **1.22 (classic)**.
- Frontend là **Vue 3 SPA** trong `frontend/` (Vite) build ra `supplycore/public/frontend/`.
  - **Quan trọng:** `supplycore/public/frontend/` **bị gitignore** và **không có root `package.json`** → `bench build` **không** tự build SPA. Image **bắt buộc** chạy `cd frontend && yarn build`.
  - `www/supplycore.html` nạp `/assets/supplycore/frontend/index.{css,js}` (output của Vite, phục vụ qua symlink `sites/assets/supplycore → apps/supplycore/supplycore/public`).
- Repo private: `github.com/mvl26/supplycore`, nhánh build = `main`.
- Máy dev **chưa cài Docker** → image build & test trên **GitHub Actions**, không build cục bộ.

## 2. Quyết định kiến trúc (đã chốt với người dùng)

| Hạng mục | Lựa chọn |
|---|---|
| Phân phối | Image dựng sẵn → registry, máy đích `docker pull` |
| Registry / Build | **GitHub Actions → GHCR** (`ghcr.io/mvl26/supplycore`) |
| Stack | **Single-stack quickstart** (1 file compose) |
| Cách cài | **Script 1-lệnh / 1-click** (Ubuntu `install.sh` + Windows `install.ps1`) |
| Dữ liệu ban đầu | **Site trống + app** (Administrator), không seed |

## 3. Chiến lược build image

**Cách tiếp cận:** vendor một `docker/Containerfile` (dựa trên frappe_docker, MIT) và build **trong build-context của frappe_docker** (clone pinned), chèn bước build Vue vào **builder stage** — trước khi stage backend "finalize" assets. Đây là cách **rủi ro thấp nhất**: tái dùng toàn bộ entrypoint/nginx/asset-handling chuẩn của frappe_docker, chỉ thêm 1 bước build SPA.

- **Pin frappe_docker:** commit `1e3d40fa65347209418e70a451d5b266e1a75b92` (main, 2026-06-08).
- **Override build-args về v15** (file gốc default v16/Python 3.14/Node 24):
  - `FRAPPE_BRANCH=version-15`
  - `PYTHON_VERSION=3.11.9`
  - `NODE_VERSION=18.20.4`
- **Token repo:** truyền apps.json qua **buildx secret mount** (`--mount=type=secret,id=apps_json`) → token **không** lưu vào layer. `.git` của app bị xóa trong build (đã có sẵn `find apps -path "*/.git" | xargs rm -fr`).
- **Chèn build Vue** vào builder stage, sau `bench init`:
  ```
  cd apps/supplycore/frontend && yarn install --frozen-lockfile && yarn build
  cd /home/frappe/frappe-bench && bench build --app supplycore
  ```
  Giữ Node 18 + script `NODE_OPTIONS=--experimental-global-webcrypto` (Node 18 cần flag này cho `globalThis.crypto`). Dùng `yarn.lock` (classic), **không** dùng `package-lock.json`.

**Lockfile:** chuẩn hóa về **yarn**. Khuyến nghị xóa `frontend/package-lock.json` (lệch ngày, gây mơ hồ) — không bắt buộc cho build.

## 4. Build & phân phối (CI)

`.github/workflows/build-image.yml` — trigger: push tag `v*` + `workflow_dispatch`.

1. Checkout supplycore + checkout frappe_docker @ pinned SHA.
2. Ghi `docker/Containerfile` đè `frappe_docker/images/custom/Containerfile`.
3. Render `apps.json` từ secret `APP_GH_TOKEN` (PAT chỉ-đọc repo) → file tạm (không commit).
4. `docker buildx build --load` (linux/amd64) với secret `apps_json`, build-args v15, tag `:<git-tag>` + `:latest`.
5. **Smoke test (bắt buộc):** `docker compose -f deploy/compose.yml up -d` → chờ healthy → `curl -f` site root + route `/supplycore` (HTTP 200) → assert `supplycore` trong `apps.txt`.
6. Nếu smoke test pass → `docker login ghcr.io` (GITHUB_TOKEN) → `docker push`.

**Secrets cần tạo:** `APP_GH_TOKEN` (fine-grained PAT, chỉ-đọc repo `mvl26/supplycore` — **mint mới**, không dùng lại token đang lộ trong git remote).

## 5. Deploy stack (single-stack quickstart)

`deploy/compose.yml` — mô phỏng `pwd.yml` nhưng image = GHCR, app = supplycore, MariaDB 10.6, Redis 6.2:

- `db` (mariadb:10.6, utf8mb4, healthcheck) · `redis-cache` · `redis-queue` (redis:6.2-alpine)
- `configurator` (1-shot): set `common_site_config.json` (db_host, redis cache/queue, socketio_port)
- `create-site` (1-shot, **idempotent**): `bench new-site --install-app supplycore --set-default`
- `backend` (gunicorn, CMD mặc định) · `websocket` (socketio.js) · `queue-short` · `queue-long` · `scheduler`
- `frontend` (nginx-entrypoint.sh) → cổng `${HTTP_PORT:-8080}`

Volumes: `sites`, `db-data`, `redis-cache-data`, `redis-queue-data`, `logs`.

`deploy/.env.example`: `SITE_NAME`, `ADMIN_PASSWORD`, `DB_PASSWORD`, `HTTP_PORT=8080`, `IMAGE=ghcr.io/mvl26/supplycore`, `IMAGE_TAG=latest`.

## 6. Cách cài (1-lệnh / 1-click)

- `deploy/install.sh` (Ubuntu): cài Docker nếu thiếu → `docker login ghcr.io` → tạo `.env` (sinh mật khẩu ngẫu nhiên nếu trống) → `docker compose up -d` → chờ `create-site` xong → in URL + tài khoản.
- `deploy/install.ps1` (+ `install.bat` bọc ngoài, Windows): kiểm tra Docker Desktop/WSL2 → các bước tương tự bằng PowerShell.
- `deploy/README.md`: hướng dẫn cả 2 nền tảng + lấy GHCR token + cập nhật phiên bản (`pull` tag mới → `up -d` → `bench migrate`).

## 7. Vận hành

- **Cập nhật:** sửa `IMAGE_TAG` → `docker compose pull && docker compose up -d` → `docker compose exec backend bench --site <site> migrate`.
- **HTTPS/domain:** ngoài phạm vi quickstart. README ghi cách bọc Caddy/nginx reverse-proxy + Let's Encrypt cho Ubuntu cloud.

## 8. Ngoài phạm vi (YAGNI)

Cụm đa-node / Traefik tự động, HTTPS tự động, seed master data, ERPNext, multi-arch (arm64 — ghi chú cho tương lai).

## 9. Kiểm thử & rủi ro

- **Verification duy nhất trước khi user deploy = smoke test trong CI** (build-only là chưa đủ). Nếu `bench build --app supplycore` hoặc curl route lỗi → CI đỏ, sửa trước khi phát hành.
- Máy dev này không chạy Docker được → không test trực tiếp tại đây; README kèm bước test trên máy thật.
- **Rủi ro token:** PAT đang lộ trong `git remote` của repo → **khuyến nghị rotate**. Không commit/bake token ở bất kỳ đâu.
