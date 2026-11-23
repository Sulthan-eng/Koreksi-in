import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import * as auth from "../api/auth.js";
import { useAuth } from "../context/AuthContext.jsx";
import { PESAN_KODE } from "../api/pesan.js";
import { REGEX_EMAIL } from "../lib/validasi.js";
import {
  fieldPertamaBermasalah,
  galatMasukDariKode,
} from "../lib/galatAuth.js";
import { berandaUntukPeran } from "../lib/peran.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";
import KolomIsian from "../components/KolomIsian.jsx";
import KolomPassword from "../components/KolomPassword.jsx";

const URUTAN_FIELD_MASUK = ["email", "password"];

function Masuk() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [galat, setGalat] = useState({ email: null, password: null });
  const [kredensialTidakValid, setKredensialTidakValid] = useState(false);
  const [kesalahanUmum, setKesalahanUmum] = useState(null);
  const [sedangKirim, setSedangKirim] = useState(false);
  const { tandaiMasuk, pesanSesi, bersihkanPesanSesi } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [pesanFlash] = useState(
    () => location.state?.pesan ?? pesanSesi ?? null,
  );

  useEffect(() => {
    if (location.state?.pesan) {
      navigate(location.pathname, { replace: true, state: null });
    }
  }, [location, navigate]);

  useEffect(() => {
    if (pesanSesi) {
      bersihkanPesanSesi();
    }
  }, [pesanSesi, bersihkanPesanSesi]);

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    const galatBaru = { email: null, password: null };

    if (email.trim() === "") {
      galatBaru.email = PESAN_KODE.EMAIL_KOSONG;
    } else if (!REGEX_EMAIL.test(email.trim())) {
      galatBaru.email = PESAN_KODE.FORMAT_EMAIL_TIDAK_VALID;
    }
    if (password === "") {
      galatBaru.password = PESAN_KODE.PASSWORD_KOSONG;
    }

    const bermasalah = fieldPertamaBermasalah(galatBaru, URUTAN_FIELD_MASUK);
    if (bermasalah) {
      setGalat(galatBaru);
      setKesalahanUmum(null);
      setKredensialTidakValid(false);
      document.getElementById(bermasalah)?.focus();
      return;
    }

    setSedangKirim(true);
    setKesalahanUmum(null);
    setGalat({ email: null, password: null });
    setKredensialTidakValid(false);

    try {
      await auth.masuk({ email, password });
      const hasil = await auth.saya();
      tandaiMasuk(
        hasil.nama,
        hasil.status_langganan,
        hasil.peran,
        hasil.masa_berlaku_pro,
      );
      navigate(berandaUntukPeran(hasil.peran), { replace: true });
    } catch (error) {
      const hasil = galatMasukDariKode(error.kode, error.pesan);
      setKredensialTidakValid(hasil.kredensialTidakValid);
      setKesalahanUmum(hasil.umum);
      setSedangKirim(false);
    }
  }

  const varianPesan = kesalahanUmum
    ? "galat"
    : pesanFlash
      ? pesanFlash === PESAN_KODE.SESI_BERAKHIR
        ? "netral"
        : "sukses"
      : null;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-latar px-4 py-6">
      <div className="flex w-full max-w-md flex-col gap-6">
        <section className="flex flex-col gap-6 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
          <div className="flex flex-col items-center gap-4">
            <img src="/logo.png" alt="Koreksi-in" className="h-16 w-auto" />
            <h1 className="text-2xl font-bold leading-8 text-teks">Masuk</h1>
          </div>

          {varianPesan && (
            <PesanForm
              varian={varianPesan}
              pesan={kesalahanUmum || pesanFlash}
              id="pesan-masuk"
              kotak
            />
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
              value={email}
              onChange={(peristiwa) => {
                setEmail(peristiwa.target.value);
                setGalat((sebelumnya) =>
                  sebelumnya.email
                    ? { ...sebelumnya, email: null }
                    : sebelumnya,
                );
                setKredensialTidakValid(false);
              }}
              galat={galat.email}
              ariaInvalid={galat.email ? undefined : kredensialTidakValid}
              ariaDescribedby={kesalahanUmum ? "pesan-masuk" : undefined}
            />
            <KolomPassword
              id="password"
              label="Password"
              autoComplete="current-password"
              value={password}
              onChange={(peristiwa) => {
                setPassword(peristiwa.target.value);
                setGalat((sebelumnya) =>
                  sebelumnya.password
                    ? { ...sebelumnya, password: null }
                    : sebelumnya,
                );
                setKredensialTidakValid(false);
              }}
              galat={galat.password}
              ariaInvalid={galat.password ? undefined : kredensialTidakValid}
              ariaDescribedby={kesalahanUmum ? "pesan-masuk" : undefined}
            />
            <Link
              to="/lupa-password"
              className="inline-flex min-h-11 items-center self-end text-sm font-semibold text-biru-utama underline"
            >
              Lupa password?
            </Link>
            <button
              type="submit"
              disabled={sedangKirim}
              className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan disabled:opacity-50"
            >
              {sedangKirim && <Spinner ukuran="size-4" />}
              Masuk
            </button>
          </form>
        </section>

        <p className="text-center text-sm text-teks-redup">
          Belum punya akun?{" "}
          <Link
            to="/daftar"
            className="inline-flex min-h-11 items-center font-semibold text-biru-utama underline"
          >
            Daftar
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Masuk;
