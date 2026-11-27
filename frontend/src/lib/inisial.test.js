import { test } from "node:test";
import { strictEqual } from "node:assert/strict";
import { inisialDariNama } from "./inisial.js";

test("inisialDariNama - nama satu kata mengambil satu huruf pertama", () => {
  strictEqual(inisialDariNama("Budi"), "B");
});

test("inisialDariNama - nama dua kata mengambil huruf pertama kata pertama dan terakhir", () => {
  strictEqual(inisialDariNama("Sari Lestari"), "SL");
});

test("inisialDariNama - nama tiga kata atau lebih tetap huruf pertama kata pertama dan terakhir", () => {
  strictEqual(inisialDariNama("Sari Ayu Lestari"), "SL");
});

test("inisialDariNama - nama dengan spasi berlebih tetap diproses benar", () => {
  strictEqual(inisialDariNama("  Sari   Lestari  "), "SL");
});

test("inisialDariNama - nama kosong atau hanya spasi mengembalikan string kosong", () => {
  strictEqual(inisialDariNama(""), "");
  strictEqual(inisialDariNama("   "), "");
});

test("inisialDariNama - nama null/undefined mengembalikan string kosong", () => {
  strictEqual(inisialDariNama(null), "");
  strictEqual(inisialDariNama(undefined), "");
});
