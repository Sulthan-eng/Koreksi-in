import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { PESAN_KODE } from "../api/pesan.js";
import {
  DAFTAR_PAKET_PRO,
  JEDA_POLLING_TRANSAKSI_MS,
  MAKS_PERCOBAAN_POLLING_TRANSAKSI,
  ambilTransaksiTerakhir,
  dapatkanPaketPro,
  formatMetodePembayaran,
  formatRingkasanPaket,
  formatRingkasanTransaksi,
  formatTanggalJamWib,
  formatTanggalSingkatWib,
  labelTombolLangganan,
  langkahPollingTransaksi,
  namaPaketTransaksi,
  pecahPesanPenolakanLangganan,
} from "./langganan.js";

describe("paket Pro dan ringkasan", () => {
  it("memuat paket 1 bulan (30 hari, Rp 30.000) dan 3 bulan (90 hari, Rp 80.000)", () => {
    assert.equal(DAFTAR_PAKET_PRO.length, 2);
    assert.equal(
      formatRingkasanPaket("pro_1_bulan"),
      "1 bulan (30 hari), Rp 30.000",
    );
    assert.equal(
      formatRingkasanPaket("pro_3_bulan"),
      "3 bulan (90 hari), Rp 80.000",
    );
    assert.equal(dapatkanPaketPro("tidak_dikenal").kode, "pro_1_bulan");
  });

  it("memformat ringkasan transaksi dengan keterangan hari", () => {
    assert.equal(
      formatRingkasanTransaksi({ paket: "pro_1_bulan", nominal: 30000 }),
      "1 bulan (30 hari), Rp 30.000",
    );
    assert.equal(
      formatRingkasanTransaksi({ paket: "pro_3_bulan", nominal: 80000 }),
      "3 bulan (90 hari), Rp 80.000",
    );
  });
});

describe("labelTombolLangganan dan ambilTransaksiTerakhir", () => {
  it("mengembalikan Upgrade ke Pro untuk Free dan Perpanjang Pro untuk Pro", () => {
    assert.equal(labelTombolLangganan("free"), "Upgrade ke Pro");
    assert.equal(labelTombolLangganan(null), "Upgrade ke Pro");
    assert.equal(labelTombolLangganan(undefined), "Upgrade ke Pro");
    assert.equal(labelTombolLangganan("pro"), "Perpanjang Pro");
  });

  it("mengambil elemen pertama sebagai transaksi terakhir atau null bila kosong", () => {
    assert.equal(ambilTransaksiTerakhir([]), null);
    assert.equal(ambilTransaksiTerakhir(null), null);
    const t1 = { id_transaksi: "1", status: "menunggu" };
    const t2 = { id_transaksi: "2", status: "berhasil" };
    assert.deepEqual(ambilTransaksiTerakhir([t1, t2]), t1);
  });
});

