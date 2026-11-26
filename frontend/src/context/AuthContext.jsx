import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import * as auth from "../api/auth.js";
import { setPenangananSesiBerakhir } from "../api/klien.js";
import { pesanUntukKode } from "../api/pesan.js";
import { normalisasiPeran } from "../lib/peran.js";

const AuthContext = createContext(null);

const STATUS_LANGGANAN_VALID = new Set(["free", "pro"]);

function normalisasiStatusLangganan(nilai) {
  return STATUS_LANGGANAN_VALID.has(nilai) ? nilai : null;
}

function normalisasiMasaBerlakuPro(nilai, statusLangganan) {
  if (statusLangganan !== "pro" || typeof nilai !== "string" || !nilai.trim()) {
    return null;
  }
  return nilai;
}

export function AuthProvider({ children }) {
  const [status, setStatus] = useState("memuat");
  const [nama, setNama] = useState(null);
  const [email, setEmail] = useState(null);
  const [statusLangganan, setStatusLangganan] = useState(null);
  const [masaBerlakuPro, setMasaBerlakuPro] = useState(null);
  const [peran, setPeran] = useState("pengajar");
  const [pesanSesi, setPesanSesi] = useState(null);
  const [keluarSengaja, setKeluarSengaja] = useState(false);
  const sudahJalanRef = useRef(false);

  useEffect(() => {
    setPenangananSesiBerakhir(() => {
      setKeluarSengaja(false);
      setPesanSesi(pesanUntukKode("SESI_BERAKHIR"));
      setNama(null);
      setEmail(null);
      setStatusLangganan(null);
      setMasaBerlakuPro(null);
      setPeran("pengajar");
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
        const langganan = normalisasiStatusLangganan(hasil.status_langganan);
        setNama(hasil.nama);
        setEmail(hasil.email);
        setStatusLangganan(langganan);
        setMasaBerlakuPro(
          normalisasiMasaBerlakuPro(hasil.masa_berlaku_pro, langganan),
        );
        setPeran(normalisasiPeran(hasil.peran));
        setStatus("terautentikasi");
      } catch {
        setStatus("tidak-terautentikasi");
      }
    })();
  }, []);

  function tandaiMasuk(
    namaPengguna,
    statusLanggananPengguna,
    peranPengguna,
    masaBerlakuProPengguna = null,
    emailPengguna = null,
  ) {
    const langganan = normalisasiStatusLangganan(statusLanggananPengguna);
    setKeluarSengaja(false);
    setNama(namaPengguna);
    setEmail(emailPengguna);
    setStatusLangganan(langganan);
    setMasaBerlakuPro(
      normalisasiMasaBerlakuPro(masaBerlakuProPengguna, langganan),
    );
    setPeran(normalisasiPeran(peranPengguna));
    setStatus("terautentikasi");
  }

  const muatUlangProfil = useCallback(
    async ({ pertahankanSaatGagal = false } = {}) => {
      try {
        const hasil = await auth.saya();
        const langganan = normalisasiStatusLangganan(hasil.status_langganan);
        if (hasil.nama) {
          setNama(hasil.nama);
        }
        if (hasil.email) {
          setEmail(hasil.email);
        }
        if (langganan !== null || !pertahankanSaatGagal) {
          setStatusLangganan(langganan);
          setMasaBerlakuPro(
            normalisasiMasaBerlakuPro(hasil.masa_berlaku_pro, langganan),
          );
        }
        setPeran(normalisasiPeran(hasil.peran));
        return hasil;
      } catch (error) {
        if (!pertahankanSaatGagal) {
          setStatusLangganan(null);
          setMasaBerlakuPro(null);
        }
        throw error;
      }
    },
    [],
  );

  async function keluar() {
    try {
      await auth.keluar();
    } finally {
      setKeluarSengaja(true);
      setNama(null);
      setEmail(null);
      setStatusLangganan(null);
      setMasaBerlakuPro(null);
      setPeran("pengajar");
      setStatus("tidak-terautentikasi");
    }
  }

  return (
    <AuthContext.Provider
      value={{
        status,
        nama,
        email,
        statusLangganan,
        masaBerlakuPro,
        peran,
        pesanSesi,
        keluarSengaja,
        bersihkanPesanSesi,
        tandaiMasuk,
        muatUlangProfil,
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
