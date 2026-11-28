"""Isi (subjek, HTML, teks polos) email FR30, dipisah dari logika pengiriman
di app/services/email.py. Modul ini hanya menyusun string -- tidak pernah
mengimpor smtplib atau menyentuh jaringan -- jadi desain emailnya bisa
diganti di sini tanpa menyentuh email.py.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

_ZONA_WIB = timezone(timedelta(hours=7))

_NAMA_BULAN = (
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
)

_GAYA_BODY = (
    "margin:0; padding:0; background-color:#F4F8FB; "
    "font-family: Arial, Helvetica, sans-serif; color:#0F2A43;"
)
_GAYA_KARTU = (
    "width:600px; max-width:600px; background-color:#FFFFFF; "
    "border:1px solid #D5E1EB; border-radius:8px;"
)
_GAYA_LOGO = "display:block; border:0; width:40px; height:40px;"
_GAYA_TEKS_MEREK = (
    "vertical-align:middle; padding-left:12px; font-size:18px; font-weight:bold; color:#0F2A43;"
)
_GAYA_JUDUL = "margin:16px 0 0; font-size:24px; line-height:32px; font-weight:bold; color:#0F2A43;"
_GAYA_SAPAAN = "margin:20px 0 0; font-size:16px; line-height:24px; color:#0F2A43;"
_GAYA_PARAGRAF = "margin:12px 0 0; font-size:16px; line-height:24px; color:#0F2A43;"
_GAYA_SEL_LABEL = (
    "padding:12px 0; border-top:1px solid #D5E1EB; font-size:14px; line-height:20px; color:#475569;"
)
_GAYA_SEL_NILAI = (
    "padding:12px 0; border-top:1px solid #D5E1EB; "
    "font-size:14px; line-height:20px; font-weight:bold; color:#0F2A43;"
)
_GAYA_SEL_LABEL_AKHIR = (
    "padding:12px 0; border-top:1px solid #D5E1EB; border-bottom:1px solid #D5E1EB; "
    "font-size:14px; line-height:20px; color:#475569;"
)
_GAYA_SEL_NILAI_AKHIR = (
    "padding:12px 0; border-top:1px solid #D5E1EB; border-bottom:1px solid #D5E1EB; "
    "font-size:14px; line-height:20px; font-weight:bold; color:#0F2A43;"
)
_GAYA_TOMBOL = (
    "display:inline-block; padding:12px 24px; font-size:16px; line-height:20px; "
    "font-weight:bold; color:#FFFFFF; text-decoration:none; border-radius:8px;"
)
_GAYA_CATATAN_KAKI = (
    "margin:32px 0 0; padding-top:20px; border-top:1px solid #D5E1EB; "
    "font-size:13px; line-height:18px; color:#475569;"
)


@dataclass(frozen=True)
class IsiEmail:
    subjek: str
    html: str
    teks: str


def format_tanggal_wib(waktu: datetime) -> str:
    """Format waktu ke '27 November 2026, 10.46 WIB' memakai selisih tetap
    UTC+7 (tanpa zoneinfo agar tidak bergantung pada tzdata di image produksi)."""
    if waktu.tzinfo is None:
        waktu = waktu.replace(tzinfo=UTC)
    wib = waktu.astimezone(_ZONA_WIB)
    nama_bulan = _NAMA_BULAN[wib.month - 1]
    return f"{wib.day} {nama_bulan} {wib.year}, {wib.hour:02d}.{wib.minute:02d} WIB"


def _format_rupiah(nominal: int) -> str:
    return f"Rp {nominal:,}".replace(",", ".")


def _url_logo(frontend_url: str, tautan_fallback: str) -> str:
    dasar = frontend_url.strip().rstrip("/")
    if not dasar:
        for pemisah in ("/invoice/", "/langganan"):
            if pemisah in tautan_fallback:
                dasar = tautan_fallback.split(pemisah, 1)[0].rstrip("/")
                break
    return f"{dasar}/logo-ikon.png" if dasar else "logo-ikon.png"


def email_pembayaran_berhasil(
    *,
    nama: str,
    nomor_invoice: str,
    nama_paket: str,
    nominal: int,
    dibayar_pada: datetime,
    tautan_invoice: str,
    frontend_url: str = "",
) -> IsiEmail:
    rupiah = _format_rupiah(nominal)
    tanggal_wib = format_tanggal_wib(dibayar_pada)
    nama_aman = html.escape(nama)
    nomor_aman = html.escape(nomor_invoice)
    paket_aman = html.escape(nama_paket)
    tautan_aman = html.escape(tautan_invoice, quote=True)
    logo_aman = html.escape(_url_logo(frontend_url, tautan_invoice), quote=True)
    gaya_lencana = (
        "display:inline-block; background-color:#DCFCE7; color:#166534; "
        "border-radius:999px; padding:3px 12px; font-size:13px; "
        "line-height:18px; font-weight:bold;"
    )

    isi_html = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<title>Pembayaran diterima - Koreksi-in</title>
<style>
  @media only screen and (max-width: 620px) {{
    .kartu {{ width: 100% !important; max-width: 100% !important; }}
    .isi {{ padding: 24px 20px !important; }}
    .judul {{ font-size: 22px !important; line-height: 30px !important; }}
  }}
</style>
</head>
<body style="{_GAYA_BODY}">

<div style="display:none; max-height:0; overflow:hidden; mso-hide:all;">\
Pembayaran {paket_aman} sudah kami terima. Ringkasannya ada di dalam email.</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" \
style="background-color:#F4F8FB;">
  <tr>
    <td align="center" style="padding:24px 12px;">

      <table role="presentation" class="kartu" width="600" cellpadding="0" \
cellspacing="0" border="0" style="{_GAYA_KARTU}">
        <tr>
          <td class="isi" style="padding:32px 40px;">

            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="vertical-align:middle;">
                  <img src="{logo_aman}" width="40" height="40" \
alt="Logo Koreksi-in" style="{_GAYA_LOGO}">
                </td>
                <td style="{_GAYA_TEKS_MEREK}">Koreksi-in</td>
              </tr>
            </table>

            <p style="margin:24px 0 0;">
              <span style="{gaya_lencana}">LUNAS</span>
            </p>

            <h1 class="judul" style="{_GAYA_JUDUL}">Pembayaran Anda sudah diterima</h1>

            <p style="{_GAYA_SAPAAN}">Halo {nama_aman},</p>
            <p style="{_GAYA_PARAGRAF}">Terima kasih, pembayaran Anda sudah kami terima. \
{paket_aman} Anda sekarang aktif. Ringkasannya ada di bawah.</p>

            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" \
border="0" style="margin-top:24px;">
              <tr>
                <td style="{_GAYA_SEL_LABEL}">No. invoice</td>
                <td align="right" style="{_GAYA_SEL_NILAI}">{nomor_aman}</td>
              </tr>
              <tr>
                <td style="{_GAYA_SEL_LABEL}">Paket</td>
                <td align="right" style="{_GAYA_SEL_NILAI}">{paket_aman}</td>
              </tr>
              <tr>
                <td style="{_GAYA_SEL_LABEL}">Total</td>
                <td align="right" style="{_GAYA_SEL_NILAI}">{rupiah}</td>
              </tr>
              <tr>
                <td style="{_GAYA_SEL_LABEL_AKHIR}">Dibayar pada</td>
                <td align="right" style="{_GAYA_SEL_NILAI_AKHIR}">{tanggal_wib}</td>
              </tr>
            </table>

            <table role="presentation" cellpadding="0" cellspacing="0" border="0" \
style="margin-top:28px;">
              <tr>
                <td align="center" bgcolor="#0F6DB5" \
style="border-radius:8px; background-color:#0F6DB5;">
                  <a href="{tautan_aman}" style="{_GAYA_TOMBOL}">Lihat invoice</a>
                </td>
              </tr>
            </table>

            <p style="{_GAYA_CATATAN_KAKI}">Email ini dikirim otomatis oleh Koreksi-in. \
Mohon tidak membalas email ini.</p>

          </td>
        </tr>
      </table>

    </td>
  </tr>
</table>

</body>
</html>"""

    isi_teks = (
        "Pembayaran Anda sudah diterima\n\n"
        f"Halo {nama},\n\n"
        f"Terima kasih, pembayaran Anda sudah kami terima. {nama_paket} Anda sekarang aktif. "
        "Ringkasannya ada di bawah.\n\n"
        f"No. invoice: {nomor_invoice}\n"
        f"Paket: {nama_paket}\n"
        f"Total: {rupiah}\n"
        f"Dibayar pada: {tanggal_wib}\n\n"
        f"Lihat invoice: {tautan_invoice}\n\n"
        "Email ini dikirim otomatis oleh Koreksi-in. Mohon tidak membalas email ini."
    )

    return IsiEmail(
        subjek="Pembayaran Koreksi-in berhasil",
        html=isi_html,
        teks=isi_teks,
    )


