import { test } from "node:test";
import { strictEqual } from "node:assert/strict";
import {
  formatAngka,
  formatJamDiperbarui,
  formatPersenPemakaian,
  labelTingkatKuota,
  lebarBilahKuota,
  sisaPanggilan,
  tingkatKuota,
} from "./dashboardPantauan.js";

test("formatAngka - format id-ID tanpa desimal", () => {
  strictEqual(formatAngka(0), "0");
  strictEqual(formatAngka(1240), "1.240");
  strictEqual(formatAngka(10000), "10.000");
});

test("formatPersenPemakaian - 29 dari 100 menjadi 29%", () => {
  strictEqual(formatPersenPemakaian(29, 100), "29%");
});

test("formatPersenPemakaian - satu desimal dan nol di belakang koma dibuang", () => {
  strictEqual(formatPersenPemakaian(1240, 10000), "12,4%");
  strictEqual(formatPersenPemakaian(50, 100), "50%");
  strictEqual(formatPersenPemakaian(0, 100), "0%");
});

test("formatPersenPemakaian - maksimal 100%", () => {
  strictEqual(formatPersenPemakaian(100, 100), "100%");
  strictEqual(formatPersenPemakaian(101, 100), "100%");
  strictEqual(formatPersenPemakaian(500, 100), "100%");
});

test("formatPersenPemakaian - batas nol atau negatif menjadi 0%", () => {
  strictEqual(formatPersenPemakaian(0, 0), "0%");
  strictEqual(formatPersenPemakaian(50, 0), "0%");
  strictEqual(formatPersenPemakaian(50, -10), "0%");
});

test("lebarBilahKuota - mengikuti nilai asli dan dibatasi 0-100%", () => {
  strictEqual(lebarBilahKuota(1240, 10000), "12.4%");
  strictEqual(lebarBilahKuota(0, 10000), "0%");
  strictEqual(lebarBilahKuota(100, 100), "100%");
  strictEqual(lebarBilahKuota(101, 100), "100%");
  strictEqual(lebarBilahKuota(50, 0), "0%");
});

test("sisaPanggilan - minimal nol", () => {
  strictEqual(sisaPanggilan(1240, 10000), 8760);
  strictEqual(sisaPanggilan(101, 100), 0);
  strictEqual(sisaPanggilan(5, 0), 0);
  strictEqual(sisaPanggilan(5, -10), 0);
});

test("tingkatKuota - ambang 80 dan 95 memakai bilangan bulat", () => {
  strictEqual(tingkatKuota(0, 100), "normal");
  strictEqual(tingkatKuota(79, 100), "normal");
  strictEqual(tingkatKuota(80, 100), "mendekati-batas");
  strictEqual(tingkatKuota(94, 100), "mendekati-batas");
  strictEqual(tingkatKuota(95, 100), "hampir-habis");
  strictEqual(tingkatKuota(99, 100), "hampir-habis");
  strictEqual(tingkatKuota(100, 100), "batas-tercapai");
});

test("tingkatKuota - terpakai melebihi batas menjadi batas tercapai", () => {
  strictEqual(tingkatKuota(101, 100), "batas-tercapai");
});

test("tingkatKuota - batas nol atau negatif menjadi batas tercapai", () => {
  strictEqual(tingkatKuota(0, 0), "batas-tercapai");
  strictEqual(tingkatKuota(5, -10), "batas-tercapai");
});

test("labelTingkatKuota - teks status sesuai ambang", () => {
  strictEqual(labelTingkatKuota("normal"), null);
  strictEqual(labelTingkatKuota("mendekati-batas"), "Mendekati batas");
  strictEqual(labelTingkatKuota("hampir-habis"), "Hampir habis");
  strictEqual(labelTingkatKuota("batas-tercapai"), "Batas tercapai");
});

test("formatJamDiperbarui - format 24 jam dengan titik", () => {
  strictEqual(formatJamDiperbarui(new Date(2026, 10, 24, 17, 32)), "17.32");
  strictEqual(formatJamDiperbarui(new Date(2026, 10, 24, 5, 5)), "05.05");
  strictEqual(formatJamDiperbarui("bukan tanggal"), "");
});
