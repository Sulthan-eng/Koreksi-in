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

export async function daftarFileJawaban(idBatch) {
  return permintaan(`/api/batch/${idBatch}/file-jawaban`);
}

export async function unggahFileJawaban(idBatch, formData) {
  return permintaan(`/api/batch/${idBatch}/file-jawaban`, {
    method: "POST",
    body: formData,
  });
}

export async function daftarHasilKoreksi(idBatch) {
  return permintaan(`/api/batch/${idBatch}/hasil`);
}
