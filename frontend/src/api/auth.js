import { permintaan, setAccessToken } from "./klien.js";

export async function daftar({ nama, email, password }) {
  return permintaan("/api/auth/daftar", {
    method: "POST",
    body: { nama, email, password },
    autentikasi: false,
  });
}

export async function masuk({ email, password }) {
  const hasil = await permintaan("/api/auth/masuk", {
    method: "POST",
    body: { email, password },
    autentikasi: false,
    sertakanKredensial: true,
  });
  setAccessToken(hasil.access_token);
  return hasil;
}

export async function refresh() {
  try {
    const hasil = await permintaan("/api/auth/refresh", {
      method: "POST",
      autentikasi: false,
      sertakanKredensial: true,
    });
    setAccessToken(hasil.access_token);
    return hasil;
  } catch (error) {
    setAccessToken(null);
    throw error;
  }
}

export async function keluar() {
  try {
    await permintaan("/api/auth/keluar", {
      method: "POST",
      autentikasi: false,
      sertakanKredensial: true,
    });
  } finally {
    setAccessToken(null);
  }
}

export async function saya() {
  return permintaan("/api/auth/saya");
}
