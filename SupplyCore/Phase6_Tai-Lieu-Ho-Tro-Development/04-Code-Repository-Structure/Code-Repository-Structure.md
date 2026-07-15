__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung ứng Vật tư Y tế Bệnh viện

__CODE REPOSITORY STRUCTURE__

Tài liệu này quy định cấu trúc tổ chức repository, quy ước đặt tên và chiến lược quản lý nhánh \(branching strategy\) cho dự án SupplyCore\.

# __1\. GitHub Organization & Repositories__

__Repository__

__Loại__

__Mô tả__

medcons/supplycore

Private

App chính – Frappe custom app

medcons/supplycore\-docker

Private

Docker compose configs cho các môi trường

medcons/supplycore\-docs

Private

Tài liệu kỹ thuật, API docs, diagrams

medcons/supplycore\-scripts

Private

Migration scripts, data import tools

medcons/supplycore\-tests

Private

E2E tests, performance tests \(Playwright, Locust\)

# __2\. Cấu trúc Thư mục – Repository chính \(supplycore\)__

Repository này là một Frappe custom app, tuân theo cấu trúc chuẩn của Frappe Framework với các mở rộng riêng của SupplyCore:

__Đường dẫn__

__Mô tả__

__supplycore/__

Root của Frappe custom app

  ├── supplycore/

Python package chính \(same name as app\)

    ├── config/

App config: desktop\.py, docs\.py

    ├── hooks\.py

Frappe hooks: scheduler, events, overrides

    ├── modules\.txt

Danh sách modules trong app

    ├── patches\.txt

Danh sách migration patches theo thứ tự

  ├── modules/

Nhóm các Modules nghiệp vụ chính

    ├── contract\_vendor/

M1: Hợp đồng & Nhà cung cấp

    ├── inventory\_planning/

M2: Kế hoạch tồn kho & Gọi hàng

    ├── goods\_receipt/

M3: Tiếp nhận & Kiểm tra chất lượng

    ├── warehouse\_mgmt/

M4: WMS & PDA

    ├── batch\_expiry/

M5: Lô, Hạn dùng & FEFO

    ├── stock\_transfer/

M6: Luân chuyển nội bộ

    ├── dispensing/

M7: Cấp phát & Ghi nhận sử dụng

    ├── accounting/

M8: Kế toán & Thanh toán

    ├── inventory\_count/

M9: Kiểm kê & Đối soát

    ├── traceability/

M10: Truy xuất & Điều tra

    ├── dashboard/

M11: Dashboard & Cảnh báo điều hành

  ├── public/

Static files phục vụ trực tiếp qua web

    ├── js/

Custom JavaScript cho Frappe Desk

    ├── css/

Custom CSS stylesheets

    ├── images/

Icons, logos, static images

  ├── templates/

Jinja2 templates: print formats, emails

  ├── tests/

Unit & integration tests

    ├── fixtures/

Test data fixtures

    ├── test\_\*\.py

Test files theo module

  ├── patches/

Database migration patches

    ├── v15\_0/

Patches theo version

  ├── utils/

Shared utilities và helper functions

    ├── batch\_utils\.py

FEFO sorting, batch allocation

    ├── notification\_utils\.py

Alert & notification helpers

    ├── report\_utils\.py

Common report helpers

  ├── \.github/

GitHub Actions CI/CD workflows

    ├── workflows/

ci\.yml, deploy\-staging\.yml, deploy\-prod\.yml

  ├── CHANGELOG\.md

Release notes, version history

  ├── requirements\.txt

Python dependencies \(pinned versions\)

  ├── setup\.py

App setup và metadata

  ├── README\.md

Giới thiệu app, quick start guide

# __3\. Cấu trúc trong mỗi Module__

Mỗi module trong thư mục modules/ tuân theo cấu trúc chuẩn sau:

__File / Folder__

__Mô tả__

__<module\_name>/__

Thư mục module

  ├── \_\_init\_\_\.py

Python package init

  ├── doctype/

Các DocTypes thuộc module này

    ├── <doctype\_name>/

Thư mục mỗi DocType

      ├── <doctype>\.json

DocType schema definition

      ├── <doctype>\.py

Python controller class

      ├── <doctype>\.js

