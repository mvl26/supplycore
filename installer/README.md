# SupplyCore — Hướng dẫn cài đặt & vận hành (cho IT bệnh viện)

Tài liệu này dành cho cán bộ IT. Mọi đường dẫn và lệnh trong đây khớp với bộ cài thực tế.

---

## 1. SupplyCore là gì

SupplyCore là phần mềm quản lý vật tư y tế (Frappe v15) chạy bên trong **một máy ảo Linux ẩn** trên máy Windows. IT chỉ cần **một file `.exe`** để cài; toàn bộ Linux + Docker + cơ sở dữ liệu được đóng gói sẵn, không phải cài thêm gì.

---

## 2. Yêu cầu phần cứng / hệ thống

| Hạng mục | Yêu cầu |
|---|---|
| Hệ điều hành | Windows 10 / 11 hoặc Windows Server, **64-bit (x64)** |
| CPU | Hỗ trợ ảo hóa và **bật trong BIOS/UEFI** (Intel VT-x / AMD-V). Khi bật, máy ảo dùng tăng tốc phần cứng **WHPX** (nhanh). Nếu không bật được, SupplyCore tự chuyển sang mô phỏng phần mềm **TCG** — vẫn chạy nhưng **rất chậm**. |
| RAM | ≥ **8 GB** (máy ảo chiếm 4 GB) |
| Đĩa trống | ≥ **40 GB** |
| Quyền | **Administrator** để cài (bộ cài yêu cầu nâng quyền) |

Máy ảo cấu hình cố định: **2 vCPU, 4096 MB RAM**, chuyển tiếp cổng `127.0.0.1:<cổng>` → cổng 80 trong máy ảo.

---

## 3. Cài đặt (giao diện)

1. Double-click `SupplyCore-Setup-vX.exe` (X là số phiên bản). Bấm **Yes** khi Windows hỏi nâng quyền Administrator.
2. **Trang mật khẩu Administrator:** nhập mật khẩu đăng nhập SupplyCore lần đầu.
   - **KHÔNG được dùng các ký tự:** `"` (nháy kép), `` ` `` (backtick), `'` (nháy đơn), `\` (gạch chéo ngược). Bộ cài sẽ báo lỗi và không cho đi tiếp nếu mật khẩu chứa các ký tự này.
3. **Trang cổng:** chọn cổng localhost để mở SupplyCore. Mặc định **80**. Bỏ trống = 80. Phải là số.
4. Bộ cài kiểm tra ảo hóa (WHPX):
   - Nếu WHPX đã sẵn sàng → cài tiếp ngay.
   - Nếu WHPX vừa được bật → **yêu cầu khởi động lại máy 1 lần**. Sau khi khởi động lại, SupplyCore tự chạy và tự mở trình duyệt.
   - Nếu máy không hỗ trợ WHPX → hiện cảnh báo chạy chế độ TCG (chậm) và vẫn tiếp tục.
5. **Lần đầu khởi động máy ảo mất vài phút** (chế độ TCG có thể lâu hơn — bộ cài chờ tới 30 phút). Sau khi sẵn sàng, trình duyệt tự mở `http://localhost/supplycore`.
6. Đăng nhập bằng tài khoản **Administrator** với mật khẩu đã đặt ở bước 2.

---

## 4. Cài im lặng (triển khai hàng loạt)

Dùng để cài tự động trên nhiều máy không cần thao tác tay:

```bat
SupplyCore-Setup-vX.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /ADMINPW="<mật khẩu>" /PORT=80
```

- `/ADMINPW="..."` — mật khẩu Administrator (tuân thủ giới hạn ký tự ở mục 3).
- `/PORT=80` — cổng truy cập (tùy chọn; mặc định 80).
- `/NORESTART` — không tự khởi động lại (nếu WHPX cần reboot, IT tự lên lịch khởi động lại; SupplyCore sẽ tự chạy ở lần boot kế tiếp).

> **CẢNH BÁO:** Ở chế độ im lặng, nếu **thiếu `/ADMINPW`** (hoặc mật khẩu rỗng/không hợp lệ), bộ cài **dừng phần khởi tạo và KHÔNG cài dịch vụ** — và do `/SUPPRESSMSGBOXES` nên việc này xảy ra **âm thầm, không báo lỗi rõ**. Luôn truyền `/ADMINPW="<mật khẩu hợp lệ>"`.

---

## 5. Truy cập

- Mở trình duyệt: **`http://localhost/supplycore`** (hoặc `http://127.0.0.1:<cổng>/supplycore` nếu chọn cổng khác).
- SupplyCore chỉ **bind `127.0.0.1`** — chỉ truy cập được **từ chính máy đã cài**. Phiên bản v1 **không mở ra mạng LAN**.

---

## 6. Dữ liệu nằm ở đâu — bền qua update

Bộ cài tách rõ "ứng dụng" và "dữ liệu" thành 2 ổ đĩa ảo:

| | Đường dẫn | Nội dung | Khi update |
|---|---|---|---|
| **Dữ liệu (disk1)** | `C:\ProgramData\SupplyCore\disk1.qcow2` | Cơ sở dữ liệu, file đính kèm (sites), và bản sao lưu | **GIỮ NGUYÊN** |
| **Ứng dụng (disk0)** | `C:\Program Files\SupplyCore\disk0.qcow2` | Image hệ thống + mã ứng dụng | Bị thay khi update |

