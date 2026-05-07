__SUPPLYCORE__

He thong Quan ly Chuoi Cung Ung Vat Tu Y Te

__WIREFRAMES – THIET KE CHI TIET CHUC NANG__

Phien ban: v1\.0  |  Ngay: 05/05/2026

Tai lieu: SC\-PH3\-WF\-013  |  Phase 3 – Thiet ke giao dien

# __1\. THONG TIN TAI LIEU__

__Thuoc tinh__

__Gia tri__

__Ten tai lieu__

Wireframes – SupplyCore

__Ma tai lieu__

SC\-PH3\-WF\-013

__Fidelity__

Lo\-fi to Mid\-fi Wireframes \(annotated\)

__Cong cu__

Dac ta chi tiet trong tai lieu nay; thuc hien trong Frappe UI \(Vue 3\)

__Pham vi__

14 wireframe chinh cho cac chuc nang quan trong

__Quy uoc__

Hop dut: vung UI component; \[X\]: nut hanh dong; \(n\): so annotation

__Tac gia__

UX Designer – SupplyCore Project

# __2\. WIREFRAMES CHI TIET__

## __WF\-01 – Man hinh Dang nhap__

Chuc nang: Xac thuc nguoi dung vao he thong SupplyCore

__████████  SupplyCore  ████████__

He thong quan ly chuoi cung ung vat tu y te

Email / Ten dang nhap

nguyen\.van\.a@hospital\.vn

Mat khau

••••••••••••

__DANG NHAP__

Quen mat khau?

__\(1\)__

Email validation: kiem tra dinh dang truoc khi gui

__\(2\)__

5 lan sai mat khau: hien canh bao; lan 6: khoa 30 phut

__\(3\)__

Dang nhap thanh cong: chuyen den Dashboard theo role

__\(4\)__

'Quen mat khau': gui link dat lai mat khau qua email

__Luong tuong tac:__

__Buoc__

__Hanh dong nguoi dung__

__Phan hoi he thong__

__Trang thai / Luu y__

__1__

Nhap email va mat khau

Form hien thi text / dots

Validate dinh dang email real\-time

__2__

Click \[DANG NHAP\]

Spinner, disable button

Gui request den Frappe auth API

__3a__

Thanh cong

Redirect den Dashboard

Cache session cookie; luu last\-login

__3b__

Sai mat khau

Thong bao do: 'Sai mat khau'

Dem so lan sai; khoa sau 5 lan

__3c__

Tai khoan khoa

Thong bao: 'Tai khoan bi khoa'

Hien so phut con lai; link lien he admin

## __WF\-02 – Form Purchase Order – Chi tiet \+ Workflow__

Chuc nang: Xem, sua, phe duyet Purchase Order

Mua hang > Purchase Order > PO\-2026\-00052

__PO\-2026\-00052   \[Cho duyet\]__

__\[Duyet\]__

__\[Tu choi\]__

\[In\]

__✓ Draft__

__● Cho duyet QL__

○ Da duyet

○ Da gui NCC

○ Hoan thanh

NCC: \[Cong ty Duoc A          v\] \(1\)

HĐK: \[SC\-FC\-2026\-00003        v\]

Ngay PO: \[03/05/2026\]

Nguoi tao: Nguyen Van A

 

 Han muc HĐK con lai: 127,600,000 VND

 

Ngay giao DK: \[10/05/2026\]

DK TT: \[30 ngay ke ngay nhan  v\]

Dia chi giao: \[Kho Tong – Tang 1\]

Ghi chu: \[                    \]

 

 

__Danh muc vat tu \(Items\):__

__Ma VT__

__Ten vat tu__

__SL__

__DVT__

__Don gia__

__Thanh tien__

__Xoa__

VT\-GLOVE\-001

Gang tay phau thuat

500

Doi

35,000

17,500,000

\[x\]

VT\-BANDAGE\-001

Bang y te cuon 5cm

200

Cuon

12,000

2,400,000

\[x\]

