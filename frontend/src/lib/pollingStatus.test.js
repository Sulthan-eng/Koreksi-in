import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { BATAS_GAGAL_POLLING, catatHasilPolling } from "./pollingStatus.js";

describe("catatHasilPolling", () => {
  it("batas default adalah 3 kegagalan beruntun", () => {
    assert.equal(BATAS_GAGAL_POLLING, 3);
  });

  it("kegagalan ke-1 dan ke-2 tidak menghentikan polling", () => {
    const pertama = catatHasilPolling(0, false);
    assert.deepEqual(pertama, { gagalBeruntun: 1, berhenti: false });

    const kedua = catatHasilPolling(pertama.gagalBeruntun, false);
    assert.deepEqual(kedua, { gagalBeruntun: 2, berhenti: false });
  });

  it("kegagalan ke-3 beruntun menghentikan polling", () => {
    const ketiga = catatHasilPolling(2, false);
    assert.deepEqual(ketiga, { gagalBeruntun: 3, berhenti: true });
  });

  it("keberhasilan mereset hitungan kegagalan beruntun ke 0", () => {
    assert.deepEqual(catatHasilPolling(0, true), {
      gagalBeruntun: 0,
      berhenti: false,
    });
    assert.deepEqual(catatHasilPolling(1, true), {
      gagalBeruntun: 0,
      berhenti: false,
    });
    assert.deepEqual(catatHasilPolling(2, true), {
      gagalBeruntun: 0,
      berhenti: false,
    });
  });

  it("urutan campur gagal-sukses baru berhenti setelah 3 kegagalan beruntun", () => {
    const urutan = [
      false,
      false,
      true, // reset ke 0
      false,
      false,
      true, // reset ke 0
      false,
      false,
      false, // ke-3 beruntun -> berhenti
    ];
    let gagalBeruntun = 0;
    const hasil = [];

    for (const berhasil of urutan) {
      const langkah = catatHasilPolling(gagalBeruntun, berhasil);
      gagalBeruntun = langkah.gagalBeruntun;
      hasil.push(langkah);
    }

    assert.deepEqual(hasil, [
      { gagalBeruntun: 1, berhenti: false },
      { gagalBeruntun: 2, berhenti: false },
      { gagalBeruntun: 0, berhenti: false },
      { gagalBeruntun: 1, berhenti: false },
      { gagalBeruntun: 2, berhenti: false },
      { gagalBeruntun: 0, berhenti: false },
      { gagalBeruntun: 1, berhenti: false },
      { gagalBeruntun: 2, berhenti: false },
      { gagalBeruntun: 3, berhenti: true },
    ]);
  });

  it("mendukung batas kustom dan tetap berhenti bila melewati batas", () => {
    assert.deepEqual(catatHasilPolling(0, false, 2), {
      gagalBeruntun: 1,
      berhenti: false,
    });
    assert.deepEqual(catatHasilPolling(1, false, 2), {
      gagalBeruntun: 2,
      berhenti: true,
    });
    assert.deepEqual(catatHasilPolling(3, false, 3), {
      gagalBeruntun: 4,
      berhenti: true,
    });
  });
});
