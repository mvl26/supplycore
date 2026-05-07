__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung ứng Vật tư Y tế Bệnh viện

__BUILD & DEPLOYMENT GUIDE__

Tài liệu này mô tả quy trình build, kiểm thử tự động và triển khai hệ thống SupplyCore qua CI/CD pipeline sử dụng GitHub Actions, cho cả môi trường Staging và Production\.

# __1\. Tổng quan CI/CD Pipeline__

__Stage__

__Trigger__

__Actions__

__Target__

CI – Lint & Test

Push to any branch

ESLint, Black, pytest, migration check

Developer feedback \(< 5 min\)

CI – Build

PR to develop

Build assets, Docker image

Xác nhận build ok

CD – Staging

Merge to develop

Deploy to staging server, smoke test

staging\.supplycore\.local

CD – Production

Merge to main \(tag release\)

Deploy prod, backup first, healthcheck

supplycore\.hospital\.vn

## __1\.1 Luồng Pipeline tổng thể__

Developer push code \-> GitHub Actions trigger CI \-> Lint & Test pass \-> PR review \-> Merge to develop \-> Auto\-deploy Staging \-> QA verify \-> Release PR to main \-> Auto\-deploy Production

# __2\. GitHub Actions Workflow__

## __2\.1 CI Workflow \(\.github/workflows/ci\.yml\)__

name: SupplyCore CI

on:

  push:

    branches: \['\*\*'\]

  pull\_request:

    branches: \[develop, main\]

jobs:

  lint:

    runs\-on: ubuntu\-22\.04

    steps:

      \- uses: actions/checkout@v4

      \- uses: actions/setup\-python@v5

        with: \{ python\-version: '3\.11' \}

      \- run: pip install black flake8 \-\-break\-system\-packages

      \- run: black \-\-check \-\-line\-length 100 apps/supplycore

      \- run: flake8 apps/supplycore \-\-max\-line\-length 100

  test:

    runs\-on: ubuntu\-22\.04

    services:

      mariadb:

        image: mariadb:10\.11

        env: \{ MARIADB\_ROOT\_PASSWORD: test123 \}

      redis:

        image: redis:7

    steps:

      \- uses: actions/checkout@v4

      \- name: Setup Frappe Bench

        run: |

          pip install frappe\-bench

          bench init \-\-frappe\-branch version\-15 test\-bench

          cd test\-bench && bench get\-app supplycore $GITHUB\_WORKSPACE

          bench new\-site test\.local \-\-mariadb\-root\-password test123

          bench \-\-site test\.local install\-app supplycore

      \- name: Run Tests

        run: bench run\-tests \-\-app supplycore \-\-coverage

      \- name: Upload Coverage

        uses: codecov/codecov\-action@v4

## __2\.2 CD Staging Workflow \(\.github/workflows/deploy\-staging\.yml\)__

name: Deploy to Staging

on:

  push:

    branches: \[develop\]

jobs:

  deploy\-staging:

    runs\-on: ubuntu\-22\.04

    environment: staging

    steps:

      \- uses: actions/checkout@v4

      \- name: Deploy via SSH

        uses: appleboy/ssh\-action@v1

        with:

          host: $\{\{ secrets\.STAGING\_HOST \}\}

          username: $\{\{ secrets\.STAGING\_USER \}\}

          key: $\{\{ secrets\.STAGING\_SSH\_KEY \}\}

          script: |

            cd /home/frappe/supplycore\-bench

            bench update \-\-pull \-\-reset

            bench \-\-site staging\.supplycore\.local migrate

            bench \-\-site staging\.supplycore\.local clear\-cache

            sudo supervisorctl restart all

      \- name: Smoke Test

        run: |

          sleep 30

          curl \-f https://staging\.supplycore\.local/api/method/frappe\.ping

## __2\.3 CD Production Workflow \(\.github/workflows/deploy\-prod\.yml\)__

name: Deploy to Production

on:

  push:

    tags: \['v\*'\]

jobs:

  deploy\-prod:

    runs\-on: ubuntu\-22\.04

    environment: production

    steps:

      \- uses: actions/checkout@v4

      \- name: Pre\-deploy Backup

        uses: appleboy/ssh\-action@v1

        with:

          host: $\{\{ secrets\.PROD\_HOST \}\}

          username: $\{\{ secrets\.PROD\_USER \}\}

          key: $\{\{ secrets\.PROD\_SSH\_KEY \}\}

          script: |

            bench \-\-site supplycore\.hospital\.vn backup \-\-with\-files

            echo 'Backup completed at $\(date\)'

      \- name: Deploy

        uses: appleboy/ssh\-action@v1

        with:

          host: $\{\{ secrets\.PROD\_HOST \}\}

          username: $\{\{ secrets\.PROD\_USER \}\}

          key: $\{\{ secrets\.PROD\_SSH\_KEY \}\}

          script: |

            cd /home/frappe/supplycore\-bench

            bench update \-\-pull \-\-reset

            bench \-\-site supplycore\.hospital\.vn set\-maintenance\-mode on

            bench \-\-site supplycore\.hospital\.vn migrate

            bench \-\-site supplycore\.hospital\.vn clear\-cache

            bench \-\-site supplycore\.hospital\.vn set\-maintenance\-mode off

            sudo supervisorctl restart all

      \- name: Health Check

        run: |

          sleep 60

          curl \-f https://supplycore\.hospital\.vn/api/method/frappe\.ping

          echo 'Production deployment successful'