def email_pembayaran_kedaluwarsa(
    *,
    nama: str,
    nomor_invoice: str,
    nama_paket: str,
    nominal: int,
    tautan_langganan: str,
    frontend_url: str = "",
) -> IsiEmail:
    rupiah = _format_rupiah(nominal)
    nama_aman = html.escape(nama)
    nomor_aman = html.escape(nomor_invoice)
    paket_aman = html.escape(nama_paket)
    tautan_aman = html.escape(tautan_langganan, quote=True)
    logo_aman = html.escape(_url_logo(frontend_url, tautan_langganan), quote=True)
    gaya_lencana = (
        "display:inline-block; background-color:#F4F8FB; color:#475569; "
        "border:1px solid #D5E1EB; border-radius:999px; padding:2px 12px; "
        "font-size:13px; line-height:18px; font-weight:bold;"
    )

    isi_html = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<title>Pesanan kedaluwarsa - Koreksi-in</title>
<style>
  @media only screen and (max-width: 620px) {{
    .kartu {{ width: 100% !important; max-width: 100% !important; }}
    .isi {{ padding: 24px 20px !important; }}
    .judul {{ font-size: 22px !important; line-height: 30px !important; }}
  }}
</style>
</head>
<body style="{_GAYA_BODY}">

<div style="display:none; max-height:0; overflow:hidden; mso-hide:all;">\
Batas waktu pembayaran {paket_aman} sudah lewat. Anda bisa membuat pesanan baru kapan saja.</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" \
style="background-color:#F4F8FB;">
  <tr>
    <td align="center" style="padding:24px 12px;">

      <table role="presentation" class="kartu" width="600" cellpadding="0" \