- Toàn bộ dữ liệu vận hành nằm trong `disk1.qcow2`. **Update không bao giờ đụng tới disk1.**
- Thư mục dữ liệu `C:\ProgramData\SupplyCore` còn chứa `seed.iso` (cấu hình khởi tạo) và log máy ảo `supplycore-vm.log`.

---

## 7. Sao lưu (backup)

- Máy ảo **tự sao lưu hằng ngày lúc 02:00** (`bench backup --with-files`) vào thư mục `/data/backups` **bên trong** `disk1.qcow2`. Vì nằm trong disk1 nên backup sống qua update.
- Lịch backup do timer trong máy ảo điều khiển (`OnCalendar=*-*-* 02:00:00`, có `Persistent=true` — nếu máy tắt lúc 02:00 thì chạy bù khi bật lại).

> **Lấy backup ra ngoài Windows — v1: làm thủ công.**
> Backup hiện nằm trong ổ đĩa ảo `disk1.qcow2`, **chưa có công cụ tự sao chép bản backup ra một thư mục Windows**. Việc lấy file backup ra ngoài là **thao tác thủ công nâng cao chạy trong máy ảo** (xem mục 8 về cách thao tác trong VM). **Các phiên bản sau sẽ tự động copy backup ra ngoài.**
> Lưu ý quan trọng: nên định kỳ **sao lưu cả file `C:\ProgramData\SupplyCore\disk1.qcow2`** (khi dịch vụ đã dừng) sang nơi an toàn — đây là cách bảo toàn toàn bộ dữ liệu đơn giản nhất ở v1.

---

## 8. Phục hồi (restore)

> **v1: thao tác thủ công nâng cao, chạy bên trong máy ảo.** Chưa có nút restore 1-click.

Bên trong máy ảo, lệnh restore thực tế là (qua wrapper `/opt/supplycore/bin/bench`, bản chất là `docker compose ... exec -T backend bench`):

```bash
bench --site supplycore.localhost restore <đường-dẫn-file-backup>
```

- Site cố định là **`supplycore.localhost`**.
- File backup nằm trong `/data/backups` bên trong máy ảo.

> **CẢNH BÁO:** Lệnh `restore` **ghi đè toàn bộ dữ liệu hiện tại**. Hãy chắc chắn trước khi chạy. Nên sao lưu trạng thái hiện tại (hoặc copy `disk1.qcow2`) trước khi restore.

---

## 9. Cập nhật (update)

- Chỉ cần **chạy file `.exe` phiên bản mới**. Bộ cài **re-runnable** (chạy lại được nhiều lần).
- Ổ ứng dụng (disk0) bị thay bằng bản mới; **ổ dữ liệu `disk1.qcow2` giữ nguyên** nên không mất dữ liệu.
- Lần khởi động đầu sau update, máy ảo tự chạy **`bench migrate`** để áp lược đồ CSDL mới (an toàn, idempotent).

---

## 10. Gỡ cài (uninstall)

- Gỡ qua **Settings → Apps → Apps & Features → SupplyCore → Uninstall**, hoặc chạy `C:\Program Files\SupplyCore\unins000.exe`.
- Quá trình gỡ sẽ **dừng và xóa dịch vụ Windows "SupplyCore"**, nhưng **KHÔNG xóa dữ liệu**: `C:\ProgramData\SupplyCore` (gồm `disk1.qcow2`, CSDL, backup) **vẫn còn nguyên**. Cài lại sẽ dùng lại dữ liệu cũ.
- **Nếu thực sự muốn xóa hết dữ liệu** (không thể khôi phục): sau khi gỡ cài, xóa thủ công thư mục `C:\ProgramData\SupplyCore`.

---

## 11. Xử lý sự cố

| Triệu chứng | Cách xử lý |
|---|---|
| SupplyCore không mở / treo | Mở `services.msc`, tìm dịch vụ **"SupplyCore"** → **Restart**. Dịch vụ đặt tự khởi động (Automatic) và tự khởi động lại sau lỗi (sau 10 giây). |
| Cần xem nhật ký máy ảo | Mở `C:\ProgramData\SupplyCore\supplycore-vm.log` (log nối tiếp của máy ảo). |
| Cần xem nhật ký dịch vụ | Xem các file log của WinSW trong `C:\Program Files\SupplyCore` (cùng thư mục `SupplyCore-service.exe`, log xoay vòng theo dung lượng). |
| Cổng 80 bị ứng dụng khác chiếm | Cài lại và **chọn cổng khác** ở trang cổng (ví dụ 8080), rồi truy cập `http://localhost:8080/supplycore`. |
| Máy rất chậm | Kiểm tra ảo hóa: nếu đang chạy chế độ **TCG** (không có WHPX) sẽ rất chậm. Vào **BIOS/UEFI bật ảo hóa** (Intel VT-x / AMD-V) rồi cài lại để dùng WHPX. |
| Vừa cài xong, chưa kịp phản hồi | Lần đầu (đặc biệt TCG) khởi động lâu. Có thể **khởi động lại máy** — dịch vụ tự chạy lại và tự mở trình duyệt khi sẵn sàng. |

---

*Tài liệu vận hành SupplyCore — bản cài Windows (v1).*
