import { PESAN_KODE } from "../api/pesan.js";

export const NAMA_FILE_EKSPOR_DEFAULT = "rekap-nilai.xlsx";

const KODE_GALAT_SPESIFIK = new Set([
  "EKSPOR_KHUSUS_PRO",
  "BATCH_BELUM_ADA_JAWABAN",
  "BATCH_TIDAK_DITEMUKAN",
  "SESI_BERAKHIR",
]);

/**
 * Ekstrak nama file dari header Content-Disposition (mis.
 * `attachment; filename="rekap-nilai-uts-2026-11-22.xlsx"`).
 * Kembalikan null jika header tidak ada atau nama file tidak aman.
 */
export function ekstrakNamaFileEkspor(contentDisposition) {
  if (typeof contentDisposition !== "string" || !contentDisposition.trim()) {
    return null;
  }

  const cocokBerpetik = contentDisposition.match(/filename\s*=\s*"([^"]+)"/i);
  const cocokTanpaPetik =
    cocokBerpetik ?? contentDisposition.match(/filename\s*=\s*([^;\s]+)/i);
  const kandidat = cocokTanpaPetik?.[1]?.trim();

  if (!kandidat) return null;
  if (
    kandidat.includes("/") ||
    kandidat.includes("\\") ||
    kandidat.includes("..")
  ) {
    return null;
  }
  for (let i = 0; i < kandidat.length; i += 1) {
    const kodeChar = kandidat.charCodeAt(i);
    if (kodeChar < 0x20 || kodeChar === 0x7f) return null;
  }
  return kandidat;
}

/**
 * Petakan galat permintaan ekspor ke teks Indonesia yang tepat.
 * Kode spesifik (Pro/kosong/tidak ditemukan/sesi) dipertahankan; kegagalan
 * server, jaringan, atau respons tak terduga dipetakan ke pesan gagal ekspor.
 */
export function pesanGalatEkspor(error) {
  if (error?.kode && KODE_GALAT_SPESIFIK.has(error.kode)) {
    if (typeof error.pesan === "string" && error.pesan.trim() !== "") {
      return error.pesan;
    }
    return PESAN_KODE[error.kode];
  }
  return PESAN_KODE.GAGAL_EKSPOR;
}
