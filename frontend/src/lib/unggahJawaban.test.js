import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  MAKS_UKURAN_FILE_BYTE,
  deteksiFormatSignature,
  pecahKiriman,
  periksaFileDiBrowser,
  periksaUkuranDanSignature,
  petakanFileBermasalah,
} from "./unggahJawaban.js";

const BYTE_PDF = new Uint8Array([
  0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x37,
]);
const BYTE_PNG = new Uint8Array([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]);
const BYTE_JPEG = new Uint8Array([
  0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46,
]);
const BYTE_DOCX = new Uint8Array([
  0x50, 0x4b, 0x03, 0x04, 0x14, 0x00, 0x06, 0x00,
]);

describe("pecahKiriman", () => {
  it("mengembalikan array kosong untuk daftar kosong", () => {
    assert.deepEqual(pecahKiriman([]), []);
  });

  it("memecah daftar menjadi potongan maksimal 10 item sesuai urutan", () => {
    const daftar3 = [1, 2, 3];
    assert.deepEqual(pecahKiriman(daftar3), [[1, 2, 3]]);

    const daftar10 = Array.from({ length: 10 }, (_, i) => i + 1);
    assert.deepEqual(pecahKiriman(daftar10), [daftar10]);

    const daftar25 = Array.from({ length: 25 }, (_, i) => i + 1);
    const kiriman = pecahKiriman(daftar25);
    assert.equal(kiriman.length, 3);
    assert.deepEqual(kiriman[0], daftar25.slice(0, 10));
    assert.deepEqual(kiriman[1], daftar25.slice(10, 20));
    assert.deepEqual(kiriman[2], daftar25.slice(20, 25));
  });
});

describe("petakanFileBermasalah", () => {
  const kamus = {
    FORMAT_FILE_TIDAK_DIDUKUNG:
      "Format file tidak didukung. Gunakan PDF, PNG, atau JPG.",
    PDF_TERLALU_BANYAK_HALAMAN: "PDF maksimal 15 halaman.",
    PDF_TIDAK_DAPAT_DIBACA: "File PDF rusak atau tidak dapat dibaca.",
  };
  const terjemahkan = (kode) => kamus[kode] ?? "Galat";

  it("memetakan indeks relatif kiriman ke baris daftar pada kiriman pertama", () => {
    const daftar = [
      { id: 1, nama: "A", galatFile: null },
      { id: 2, nama: "B", galatFile: null },
      { id: 3, nama: "C", galatFile: null },
    ];
    const hasil = petakanFileBermasalah(
      daftar,
      [
        { indeks: 0, kode: "FORMAT_FILE_TIDAK_DIDUKUNG" },
        { indeks: 2, kode: "PDF_TERLALU_BANYAK_HALAMAN" },
      ],
      terjemahkan,
      0,
    );
    assert.equal(
      hasil[0].galatFile,
      "Format file tidak didukung. Gunakan PDF, PNG, atau JPG.",
    );
    assert.equal(hasil[1].galatFile, null);
    assert.equal(hasil[2].galatFile, "PDF maksimal 15 halaman.");
  });

  it("memetakan indeks dengan offset kiriman dan mengabaikan indeks di luar daftar", () => {
    const daftar = [
      { id: 1, nama: "A", galatFile: null },
      { id: 2, nama: "B", galatFile: null },
      { id: 3, nama: "C", galatFile: null },
    ];
    const hasil = petakanFileBermasalah(
      daftar,
      [
        { indeks: 1, kode: "PDF_TIDAK_DAPAT_DIBACA" },
        { indeks: 99, kode: "PDF_TERLALU_BANYAK_HALAMAN" },
      ],
      terjemahkan,
      1,
    );
    assert.equal(hasil[0].galatFile, null);
    assert.equal(hasil[1].galatFile, null);
    assert.equal(hasil[2].galatFile, "File PDF rusak atau tidak dapat dibaca.");
  });
});

describe("periksaUkuranDanSignature dan periksaFileDiBrowser", () => {
  it("mendeteksi signature PDF, PNG, dan JPEG dengan benar", () => {
    assert.equal(deteksiFormatSignature(BYTE_PDF), "pdf");
    assert.equal(deteksiFormatSignature(BYTE_PNG), "png");
    assert.equal(deteksiFormatSignature(BYTE_JPEG), "jpg");
    assert.equal(deteksiFormatSignature(BYTE_DOCX), null);
    assert.equal(
      deteksiFormatSignature(new Uint8Array([0x25, 0x50, 0x44, 0x46])),
      null,
    );
    assert.equal(deteksiFormatSignature(new Uint8Array(0)), null);
  });

  it("meloloskan PDF, PNG, dan JPEG hingga batas tepat 10 MB tanpa memeriksa ekstensi", () => {
    assert.equal(
      periksaUkuranDanSignature({
        ukuranByte: 1024,
        kepalaByte: BYTE_PDF,
      }),
      null,
    );
    assert.equal(
      periksaUkuranDanSignature({
        ukuranByte: MAKS_UKURAN_FILE_BYTE,
        kepalaByte: BYTE_PNG,
      }),
      null,
    );
    assert.equal(
      periksaUkuranDanSignature({
        ukuranByte: 500,
        kepalaByte: BYTE_JPEG,
      }),
      null,
    );
  });

  it("menolak ukuran di atas 10 MB dengan FILE_TERLALU_BESAR", () => {
    assert.equal(
      periksaUkuranDanSignature({
        ukuranByte: MAKS_UKURAN_FILE_BYTE + 1,
        kepalaByte: BYTE_PDF,
      }),
      "FILE_TERLALU_BESAR",
    );
  });

  it("menolak berkas 0 byte atau signature tidak dikenal dengan FORMAT_FILE_TIDAK_DIDUKUNG", () => {
    assert.equal(
      periksaUkuranDanSignature({
        ukuranByte: 0,
        kepalaByte: new Uint8Array(0),
      }),
      "FORMAT_FILE_TIDAK_DIDUKUNG",
    );
    assert.equal(
      periksaUkuranDanSignature({
        ukuranByte: 2048,
        kepalaByte: BYTE_DOCX,
      }),
      "FORMAT_FILE_TIDAK_DIDUKUNG",
    );
  });

  it("melewati pemeriksaan browser (mengembalikan null) jika pembacaan slice melempar galat", async () => {
    const fileGagalBaca = {
      size: 1024,
      slice() {
        return {
          async arrayBuffer() {
            throw new Error("Gagal baca");
          },
        };
      },
    };
    const hasil = await periksaFileDiBrowser(fileGagalBaca);
    assert.equal(hasil, null);
  });
});
