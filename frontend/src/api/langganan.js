import { permintaan } from "./klien.js";

export async function buatTransaksi({ paket }) {
  return permintaan("/api/langganan/transaksi", {
    method: "POST",
    body: { paket },
  });
}

export async function daftarTransaksi() {
  return permintaan("/api/langganan/transaksi");
}
