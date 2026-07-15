"""Đọc số tiền VND bằng chữ tiếng Việt — phục vụ Print Format theo TT99/2025.

`frappe.utils.money_in_words` không đọc đúng tiếng Việt; TT99 yêu cầu chứng từ có
số tiền bằng chữ. Hàm `dong_in_words` trả chuỗi kiểu:
  1.234.000 -> "Một triệu hai trăm ba mươi bốn nghìn đồng"
"""

from frappe.utils import flt

_ONES = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]


def _read_three(num: int, full: bool) -> str:
    """Đọc khối 3 chữ số (0..999). `full`=True thì đọc cả 'không trăm' khi có khối
    lớn hơn phía trước (vd 1.005 -> 'một nghìn không trăm lẻ năm')."""
    tram, chuc, donvi = num // 100, (num % 100) // 10, num % 10
    parts = []
    if tram > 0:
        parts.append(f"{_ONES[tram]} trăm")
    elif full and (chuc > 0 or donvi > 0):
        parts.append("không trăm")

    if chuc > 1:
        parts.append(f"{_ONES[chuc]} mươi")
        if donvi == 1:
            parts.append("mốt")
        elif donvi == 5:
            parts.append("lăm")
        elif donvi > 0:
            parts.append(_ONES[donvi])
    elif chuc == 1:
        parts.append("mười")
        if donvi == 5:
            parts.append("lăm")
        elif donvi > 0:
            parts.append(_ONES[donvi])
    elif chuc == 0 and donvi > 0:
        if tram > 0 or (full and tram == 0):
            parts.append("lẻ")
        parts.append(_ONES[donvi])
    return " ".join(parts)


_SCALES = ["", " nghìn", " triệu", " tỷ"]


def dong_in_words(amount) -> str:
    """Đọc số tiền VND bằng chữ (làm tròn xuống tới đồng). Hỗ trợ tới hàng nghìn tỷ."""
    n = int(flt(amount))
    if n == 0:
        return "Không đồng"

    # Tách thành các khối 3 chữ số từ phải sang: [tỷ, triệu, nghìn, đơn vị]
    groups = []
    while n > 0:
        groups.append(n % 1000)
        n //= 1000

    words = []
    ngroups = len(groups)
    for idx in range(ngroups - 1, -1, -1):
        g = groups[idx]
        # 'full' = có khối lớn hơn đứng trước và khối này khác cách đầu chuỗi
        is_first_spoken = (idx == ngroups - 1)
        if g == 0:
            continue
        chunk = _read_three(g, full=not is_first_spoken)
        scale = _SCALES[idx] if idx < len(_SCALES) else _read_scale(idx)
        words.append(chunk + scale)

    text = " ".join(words).strip()
    text = " ".join(text.split())  # gộp khoảng trắng thừa
    return text[0].upper() + text[1:] + " đồng"


def _read_scale(idx: int) -> str:
    # idx >= 4: tỷ lũy tiến — vd 4 -> ' nghìn tỷ', 5 -> ' triệu tỷ'
    base = idx % 3
    ty_count = idx // 3
    return _SCALES[base] + (" tỷ" * ty_count)
