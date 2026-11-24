import { test } from "node:test";
import { strictEqual } from "node:assert/strict";
import {
  REGEX_EMAIL,
  validasiPanjangEmail,
  validasiPanjangNama,
  validasiPanjangPassword,
} from "./validasi.js";

test("REGEX_EMAIL - menerima format email yang wajar", () => {
  strictEqual(REGEX_EMAIL.test("nama@email.com"), true);
  strictEqual(REGEX_EMAIL.test("nama.lengkap@sub.email.co.id"), true);
});

test("REGEX_EMAIL - menolak titik ganda atau berurutan di domain, selaras POLA_EMAIL backend", () => {
  strictEqual(REGEX_EMAIL.test("rana@gmail..com"), false);
  strictEqual(REGEX_EMAIL.test("rana@.gmail.com"), false);
  strictEqual(REGEX_EMAIL.test("rana@gmail.com."), false);
});

test("REGEX_EMAIL - menolak tanpa @, tanpa domain, atau mengandung spasi", () => {
  strictEqual(REGEX_EMAIL.test("ranagmail.com"), false);
  strictEqual(REGEX_EMAIL.test("rana@gmailcom"), false);
  strictEqual(REGEX_EMAIL.test("rana @gmail.com"), false);
});

test("validasiPanjangNama - menerima tepat 100 karakter, menolak 101", () => {
  strictEqual(validasiPanjangNama("a".repeat(100)), null);
  strictEqual(validasiPanjangNama("a".repeat(101)), "NAMA_TERLALU_PANJANG");
});

test("validasiPanjangNama - menghitung dari nilai mentah (belum di-trim)", () => {
  // 99 huruf + 2 spasi ujung = 101 karakter mentah, harus ditolak walau hasil trim 99 karakter.
  strictEqual(
    validasiPanjangNama(` ${"a".repeat(99)} `),
    "NAMA_TERLALU_PANJANG",
  );
});

test("validasiPanjangNama - menghitung code point, bukan unit UTF-16 (emoji tidak dihitung dua kali)", () => {
  // "😀" adalah satu code point tapi dua unit UTF-16, jadi .length bawaan akan salah menghitungnya sebagai 200.
  strictEqual(validasiPanjangNama("😀".repeat(100)), null);
  strictEqual(validasiPanjangNama("😀".repeat(101)), "NAMA_TERLALU_PANJANG");
});

test("validasiPanjangEmail - menerima tepat 255 karakter, menolak 256", () => {
  strictEqual(validasiPanjangEmail("a".repeat(255)), null);
  strictEqual(validasiPanjangEmail("a".repeat(256)), "EMAIL_TERLALU_PANJANG");
});

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