Client\-side scripts

      ├── test\_<doctype>\.py

Unit tests cho DocType

  ├── report/

Custom reports của module

    ├── <report\_name>/

Script report, query report

  ├── notification/

Notification templates

  ├── workspace/

Frappe Workspace config

  ├── api\.py

Public API endpoints \(@whitelist\)

  ├── utils\.py

Business logic helpers của module

  ├── constants\.py

Module\-level constants

# __4\. Branch Strategy__

## __4\.1 Branch Model – GitHub Flow mở rộng__

__Branch__

__Vòng đời__

__Naming Convention__

__Ví dụ__

main

Permanent

main

main

develop

Permanent

develop

develop

feature

Per feature

feature/<module>/<desc>

feature/batch\-expiry/fefo\-sort

bugfix

Per bug

bugfix/<ticket>\-<desc>

bugfix/SC\-123\-fix\-grn\-validation

hotfix

Per incident

hotfix/<version>\-<desc>

hotfix/v1\.2\.1\-fix\-stock\-calc

release

Per release

release/<version>

release/v1\.0\.0

## __4\.2 Quy tắc Merge__

- feature/\* → develop: PR với ít nhất 1 approval, CI pass
- bugfix/\* → develop: PR với ít nhất 1 approval, CI pass
- develop → release/\*: PM tạo release branch, freeze features
- release/\* → main: PR với 2 approvals \(Tech Lead \+ PM\), CI \+ E2E pass
- release/\* → develop: merge lại để sync hotfixes
- hotfix/\* → main VÀ develop: cả hai branch đều nhận hotfix
- KHÔNG được merge trực tiếp vào main hoặc develop mà không qua PR

## __4\.3 Versioning – Semantic Versioning__

Dự án tuân thủ SemVer 2\.0\.0: MAJOR\.MINOR\.PATCH

__Loại__

__Khi nào tăng__

__Ví dụ__

MAJOR

Breaking changes không tương thích ngược

v1\.x\.x → v2\.0\.0 \(thay đổi API lớn\)

MINOR

Thêm tính năng mới, tương thích ngược

v1\.2\.x → v1\.3\.0 \(thêm module mới\)

PATCH

Bug fixes, không thay đổi API

v1\.2\.3 → v1\.2\.4 \(sửa lỗi tính toán\)

Release tags: v1\.0\.0 \(stable\), v1\.0\.0\-rc\.1 \(release candidate\), v1\.0\.0\-beta\.1 \(beta\)

# __5\. File đặc biệt bắt buộc__

__File__

__Vị trí__

__Nội dung bắt buộc__

\.gitignore

root

\*\.pyc, \_\_pycache\_\_, \.env, node\_modules, \*\.log, site\_config\.json

\.editorconfig

root

indent\_style=space, indent\_size=1 \(tab=1 for JS, 4 for Python\.\.\. theo Black\)

pyproject\.toml

root

Black config: line\-length=100; isort config

\.eslintrc\.js

root

Extends frappe ESLint config chuẩn

CHANGELOG\.md

root

Keep a Changelog format; cập nhật mỗi release

requirements\.txt

root

All Python deps với version pin \(==\) không dùng >=

CODEOWNERS

\.github/

Assign auto\-reviewer theo module/folder

## __CODEOWNERS mẫu__

\# \.github/CODEOWNERS

\# Mỗi module có code owner riêng

apps/supplycore/modules/batch\_expiry/     @dev\-batch\-team

apps/supplycore/modules/accounting/       @dev\-finance\-team

apps/supplycore/modules/warehouse\_mgmt/   @dev\-wms\-team

apps/supplycore/\.github/                  @tech\-lead

apps/supplycore/hooks\.py                  @tech\-lead

# __6\. Code Review Guidelines__

- Reviewer phải xem xét: logic đúng, security, performance, test coverage, documentation
- Không approve PR có TODO/FIXME chưa resolve \(trừ có ticket theo dõi\)
- Comment constructively: giải thích lý do, đề xuất cụ thể, không chỉ trích
- Author phải respond mọi comment trước khi merge: resolve hoặc explain
- Squash merge vào develop; merge commit vào main \(để giữ lịch sử release\)

