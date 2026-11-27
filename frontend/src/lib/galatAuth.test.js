import { test } from "node:test";
import { deepStrictEqual, strictEqual } from "node:assert/strict";
import {
  fieldPertamaBermasalah,
  galatAturUlangPasswordDariKode,
  galatDaftarDariKode,
  galatGantiPasswordDariKode,
  galatMasukDariKode,
  galatUbahProfilDariKode,
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

test("galatAturUlangPasswordDariKode - PASSWORD_TERLALU_PENDEK dan PASSWORD_TERLALU_PANJANG dipetakan ke kolom password baru", () => {
  deepStrictEqual(
    galatAturUlangPasswordDariKode(
      "PASSWORD_TERLALU_PENDEK",
      "Password minimal 8 karakter",
    ),
    {
      passwordBaru: "Password minimal 8 karakter",
      konfirmasiPassword: null,
      umum: null,
    },
  );
  deepStrictEqual(
    galatAturUlangPasswordDariKode(
      "PASSWORD_TERLALU_PANJANG",
      "Password maksimal 72 karakter",
    ),
    {
      passwordBaru: "Password maksimal 72 karakter",
      konfirmasiPassword: null,
      umum: null,
    },
  );
});

test("galatAturUlangPasswordDariKode - kode lain jatuh ke galat umum", () => {
  deepStrictEqual(
    galatAturUlangPasswordDariKode(
      "GAGAL_UBAH_PASSWORD",
      "Gagal mengubah password, silakan coba lagi.",
    ),
    {
      passwordBaru: null,
      konfirmasiPassword: null,
      umum: "Gagal mengubah password, silakan coba lagi.",
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

test("galatUbahProfilDariKode - NAMA_KOSONG dan NAMA_TERLALU_PANJANG dipetakan ke kolom nama", () => {
  deepStrictEqual(galatUbahProfilDariKode("NAMA_KOSONG", "Nama wajib diisi."), {
    nama: "Nama wajib diisi.",
    umum: null,
  });
  deepStrictEqual(
    galatUbahProfilDariKode(
      "NAMA_TERLALU_PANJANG",
      "Nama maksimal 100 karakter.",
    ),
    {
      nama: "Nama maksimal 100 karakter.",
      umum: null,
    },
  );
});

test("galatUbahProfilDariKode - kode lain jatuh ke galat umum", () => {
  deepStrictEqual(
    galatUbahProfilDariKode("VALIDASI_GAGAL", "Data yang dikirim tidak valid."),
    {
      nama: null,
      umum: "Data yang dikirim tidak valid.",
    },
  );
});

test("galatGantiPasswordDariKode - PASSWORD_LAMA_SALAH dipetakan ke kolom kata sandi saat ini", () => {
  deepStrictEqual(
    galatGantiPasswordDariKode(
      "PASSWORD_LAMA_SALAH",
      "Kata sandi saat ini tidak sesuai.",
    ),
    {
      passwordLama: "Kata sandi saat ini tidak sesuai.",
      passwordBaru: null,
      umum: null,
    },
  );
});

test("galatGantiPasswordDariKode - PASSWORD_TERLALU_PENDEK, PASSWORD_TERLALU_PANJANG, dan PASSWORD_BARU_SAMA dipetakan ke kolom kata sandi baru", () => {
  deepStrictEqual(
    galatGantiPasswordDariKode(
      "PASSWORD_TERLALU_PENDEK",
      "Password minimal 8 karakter",
    ),
    {
      passwordLama: null,
      passwordBaru: "Password minimal 8 karakter",
      umum: null,
    },
  );
  deepStrictEqual(
    galatGantiPasswordDariKode(
      "PASSWORD_TERLALU_PANJANG",
      "Password maksimal 72 karakter",
    ),
    {
      passwordLama: null,
      passwordBaru: "Password maksimal 72 karakter",
      umum: null,
    },
  );
  deepStrictEqual(
    galatGantiPasswordDariKode(
      "PASSWORD_BARU_SAMA",
      "Password baru tidak boleh sama dengan password saat ini.",
    ),
    {
      passwordLama: null,
      passwordBaru: "Password baru tidak boleh sama dengan password saat ini.",
      umum: null,
    },
  );
});

test("galatGantiPasswordDariKode - kode lain (mis. lockout) jatuh ke galat umum", () => {
  deepStrictEqual(
    galatGantiPasswordDariKode(
      "GANTI_PASSWORD_TERKUNCI",
      "Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.",
    ),
    {
      passwordLama: null,
      passwordBaru: null,
      umum: "Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.",
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
