/**
 * Rapikan newline hasil OCR agar tidak patah di tengah kalimat.
 *
 * Fungsi murni (tanpa DOM/React) agar bisa diuji oleh node --test.
 *
 * Aturan:
 * - \r\n dan \r dinormalisasi jadi \n lebih dulu.
 * - Baris kosong ganda (batas paragraf) dipertahankan apa adanya.
 * - Kata yang diakhiri tanda hubung "-" tepat sebelum newline digabung
 *   tanpa spasi HANYA bila karakter sebelum "-" adalah huruf DAN baris
 *   berikutnya diawali huruf kecil (indikasi kata terpotong hyphenation).
 *   Selain itu tanda hubung dibiarkan (kata majemuk, rentang angka seperti
 *   "2020-2021", bukan pemisah kata).
 * - Baris tunggal lain digabung jadi spasi KECUALI baris sebelumnya
 *   diakhiri tanda baca penutup (. ? ! : ;) ATAU baris berikutnya diawali
 *   penanda daftar (-, •, *, "1.", "1)", "a.", "a)") yang diikuti spasi
 *   (supaya "3.5 persen" atau "-5 derajat" di awal baris tidak salah
 *   dikenali sebagai penanda daftar).
 * - Spasi berlebih dirapikan jadi satu spasi.
 * - String kosong/hanya spasi aman, selalu kembalikan "", tidak pernah throw.
 *
 * Catatan: aturan tanda baca penutup bisa salah pada singkatan (dst., dll.)
 * yang diikuti kalimat baru. Ini batasan yang disengaja, bukan bug.
 */

const AKHIR_KALIMAT = /[.?!:;]\s*$/;
const PENANDA_DAFTAR = /^(?:[-•*]|\d+[.)]|[a-zA-Z][.)])\s/;
const HURUF = /[a-zA-Z]/;
const AWAL_HURUF_KECIL = /^[a-z]/;

export function rapikanTeksOcr(teks) {
  if (!teks || !teks.trim()) return "";

  const dinormalisasi = teks.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const paragraf = dinormalisasi.split(/\n{2,}/);

  const hasilParagraf = paragraf.map((satuParagraf) =>
    gabungBarisDalamParagraf(satuParagraf),
  );

  return hasilParagraf
    .map((p) => p.trim())
    .filter((p) => p !== "")
    .join("\n\n");
}

function gabungBarisDalamParagraf(paragraf) {
  const baris = paragraf.split("\n");
  let hasil = "";

  for (let i = 0; i < baris.length; i++) {
    const barisSaatIni = baris[i].trim();
    if (barisSaatIni === "") continue;

    if (hasil === "") {
      hasil = barisSaatIni;
      continue;
    }

    const karakterTerakhirSebelumnya = hasil.slice(-1);
    if (
      karakterTerakhirSebelumnya === "-" &&
      HURUF.test(hasil.slice(-2, -1)) &&
      AWAL_HURUF_KECIL.test(barisSaatIni)
    ) {
      hasil = hasil.slice(0, -1) + barisSaatIni;
      continue;
    }

    const akhiriDenganTandaBaca = AKHIR_KALIMAT.test(hasil);
    const mulaiDenganPenandaDaftar = PENANDA_DAFTAR.test(barisSaatIni);

    if (akhiriDenganTandaBaca || mulaiDenganPenandaDaftar) {
      hasil = `${hasil}\n${barisSaatIni}`;
    } else {
      hasil = `${hasil} ${barisSaatIni}`;
    }
  }

  return hasil.replace(/[ \t]+/g, " ").trim();
}

/**
 * Tentukan teks apa yang dikirim ke server saat Simpan ditekan.
 *
 * Bila draf (setelah normalisasi) secara isi identik dengan teks asli
 * tersimpan (juga setelah normalisasi), kembalikan teks ASLI mentah
 * (bukan draf yang sudah dinormalisasi) supaya server menerima teks yang
 * sama persis dengan yang sudah tersimpan dan tidak memicu penilaian ulang
 * yang sebenarnya tidak perlu. Bila berbeda, kembalikan draf apa adanya.
 */
export function teksUntukDisimpan(teksDraft, teksAsli) {
  const draftDinormalisasi = rapikanTeksOcr(teksDraft).trim();
  const asliDinormalisasi = rapikanTeksOcr(teksAsli).trim();

  if (draftDinormalisasi === asliDinormalisasi) return teksAsli;
  return teksDraft;
}
