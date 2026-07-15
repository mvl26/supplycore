__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung ứng Vật tư Y tế Bệnh viện

__ENVIRONMENT SETUP GUIDE__

Hướng dẫn này giúp developer thiết lập môi trường phát triển SupplyCore trên máy local hoặc server staging\. Toàn bộ lệnh được viết cho Ubuntu 22\.04 LTS – khuyến nghị dùng WSL2 trên Windows\.

# __1\. Yêu cầu Hệ thống__

__Môi trường__

__CPU__

__RAM__

__Disk__

Developer Local

4 cores \(8 khuyến nghị\)

8 GB \(16 GB tốt nhất\)

50 GB SSD trống

Staging Server

4 vCPU

16 GB

100 GB SSD

Production Server

8\+ vCPU

32 GB\+

500 GB SSD \+ Backup

## __1\.1 Phần mềm yêu cầu__

__Phần mềm__

__Phiên bản tối thiểu__

__Khuyến nghị__

__Ghi chú__

Ubuntu / WSL2

20\.04 LTS

22\.04 LTS

OS chính thức hỗ trợ

Python

3\.10

3\.11

Frappe v15 yêu cầu

Node\.js

18\.x LTS

20\.x LTS

Frontend build

MariaDB

10\.6

10\.11

Database chính

Redis

6\.x

7\.x

Cache và queue

Git

2\.30

Latest

Version control

Docker \+ Docker Compose

24\.x

Latest stable

Container \(tùy chọn\)

VS Code \(IDE\)

1\.85\+

Latest

Khuyến nghị IDE chính

# __2\. Cài đặt Môi trường \(Manual\)__

__Bước 1:  Chuẩn bị hệ thống Ubuntu__

sudo apt\-get update && sudo apt\-get upgrade \-y

sudo apt\-get install \-y git python3\-dev python3\-pip redis\-server \\

  wkhtmltopdf libssl\-dev libffi\-dev build\-essential \\

  libmysqlclient\-dev python3\-setuptools

__Bước 2:  Cài đặt Node\.js 20 LTS__

curl \-fsSL https://deb\.nodesource\.com/setup\_20\.x | sudo \-E bash \-

sudo apt\-get install \-y nodejs

node \-\-version   \# Kiểm tra: v20\.x\.x

npm \-\-version    \# Kiểm tra: 10\.x\.x

__Bước 3:  Cài đặt MariaDB 10\.11__

curl \-LsS https://r\.mariadb\.com/downloads/mariadb\_repo\_setup | sudo bash

sudo apt\-get install \-y mariadb\-server mariadb\-client

sudo mysql\_secure\_installation

\# Khi hỏi: root password \-> đặt password mạnh

\# Remove anonymous users: Y | Disallow root login remotely: Y

sudo mysql \-u root \-p

CREATE USER 'frappe'@'localhost' IDENTIFIED BY 'StrongPassword123\!';

GRANT ALL PRIVILEGES ON \*\.\* TO 'frappe'@'localhost' WITH GRANT OPTION;

FLUSH PRIVILEGES; EXIT;

__Bước 4:  Cài đặt Frappe Bench__

sudo pip3 install frappe\-bench \-\-break\-system\-packages

\# Hoặc dùng pipx \(khuyến nghị\):

sudo apt install pipx && pipx install frappe\-bench

bench \-\-version   \# Kiểm tra cài đặt thành công

__Bước 5:  Khởi tạo Bench & cài ERPNext__

cd ~

bench init \-\-frappe\-branch version\-15 supplycore\-bench

cd supplycore\-bench

bench get\-app \-\-branch version\-15 erpnext

\# Clone SupplyCore custom app từ GitHub

bench get\-app supplycore https://github\.com/medcons/supplycore\.git

__Bước 6:  Tạo Site và cài đặt Apps__

bench new\-site supplycore\.local \\

  \-\-mariadb\-root\-password <root\_password> \\

  \-\-admin\-password Admin@123

bench \-\-site supplycore\.local install\-app erpnext

bench \-\-site supplycore\.local install\-app supplycore

bench \-\-site supplycore\.local migrate

__Bước 7:  Khởi động Development Server__

bench start

\# Truy cập: http://localhost:8000

\# Login: Administrator / Admin@123

# __3\. Cài đặt bằng Docker \(Khuyến nghị cho Staging\)__

Docker setup đảm bảo môi trường nhất quán giữa các developer và staging server\.

__Bước 1:  Cài đặt Docker__

