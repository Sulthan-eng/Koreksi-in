/**
 * Gabungkan alamat dasar API dengan path permintaan.
 *
 * Fungsi murni (tanpa import.meta) agar bisa diuji oleh node --test.
 *
 * - basis kosong ("") -> kembalikan path apa adanya (path relatif /api/...,
 *   dipakai saat dev lewat proxy Vite sehingga perilaku lama tidak berubah).
 * - basis diisi -> gabungkan tanpa trailing slash ganda.
 */
export function gabungUrl(basis, path) {
  if (!basis) return path;
  return `${basis.replace(/\/+$/, "")}${path}`;
}
