import { test } from "node:test";
import { deepStrictEqual, strictEqual } from "node:assert/strict";
import {
  fieldPertamaBermasalah,
  galatDaftarDariKode,
  galatMasukDariKode,
} from "./galatAuth.js";

test("galatDaftarDariKode - EMAIL_SUDAH_TERDAFTAR dipetakan ke kolom email", () => {
  deepStrictEqual(
    galatDaftarDariKode("EMAIL_SUDAH_TERDAFTAR", "Email sudah terdaftar"),
    {
      nama: null,
      email: "Email sudah terdaftar",
      password: null,
      umum: null,
    },
  );
});

test("galatDaftarDariKode - PASSWORD_TERLALU_PENDEK dan PASSWORD_TERLALU_PANJANG dipetakan ke kolom password", () => {
  deepStrictEqual(
    galatDaftarDariKode(
      "PASSWORD_TERLALU_PENDEK",
      "Password minimal 8 karakter",
    ),
    {
      nama: null,
      email: null,
      password: "Password minimal 8 karakter",
      umum: null,
    },
  );
  deepStrictEqual(
    galatDaftarDariKode(
      "PASSWORD_TERLALU_PANJANG",
      "Password maksimal 72 karakter",
    ),
    {
      nama: null,
      email: null,
      password: "Password maksimal 72 karakter",
      umum: null,
    },
  );
});

test("galatDaftarDariKode - kode lain jatuh ke galat umum", () => {
  deepStrictEqual(
    galatDaftarDariKode("VALIDASI_GAGAL", "Data yang dikirim tidak valid."),
    {
      nama: null,
      email: null,
      password: null,
      umum: "Data yang dikirim tidak valid.",
    },
  );
});

test("galatMasukDariKode - LOGIN_GAGAL menandai kredensial ambigu", () => {
  deepStrictEqual(
    galatMasukDariKode("LOGIN_GAGAL", "Email atau password salah"),
    {
      kredensialTidakValid: true,
      umum: "Email atau password salah",
    },
  );
});

test("galatMasukDariKode - kode lain tidak menandai kredensial", () => {
  deepStrictEqual(
    galatMasukDariKode("UMUM", "Terjadi kesalahan, silakan coba lagi."),
    {
      kredensialTidakValid: false,
      umum: "Terjadi kesalahan, silakan coba lagi.",
    },
  );
});

test("fieldPertamaBermasalah - mengembalikan null jika tidak ada yang bermasalah", () => {
  strictEqual(
    fieldPertamaBermasalah({ nama: null, email: null, password: null }, [
      "nama",
      "email",
      "password",
    ]),
    null,
  );
});

test("fieldPertamaBermasalah - mengembalikan field pertama sesuai urutan", () => {
  strictEqual(
    fieldPertamaBermasalah(
      {
        nama: null,
        email: "Email wajib diisi.",
        password: "Password wajib diisi.",
      },
      ["nama", "email", "password"],
    ),
    "email",
  );
});

test("fieldPertamaBermasalah - mengabaikan field yang tidak ada di urutan", () => {
  strictEqual(
    fieldPertamaBermasalah({ email: "Email wajib diisi." }, ["password"]),
    null,
  );
});