curl \-fsSL https://get\.docker\.com \-o get\-docker\.sh && sh get\-docker\.sh

sudo usermod \-aG docker $USER && newgrp docker

docker \-\-version && docker compose version

__Bước 2:  Clone Docker Config SupplyCore__

git clone https://github\.com/medcons/supplycore\-docker\.git

cd supplycore\-docker

cp \.env\.example \.env

\# Chỉnh sửa \.env: DB\_PASSWORD, ADMIN\_PASSWORD, SITES

__Bước 3:  Khởi động Container__

docker compose \-f compose\.yaml \\

  \-f overrides/compose\.mariadb\.yaml \\

  \-f overrides/compose\.redis\.yaml up \-d

docker compose exec backend bench new\-site supplycore\.local \\

  \-\-mariadb\-root\-password changeit \-\-admin\-password Admin@123

docker compose exec backend bench \-\-site supplycore\.local \\

  install\-app erpnext supplycore

# __4\. Cấu hình VS Code \(IDE\)__

## __4\.1 Extensions bắt buộc__

__Extension__

__ID__

__Mục đích__

Python

ms\-python\.python

Python language support

Pylance

ms\-python\.vscode\-pylance

Python IntelliSense

Black Formatter

ms\-python\.black\-formatter

Auto code formatting

ESLint

dbaeumer\.vscode\-eslint

JavaScript linting

GitLens

eamodio\.gitlens

Git blame, history

Docker

ms\-azuretools\.vscode\-docker

Docker management

REST Client

humao\.rest\-client

Test API endpoints

## __4\.2 Workspace Settings \(\.vscode/settings\.json\)__

\{

  "python\.defaultInterpreterPath": "~/supplycore\-bench/env/bin/python",

  "editor\.formatOnSave": true,

  "\[python\]": \{ "editor\.defaultFormatter": "ms\-python\.black\-formatter" \},

  "black\-formatter\.args": \["\-\-line\-length", "100"\],

  "editor\.rulers": \[100\],

  "files\.exclude": \{ "\*\*/\_\_pycache\_\_": true, "\*\*/\*\.pyc": true \}

\}

# __5\. Biến môi trường & Config__

## __5\.1 site\_config\.json \(quan trọng\)__

\{

  "db\_host": "localhost",

  "db\_port": 3306,

  "developer\_mode": 1,

  "maintenance\_mode": 0,

  "socketio\_port": 9000,

  "supplycore\_smtp\_host": "smtp\.hospital\.vn",

  "supplycore\_alert\_email": "alert@hospital\.vn"

\}

## __5\.2 Environment Variables \(\.env\)__

__Variable__

__Ví dụ giá trị__

__Mô tả__

FRAPPE\_SITE\_NAME

supplycore\.local

Tên site Frappe

DB\_ROOT\_PASSWORD

\[bắt buộc thay đổi\]

Mật khẩu root MariaDB

ADMIN\_PASSWORD

\[bắt buộc thay đổi\]

Mật khẩu tài khoản Administrator

REDIS\_CACHE\_HOST

redis\-cache:6379

Redis cache endpoint

REDIS\_QUEUE\_HOST

redis\-queue:6379

Redis queue endpoint

SUPPLYCORE\_ENV

development | staging | production

Môi trường triển khai

# __6\. Xác minh Cài đặt__

Sau khi cài đặt xong, chạy lệnh sau để kiểm tra:

bench \-\-site supplycore\.local doctor

\# Kết quả mong đợi: All checks passed

bench run\-tests \-\-app supplycore

\# Kết quả mong đợi: All tests passed

curl http://localhost:8000/api/method/frappe\.ping

\# Kết quả mong đợi: \{"message": "pong"\}

# __7\. Troubleshooting thường gặp__

__Lỗi__

__Nguyên nhân__

__Cách xử lý__

bench start: Port 8000 in use

Port đang được chiếm bởi process khác

kill $\(lsof \-t \-i:8000\) rồi bench start lại

MariaDB connection refused

MariaDB chưa start hoặc sai password

sudo systemctl start mariadb; kiểm tra credentials

Redis connection error

Redis service chưa chạy

sudo systemctl start redis\-server

ModuleNotFoundError frappe

Virtual env chưa activate

source ~/supplycore\-bench/env/bin/activate

bench migrate fails

Migration conflict hoặc syntax error

Xem log tại logs/migrate\.log; chạy bench \-\-site x clear\-cache

wkhtmltopdf not found

Thiếu dependency cho PDF generation

sudo apt install wkhtmltopdf hoặc cài từ GitHub release

