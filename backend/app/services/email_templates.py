"""Isi (subjek, HTML, teks polos) email FR30, dipisah dari logika pengiriman
di app/services/email.py. Modul ini hanya menyusun string -- tidak pernah
mengimpor smtplib atau menyentuh jaringan -- jadi desain emailnya bisa
diganti di sini tanpa menyentuh email.py.
"""

from __future__ import annotations

import html
from dataclasses import dataclass


@dataclass(frozen=True)
class IsiEmail:
    subjek: str
    html: str
    teks: str


def email_pembayaran_berhasil(
    *, nama: str, nomor_invoice: str, nama_paket: str, nominal: int, tautan_invoice: str
) -> IsiEmail:
    rupiah = f"Rp{nominal:,}".replace(",", ".")
    nama_aman = html.escape(nama)
    return IsiEmail(
        subjek="Pembayaran Koreksi-in berhasil",
        html=f"""
        <p>Halo {nama_aman},</p>
        <p>Pembayaran Anda untuk <strong>{nama_paket}</strong> sebesar <strong>{rupiah}</strong>
        telah berhasil. Nomor invoice: <strong>{nomor_invoice}</strong>.</p>
        <p><a href="{tautan_invoice}">Lihat invoice</a></p>
        """,
        teks=(
            f"Halo {nama},\n\n"
            f"Pembayaran Anda untuk {nama_paket} sebesar {rupiah} telah berhasil.\n"
            f"Nomor invoice: {nomor_invoice}.\n\n"
            f"Lihat invoice: {tautan_invoice}"
        ),
    )


def email_pembayaran_kedaluwarsa(
    *, nama: str, nomor_invoice: str, nama_paket: str, nominal: int, tautan_langganan: str
) -> IsiEmail:
    rupiah = f"Rp{nominal:,}".replace(",", ".")
    nama_aman = html.escape(nama)
    return IsiEmail(
        subjek="Pembayaran Koreksi-in kedaluwarsa",
        html=f"""
        <p>Halo {nama_aman},</p>
        <p>Pembayaran Anda untuk <strong>{nama_paket}</strong> sebesar <strong>{rupiah}</strong>
        (nomor invoice {nomor_invoice}) sudah kedaluwarsa dan tidak diproses.</p>
        <p><a href="{tautan_langganan}">Buka halaman Langganan</a> untuk mencoba lagi.</p>
        """,
        teks=(
            f"Halo {nama},\n\n"
            f"Pembayaran Anda untuk {nama_paket} sebesar {rupiah} "
            f"(nomor invoice {nomor_invoice}) sudah kedaluwarsa dan tidak diproses.\n\n"
            f"Buka halaman Langganan untuk mencoba lagi: {tautan_langganan}"
        ),
    )