VT\-SYRINGE\-5

Kim tiem 5ml

1000

Cai

1,500

1,500,000

\[x\]

\[ \+ Them VT \]

TONG CONG:

21,400,000

__\(1\)__

Chon NCC: filter chi NCC co HĐK con hieu luc; auto\-fill don gia

__\(2\)__

Workflow bar: click vao buoc da hoan thanh de xem lich su \+ nguoi thuc hien

__\(3\)__

Tong > Han muc HĐK: highlight do, disable \[Gui duyet\] cho den khi chinh sua

__\(4\)__

\[Tu choi\]: hien dialog nhap ly do; gui email bao nguoi tao

__\(5\)__

\[Duyet\] chi hien voi SC\-MANAGER khi PO o trang thai 'Cho duyet QL'

__Buoc__

__Hanh dong nguoi dung__

__Phan hoi he thong__

__Trang thai / Luu y__

__1__

Chon NCC

Load HĐK co hieu luc tuong ung

Hien so du HĐK ben canh toan tien

__2__

Chon HĐK

Load gia san theo FC Item

Highlight vat tu khong co trong HĐK

__3__

Sua don gia

Hien canh bao: 'Gia khac HĐK'

Luu log: ly do thay doi gia

__4__

Click \[Gui duyet\]

Submit form, chuyen trang thai

GUI email cho approver; hien badge 'Cho duyet'

__5__

Click \[Duyet\]

Dialog xac nhan

Workflow chuyen sang 'Da duyet'; email bao nguoi tao

## __WF\-03 – Stock Balance – Tra cuu ton kho__

Chuc nang: Tra cuu ton kho theo vat tu, kho, lo hang, vi tri bin

__Ton kho – Stock Balance__

Kho: \[Tat ca v\]

Nhom VT: \[Tat ca v\]

Co ton: \[Co v\]

Lo: \[          \]

Han dung: \[  \]den\[  \]

Tim: \[       \]

\[Loc\]

__Ma VT__

__Ten vat tu__

__Kho__

__Bin__

__So lo__

__Han dung__

__Ton kho__

__Don vi__

VT\-GLOVE\-001

Gang tay phau thuat

Kho Tong

Ke A1

LOT\-G\-202601

15/06/2026

150

Doi

VT\-GLOVE\-001

Gang tay phau thuat

Kho Tong

Ke A1

LOT\-G\-202603

30/09/2026

300

Doi

VT\-BANDAGE\-001

Bang y te cuon 5cm

Kho Noi

Ke B2

LOT\-B\-202602

28/02/2028

80

Cuon

VT\-SYRINGE\-5

Kim tiem 5ml

Kho Tong

Ke B1

LOT\-K\-202601

30/06/2027

500

Cai

Tong cong – VT\-GLOVE\-001:

450 Doi

\[Xuat Excel\]   \[In\]   \[Refresh\]

__\(1\)__

Dong mau do = lo sap het han \(<30 ngay\); click de xem lich su lo hang

__\(2\)__

Click ten vat tu: expand xem tat ca lo hang; collapse lai khi click lai

__\(3\)__

Tong dong: chi hien khi loc theo 1 vat tu; hien tong tat ca lo

__\(4\)__

\[Xuat Excel\]: xuat du lieu hien thi \(da loc\); giu cac filter da chon

__\(5\)__

Real\-time: so lieu cap nhat khi co giao dich moi \(Frappe real\-time via Socket\.IO\)

## __WF\-04 – Quality Inspection – Kiem tra chat luong hang nhap__

Chuc nang: Kiem tra QC tung vat tu trong lo hang vua nhan

__Quality Inspection: QI\-2026\-00089  |  \[Cho QC\]__

Vat tu: Gang tay phau thuat \(VT\-GLOVE\-001\)

So lo: LOT\-G\-202601

Han dung: 15/06/2026

SL nhan: 498 Doi

Purchase Receipt: MAT\-REC\-2026\-00038

