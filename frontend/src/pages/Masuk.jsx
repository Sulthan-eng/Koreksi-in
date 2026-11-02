import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import * as auth from "../api/auth.js";
import { useAuth } from "../context/AuthContext.jsx";
import { PESAN_KODE } from "../api/pesan.js";
import { REGEX_EMAIL } from "../lib/validasi.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";

function Masuk() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [kesalahan, setKesalahan] = useState(null);
  const [kolomTidakValid, setKolomTidakValid] = useState(new Set());
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
    const tidakValid = new Set();

    if (email.trim() === "" || !REGEX_EMAIL.test(email.trim())) {
      tidakValid.add("email");
    }
    if (password === "") {
      tidakValid.add("password");
    }

    if (tidakValid.size > 0) {
      setKolomTidakValid(tidakValid);
      setKesalahan(PESAN_KODE.VALIDASI_GAGAL);
      return;
    }

    setSedangKirim(true);
    setKesalahan(null);
    setKolomTidakValid(new Set());

    try {
      await auth.masuk({ email, password });
      const hasil = await auth.saya();
      tandaiMasuk(hasil.nama);
      navigate("/", { replace: true });
    } catch (error) {
      if (error.kode === "LOGIN_GAGAL") {
        setKolomTidakValid(new Set(["email", "password"]));
      }
      setKesalahan(error.pesan);
      setSedangKirim(false);
    }
  }

  const varianPesan = kesalahan
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
              pesan={kesalahan || pesanFlash}
              id="pesan-masuk"
              kotak
            />
          )}

          <form
            noValidate
            onSubmit={tanganiSubmit}
            className="flex flex-col gap-4"
          >
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-semibold text-teks">Email</span>
              <input
                id="email"
                type="text"
                autoComplete="email"
                value={email}
                onChange={(peristiwa) => setEmail(peristiwa.target.value)}
                aria-invalid={kolomTidakValid.has("email") ? "true" : undefined}
                aria-describedby={kesalahan ? "pesan-masuk" : undefined}
                className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip"
              />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-semibold text-teks">Password</span>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(peristiwa) => setPassword(peristiwa.target.value)}
                aria-invalid={
                  kolomTidakValid.has("password") ? "true" : undefined
                }
                aria-describedby={kesalahan ? "pesan-masuk" : undefined}
                className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip"
              />
            </label>
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
