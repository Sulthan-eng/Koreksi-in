import { test } from "node:test";
import { strictEqual } from "node:assert/strict";
import { normalisasiPeran, berandaUntukPeran } from "./peran.js";

test("normalisasiPeran", (t) => {
  test("menerima nilai valid", () => {
    strictEqual(normalisasiPeran("pengajar"), "pengajar");
    strictEqual(normalisasiPeran("admin"), "admin");
  });

  test("jatuh ke pengajar untuk nilai invalid", () => {
    strictEqual(normalisasiPeran(undefined), "pengajar");
    strictEqual(normalisasiPeran(null), "pengajar");
    strictEqual(normalisasiPeran(""), "pengajar");
    strictEqual(normalisasiPeran("unknown"), "pengajar");
  });
});

test("berandaUntukPeran", (t) => {
  test("kembali ke / untuk pengajar", () => {
    strictEqual(berandaUntukPeran("pengajar"), "/");
  });

  test("kembali ke /admin untuk admin", () => {
    strictEqual(berandaUntukPeran("admin"), "/admin");
  });

  test("default ke / untuk nilai lain", () => {
    strictEqual(berandaUntukPeran(undefined), "/");
    strictEqual(berandaUntukPeran(""), "/");
  });
});
