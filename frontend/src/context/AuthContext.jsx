import { createContext, useContext, useEffect, useRef, useState } from "react";
import * as auth from "../api/auth.js";
import { setPenangananSesiBerakhir } from "../api/klien.js";
import { pesanUntukKode } from "../api/pesan.js";

const AuthContext = createContext(null);

const STATUS_LANGGANAN_VALID = new Set(["free", "pro"]);

function normalisasiStatusLangganan(nilai) {
  return STATUS_LANGGANAN_VALID.has(nilai) ? nilai : null;
}

export function AuthProvider({ children }) {
  const [status, setStatus] = useState("memuat");
  const [nama, setNama] = useState(null);
  const [statusLangganan, setStatusLangganan] = useState(null);
  const [pesanSesi, setPesanSesi] = useState(null);
  const [keluarSengaja, setKeluarSengaja] = useState(false);
  const sudahJalanRef = useRef(false);

  useEffect(() => {
    setPenangananSesiBerakhir(() => {
      setKeluarSengaja(false);
      setPesanSesi(pesanUntukKode("SESI_BERAKHIR"));
      setNama(null);
      setStatusLangganan(null);
      setStatus("tidak-terautentikasi");
    });
  }, []);

  function bersihkanPesanSesi() {
    setPesanSesi(null);
  }

  useEffect(() => {
    if (sudahJalanRef.current) return;
    sudahJalanRef.current = true;

    (async () => {
      try {
        await auth.refresh();
        const hasil = await auth.saya();
        setNama(hasil.nama);
        setStatusLangganan(normalisasiStatusLangganan(hasil.status_langganan));
        setStatus("terautentikasi");
      } catch {
        setStatus("tidak-terautentikasi");
      }
    })();
  }, []);

  function tandaiMasuk(namaPengguna, statusLanggananPengguna) {
    setKeluarSengaja(false);
    setNama(namaPengguna);
    setStatusLangganan(normalisasiStatusLangganan(statusLanggananPengguna));
    setStatus("terautentikasi");
  }

  async function keluar() {
    try {
      await auth.keluar();
    } finally {
      setKeluarSengaja(true);
      setNama(null);
      setStatusLangganan(null);
      setStatus("tidak-terautentikasi");
    }
  }

  return (
    <AuthContext.Provider
      value={{
        status,
        nama,
        statusLangganan,
        pesanSesi,
        keluarSengaja,
        bersihkanPesanSesi,
        tandaiMasuk,
        keluar,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components -- hook berbagi context dengan AuthProvider, memisahkan file menambah indirection tanpa manfaat di prototipe ini
export function useAuth() {
  return useContext(AuthContext);
}
