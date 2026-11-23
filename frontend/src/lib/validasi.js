export const REGEX_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const encoder = new TextEncoder();

export function validasiPanjangPassword(password) {
  const panjangByte = encoder.encode(password).length;
  if (panjangByte < 8) {
    return "PASSWORD_TERLALU_PENDEK";
  }
  if (panjangByte > 72) {
    return "PASSWORD_TERLALU_PANJANG";
  }
  return null;
}

export function validasiPasswordBaru(password, konfirmasiPassword) {
  const kodePanjang = validasiPanjangPassword(password);
  if (kodePanjang) {
    return kodePanjang;
  }
  if (konfirmasiPassword !== password) {
    return "KONFIRMASI_PASSWORD_TIDAK_SAMA";
  }
  return null;
}
