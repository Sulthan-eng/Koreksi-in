import { permintaan } from "./klien.js";

export async function daftarBatch() {
  return permintaan("/api/batch");
}

export async function buatBatch({ nama_batch }) {
  return permintaan("/api/batch", {
    method: "POST",
    body: { nama_batch },
  });
}

export async function ambilBatch(idBatch) {
  return permintaan(`/api/batch/${idBatch}`);
}

export async function daftarSoal(idBatch) {
  return permintaan(`/api/batch/${idBatch}/soal`);
}

export async function tambahSoal(idBatch, { kunci_jawaban }) {
  return permintaan(`/api/batch/${idBatch}/soal`, {
    method: "POST",
    body: { kunci_jawaban },
  });
}
