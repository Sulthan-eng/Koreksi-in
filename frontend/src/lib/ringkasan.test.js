import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { kartuRingkasan } from "./ringkasan.js";

describe("kartuRingkasan", () => {
  it("mengembalikan 4 kartu berurutan untuk akun Free", () => {
    const kartu = kartuRingkasan({
      total_batch: 2,
      peserta_didik_dikoreksi: 14,
      sisa_slot_batch_aktif: 0,
      sisa_slot_jawaban_per_batch: 1,
    });
    assert.deepEqual(kartu, [
      { label: "Total batch", nilai: 2 },
      { label: "Peserta didik sudah dikoreksi", nilai: 14 },
      { label: "Sisa slot batch aktif", nilai: 0 },
      { label: "Sisa slot jawaban per batch", nilai: 1 },
    ]);
  });

  it("mengembalikan 2 kartu untuk akun Pro (dua field null disembunyikan)", () => {
    const kartu = kartuRingkasan({
      total_batch: 5,
      peserta_didik_dikoreksi: 40,
      sisa_slot_batch_aktif: null,
      sisa_slot_jawaban_per_batch: null,
    });
    assert.deepEqual(kartu, [
      { label: "Total batch", nilai: 5 },
      { label: "Peserta didik sudah dikoreksi", nilai: 40 },
    ]);
  });

  it("nilai 0 tetap tampil di keempat kartu, tidak dianggap kosong", () => {
    const kartu = kartuRingkasan({
      total_batch: 0,
      peserta_didik_dikoreksi: 0,
      sisa_slot_batch_aktif: 0,
      sisa_slot_jawaban_per_batch: 0,
    });
    assert.deepEqual(kartu, [
      { label: "Total batch", nilai: 0 },
      { label: "Peserta didik sudah dikoreksi", nilai: 0 },
      { label: "Sisa slot batch aktif", nilai: 0 },
      { label: "Sisa slot jawaban per batch", nilai: 0 },
    ]);
  });

  it("menyembunyikan kartu hanya untuk field yang null, bukan keduanya sekaligus", () => {
    const kartu = kartuRingkasan({
      total_batch: 1,
      peserta_didik_dikoreksi: 3,
      sisa_slot_batch_aktif: null,
      sisa_slot_jawaban_per_batch: 7,
    });
    assert.deepEqual(kartu, [
      { label: "Total batch", nilai: 1 },
      { label: "Peserta didik sudah dikoreksi", nilai: 3 },
      { label: "Sisa slot jawaban per batch", nilai: 7 },
    ]);
  });
});
