# SupplyCore — cài đặt bằng Docker

Chạy SupplyCore (Frappe v15) bằng một stack Docker duy nhất — cài được trên **Ubuntu cloud server** và **Windows (Docker Desktop)**. Image dựng sẵn được kéo từ **GitHub Container Registry** (`ghcr.io/mvl26/supplycore`).

> Image là **private** → cần một **GitHub Personal Access Token** có quyền `read:packages` để `docker pull`. Xem mục [Token](#token-ghcr).

---

## Yêu cầu

| Nền tảng | Cần có |
|---|---|
| Ubuntu (cloud/VM) | Có quyền sudo. Script tự cài Docker nếu thiếu. RAM ≥ 2 GB. |
| Windows 10/11 | [Docker Desktop](https://www.docker.com/products/docker-desktop) (bật WSL2) đang chạy. |

---

## Cài nhanh (1 lệnh / 1 click)

### Ubuntu / Linux
```bash
# Lấy thư mục deploy (clone repo hoặc copy riêng thư mục này)
cd deploy
chmod +x install.sh
./install.sh
```
Script sẽ: cài Docker nếu thiếu → tạo `.env` (sinh mật khẩu ngẫu nhiên) → đăng nhập GHCR → kéo image → `docker compose up -d` → chờ tạo site → in URL + mật khẩu Administrator.

### Windows (Docker Desktop)
1. Mở **Docker Desktop**, đợi đến khi nó "Running".
2. Vào thư mục `deploy`, **double-click `install.bat`** (hoặc chuột phải `install.ps1` → *Run with PowerShell*).
3. Nhập username GitHub + token khi được hỏi. Xong, mở `http://localhost:8080`.

---

## Cài thủ công (tùy chọn)

```bash
cd deploy
cp .env.example .env          # rồi sửa SITE_NAME / mật khẩu / HTTP_PORT
echo "<TOKEN>" | docker login ghcr.io -u <github-username> --password-stdin
docker compose up -d
docker compose logs -f create-site   # theo dõi quá trình tạo site lần đầu
```
Mở `http://<host>:8080`, đăng nhập **Administrator** với mật khẩu trong `.env`.

---

## Token GHCR

1. GitHub → *Settings* → *Developer settings* → **Personal access tokens**.
2. Tạo token có quyền **`read:packages`** (classic) — hoặc fine-grained cho phép đọc packages của `mvl26`.
3. Dùng token này khi script hỏi, hoặc đặt sẵn biến môi trường:
   ```bash
   export GHCR_USER=<github-username>
   export GHCR_TOKEN=<token>
   ./install.sh
   ```

---

## Cấu hình (`.env`)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `IMAGE` | `ghcr.io/mvl26/supplycore` | Tên image |
| `IMAGE_TAG` | `latest` | Phiên bản image |
| `PULL_POLICY` | `missing` | `always`/`missing`/`never` |
| `SITE_NAME` | `supplycore.localhost` | Tên site (cũng là Host nginx phục vụ) |
| `ADMIN_PASSWORD` | *(sinh ngẫu nhiên)* | Mật khẩu Administrator |
| `DB_PASSWORD` | *(sinh ngẫu nhiên)* | Mật khẩu root MariaDB |
| `HTTP_PORT` | `8080` | Cổng host → nginx |

---

## Vận hành

```bash
docker compose ps                 # trạng thái
docker compose logs -f backend    # log
docker compose down               # dừng (giữ dữ liệu)
docker compose down -v            # XÓA luôn dữ liệu (db + sites)
```

### Cập nhật phiên bản
```bash
# sửa IMAGE_TAG trong .env sang tag mới, rồi:
docker compose pull
docker compose up -d
docker compose exec backend bench --site <SITE_NAME> migrate
```

### Sao lưu / phục hồi
```bash
docker compose exec backend bench --site <SITE_NAME> backup --with-files
# file backup nằm trong volume 'sites' (sites/<SITE_NAME>/private/backups)
```

---

## HTTPS + tên miền (Ubuntu cloud)

Quickstart phục vụ HTTP cổng 8080. Để có domain + HTTPS, đặt một reverse proxy trước `frontend` (ví dụ Caddy — tự động Let's Encrypt):

```
# /etc/caddy/Caddyfile
supplycore.example.com {
    reverse_proxy 127.0.0.1:8080
}
```
Rồi đặt `SITE_NAME=supplycore.example.com` trong `.env` và tạo lại site (hoặc dùng `bench setup add-domain`).

---

## Sự cố thường gặp

| Triệu chứng | Nguyên nhân / cách xử lý |
|---|---|
| `denied` khi pull | Chưa `docker login ghcr.io` hoặc token thiếu `read:packages`. |
| Trang trắng, SPA không lên | Asset Vue chưa build trong image — kiểm tra CI smoke test (xem `.github/workflows/build-image.yml`). |
| `create-site` lỗi | `docker compose logs create-site`. Thường do mật khẩu DB sai hoặc DB chưa healthy. |
| Cổng 8080 bận | Đổi `HTTP_PORT` trong `.env`, rồi `docker compose up -d`. |
| Windows: "Docker not running" | Mở Docker Desktop, đợi "Running", chạy lại. |

---

## Build image (chỉ maintainer)

Image được dựng tự động bởi GitHub Actions khi push tag `v*` (xem `.github/workflows/build-image.yml`) — không cần Docker trên máy dev. Quy trình clone `frappe_docker` (ghim commit `1e3d40f`), chèn `docker/Containerfile`, build Frappe v15 + SupplyCore (kèm build Vue SPA), smoke-test, rồi push lên GHCR. Cần secret repo `APP_GH_TOKEN` (PAT chỉ-đọc repo).
