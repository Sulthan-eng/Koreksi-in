import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  apakahGalatJaringan,
  formatTanggalWib,
  hariIniWib,
  keTanggalInputWib,
  terapkanPerubahanAkun,
  validasiMasaBerlakuPro,
} from "./akunPengajar.js";

describe("formatTanggalWib dan keTanggalInputWib", () => {
  it("mempertahankan tanggal WIB untuk batas 23:59:59 WIB (16:59:59Z) tanpa geser hari", () => {
    const iso = "2026-11-30T16:59:59Z";
    assert.equal(formatTanggalWib(iso), "30 November 2026");
    assert.equal(keTanggalInputWib(iso), "2026-11-30");
  });

  it("berpindah hari tepat pada 00:00:00 WIB (17:00:00Z)", () => {
    const iso = "2026-11-30T17:00:00Z";
    assert.equal(formatTanggalWib(iso), "1 Desember 2026");
    assert.equal(keTanggalInputWib(iso), "2026-12-01");
  });

  it("mengembalikan string kosong untuk nilai kosong atau tidak valid", () => {
    assert.equal(formatTanggalWib(null), "");
    assert.equal(keTanggalInputWib(null), "");
    assert.equal(keTanggalInputWib("bukan-tanggal"), "");
  });
});

describe("hariIniWib dan validasiMasaBerlakuPro", () => {
  it("menghitung hari ini menurut zona waktu WIB (UTC+7)", () => {
    assert.equal(hariIniWib(new Date("2026-11-22T16:59:59Z")), "2026-11-22");
    assert.equal(hariIniWib(new Date("2026-11-22T17:00:00Z")), "2026-11-23");
  });

  it("menolak kosong, format salah, tanggal kalender fiktif, masa lalu, dan hari ini WIB", () => {
    const sekarang = new Date("2026-11-22T10:00:00Z"); // 17:00 WIB -> 2026-11-22
    assert.equal(validasiMasaBerlakuPro("", sekarang), false);
    assert.equal(validasiMasaBerlakuPro(null, sekarang), false);
    assert.equal(validasiMasaBerlakuPro("22-11-2026", sekarang), false);
    assert.equal(validasiMasaBerlakuPro("2026-02-30", sekarang), false);
    assert.equal(validasiMasaBerlakuPro("2026-11-21", sekarang), false);
    assert.equal(validasiMasaBerlakuPro("2026-11-22", sekarang), false);
  });

  it("menerima tanggal setelah hari ini (WIB)", () => {
    const sekarang = new Date("2026-11-22T10:00:00Z"); // 2026-11-22 WIB
    assert.equal(validasiMasaBerlakuPro("2026-11-23", sekarang), true);
    assert.equal(validasiMasaBerlakuPro("2027-01-01", sekarang), true);
  });
});

describe("terapkanPerubahanAkun", () => {
  const daftarAwal = [
    {
      id_pengguna: "1",
      nama: "Sari",
      status_langganan: "free",
      dinonaktifkan_pada: null,
    },
    {
      id_pengguna: "2",
      nama: "Budi",
      status_langganan: "free",
      dinonaktifkan_pada: null,
    },
  ];

  it("memperbarui baris di tempat saat tidak ada filter aktif", () => {
    const hasil = terapkanPerubahanAkun(daftarAwal, {
      id_pengguna: "1",
      nama: "Sari",
      status_langganan: "pro",
      dinonaktifkan_pada: null,
    });
    assert.equal(hasil.length, 2);
    assert.equal(hasil[0].status_langganan, "pro");
  });

  it("mengeluarkan baris yang tidak lagi cocok dengan filter status langganan", () => {
    const hasil = terapkanPerubahanAkun(
      daftarAwal,
      {
        id_pengguna: "1",
        nama: "Sari",
        status_langganan: "pro",
        dinonaktifkan_pada: null,
      },
      { statusLangganan: "free", statusAkun: "" },
    );
    assert.deepEqual(
      hasil.map((a) => a.id_pengguna),
      ["2"],
    );
  });

  it("mengeluarkan baris yang tidak lagi cocok dengan filter status akun", () => {
    const hasil = terapkanPerubahanAkun(
      daftarAwal,
      {
        id_pengguna: "2",
        nama: "Budi",
        status_langganan: "free",
        dinonaktifkan_pada: "2026-11-22T10:00:00Z",
      },
      { statusLangganan: "", statusAkun: "aktif" },
    );
    assert.deepEqual(
      hasil.map((a) => a.id_pengguna),
      ["1"],
    );
  });
});

describe("apakahGalatJaringan", () => {
  it("mengenali flag jaringan atau status offline", () => {
    assert.equal(
      apakahGalatJaringan({ kode: "UMUM", jaringan: true }, true),
      true,
    );
    assert.equal(apakahGalatJaringan({ kode: "UMUM" }, false), true);
    assert.equal(
      apakahGalatJaringan({ kode: "KESALAHAN_SERVER", status: 500 }, true),
      false,
    );
  });
});