cellspacing="0" border="0" style="{_GAYA_KARTU}">
        <tr>
          <td class="isi" style="padding:32px 40px;">

            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="vertical-align:middle;">
                  <img src="{logo_aman}" width="40" height="40" \
alt="Logo Koreksi-in" style="{_GAYA_LOGO}">
                </td>
                <td style="{_GAYA_TEKS_MEREK}">Koreksi-in</td>
              </tr>
            </table>

            <p style="margin:24px 0 0;">
              <span style="{gaya_lencana}">KEDALUWARSA</span>
            </p>

            <h1 class="judul" style="{_GAYA_JUDUL}">Pesanan Anda sudah kedaluwarsa</h1>

            <p style="{_GAYA_SAPAAN}">Halo {nama_aman},</p>
            <p style="{_GAYA_PARAGRAF}">Batas waktu pembayaran untuk pesanan berikut sudah lewat, \
jadi pesanan ini tidak lagi aktif. Anda bisa membuat pesanan baru kapan saja dari \
halaman Langganan.</p>

            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" \
border="0" style="margin-top:24px;">
              <tr>
                <td style="{_GAYA_SEL_LABEL}">Paket</td>
                <td align="right" style="{_GAYA_SEL_NILAI}">{paket_aman}</td>
              </tr>
              <tr>
                <td style="{_GAYA_SEL_LABEL}">Nominal</td>
                <td align="right" style="{_GAYA_SEL_NILAI}">{rupiah}</td>
              </tr>
              <tr>
                <td style="{_GAYA_SEL_LABEL_AKHIR}">No. pesanan</td>
                <td align="right" style="{_GAYA_SEL_NILAI_AKHIR}">{nomor_aman}</td>
              </tr>
            </table>

            <table role="presentation" cellpadding="0" cellspacing="0" border="0" \
style="margin-top:28px;">
              <tr>
                <td align="center" bgcolor="#0F6DB5" \
style="border-radius:8px; background-color:#0F6DB5;">
                  <a href="{tautan_aman}" style="{_GAYA_TOMBOL}">Kembali ke Langganan</a>
                </td>
              </tr>
            </table>

            <p style="{_GAYA_CATATAN_KAKI}">Email ini dikirim otomatis oleh Koreksi-in. \
Mohon tidak membalas email ini.</p>

          </td>
        </tr>
      </table>

    </td>
  </tr>
</table>

</body>
</html>"""

    isi_teks = (
        "Pesanan Anda sudah kedaluwarsa\n\n"
        f"Halo {nama},\n\n"
        "Batas waktu pembayaran untuk pesanan berikut sudah lewat, jadi pesanan ini tidak lagi "
        "aktif. Anda bisa membuat pesanan baru kapan saja dari halaman Langganan.\n\n"
        f"Paket: {nama_paket}\n"
        f"Nominal: {rupiah}\n"
        f"No. pesanan: {nomor_invoice}\n\n"
        f"Kembali ke Langganan: {tautan_langganan}\n\n"
        "Email ini dikirim otomatis oleh Koreksi-in. Mohon tidak membalas email ini."
    )

    return IsiEmail(
        subjek="Pembayaran Koreksi-in kedaluwarsa",
        html=isi_html,
        teks=isi_teks,
    )
