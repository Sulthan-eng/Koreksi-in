import { test } from "node:test";
import { strictEqual } from "node:assert/strict";
import { normalisasiPeran, berandaUntukPeran } from "./peran.js";

test("normalisasiPeran - menerima nilai valid", () => {
  strictEqual(normalisasiPeran("pengajar"), "pengajar");
  strictEqual(normalisasiPeran("admin"), "admin");
});

test("normalisasiPeran - jatuh ke pengajar untuk nilai invalid", () => {
  strictEqual(normalisasiPeran(undefined), "pengajar");
  strictEqual(normalisasiPeran(null), "pengajar");
  strictEqual(normalisasiPeran(""), "pengajar");
  strictEqual(normalisasiPeran("unknown"), "pengajar");
});

test("berandaUntukPeran - kembali ke / untuk pengajar", () => {
  strictEqual(berandaUntukPeran("pengajar"), "/");
});

test("berandaUntukPeran - kembali ke /admin untuk admin", () => {
  strictEqual(berandaUntukPeran("admin"), "/admin");
});

test("berandaUntukPeran - default ke / untuk nilai lain", () => {
  strictEqual(berandaUntukPeran(undefined), "/");
  strictEqual(berandaUntukPeran(""), "/");
});