describe("langkahPollingTransaksi", () => {
  it("memakai jeda 3 detik dan maksimal 10 percobaan secara default", () => {
    assert.equal(JEDA_POLLING_TRANSAKSI_MS, 3000);
    assert.equal(MAKS_PERCOBAAN_POLLING_TRANSAKSI, 10);
  });

  it("berhenti dan meminta muat ulang profil saat transaksi berubah jadi berhasil", () => {
    const hasil = langkahPollingTransaksi({
      statusTransaksi: "berhasil",
      percobaanSaatIni: 2,
      gagalBeruntunSaatIni: 1,
      berhasil: true,
    });
    assert.deepEqual(hasil, {
      percobaan: 3,
      gagalBeruntun: 0,
      berhenti: true,
      belumTerkonfirmasi: false,
      perluMuatUlangProfil: true,
    });
  });

  it("berhenti tanpa muat ulang profil saat transaksi menjadi gagal atau kedaluwarsa", () => {
    for (const status of ["gagal", "kedaluwarsa"]) {
      const hasil = langkahPollingTransaksi({
        statusTransaksi: status,
        percobaanSaatIni: 1,
        gagalBeruntunSaatIni: 0,
        berhasil: true,
      });
      assert.deepEqual(hasil, {
        percobaan: 2,
        gagalBeruntun: 0,
        berhenti: true,
        belumTerkonfirmasi: false,
        perluMuatUlangProfil: false,
      });
    }
  });

  it("terus berjalan selama masih menunggu di bawah batas percobaan, lalu berhenti dengan penanda belumTerkonfirmasi pada percobaan ke-10", () => {
    const langkahKe9 = langkahPollingTransaksi({
      statusTransaksi: "menunggu",
      percobaanSaatIni: 8,
      gagalBeruntunSaatIni: 0,
      berhasil: true,
    });
    assert.deepEqual(langkahKe9, {
      percobaan: 9,
      gagalBeruntun: 0,
      berhenti: false,
      belumTerkonfirmasi: false,
      perluMuatUlangProfil: false,
    });

    const langkahKe10 = langkahPollingTransaksi({
      statusTransaksi: "menunggu",
      percobaanSaatIni: 9,
      gagalBeruntunSaatIni: 0,
      berhasil: true,
    });
    assert.deepEqual(langkahKe10, {
      percobaan: 10,
      gagalBeruntun: 0,
      berhenti: true,
      belumTerkonfirmasi: true,
      perluMuatUlangProfil: false,
    });
  });

  it("mengabaikan gagal jaringan ke-1 dan ke-2 lalu berhenti dengan belumTerkonfirmasi pada gagal ke-3 beruntun", () => {
    const g1 = langkahPollingTransaksi({
      statusTransaksi: "menunggu",
      percobaanSaatIni: 0,
      gagalBeruntunSaatIni: 0,
      berhasil: false,
    });
    assert.deepEqual(g1, {
      percobaan: 1,
      gagalBeruntun: 1,
      berhenti: false,
      belumTerkonfirmasi: false,
      perluMuatUlangProfil: false,
    });

    const g2 = langkahPollingTransaksi({
      statusTransaksi: "menunggu",
      percobaanSaatIni: g1.percobaan,
      gagalBeruntunSaatIni: g1.gagalBeruntun,
      berhasil: false,
    });
    assert.deepEqual(g2, {
      percobaan: 2,
      gagalBeruntun: 2,
      berhenti: false,
      belumTerkonfirmasi: false,
      perluMuatUlangProfil: false,
    });

    const g3 = langkahPollingTransaksi({
      statusTransaksi: "menunggu",
      percobaanSaatIni: g2.percobaan,
      gagalBeruntunSaatIni: g2.gagalBeruntun,
      berhasil: false,
    });
    assert.deepEqual(g3, {
      percobaan: 3,
      gagalBeruntun: 3,
      berhenti: true,
      belumTerkonfirmasi: true,
      perluMuatUlangProfil: false,
    });
  });
});