Checklist QC – Nhom vat tu: Vat tu tieu hao

Nguoi kiem tra: \[Thu kho – Tran Van C  v\]

Ngay kiem tra: \[05/05/2026\]

Ghi chu tong: \[                          \]

__Checklist kiem tra:__

__Tieu chi kiem tra__

__Dat__

__Khong dat__

__Ghi chu__

Bao bi nguyen ven, khong bi rach / vung / am uot

\( ● \)

\(   \)

Nhan mac dung: ten san pham, hang SX, han dung

\( ● \)

\(   \)

So lo khop voi chung tu giao hang

\( ● \)

\(   \)

Han su dung >= 6 thang ke tu ngay nhan

\( ● \)

\(   \)

Quy cach dung: kich thuoc, mau sac, chung loai

\( ● \)

\(   \)

So luong kip len co mat

\( ● \)

\(   \)

Khong co mui la / bien sac bat thuong

\(   \)

\( ● \)

\[Mui la bat thuong, co the bi nhiet am\]

Ket qua tong the: \[KHONG DAT – 1/7 tieu chi that bai\]

\[CHAP NHAN CO DK\]

\[TRA HANG NCC\]

__\(1\)__

Checklist tu dong load theo Item Group – co the tuy chinh theo loai vat tu

__\(2\)__

Nut \[DAT\] / \[KHONG DAT\] la toggle; co the sua truoc khi submit

__\(3\)__

\[TRA HANG NCC\]: auto\-create Supplier Return draft; lock han muc ton kho

__\(4\)__

\[CHAP NHAN CO DK\]: nhap ly do; luu audit trail; giam diem danh gia NCC

__\(5\)__

Ket qua tong the tu dong tinh: tat ca dat = PASS; bat ky 1 khong dat = FAIL

## __WF\-05 – Patient Dispensing – Ghi nhan cap phat cho Benh nhan__

Chuc nang: Ghi nhan vat tu su dung cho benh nhan, tinh chi phi BHYT tu dong

__Phieu cap phat benh nhan – SC\-PD\-2026\-00045  |  \[Draft\]__

Ma benh nhan: \[BN\-2026\-00123\]  \[Quet the\]

Ten: Nguyen Thi X \(auto\-fill\)

Ngay sinh: 15/03/1985 \(auto\-fill\)

So the BHYT: \[1234 5678 9012\] \(1\)

Loai BH: \[BHYT \- Muc 80%\] \(auto\-fill\)

Ngay cap phat: \[05/05/2026\]

Khoa dieu tri: \[Ngoai tong hop\] \(auto\)

Phieu xuat kho: \[STE\-2026\-00078\]

Ghi chu: \[                    \]

__Danh muc vat tu da cap phat:__

__Ma VT__

__Ten vat tu__

__SL__

__DVT__

__Don gia__

__Ma BHYT__

__Nhom__

__BHYT tra__

__BN tra__

VT\-GLOVE\-001

Gang tay PT

2

Doi

35,000

BHYT\-0012

N05

56,000

14,000

VT\-BANDAGE\-001

Bang y te

1

Cuon

12,000

BHYT\-0008

N05

9,600

2,400

VT\-SYRINGE\-5

Kim tiem 5ml

3

Cai

1,500

BHYT\-0001

N05

3,600

900

TONG CONG:

69,200

17,300

Tong chi phi: 86,500 VND  |  BHYT chi tra: 69,200 VND \(80%\)  |  Benh nhan tu tra: 17,300 VND

\[LUU & IN PHIEU\]

__\(1\)__

Quet the BHYT: tu dong dien so the; ket noi HIS de lay thong tin BN \(GD2\)

__\(2\)__

Ma BHYT va ty le: tu dong lay tu BHYT Code Config hien hanh; co the override

__\(3\)__

Tinh phi BHYT real\-time khi nhap so luong; canh bao neu khong co ma BHYT

__\(4\)__

\[LUU & IN PHIEU\]: luu database \+ mo dialog xem truoc phieu cap phat de in

