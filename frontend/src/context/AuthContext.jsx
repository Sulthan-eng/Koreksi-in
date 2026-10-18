import { createContext, useContext, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as auth from "../api/auth.js";
import { setPenangananSesiBerakhir } from "../api/klien.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [status, setStatus] = useState("memuat");
  const [nama, setNama] = useState(null);
  const sudahJalanRef = useRef(false);
  const navigate = useNavigate();

  useEffect(() => {
    setPenangananSesiBerakhir(() => {
      setNama(null);
      setStatus("tidak-terautentikasi");
      navigate("/masuk", {
        state: { pesan: "Sesi berakhir, silakan masuk kembali." },
      });
    });
  }, [navigate]);

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
    <AuthContext.Provider value={{ status, nama, tandaiMasuk, keluar }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components -- hook berbagi context dengan AuthProvider, memisahkan file menambah indirection tanpa manfaat di prototipe ini
export function useAuth() {
  return useContext(AuthContext);
}
