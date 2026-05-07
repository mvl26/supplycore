__SUPPLYCORE__

Hệ thống Quản lý Chuỗi Cung ứng Vật tư Y tế Bệnh viện

__DEVELOPMENT STANDARDS & GUIDELINES__

Tài liệu này quy định các tiêu chuẩn phát triển phần mềm bắt buộc áp dụng cho toàn bộ team SupplyCore\. Mọi code contribution phải tuân thủ các quy tắc này trước khi được merge vào branch chính\.

# __1\. Tổng quan Tech Stack__

__Layer__

__Công nghệ__

__Phiên bản__

__Ghi chú__

Backend Framework

Frappe Framework

v15\.x \(pin\)

Python\-based full\-stack

ERP Base

ERPNext

v15\.x \(pin\)

Kế thừa Accounting, HR

Language \(Backend\)

Python

3\.11\+

Server\-side logic, API

Language \(Frontend\)

JavaScript / Vue\.js

ES2020\+ / Vue 3

Frappe desk UI

Database

MariaDB

10\.6\+

Primary data store

Cache / Queue

Redis

6\.x\+

Session, cache, background jobs

Web Server

Nginx \+ Gunicorn

Latest stable

Reverse proxy, WSGI

Task Queue

RQ \(Redis Queue\)

Built\-in Frappe

Background jobs

Version Control

Git / GitHub

Git 2\.x\+

Source code management

CI/CD

GitHub Actions

Latest

Automated build, test, deploy

Container

Docker / Docker Compose

Docker 24\+

Dev & staging environment

# __2\. Python Coding Standards__

## __2\.1 Style Guide__

Tuân thủ PEP 8 là bắt buộc\. Sử dụng Black formatter để format tự động trước khi commit\.

__Quy tắc__

__Đúng__

__Sai__

__Độ dài dòng__

OK  max 100 ký tự/dòng

X   dòng > 100 ký tự không wrap

__Đặt tên biến__

OK  snake\_case cho biến, hàm

X   camelCase cho Python code

__Đặt tên class__

OK  PascalCase

X   snake\_case cho class

__Đặt tên hằng số__

OK  UPPER\_SNAKE\_CASE

X   upper\_case hoặc camelCase

__Import__

OK  import theo nhóm: stdlib, third\-party, local

X   import wildcard \(from x import \*\)

__Docstring__

OK  def fn\(\):
    """Mô tả ngắn\."""

X   Không có docstring cho public functions

__Type hints__

OK  def fn\(x: int\) \-> str:

X   def fn\(x, y\) không có type hints

## __2\.2 Frappe\-specific Standards__

- Luôn dùng frappe\.db\.get\_value\(\) thay vì raw SQL query để lấy đơn giá trị
- Dùng frappe\.get\_doc\(\) cho thao tác với DocType đầy đủ
- Validation logic đặt trong validate\(\) method của DocType class
- Business logic phức tạp tách riêng vào utils\.py hoặc service layer
- Không commit trực tiếp vào database trong before\_save hook – dùng after\_insert/after\_submit
- Mọi API endpoint public phải có decorator @frappe\.whitelist\(\)
- Permission check bắt buộc: frappe\.has\_permission\(\) trước mọi thao tác data
- Sử dụng frappe\.throw\(\) thay vì raise Exception để lỗi hiển thị đúng trên UI

## __2\.3 Xử lý lỗi & Logging__

\# Chuẩn xử lý lỗi trong SupplyCore

try:

    result = process\_batch\(batch\_no\)

except frappe\.ValidationError as e:

    frappe\.log\_error\(title='Batch Process Error', message=str\(e\)\)

    frappe\.throw\(\_\(str\(e\)\)\)

except Exception as e:

    frappe\.log\_error\(title='Unexpected Error', message=frappe\.get\_traceback\(\)\)

    frappe\.throw\(\_\('Loi he thong\. Vui long lien he quan tri vien\.'\)\)

# __3\. JavaScript / Frontend Standards__

## __3\.1 Code Style__

- Dùng ESLint với config Frappe chuẩn – chạy tự động trong pre\-commit hook
- Sử dụng const/let, không dùng var
- Arrow functions cho callbacks ngắn; regular function cho methods có this binding
- Async/await thay vì Promise chain khi có thể
- Tên file: kebab\-case\.js \(ví dụ: batch\-tracker\.js\)
- Component Vue: PascalCase \(ví dụ: BatchTracker\.vue\)

## __3\.2 Frappe UI \(Desk\) Custom Scripts__

- Custom scripts đặt trong <app>/public/js/ hoặc dùng Client Scripts trong DocType
- Không sử dụng jQuery trực tiếp – dùng Frappe's cur\_frm\.set\_value\(\) và frappe\.call\(\)
- Event handlers đặt trong frappe\.ui\.form\.on\(\) – không dùng inline onclick
- Loading states: dùng frappe\.dom\.freeze\(\) / frappe\.dom\.unfreeze\(\)