__\(5\)__

Sau luu: du lieu tong hop vao bao cao quyet toan BHYT thang

## __WF\-06 – Alert Center – Trung tam canh bao__

Chuc nang: Xem tat ca canh bao he thong, phan loai uu tien va xu ly

__Trung tam canh bao  |  12 chua xu ly__

\[Danh dau tat la da doc\]

\[Tat ca \(12\)\]

\[Khan cap \(5\)\]

\[Quan trong \(4\)\]

\[Thong tin \(3\)\]

\[\!\!\!\]

__HET HANG: Gang tay phau thuat – Kho Tong__

Ton kho hien tai: 0 / Muc toi thieu: 100 Doi

5 phut truoc

\[Tao MR\]

\[\!\!\!\]

__SAP HET HAN: Kim tiem 5ml – LOT\-K\-202512__

Han dung: 15/05/2026 \(con 10 ngay\)\. Kho Tong – Ke B1\. Ton: 200 cai

27 phut truoc

\[Uu tien xuat\]

\[\!\!\]

__HAN MUC HĐK: HĐ SC\-FC\-2026\-00003 gan het han muc__

Da su dung: 380/500 trieu VND \(76%\)\. Con lai: 120 trieu

2 gio truoc

\[Xem HĐK\]

\[\!\!\]

__PO QUA HAN: PO\-2026\-00049 chua nhan hang__

Ngay giao DK: 05/05/2026 \(tre 0 ngay\)\. NCC: Cong ty Duoc A

3 gio truoc

\[Lien he NCC\]

\[\!\]

__HOP DONG SAP HET HAN: SC\-FC\-2026\-00001__

NCC: Cong ty TB Y te B\. Het han: 01/06/2026 \(con 27 ngay\)

1 ngay truoc

\[Gia han\]

__\(1\)__

Tab filter: click de loc theo muc do; badge so luong cap nhat real\-time

__\(2\)__

Quick action button: thuc hien truc tiep tu canh bao; mo form lien quan

__\(3\)__

Danh dau da doc: canh bao van hien neu chua xu ly nguyen nhan

__\(4\)__

Canh bao tu resolve khi dieu kien het con thoa man \(vi du: da dat MR\)

## __WF\-07 – Batch Traceability – Truy xuat nguon goc lo hang__

Chuc nang: Truy xuat toan bo lich su vong doi cua 1 lo vat tu

__Truy xuat lo hang – Batch Traceability__

Nhap so lo / Batch ID: \[LOT\-G\-202601          \]

\[    \]

\[TRA CUU\]

__Ket qua truy xuat: VT\-GLOVE\-001 – LOT\-G\-202601 – Han dung: 15/06/2026__

\[NHAP KHO\]

Ngay: 20/01/2026  |  Purchase Receipt: MAT\-REC\-2026\-00010

NCC: Cong ty Duoc A  |  PO: PO\-2026\-00015

So luong nhan: 500 Doi  |  QC: DAT

Vi tri: Kho Tong – Ke A1

Nguoi nhan: Thu kho Tran Van C

\[CHUYEN KHO\]

Ngay: 01/02/2026  |  Stock Entry: STE\-2026\-00025

Tu: Kho Tong – Ke A1  →  Den: Kho Ngoai – Ke X1

So luong: 100 Doi  |  Nguoi thuc hien: Thu kho Tran Van C

\[CAP PHAT\]

Ngay: 10/02/2026  |  Patient Dispensing: SC\-PD\-2026\-00012

Khoa: Ngoai tong hop  |  Ma BN: BN\-2026\-00045

So luong: 10 Doi  |  Nguoi cap phat: Thu kho Le Thi D

Chi phi: 350,000 VND  |  BHYT: 280,000 VND  |  BN: 70,000 VND

\[TON KHO\]

Ton hien tai: 150 Doi \(Kho Tong – Ke A1\) \+ 80 Doi \(Kho Ngoai – Ke X1\)

