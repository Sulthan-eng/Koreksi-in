import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  buatPesanKendalaPembayaran,
  buatTautanWhatsAppAdmin,
} from "./kontakAdmin.js";

describe("buatPesanKendalaPembayaran", () => {
  it("menyertakan nama, email, dan rincian transaksi lengkap", () => {
    const pesan = buatPesanKendalaPembayaran({
      nama: "Budi Santoso",
      email: "budi@contoh.com",
      transaksi: {
        paket: "pro_1_bulan",
        nominal: 30000,
        status: "menunggu",
        dibuat_pada: "2026-11-27T05:30:00Z",
        id_order: "KRS-abc123",
      },
    });
    const baris = pesan.split("\n");

    // Format jam dari Intl id-ID (kata "pukul", pemisah jam) bisa berbeda
    // antar versi ICU/Node, jadi baris ini dicek dengan pola toleran,
    // sedangkan baris lain tetap dibandingkan persis termasuk urutannya.
    assert.deepEqual(
      [baris[0], baris[1], baris[2], baris[3], baris[4], baris[5], baris[7]],
      [
        "Halo Admin Koreksi-in, saya mengalami kendala pembayaran.",
        "Nama: Budi Santoso",
        "Email akun: budi@contoh.com",
        "Paket: 1 bulan (30 hari), Rp 30.000",
        "Nominal: Rp 30.000",
        "Status: Menunggu",
        "Order ID: KRS-abc123",
      ],
    );
    assert.equal(baris.length, 8);
    assert.match(
      baris[6],
      /^Waktu transaksi: 27 November 2026 (pukul )?12[.:]30 WIB$/,
    );
  });

  it("melewati seluruh baris transaksi bila tidak ada transaksi", () => {
    const pesan = buatPesanKendalaPembayaran({
      nama: "Budi Santoso",
      email: "budi@contoh.com",
    });

    assert.equal(
      pesan,
      [
        "Halo Admin Koreksi-in, saya mengalami kendala pembayaran.",
        "Nama: Budi Santoso",
        "Email akun: budi@contoh.com",
      ].join("\n"),
    );
    assert.ok(!pesan.includes("undefined"));
  });

  it("melewati baris nama/email bila tidak ada, dan tidak pernah menulis 'undefined'", () => {
    const pesan = buatPesanKendalaPembayaran({});

    assert.equal(
      pesan,
      "Halo Admin Koreksi-in, saya mengalami kendala pembayaran.",
    );
    assert.ok(!pesan.includes("undefined"));
  });

  it("melewati baris transaksi yang datanya kosong satu per satu", () => {
    const pesan = buatPesanKendalaPembayaran({
      nama: "Budi",
      email: "budi@contoh.com",
      transaksi: { status: "berhasil" },
    });

    assert.equal(
      pesan,
      [
        "Halo Admin Koreksi-in, saya mengalami kendala pembayaran.",
        "Nama: Budi",
        "Email akun: budi@contoh.com",
        "Status: Berhasil",
      ].join("\n"),
    );
  });
});

describe("buatTautanWhatsAppAdmin", () => {
  it("membuat tautan wa.me dengan pesan ter-encode", () => {
    const tautan = buatTautanWhatsAppAdmin({
      nomor: "628123456789",
      pesan: "Halo Admin, saya butuh bantuan & info.",
    });

    assert.equal(
      tautan,
      "https://wa.me/628123456789?text=Halo%20Admin%2C%20saya%20butuh%20bantuan%20%26%20info.",
    );
  });

  it("membersihkan nomor dari spasi, plus, dan strip", () => {
    const tautan = buatTautanWhatsAppAdmin({
      nomor: "+62 812-3456-789",
      pesan: "Tes",
    });

    assert.equal(tautan, "https://wa.me/628123456789?text=Tes");
  });

  it("mengembalikan null bila nomor kosong atau kosong setelah dibersihkan", () => {
    assert.equal(buatTautanWhatsAppAdmin({ nomor: "", pesan: "Tes" }), null);
    assert.equal(
      buatTautanWhatsAppAdmin({ nomor: undefined, pesan: "Tes" }),
      null,
    );
    assert.equal(
      buatTautanWhatsAppAdmin({ nomor: "  +  --  ", pesan: "Tes" }),
      null,
    );
  });

  it("meng-encode karakter khusus pada emoji dan tanda baca", () => {
    const tautan = buatTautanWhatsAppAdmin({
      nomor: "628123456789",
      pesan: "Kendala 😀 / pembayaran?",
    });

    assert.equal(
      tautan,
      `https://wa.me/628123456789?text=${encodeURIComponent("Kendala 😀 / pembayaran?")}`,
    );
  });
});
