import { test } from "node:test";
import { strictEqual } from "node:assert/strict";
import { jenisInputPassword, labelTombolPassword } from "./kolomPassword.js";

test("jenisInputPassword - mengembalikan text saat tampilkan true", () => {
  strictEqual(jenisInputPassword(true), "text");
});

test("jenisInputPassword - mengembalikan password saat tampilkan false", () => {
  strictEqual(jenisInputPassword(false), "password");
});

test("labelTombolPassword - mengembalikan label sembunyikan saat tampilkan true", () => {
  strictEqual(labelTombolPassword(true), "Sembunyikan password");
});

test("labelTombolPassword - mengembalikan label tampilkan saat tampilkan false", () => {
  strictEqual(labelTombolPassword(false), "Tampilkan password");
});
