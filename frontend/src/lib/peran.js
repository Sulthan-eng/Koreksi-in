const PERAN_VALID = new Set(["pengajar", "admin"]);

export function normalisasiPeran(nilai) {
  return PERAN_VALID.has(nilai) ? nilai : "pengajar";
}

export function berandaUntukPeran(peran) {
  return peran === "admin" ? "/admin" : "/";
}
