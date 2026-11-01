import { createContext, useContext, useEffect, useRef, useState } from "react";
import * as auth from "../api/auth.js";
import { setPenangananSesiBerakhir } from "../api/klien.js";
import { pesanUntukKode } from "../api/pesan.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [status, setStatus] = useState("memuat");
  const [nama, setNama] = useState(null);
  const [pesanSesi, setPesanSesi] = useState(null);
  const sudahJalanRef = useRef(false);

  useEffect(() => {
    setPenangananSesiBerakhir(() => {
      setPesanSesi(pesanUntukKode("SESI_BERAKHIR"));
      setNama(null);
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
        setStatus("terautentikasi");
      } catch {
        setStatus("tidak-terautentikasi");
      }
    })();
  }, []);

  function tandaiMasuk(namaPengguna) {
    setNama(namaPengguna);
    setStatus("terautentikasi");
  }

  async function keluar() {
    try {
      await auth.keluar();
    } finally {
      setNama(null);
      setStatus("tidak-terautentikasi");
    }
  }

  return (
    <AuthContext.Provider
      value={{
        status,
        nama,
        pesanSesi,
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
