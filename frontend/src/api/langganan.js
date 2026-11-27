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

export async function ambilInvoice(idOrder) {
  return permintaan(`/api/langganan/invoice/${encodeURIComponent(idOrder)}`);
}