describe("pecahPesanPenolakanLangganan", () => {
  it("memecah konstanta PESAN_KODE.BATAS_BATCH_AKTIF_TERCAPAI dengan tautan Upgrade ke Pro", () => {
    const hasil = pecahPesanPenolakanLangganan(
      "BATAS_BATCH_AKTIF_TERCAPAI",
      PESAN_KODE.BATAS_BATCH_AKTIF_TERCAPAI,
    );
    assert.deepEqual(hasil, {
      awalan: "Batas batch aktif untuk akun Free telah tercapai. ",
      teksTautan: "Upgrade ke Pro",
      akhiran: " untuk batch tidak terbatas.",
    });
    assert.equal(
      `${hasil.awalan}${hasil.teksTautan}${hasil.akhiran}`,
      PESAN_KODE.BATAS_BATCH_AKTIF_TERCAPAI,
    );
  });

  it("memecah konstanta PESAN_KODE.BATAS_JAWABAN_TERLAMPAUI (Free) dan pesan server dengan sisa N slot", () => {
    const dariKonstanta = pecahPesanPenolakanLangganan(
      "BATAS_JAWABAN_TERLAMPAUI",
      PESAN_KODE.BATAS_JAWABAN_TERLAMPAUI,
    );
    assert.deepEqual(dariKonstanta, {
      awalan:
        "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 0 slot. Kurangi jumlah file atau ",
      teksTautan: "upgrade ke Pro",
      akhiran: ".",
    });
    assert.equal(
      `${dariKonstanta.awalan}${dariKonstanta.teksTautan}${dariKonstanta.akhiran}`,
      PESAN_KODE.BATAS_JAWABAN_TERLAMPAUI,
    );

    const pesanServerSisa3 =
      "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 3 slot. Kurangi jumlah file atau upgrade ke Pro.";
    const dariServer = pecahPesanPenolakanLangganan(
      "BATAS_JAWABAN_TERLAMPAUI",
      pesanServerSisa3,
    );
    assert.deepEqual(dariServer, {
      awalan:
        "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 3 slot. Kurangi jumlah file atau ",
      teksTautan: "upgrade ke Pro",
      akhiran: ".",
    });
  });

  it("mengembalikan null untuk BATAS_JAWABAN_TERLAMPAUI milik akun Pro", () => {
    const pesanPro =
      "Upload ditolak: batas jawaban akun Pro adalah 50, tersisa 2 slot. Kurangi jumlah file.";
    assert.equal(
      pecahPesanPenolakanLangganan("BATAS_JAWABAN_TERLAMPAUI", pesanPro),
      null,
    );
  });

  it("memecah konstanta PESAN_KODE.EKSPOR_KHUSUS_PRO dengan tautan Upgrade", () => {
    const hasil = pecahPesanPenolakanLangganan(
      "EKSPOR_KHUSUS_PRO",
      PESAN_KODE.EKSPOR_KHUSUS_PRO,
    );
    assert.deepEqual(hasil, {
      awalan: "Fitur ekspor hanya tersedia untuk akun Pro. ",
      teksTautan: "Upgrade",
      akhiran: " untuk mengakses fitur ini.",
    });
    assert.equal(
      `${hasil.awalan}${hasil.teksTautan}${hasil.akhiran}`,
      PESAN_KODE.EKSPOR_KHUSUS_PRO,
    );
  });

  it("menolak kode error lain meski isi teksnya mengandung kata Upgrade", () => {
    assert.equal(
      pecahPesanPenolakanLangganan(
        "GAGAL_BUAT_BATCH",
        PESAN_KODE.BATAS_BATCH_AKTIF_TERCAPAI,
      ),
      null,
    );
    assert.equal(
      pecahPesanPenolakanLangganan(null, PESAN_KODE.EKSPOR_KHUSUS_PRO),
      null,
    );
    assert.equal(
      pecahPesanPenolakanLangganan("GAGAL_EKSPOR", PESAN_KODE.GAGAL_EKSPOR),
      null,
    );
  });
});

describe("fungsi murni riwayat transaksi dan invoice", () => {
  it("memetakan kode paket ke nama paket tampilan riwayat transaksi", () => {
    assert.equal(namaPaketTransaksi("pro_1_bulan"), "Langganan Pro 1 Bulan");
    assert.equal(namaPaketTransaksi("pro_3_bulan"), "Langganan Pro 3 Bulan");
    assert.equal(namaPaketTransaksi("tidak_dikenal"), "Langganan Pro 1 Bulan");
  });

  it("memformat tanggal singkat WIB untuk riwayat transaksi", () => {
    assert.equal(
      formatTanggalSingkatWib("2026-11-27T03:46:00Z"),
      "27 Nov 2026",
    );
    // 17.00 UTC = 00.00 WIB hari berikutnya
    assert.equal(
      formatTanggalSingkatWib("2026-11-26T17:00:00Z"),
      "27 Nov 2026",
    );
    assert.equal(formatTanggalSingkatWib(null), "");
    assert.equal(formatTanggalSingkatWib("bukan-tanggal"), "");
  });

  it("memformat tanggal dan jam WIB untuk halaman invoice", () => {
    assert.equal(
      formatTanggalJamWib("2026-11-27T03:46:00Z"),
      "27 November 2026, 10.46 WIB",
    );
    assert.equal(
      formatTanggalJamWib("2026-11-26T17:05:00Z"),
      "27 November 2026, 00.05 WIB",
    );
    assert.equal(formatTanggalJamWib(""), "");
    assert.equal(formatTanggalJamWib("bukan-tanggal"), "");
  });

  it("memformat metode pembayaran dengan tanda strip bila kosong", () => {
    assert.equal(formatMetodePembayaran("Transfer Bank"), "Transfer Bank");
    assert.equal(formatMetodePembayaran("QRIS"), "QRIS");
    assert.equal(formatMetodePembayaran(null), "-");
    assert.equal(formatMetodePembayaran(undefined), "-");
    assert.equal(formatMetodePembayaran(""), "-");
    assert.equal(formatMetodePembayaran("   "), "-");
  });
});
