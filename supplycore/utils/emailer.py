"""Helper dựng email thông báo CHI TIẾT, nhất quán cho toàn SupplyCore.

Mọi email nghiệp vụ nên đi qua đây để đảm bảo:
- Có bảng THÔNG TIN PHIẾU (mã, đối tác, ngày, giá trị, trạng thái...).
- Có dòng NGƯỜI THỰC HIỆN/DUYỆT + thời gian (audit).
- Có nút "Xem phiếu" trỏ ĐÚNG SPA nội bộ (/supplycore/doc/...), không phải Frappe Desk.
"""

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import format_datetime, get_url, now_datetime

BRAND = "SupplyCore"
_ACCENT = "#2456C9"
_NAVY = "#0F2244"


def sc_doc_url(doctype: str, name: str) -> str:
    """Link tới phiếu trên SPA nội bộ (tuyệt đối, kèm domain)."""
    return get_url(f"/supplycore/doc/{quote(doctype)}/{quote(name)}")


def role_emails(roles) -> list[str]:
    """Danh sách email (enabled) của các user thuộc 1 trong các role."""
    if isinstance(roles, str):
        roles = [roles]
    if not roles:
        return []
    rows = frappe.get_all(
        "Has Role",
        filters={"role": ["in", roles], "parenttype": "User"},
        pluck="parent",
    )
    out = []
    for u in set(rows):
        if u in ("Administrator", "Guest"):
            continue
        email = frappe.db.get_value("User", u, ["email", "enabled"], as_dict=True)
        if email and email.enabled and email.email:
            out.append(email.email)
    return out


def _full_name(user: str) -> str:
    if not user:
        return ""
    return frappe.db.get_value("User", user, "full_name") or user


def _row(label, value) -> str:
    if value in (None, ""):
        return ""
    return (
        f"<tr><td style='padding:5px 16px 5px 0;color:#6b7280;font-size:13px;"
        f"white-space:nowrap;vertical-align:top'>{label}</td>"
        f"<td style='padding:5px 0;color:#111827;font-size:13px;font-weight:600'>{value}</td></tr>"
    )


def sc_list_url(doctype: str) -> str:
    """Link tới danh sách 1 doctype trên SPA nội bộ (tuyệt đối)."""
    return get_url(f"/supplycore/list/{quote(doctype)}")


def render_email(*, title, intro=None, info_rows=None, body_html=None, actor_line=None,
                 cta_label=None, cta_url=None, note=None, note_kind="info") -> str:
    """Trả HTML email nhất quán: header + intro + bảng thông tin (+ body_html tùy ý) + người duyệt + nút xem.

    body_html: HTML thô chèn thêm (vd bảng digest nhiều dòng) — đã được tin cậy/escape từ nơi gọi.
    """
    rows_html = "".join(_row(l, v) for (l, v) in (info_rows or []))
    info_block = (
        f"<table cellpadding='0' cellspacing='0' style='margin:14px 0 4px'>{rows_html}</table>"
        if rows_html else ""
    )
    body_block = f"<div style='margin:14px 0 0'>{body_html}</div>" if body_html else ""
    intro_block = f"<p style='color:#374151;font-size:14px;margin:0 0 6px'>{intro}</p>" if intro else ""
    actor_block = (
        f"<p style='color:#4b5563;font-size:13px;margin:12px 0 0'>{actor_line}</p>"
        if actor_line else ""
    )
    note_color = {"info": _ACCENT, "warn": "#9C6511", "crit": "#BE3A3A"}.get(note_kind, _ACCENT)
    note_bg = {"info": "#EAF0FC", "warn": "#F8EFDC", "crit": "#FBEBEB"}.get(note_kind, "#EAF0FC")
    note_block = (
        f"<div style='margin:14px 0 0;padding:10px 14px;background:{note_bg};"
        f"border-left:3px solid {note_color};border-radius:0 8px 8px 0;color:#374151;"
        f"font-size:13px'>{note}</div>" if note else ""
    )
    cta_block = (
        f"<p style='margin:20px 0 4px'><a href='{cta_url}' style='background:{_ACCENT};"
        f"color:#ffffff;padding:11px 22px;border-radius:8px;text-decoration:none;"
        f"font-weight:600;font-size:14px;display:inline-block'>{cta_label or 'Xem phiếu'}</a></p>"
        if cta_url else ""
    )
    return f"""
    <div style="max-width:560px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif">
      <div style="border-bottom:2px solid {_ACCENT};padding-bottom:10px;margin-bottom:16px">
        <span style="font-size:16px;font-weight:800;color:{_NAVY}">Supply<span style="color:{_ACCENT}">Core</span></span>
        <span style="font-size:11px;color:#9ca3af;letter-spacing:.12em;text-transform:uppercase;margin-left:8px">Thông báo hệ thống</span>
      </div>
      <h2 style="font-size:17px;color:{_NAVY};margin:0 0 8px">{title}</h2>
      {intro_block}
      {info_block}
      {body_block}
      {actor_block}
      {note_block}
      {cta_block}
      <p style="margin:22px 0 0;padding-top:12px;border-top:1px solid #e5e7eb;color:#9ca3af;font-size:11px">
        Email tự động từ hệ thống SupplyCore · Miyano Việt Nam. Vui lòng không trả lời email này.
      </p>
    </div>
    """


def send_doc_email(*, doctype, name, recipients, subject, title,
                   intro=None, info_rows=None, actor=None, action=None,
                   note=None, note_kind="info", cta_label="Xem phiếu",
                   now=False, delayed=True) -> None:
    """Gửi 1 email thông báo CHI TIẾT gắn với 1 phiếu.

    - actor + action → dòng "‹action› bởi ‹Họ tên› lúc ‹thời gian›".
    - Tự gắn nút "Xem phiếu" trỏ SPA.
    """
    recipients = [r for r in (recipients or []) if r]
    if not recipients:
        return
    actor_line = None
    if actor or action:
        actor_line = (
            f"{action or ''} bởi <b>{_full_name(actor)}</b> lúc "
            f"{format_datetime(now_datetime(), 'dd/MM/yyyy HH:mm')}"
        ).strip()
    html = render_email(
        title=title, intro=intro, info_rows=info_rows, actor_line=actor_line,
        cta_label=cta_label, cta_url=sc_doc_url(doctype, name), note=note, note_kind=note_kind,
    )
    frappe.sendmail(recipients=recipients, subject=subject, message=html,
                    now=now, delayed=delayed)


def send_email(*, recipients, subject, title, intro=None, info_rows=None,
               body_html=None, note=None, note_kind="info", cta_url=None,
               cta_label=None, now=False, delayed=True) -> None:
    """Gửi email thông báo CHI TIẾT KHÔNG gắn 1 phiếu cụ thể (digest, cảnh báo, danh sách).

    cta_url: link tùy ý (vd danh sách SPA qua sc_list_url) — không bắt buộc.
    """
    recipients = [r for r in (recipients or []) if r]
    if not recipients:
        return
    html = render_email(
        title=title, intro=intro, info_rows=info_rows, body_html=body_html,
        cta_label=cta_label, cta_url=cta_url, note=note, note_kind=note_kind,
    )
    frappe.sendmail(recipients=recipients, subject=subject, message=html,
                    now=now, delayed=delayed)
