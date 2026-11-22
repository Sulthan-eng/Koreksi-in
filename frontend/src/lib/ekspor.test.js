import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { PESAN_KODE } from "../api/pesan.js";
import {
  NAMA_FILE_EKSPOR_DEFAULT,
  ekstrakNamaFileEkspor,
  pesanGalatEkspor,
} from "./ekspor.js";

describe("ekstrakNamaFileEkspor", () => {
  it("mengekstrak nama file dari Content-Disposition berpetik", () => {
    assert.equal(
      ekstrakNamaFileEkspor(
        'attachment; filename="rekap-nilai-uts-2026-11-22.xlsx"',
      ),
      "rekap-nilai-uts-2026-11-22.xlsx",
    );
  });

  it("mengekstrak nama file tanpa tanda petik dan tidak peka huruf besar", () => {
    assert.equal(
      ekstrakNamaFileEkspor("ATTACHMENT; FILENAME=rekap-nilai.xlsx; size=100"),
      "rekap-nilai.xlsx",
    );
  });

  it("mengembalikan null bila header kosong atau tanpa filename", () => {
    assert.equal(ekstrakNamaFileEkspor(null), null);
    assert.equal(ekstrakNamaFileEkspor(undefined), null);
    assert.equal(ekstrakNamaFileEkspor(""), null);
    assert.equal(ekstrakNamaFileEkspor("attachment"), null);
  });

  it("menolak nama file dengan pemisah path, traversal, atau karakter kontrol", () => {
    assert.equal(
      ekstrakNamaFileEkspor('attachment; filename="../rahasia.xlsx"'),
      null,
    );
    assert.equal(
      ekstrakNamaFileEkspor('attachment; filename="a/b.xlsx"'),
      null,
    );
    assert.equal(
      ekstrakNamaFileEkspor('attachment; filename="a\\b.xlsx"'),
      null,
    );
    assert.equal(
      ekstrakNamaFileEkspor('attachment; filename="rekap\r\n.xlsx"'),
      null,
    );
  });

  it("fallback statis bernilai rekap-nilai.xlsx", () => {
    assert.equal(NAMA_FILE_EKSPOR_DEFAULT, "rekap-nilai.xlsx");
  });
});

describe("pesanGalatEkspor", () => {
  it("mempertahankan pesan spesifik akun Free (403)", () => {
    assert.equal(
      pesanGalatEkspor({
        kode: "EKSPOR_KHUSUS_PRO",
        pesan: PESAN_KODE.EKSPOR_KHUSUS_PRO,
        status: 403,
      }),
      "Fitur ekspor hanya tersedia untuk akun Pro. Upgrade untuk mengakses fitur ini.",
    );
  });

  it("mempertahankan pesan spesifik batch tanpa jawaban (400)", () => {
    assert.equal(
      pesanGalatEkspor({
        kode: "BATCH_BELUM_ADA_JAWABAN",
        pesan: PESAN_KODE.BATCH_BELUM_ADA_JAWABAN,
        status: 400,
      }),
      "Belum ada jawaban peserta didik pada batch ini untuk diekspor.",
    );
  });

  it("mempertahankan pesan batch tidak ditemukan dan sesi berakhir", () => {
    assert.equal(
      pesanGalatEkspor({
        kode: "BATCH_TIDAK_DITEMUKAN",
        pesan: PESAN_KODE.BATCH_TIDAK_DITEMUKAN,
      }),
      "Batch tidak ditemukan",
    );
    assert.equal(
      pesanGalatEkspor({
        kode: "SESI_BERAKHIR",
        pesan: PESAN_KODE.SESI_BERAKHIR,
      }),
      "Sesi berakhir, silakan masuk kembali.",
    );
  });

  it("memetakan galat server, jaringan, dan kode tak dikenal ke pesan gagal ekspor", () => {
    for (const galat of [
      { kode: "GAGAL_EKSPOR", pesan: PESAN_KODE.GAGAL_EKSPOR, status: 500 },
      { kode: "KESALAHAN_SERVER", pesan: PESAN_KODE.UMUM, status: 500 },
      { kode: "UMUM", pesan: PESAN_KODE.UMUM },
      { kode: "KODE_ASING", pesan: "detail mentah" },
      null,
      undefined,
    ]) {
      assert.equal(
        pesanGalatEkspor(galat),
        "Gagal membuat file ekspor, silakan coba lagi",
      );
    }
  });
});
