import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { rapikanTeksOcr, teksUntukDisimpan } from "./teksOcr.js";

describe("rapikanTeksOcr", () => {
  it("menggabungkan paragraf biasa yang patah antar baris jadi satu baris", () => {
    assert.equal(
      rapikanTeksOcr(
        "Ini adalah kalimat yang\npanjang dan terpotong\ndi tengah jalan.",
      ),
      "Ini adalah kalimat yang panjang dan terpotong di tengah jalan.",
    );
  });

  it("tidak menggabungkan daftar bernomor (1. 2.)", () => {
    assert.equal(
      rapikanTeksOcr("Daftar:\n1. Item pertama\n2. Item kedua"),
      "Daftar:\n1. Item pertama\n2. Item kedua",
    );
  });

  it("tidak menggabungkan daftar bernomor dengan tanda kurung (1))", () => {
    assert.equal(
      rapikanTeksOcr("Langkah:\n1) Siapkan alat\n2) Mulai"),
      "Langkah:\n1) Siapkan alat\n2) Mulai",
    );
  });

  it("tidak menggabungkan daftar berhuruf (a. a))", () => {
    assert.equal(
      rapikanTeksOcr("Pilihan:\na. Benar\nb. Salah"),
      "Pilihan:\na. Benar\nb. Salah",
    );
  });

  it("tidak menggabungkan marker - dan •", () => {
    assert.equal(
      rapikanTeksOcr("Bahan:\n- Tepung\n- Gula\n• Garam"),
      "Bahan:\n- Tepung\n- Gula\n• Garam",
    );
  });

  it("tidak salah mengenali angka desimal di awal baris sebagai daftar bernomor", () => {
    assert.equal(
      rapikanTeksOcr("Sekitar 3.5\npersen dari total"),
      "Sekitar 3.5 persen dari total",
    );
  });

  it("tidak salah mengenali angka negatif di awal baris sebagai marker -", () => {
    assert.equal(
      rapikanTeksOcr("Suhu turun\n-5 derajat celcius"),
      "Suhu turun -5 derajat celcius",
    );
  });

  it("menggabungkan kata yang terpotong tanda hubung di ujung baris tanpa spasi", () => {
    assert.equal(
      rapikanTeksOcr("Teks dengan tanda hu-\nbung terpotong"),
      "Teks dengan tanda hubung terpotong",
    );
  });

  it("tidak menggabungkan tanda hubung pada rentang angka (bukan huruf sebelum -)", () => {
    assert.equal(
      rapikanTeksOcr("Rentang tahun 2020-\n2021 tetap"),
      "Rentang tahun 2020- 2021 tetap",
    );
  });

  it("tidak menggabungkan tanda hubung bila baris berikut tidak diawali huruf kecil", () => {
    assert.equal(
      rapikanTeksOcr("Kata majemuk anti-\nKorupsi tetap"),
      "Kata majemuk anti- Korupsi tetap",
    );
  });

  it("mempertahankan baris kosong ganda sebagai batas paragraf", () => {
    assert.equal(
      rapikanTeksOcr("Paragraf satu.\n\nParagraf dua."),
      "Paragraf satu.\n\nParagraf dua.",
    );
  });

  it("tidak mengubah baris yang diakhiri tanda baca penutup", () => {
    assert.equal(
      rapikanTeksOcr("Kalimat pertama selesai.\nKalimat kedua baru mulai."),
      "Kalimat pertama selesai.\nKalimat kedua baru mulai.",
    );
  });

  it("membiarkan teks tanpa newline sama sekali", () => {
    assert.equal(
      rapikanTeksOcr("Teks satu baris saja tanpa newline"),
      "Teks satu baris saja tanpa newline",
    );
  });

  it("merapikan spasi berlebih", () => {
    assert.equal(
      rapikanTeksOcr("Teks   dengan     spasi berlebih\ndi sini"),
      "Teks dengan spasi berlebih di sini",
    );
  });

  it("string kosong mengembalikan string kosong, tidak throw", () => {
    assert.equal(rapikanTeksOcr(""), "");
  });

  it("string hanya spasi mengembalikan string kosong", () => {
    assert.equal(rapikanTeksOcr("   \n   \n  "), "");
  });

  it("menormalisasi \\r\\n dan \\r jadi \\n", () => {
    assert.equal(
      rapikanTeksOcr("Baris satu.\r\nBaris dua baru.\rBaris tiga baru."),
      "Baris satu.\nBaris dua baru.\nBaris tiga baru.",
    );
  });

  describe("idempoten (rapikanTeksOcr(rapikanTeksOcr(x)) === rapikanTeksOcr(x))", () => {
    const contoh = [
      "Ini adalah kalimat yang\npanjang dan terpotong\ndi tengah jalan.",
      "Daftar:\n1. Item pertama\n2. Item kedua",
      "Teks dengan tanda hu-\nbung terpotong",
      "Paragraf satu.\n\nParagraf dua.",
    ];

    for (const teks of contoh) {
      it(`stabil untuk: ${JSON.stringify(teks)}`, () => {
        const sekaliRapi = rapikanTeksOcr(teks);
        assert.equal(rapikanTeksOcr(sekaliRapi), sekaliRapi);
      });
    }
  });
});

describe("teksUntukDisimpan", () => {
  it("mengembalikan teks asli bila draf secara normalisasi identik", () => {
    assert.equal(
      teksUntukDisimpan(
        "Ini adalah kalimat yang\npanjang dan terpotong.",
        "Ini adalah kalimat yang panjang dan terpotong.",
      ),
      "Ini adalah kalimat yang panjang dan terpotong.",
    );
  });

  it("mengembalikan draf bila isinya benar-benar berbeda", () => {
    assert.equal(
      teksUntukDisimpan("Teks yang sudah diedit pengajar.", "Teks asli."),
      "Teks yang sudah diedit pengajar.",
    );
  });
});