Tong da xuat: 270 Doi  |  Con lai trong he thong: 230 Doi

\[Xuat bao cao PDF\]   \[Tao Recall Notice\]   \[In\]

__\(1\)__

Timeline hien thi theo thu tu thoi gian; mau sac theo loai su kien

__\(2\)__

Click vao tung buoc: expand xem chi tiet document goc \(PR, SE, PD\)

__\(3\)__

\[Tao Recall Notice\]: mo form thu hoi voi batch\_no da dien san

__\(4\)__

Nut \[Xuat PDF\]: tao bao cao trace day du, co chu ky dien tu \(phuc vu audit\)

## __WF\-08 – Mobile PDA – Luong lam viec offline__

Chuc nang: Thu kho su dung PDA quet barcode kiem ke khi mat mang

__Buoc 1__

__Buoc 2__

__Buoc 3__

__Buoc 4__

Mo app PDA

Chon: Kiem ke

Chon: Kho Tong

Hien thi:

'Offline mode'

\[bat dau offline\]

Quet barcode

vat tu tung lo

Nhap so dem

thuc te

Luu local

\(IndexedDB\)

App hien thi:

\[Offline: 45

ban ghi chua

dong bo\]

Ket noi Wifi

Tap \[Dong bo\]

Upload 45 ban

ghi len server

Hien thanh

cong / loi

Tao draft

Stock Reconciliation

__Buoc__

__Hanh dong nguoi dung__

__Phan hoi he thong__

__Trang thai / Luu y__

__1__

Vao app khi co Wifi

Luu session cache; tai danh sach vat tu

Cho phep dung offline sau khi tai xong

__2__

Mat Wifi

App hien banner: 'Dang o che do offline'

Giao dich luu vao IndexedDB local

__3__

Co Wifi lai

App hien: 'X ban ghi chua dong bo'

Nut \[Dong bo ngay\] noi bat

__4__

Click \[Dong bo\]

Upload IndexedDB \-> Server API

Hien tien trinh; bao cao ket qua dong bo

__5__

Xung dot du lieu

Hien thi conflict item

Yeu cau chon: giu local hay server

# __3\. DAC TA COMPONENT CHUNG__

## __3\.1 Form field states__

__Trang thai__

__Giao dien__

__Trigger__

__Xu ly__

__Default__

Vien xam nhat

Focus → vien xanh

—

__Focus__

Vien xanh MED\_BLUE

Click vao field

Hien label float tren

__Filled__

Vien xam trung

Sau khi nhap

Hien icon xoa \(x\)

__Error__

Vien do \+ text do ben duoi

Validate fail

Hien message loi cu the

__Disabled__

Nen xam nhat, text xam

Read\-only state

Khong cho click/nhap

__Loading__

Spinner trong field

API call \(e\.g\. link field\)

Disable field khi dang tai

__Success__

Vien xanh la \+ check icon

Sau validate thanh cong

Tu tat sau 2 giay

## __3\.2 Table interaction patterns__

• Hover: dong duoc highlight nhe \(xam nhat\)

• Click dong: mo detail panel ben phai \(split view\); khong chuyen trang

• Multi\-select: checkbox dau dong; hien toolbar hanh dong hang loat

• Sort: click tieu de cot; mui ten chi chieu sap xep

• Resize cot: keo vien phai cua tieu de cot

• Sticky header: tieu de cot co dinh khi scroll xuong

## __3\.3 Responsive breakpoints__

__Breakpoint__

__Width__

__Thiet bi__

__Thay doi layout__

__Desktop XL__

≥ 1920px

Man hinh lon

Layout day du, sidebar rong, table nhieu cot

__Desktop__

1366–1919px

Man hinh laptop

Layout chuan – thiet ke cho khung nay

__Tablet__

768–1365px

iPad, tablet

Sidebar thu gon thanh icon; table an bot cot phu

__Mobile/PDA__

< 768px

Dien thoai, may PDA

Giao dien 1 cot; menu hamburger; form full screen

