import { pesanUntukKode } from "./pesan.js";

let accessToken = null;
let refreshPromise = null;
let penangananSesiBerakhir = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function setPenangananSesiBerakhir(callback) {
  penangananSesiBerakhir = callback;
}

function lemparKesalahan(kode) {
  throw { kode, pesan: pesanUntukKode(kode) };
}

async function kirim(
  path,
  { method = "GET", body, autentikasi, sertakanKredensial },
) {
  let response;
  try {
    response = await fetch(path, {
      method,
      headers: {
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(autentikasi && accessToken
          ? { Authorization: `Bearer ${accessToken}` }
          : {}),
      },
      credentials: sertakanKredensial ? "include" : "same-origin",
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  } catch {
    lemparKesalahan("UMUM");
  }

  if (response.status === 204) {
    if (!response.ok) lemparKesalahan("UMUM");
    return null;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    lemparKesalahan("UMUM");
  }

  if (!response.ok) {
    throw {
      kode: data.kode,
      pesan: pesanUntukKode(data.kode),
      status: response.status,
    };
  }

  return data;
}

async function cobaRefresh() {
  if (!refreshPromise) {
    refreshPromise = kirim("/api/auth/refresh", {
      method: "POST",
      autentikasi: false,
      sertakanKredensial: true,
    }).finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function permintaan(
  path,
  { method = "GET", body, autentikasi = true, sertakanKredensial = false } = {},
  _sudahDicobaUlang = false,
) {
  try {
    return await kirim(path, { method, body, autentikasi, sertakanKredensial });
  } catch (error) {
    if (autentikasi && !_sudahDicobaUlang && error?.kode === "SESI_BERAKHIR") {
      try {
        const hasil = await cobaRefresh();
        setAccessToken(hasil.access_token);
      } catch {
        setAccessToken(null);
        penangananSesiBerakhir?.();
        throw error;
      }
      return permintaan(
        path,
        { method, body, autentikasi, sertakanKredensial },
        true,
      );
    }
    throw error;
  }
}