# __3\. Quy trình Deploy Thủ công \(Manual\)__

## __3\.1 Deploy lên Staging__

__Staging Deployment Checklist__

__STT__

__Bước thực hiện__

__Lệnh / Xác nhận__

1

Xác nhận CI pass trên develop branch

GitHub Actions: all green

2

SSH vào staging server

ssh deploy@staging\-server

3

Pull code mới nhất

bench update \-\-pull \-\-reset

4

Chạy migration database

bench \-\-site X migrate

5

Clear cache

bench \-\-site X clear\-cache

6

Restart services

sudo supervisorctl restart all

7

Kiểm tra smoke test

curl /api/method/frappe\.ping

8

Thông báo team QA bắt đầu test

Email / Slack notify

## __3\.2 Deploy lên Production__

__Production Deployment Checklist – BẮT BUỘC FOLLOW ĐÚNG THỨ TỰ__

__STT__

__Bước thực hiện__

__Người chịu TN__

1

PM xác nhận Release Approval từ Sponsor

PM

2

Thông báo downtime đến người dùng \(trước 24h\)

PM \+ Hospital IT

3

Backup đầy đủ database và files production

Tech Lead \+ DBA

4

Xác nhận backup thành công \(restore test\)

DBA

5

Bật Maintenance Mode

bench \-\-site X set\-maintenance\-mode on

6

Pull code từ tag release

bench update \-\-pull \-\-reset

7

Chạy migration database

bench \-\-site X migrate

8

Build assets frontend

bench build \-\-app supplycore

9

Clear cache và sessions

bench \-\-site X clear\-cache

10

Tắt Maintenance Mode

bench \-\-site X set\-maintenance\-mode off

11

Restart tất cả services

sudo supervisorctl restart all

12

Health check toàn diện \(API \+ UI \+ background jobs\)

QA Lead

13

Thông báo Go\-Live thành công

PM

# __4\. Rollback Plan__

Trong trường hợp deployment thất bại hoặc phát hiện lỗi nghiêm trọng sau Go\-Live:

## __4\.1 Rollback tự động \(trong vòng 30 phút sau deploy\)__

cd /home/frappe/supplycore\-bench

bench \-\-site supplycore\.hospital\.vn set\-maintenance\-mode on

\# Restore database từ backup gần nhất

bench \-\-site supplycore\.hospital\.vn restore \\

  /path/to/backup/backup\_YYYYMMDD\_HHMMSS\.sql\.gz

bench \-\-site supplycore\.hospital\.vn restore\-files \\

  /path/to/backup/files\_backup\.tar

\# Checkout code phiên bản cũ

git \-C apps/supplycore checkout <previous\-tag>

bench \-\-site supplycore\.hospital\.vn migrate

bench \-\-site supplycore\.hospital\.vn set\-maintenance\-mode off

sudo supervisorctl restart all

## __4\.2 Quy trình quyết định Rollback__

__Tình huống__

__Điều kiện Rollback__

__Người quyết định__

__Thời hạn__

Lỗi nghiêm trọng P1

System down hoặc mất dữ liệu

Tech Lead \(không cần hỏi\)

Ngay lập tức

Lỗi cao P2

Core feature không hoạt động

PM \+ Tech Lead

Trong 2 giờ

Lỗi trung bình P3

Feature phụ lỗi, có workaround

PM quyết định

Hotfix thay vì rollback

# __5\. Cấu hình GitHub Secrets__

__Secret Name__

__Môi trường__

__Mô tả__

STAGING\_HOST

staging

IP/domain staging server

STAGING\_USER

staging

SSH username

STAGING\_SSH\_KEY

staging

Private SSH key \(Ed25519\)

PROD\_HOST

production

IP/domain production server

PROD\_USER

production

SSH username \(deploy user\)

PROD\_SSH\_KEY

production

Private SSH key production

SLACK\_WEBHOOK\_URL

both

Slack notification webhook

CODECOV\_TOKEN

ci

Coverage reporting token

Lưu ý bảo mật: Không bao giờ commit secrets vào code\. Sử dụng GitHub Environments với required reviewers cho production secrets\.

