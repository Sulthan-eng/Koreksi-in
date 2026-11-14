export const MAKS_FILE_PER_KIRIMAN = 10;
export const MAKS_UKURAN_FILE_BYTE = 10 * 1024 * 1024;

const SIGNATURE_PDF = [0x25, 0x50, 0x44, 0x46, 0x2d]; // %PDF-
const SIGNATURE_PNG = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const SIGNATURE_JPEG = [0xff, 0xd8, 0xff];

function diawaliByte(bytes, pola) {
  if (!(bytes instanceof Uint8Array) || bytes.length < pola.length) {
    return false;
  }
  for (let i = 0; i < pola.length; i += 1) {
    if (bytes[i] !== pola[i]) return false;
  }
  return true;
}

export function deteksiFormatSignature(bytes) {
  if (diawaliByte(bytes, SIGNATURE_PDF)) return "pdf";
  if (diawaliByte(bytes, SIGNATURE_PNG)) return "png";
  if (diawaliByte(bytes, SIGNATURE_JPEG)) return "jpg";
  return null;
}

export function periksaUkuranDanSignature({ ukuranByte, kepalaByte }) {
  if (ukuranByte > MAKS_UKURAN_FILE_BYTE) {
    return "FILE_TERLALU_BESAR";
  }
  if (ukuranByte === 0 || !deteksiFormatSignature(kepalaByte)) {
    return "FORMAT_FILE_TIDAK_DIDUKUNG";
  }
  return null;
}

export async function periksaFileDiBrowser(file) {
  if (file.size > MAKS_UKURAN_FILE_BYTE) {
    return "FILE_TERLALU_BESAR";
  }
  if (file.size === 0) {
    return "FORMAT_FILE_TIDAK_DIDUKUNG";
  }
  try {
    const buffer = await file.slice(0, 8).arrayBuffer();
    const kepalaByte = new Uint8Array(buffer);
    return periksaUkuranDanSignature({
      ukuranByte: file.size,
      kepalaByte,
    });
  } catch {
    return null;
  }
}

export function pecahKiriman(daftar, ukuranKiriman = MAKS_FILE_PER_KIRIMAN) {
  if (!Array.isArray(daftar) || daftar.length === 0) {
    return [];
  }
  const hasil = [];
  for (let i = 0; i < daftar.length; i += ukuranKiriman) {
    hasil.push(daftar.slice(i, i + ukuranKiriman));
  }
  return hasil;
}

export function petakanFileBermasalah(
  daftar,
  fileBermasalah,
  terjemahkanKode,
  offsetKiriman = 0,
) {
  if (!Array.isArray(fileBermasalah) || fileBermasalah.length === 0) {
    return daftar;
  }
  const petaIndeksKePesan = new Map();
  for (const item of fileBermasalah) {
    if (item && typeof item.indeks === "number" && item.kode) {
      petaIndeksKePesan.set(
        offsetKiriman + item.indeks,
        terjemahkanKode(item.kode),
      );
    }
  }
  return daftar.map((baris, indeks) => {
    if (!petaIndeksKePesan.has(indeks)) return baris;
    return {
      ...baris,
      galatFile: petaIndeksKePesan.get(indeks),
    };
  });
}
