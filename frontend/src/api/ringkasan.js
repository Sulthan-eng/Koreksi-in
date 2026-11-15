import { permintaan } from "./klien.js";

export async function ambilRingkasan() {
  return permintaan("/api/ringkasan");
}
