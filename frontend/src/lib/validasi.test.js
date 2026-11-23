import { test } from "node:test";
import { strictEqual } from "node:assert/strict";
import { validasiPanjangPassword, validasiPasswordBaru } from "./validasi.js";

test("validasiPanjangPassword - menolak password kurang dari 8 byte", () => {
  strictEqual(validasiPanjangPassword("1234567"), "PASSWORD_TERLALU_PENDEK");
  strictEqual(validasiPanjangPassword(""), "PASSWORD_TERLALU_PENDEK");
});

test("validasiPanjangPassword - menghitung karakter multi-byte UTF-8 sebagai byte, bukan karakter", () => {
  // "é" adalah 2 byte UTF-8; 4 karakter "é" = 8 byte, jadi tidak boleh ditolak sebagai terlalu pendek.
  strictEqual(validasiPanjangPassword("éééé"), null);
  // 3 karakter "é" = 6 byte, masih kurang dari 8 byte walau 3 karakter.
  strictEqual(validasiPanjangPassword("ééé"), "PASSWORD_TERLALU_PENDEK");
});

test("validasiPanjangPassword - menerima tepat 8 dan tepat 72 byte", () => {
  strictEqual(validasiPanjangPassword("12345678"), null);
  strictEqual(validasiPanjangPassword("a".repeat(72)), null);
});

test("validasiPanjangPassword - menolak password lebih dari 72 byte", () => {
  strictEqual(
    validasiPanjangPassword("a".repeat(73)),
    "PASSWORD_TERLALU_PANJANG",
  );
});

test("validasiPasswordBaru - meneruskan kode galat panjang password", () => {
  strictEqual(
    validasiPasswordBaru("pendek", "pendek"),
    "PASSWORD_TERLALU_PENDEK",
  );
  strictEqual(
    validasiPasswordBaru("a".repeat(73), "a".repeat(73)),
    "PASSWORD_TERLALU_PANJANG",
  );
});

test("validasiPasswordBaru - menolak konfirmasi yang tidak sama", () => {
  strictEqual(
    validasiPasswordBaru("passwordvalid", "beda"),
    "KONFIRMASI_PASSWORD_TIDAK_SAMA",
  );
});

test("validasiPasswordBaru - menerima password dan konfirmasi yang valid", () => {
  strictEqual(validasiPasswordBaru("passwordvalid", "passwordvalid"), null);
});
