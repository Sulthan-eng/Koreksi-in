import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Mail, ArrowLeft } from "lucide-react";
import * as auth from "../api/auth.js";
import { PESAN_KODE, pesanTautanResetTerkirim } from "../api/pesan.js";
import { REGEX_EMAIL } from "../lib/validasi.js";
import {
  sisaDetik,
  waktuBerakhirBaru,
  bacaStatusTersimpan,
  labelTombolLupaPassword,
  KUNCI_SESSION_STORAGE_LUPA_PASSWORD,
} from "../lib/lupaPassword.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";
import KolomIsian from "../components/KolomIsian.jsx";

function bacaNilaiTersimpan() {
  try {
    return sessionStorage.getItem(KUNCI_SESSION_STORAGE_LUPA_PASSWORD);
  } catch {
    return null;
  }
}

function hapusNilaiTersimpan() {
  try {
    sessionStorage.removeItem(KUNCI_SESSION_STORAGE_LUPA_PASSWORD);
  } catch {
    // diabaikan, sessionStorage opsional untuk pemulihan tampilan
  }
}

function simpanNilai(email, waktuBerakhir) {
  try {
    sessionStorage.setItem(
      KUNCI_SESSION_STORAGE_LUPA_PASSWORD,
      JSON.stringify({ email, waktuBerakhir }),
    );
  } catch {
    // diabaikan, hitungan mundur tetap berjalan di memori
  }
}

function statusAwal() {
  return bacaStatusTersimpan(bacaNilaiTersimpan(), Date.now());
}

function LupaPassword() {
  const [statusTersimpan] = useState(statusAwal);
  const [email, setEmail] = useState(() => statusTersimpan?.email ?? "");
  const [kesalahanEmail, setKesalahanEmail] = useState(null);
  const [kesalahanServer, setKesalahanServer] = useState(null);
  const [sedangKirim, setSedangKirim] = useState(false);
  const [sukses, setSukses] = useState(() => statusTersimpan !== null);
  const [emailSukses, setEmailSukses] = useState(
    () => statusTersimpan?.email ?? null,
  );
  const [sisaDetikTersisa, setSisaDetikTersisa] = useState(
    () => statusTersimpan?.sisaDetik ?? 0,
  );
  const [sedangMenghitungMundur, setSedangMenghitungMundur] = useState(
    () => statusTersimpan !== null,
  );
  const waktuBerakhirRef = useRef(statusTersimpan?.waktuBerakhir ?? null);

  useEffect(() => {
    if (statusTersimpan === null) {
      hapusNilaiTersimpan();
    }
  }, [statusTersimpan]);

  useEffect(() => {
    if (!sedangMenghitungMundur) return;

    const id = setInterval(() => {
      const baru = sisaDetik(waktuBerakhirRef.current, Date.now());
      setSisaDetikTersisa(baru);
      if (baru <= 0) {
        setSedangMenghitungMundur(false);
        hapusNilaiTersimpan();
      }
    }, 1000);

    return () => clearInterval(id);
  }, [sedangMenghitungMundur]);

  function tanganiUbahEmail(peristiwa) {
    setEmail(peristiwa.target.value);
    setKesalahanEmail(null);
    if (sukses || sedangMenghitungMundur) {
      setSukses(false);
      setSedangMenghitungMundur(false);
      setSisaDetikTersisa(0);
      waktuBerakhirRef.current = null;
      hapusNilaiTersimpan();
    }
  }

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    if (sedangKirim || sedangMenghitungMundur) return;

    setKesalahanEmail(null);
    setKesalahanServer(null);

    const emailBersih = email.trim();
    if (emailBersih === "" || !REGEX_EMAIL.test(emailBersih)) {
      setKesalahanEmail(PESAN_KODE.FORMAT_EMAIL_TIDAK_VALID);
      return;
    }

    setSedangKirim(true);
    try {
      await auth.lupaPassword({ email: emailBersih });
      const sekarang = Date.now();
      const berakhir = waktuBerakhirBaru(sekarang);
      waktuBerakhirRef.current = berakhir;
      setEmailSukses(emailBersih);
      setSukses(true);
      setSisaDetikTersisa(sisaDetik(berakhir, sekarang));
      setSedangMenghitungMundur(true);
      simpanNilai(emailBersih, berakhir);
    } catch (error) {
      if (error?.kode === "VALIDASI_GAGAL") {
        setKesalahanEmail(PESAN_KODE.FORMAT_EMAIL_TIDAK_VALID);
      } else {
        setSukses(false);
        setKesalahanServer(PESAN_KODE.GAGAL_KIRIM_TAUTAN);
      }
    } finally {
      setSedangKirim(false);
    }
  }

  const tombolTidakAktif = sedangKirim || sedangMenghitungMundur;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-latar px-4 py-6">
      <main className="flex w-full max-w-md flex-col gap-6">
        <section className="flex flex-col gap-6 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
          <Link
            to="/masuk"
            className="inline-flex min-h-11 w-fit items-center gap-1.5 self-start text-sm font-semibold text-biru-utama underline"
          >
            <ArrowLeft className="size-4" aria-hidden="true" />
            Kembali ke Masuk
          </Link>

          <div className="flex flex-col items-center gap-4">
            <img src="/logo.png" alt="Koreksi-in" className="h-16 w-auto" />
            <h1 className="text-2xl font-bold leading-8 text-teks">
              Lupa Password
            </h1>
            <p className="text-center text-sm leading-5 text-teks-redup">
              Masukkan email akun Anda. Jika terdaftar, kami kirim tautan untuk
              mengatur ulang password.
            </p>
          </div>

          {sukses && !kesalahanServer && (
            <PesanForm
              varian="sukses"
              pesan={pesanTautanResetTerkirim(emailSukses)}
              kotak
            />
          )}

          {!sukses && kesalahanServer && (
            <PesanForm varian="galat" pesan={kesalahanServer} kotak />
          )}

          <form
            noValidate
            onSubmit={tanganiSubmit}
            className="flex flex-col gap-4"
          >
            <KolomIsian
              id="email"
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="nama@email.com"
              Ikon={Mail}
              value={email}
              onChange={tanganiUbahEmail}
              galat={kesalahanEmail}
            />
            <button
              type="submit"
              aria-disabled={tombolTidakAktif ? "true" : undefined}
              onClick={(peristiwa) => {
                if (tombolTidakAktif) peristiwa.preventDefault();
              }}
              className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan aria-disabled:opacity-50"
            >
              {sedangKirim && <Spinner ukuran="size-4" />}
              {labelTombolLupaPassword(sisaDetikTersisa)}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

export default LupaPassword;
