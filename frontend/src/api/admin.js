import { permintaan } from "./klien.js";

export async function daftarAkunPengajar({
  cari = "",
  status_langganan = "",
  status_akun = "",
} = {}) {
  const params = new URLSearchParams();
  if (cari.trim() !== "") {
    params.set("cari", cari.trim());
  }
  if (status_langganan !== "") {
    params.set("status_langganan", status_langganan);
  }
  if (status_akun !== "") {
    params.set("status_akun", status_akun);
  }
  const query = params.toString();
  const path = query
    ? `/api/admin/akun-pengajar?${query}`
    : "/api/admin/akun-pengajar";
  return permintaan(path);
}

export async function ubahLanggananPengajar(
  idPengguna,
  { status_langganan, masa_berlaku_pro },
) {
  return permintaan(`/api/admin/akun-pengajar/${idPengguna}/langganan`, {
    method: "PATCH",
    body: { status_langganan, masa_berlaku_pro },
  });
}

export async function nonaktifkanPengajar(idPengguna) {
  return permintaan(`/api/admin/akun-pengajar/${idPengguna}/nonaktifkan`, {
    method: "POST",
  });
}

export async function aktifkanPengajar(idPengguna) {
  return permintaan(`/api/admin/akun-pengajar/${idPengguna}/aktifkan`, {
    method: "POST",
  });
}
