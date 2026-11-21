import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { gabungUrl } from "./urlApi.js";

describe("gabungUrl", () => {
  it("basis kosong mengembalikan path apa adanya (dev lokal lewat proxy)", () => {
    assert.equal(gabungUrl("", "/api/auth/saya"), "/api/auth/saya");
  });

  it("basis tanpa trailing slash digabung langsung", () => {
    assert.equal(
      gabungUrl("https://api.contoh.id", "/api/auth/saya"),
      "https://api.contoh.id/api/auth/saya",
    );
  });

  it("basis dengan trailing slash tidak menghasilkan slash ganda", () => {
    assert.equal(
      gabungUrl("https://api.contoh.id/", "/api/auth/saya"),
      "https://api.contoh.id/api/auth/saya",
    );
  });

  it("basis dengan beberapa trailing slash tetap dirapikan", () => {
    assert.equal(
      gabungUrl("https://api.contoh.id///", "/api/auth/saya"),
      "https://api.contoh.id/api/auth/saya",
    );
  });
});