# __4\. Database Standards__

## __4\.1 Naming Conventions__

__Đối tượng__

__Convention__

__Ví dụ__

DocType Name

Title Case \(Frappe tự tạo table\)

SC Warehouse Entry, SC Batch Log

Field Name

snake\_case

batch\_no, expiry\_date, warehouse\_id

Table prefix

tab<DocType> \(auto Frappe\)

tabSC Warehouse Entry

Index

idx\_<table>\_<field>

idx\_sc\_batch\_expiry\_date

Stored Procedure

sp\_<action>\_<entity>

sp\_calculate\_reorder\_point

## __4\.2 Query Standards__

- Không dùng SELECT \* – chỉ lấy fields cần thiết
- Mọi query lọc theo warehouse/company phải có WHERE clause tương ứng
- Index bắt buộc cho các field: batch\_no, expiry\_date, warehouse, item\_code, posting\_date
- Query phức tạp \(JOIN > 3 bảng\) phải có explain plan review trước khi merge
- Tránh N\+1 query – dùng frappe\.get\_all\(\) với filters thay vì loop get\_doc\(\)

# __5\. Git Workflow & Code Review__

## __5\.1 Branch Strategy__

__Branch__

__Mục đích__

__Protected__

__Merge từ__

main

Production\-ready code

Có – require PR

release/\*

develop

Integration branch

Có – require PR

feature/\*, bugfix/\*

feature/<name>

Phát triển tính năng mới

Không

develop

bugfix/<name>

Sửa lỗi trong develop

Không

develop

hotfix/<name>

Sửa lỗi khẩn trên production

Không

main \+ develop

release/<version>

Chuẩn bị release

Có

develop

## __5\.2 Commit Message Convention__

Tuân thủ Conventional Commits format:

feat\(warehouse\): add FEFO sorting for batch allocation

fix\(qc\): correct lot number validation logic

docs\(api\): update endpoint documentation for GRN

refactor\(stock\): extract reorder calculation to service layer

test\(batch\): add unit tests for expiry date alerts

chore\(deps\): upgrade frappe to v15\.28\.0

Commit message phải bằng tiếng Anh, dòng đầu tối đa 72 ký tự\.

## __5\.3 Pull Request \(PR\) Checklist__

- PR title theo convention: \[MODULE\] Short description
- Mô tả PR: What changed / Why / How to test
- Bắt buộc: ít nhất 1 reviewer approve trước khi merge vào develop
- Bắt buộc: ít nhất 2 reviewer \(Tech Lead \+ 1\) trước khi merge vào main
- CI phải pass: lint \+ unit tests \+ migration check
- Không self\-merge \(người tạo PR không được merge PR của mình\)
- PR size: tối đa 400 dòng changed – chia nhỏ nếu lớn hơn

# __6\. Testing Standards__

## __6\.1 Coverage Requirements__

__Loại test__

__Tool__

__Coverage tối thiểu__

__Thực hiện khi__

Unit Test

pytest \+ frappe\.tests

70% trên business logic

Mỗi PR

Integration Test

pytest

API endpoints chính

Mỗi PR

UI Test

Playwright

Happy path mỗi module

Pre\-release

Performance Test

Locust

100 concurrent users

Trước Go\-Live

Security Test

OWASP ZAP \+ manual

Toàn bộ API endpoints

Trước Go\-Live

## __6\.2 Test Naming Convention__

\# File: tests/test\_batch\_tracking\.py

class TestBatchTracking\(FrappeTestCase\):

    def test\_fefo\_sorting\_returns\_earliest\_expiry\_first\(self\):

        \# Arrange

        \.\.\.

    def test\_expired\_batch\_raises\_validation\_error\(self\):

        \.\.\.

# __7\. Security Standards__

- Không hardcode secrets, API keys, passwords trong source code
- Dùng frappe\.conf để đọc sensitive configuration
- Mọi input từ user phải được validate/sanitize trước khi xử lý
- SQL: luôn dùng parameterized queries – không string concatenation
- File upload: validate file type, size, scan malware trước khi lưu
- Log: không ghi thông tin nhạy cảm \(password, token\) vào log
- HTTPS bắt buộc cho mọi môi trường production và staging
- Rate limiting: API endpoints nhạy cảm giới hạn 100 req/phút/IP

# __8\. Documentation Standards__

- Mọi public function/method phải có docstring mô tả params và return value
- Thay đổi API phải cập nhật API Documentation trước khi merge
- README module cập nhật khi thêm tính năng mới hoặc thay đổi setup
- Changelog: cập nhật CHANGELOG\.md mỗi release theo Keep a Changelog format
- Inline comment: giải thích WHY, không giải thích WHAT \(code tự nói lên điều đó\)

