import { ekstrakNamaFileEkspor } from "../lib/ekspor.js";
import { gabungUrl } from "../lib/urlApi.js";
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
  { method = "GET", body, autentikasi, sertakanKredensial, respons = "json" },
) {
  const isFormData = body instanceof FormData;
  let response;
  try {
    response = await fetch(
      gabungUrl(import.meta.env.VITE_API_URL ?? "", path),
      {
        method,
        headers: {
          ...(body && !isFormData
            ? { "Content-Type": "application/json" }
            : {}),
          ...(autentikasi && accessToken
            ? { Authorization: `Bearer ${accessToken}` }
            : {}),
        },
        credentials: sertakanKredensial ? "include" : "same-origin",
        ...(body ? { body: isFormData ? body : JSON.stringify(body) } : {}),
      },
    );
  } catch {
    lemparKesalahan("UMUM");
  }

  if (response.status === 204) {
    if (!response.ok) lemparKesalahan("UMUM");
    return null;
  }

  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      lemparKesalahan("UMUM");
    }
    const objek = data && typeof data === "object" ? data : {};
    throw {
      kode: objek.kode,
      pesan: pesanUntukKode(objek.kode, objek.pesan),
      status: response.status,
      ...(Array.isArray(objek.file_bermasalah)
        ? { file_bermasalah: objek.file_bermasalah }
        : {}),
    };
  }

  if (respons === "blob") {
    const contentType = (
      response.headers.get("content-type") ?? ""
    ).toLowerCase();
    if (!contentType.includes("spreadsheetml")) {
      lemparKesalahan("GAGAL_EKSPOR");
    }
    const blob = await response.blob();
    return {
      blob,
      namaFile: ekstrakNamaFileEkspor(
        response.headers.get("content-disposition"),
      ),
    };
  }

  try {
    return await response.json();
  } catch {
    lemparKesalahan("UMUM");
  }
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
  {
    method = "GET",
    body,
    autentikasi = true,
    sertakanKredensial = false,
    respons = "json",
  } = {},
  _sudahDicobaUlang = false,
) {
  try {
    return await kirim(path, {
      method,
      body,
      autentikasi,
      sertakanKredensial,
      respons,
    });
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
        { method, body, autentikasi, sertakanKredensial, respons },
        true,
      );
    }
    throw error;
  }
}
