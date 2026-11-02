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

export async function ubahTeksOcr(idBatch, idKoreksi, { teks_ocr }) {
  return permintaan(`/api/batch/${idBatch}/hasil/${idKoreksi}`, {
    method: "PATCH",
    body: { teks_ocr },
  });
}

export async function ubahNilaiAkhir(idBatch, idKoreksi, { skor_revisi }) {
  return permintaan(`/api/batch/${idBatch}/hasil/${idKoreksi}/nilai-akhir`, {
    method: "PATCH",
    body: { skor_revisi },
  });
}

export async function hapusBatch(idBatch) {
  return permintaan(`/api/batch/${idBatch}`, { method: "DELETE" });
}

export async function selesaikanBatch(idBatch) {
  return permintaan(`/api/batch/${idBatch}/selesaikan`, { method: "POST" });
}

export async function cobaLagiFileJawaban(idBatch, idFile) {
  return permintaan(`/api/batch/${idBatch}/file-jawaban/${idFile}/coba-lagi`, {
    method: "POST",
  });
}
