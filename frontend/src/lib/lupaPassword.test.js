import { test } from "node:test";
import { strictEqual, deepStrictEqual } from "node:assert/strict";
import {
  sisaDetik,
  waktuBerakhirBaru,
  bacaStatusTersimpan,
  labelTombolLupaPassword,
} from "./lupaPassword.js";

test("sisaDetik - mengembalikan 60 saat waktuBerakhir 60 detik ke depan", () => {
  strictEqual(sisaDetik(60_000, 0), 60);
});

test("sisaDetik - mengembalikan 0 saat waktuBerakhir sudah lewat", () => {
  strictEqual(sisaDetik(1_000, 5_000), 0);
});

test("sisaDetik - mengembalikan 0 saat waktuBerakhir sama dengan sekarang", () => {
  strictEqual(sisaDetik(5_000, 5_000), 0);
});

test("sisaDetik - membatasi hasil maksimal 60 meski selisih lebih dari 60000 ms", () => {
  strictEqual(sisaDetik(120_000, 0), 60);
});

test("sisaDetik - membulatkan ke atas sisa milidetik pecahan menjadi 1 detik", () => {
  strictEqual(sisaDetik(500, 0), 1);
});

test("waktuBerakhirBaru - mengembalikan sekarang ditambah 60000 ms", () => {
  strictEqual(waktuBerakhirBaru(1_000), 61_000);
});

test("bacaStatusTersimpan - mengembalikan null saat nilai null", () => {
  strictEqual(bacaStatusTersimpan(null, 0), null);
});

test("bacaStatusTersimpan - mengembalikan null saat nilai string kosong", () => {
  strictEqual(bacaStatusTersimpan("", 0), null);
});

test("bacaStatusTersimpan - mengembalikan null saat JSON tidak valid", () => {
  strictEqual(bacaStatusTersimpan("{tidak valid", 0), null);
});

test("bacaStatusTersimpan - mengembalikan null saat email bukan string", () => {
  strictEqual(
    bacaStatusTersimpan(JSON.stringify({ email: 5, waktuBerakhir: 60_000 }), 0),
    null,
  );
});

test("bacaStatusTersimpan - mengembalikan null saat email string kosong", () => {
  strictEqual(
    bacaStatusTersimpan(
      JSON.stringify({ email: "", waktuBerakhir: 60_000 }),
      0,
    ),
    null,
  );
});

test("bacaStatusTersimpan - mengembalikan null saat waktuBerakhir bukan angka", () => {
  strictEqual(
    bacaStatusTersimpan(
      JSON.stringify({ email: "a@b.com", waktuBerakhir: "60000" }),
      0,
    ),
    null,
  );
});

test("bacaStatusTersimpan - mengembalikan null saat waktuBerakhir NaN", () => {
  strictEqual(
    bacaStatusTersimpan(
      JSON.stringify({ email: "a@b.com", waktuBerakhir: NaN }),
      0,
    ),
    null,
  );
});

test("bacaStatusTersimpan - mengembalikan null saat waktuBerakhir sudah lewat", () => {
  strictEqual(
    bacaStatusTersimpan(
      JSON.stringify({ email: "a@b.com", waktuBerakhir: 1_000 }),
      5_000,
    ),
    null,
  );
});

test("bacaStatusTersimpan - mengembalikan email, sisaDetik, dan waktuBerakhir saat data valid dan belum lewat", () => {
  deepStrictEqual(
    bacaStatusTersimpan(
      JSON.stringify({ email: "a@b.com", waktuBerakhir: 60_000 }),
      0,
    ),
    { email: "a@b.com", sisaDetik: 60, waktuBerakhir: 60_000 },
  );
});

test("bacaStatusTersimpan - mengabaikan field tak dikenal pada data tersimpan", () => {
  deepStrictEqual(
    bacaStatusTersimpan(
      JSON.stringify({
        email: "a@b.com",
        waktuBerakhir: 60_000,
        lainnya: "x",
      }),
      0,
    ),
    { email: "a@b.com", sisaDetik: 60, waktuBerakhir: 60_000 },
  );
});

test("labelTombolLupaPassword - mengembalikan Kirim Tautan saat sisaDetik 0", () => {
  strictEqual(labelTombolLupaPassword(0), "Kirim Tautan");
});

test("labelTombolLupaPassword - mengembalikan label hitungan mundur saat sisaDetik lebih dari 0", () => {
  strictEqual(labelTombolLupaPassword(60), "Kirim ulang dalam 60 detik");
  strictEqual(labelTombolLupaPassword(1), "Kirim ulang dalam 1 detik");
});
