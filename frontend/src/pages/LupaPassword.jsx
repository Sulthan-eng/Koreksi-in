import { useState } from "react";
import { Link } from "react-router-dom";
import * as auth from "../api/auth.js";
import { PESAN_KODE } from "../api/pesan.js";
import { REGEX_EMAIL } from "../lib/validasi.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";

function LupaPassword() {
  const [email, setEmail] = useState("");
  const [terkirim, setTerkirim] = useState(false);
  const [kesalahanEmail, setKesalahanEmail] = useState(null);
  const [kesalahanServer, setKesalahanServer] = useState(null);
  const [sedangKirim, setSedangKirim] = useState(false);

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    if (sedangKirim) return;

    setTerkirim(false);
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
      setTerkirim(true);
    } catch (error) {
      if (error?.kode === "VALIDASI_GAGAL") {
        setKesalahanEmail(PESAN_KODE.FORMAT_EMAIL_TIDAK_VALID);
      } else {
        setKesalahanServer(PESAN_KODE.GAGAL_KIRIM_TAUTAN);
      }
    } finally {
      setSedangKirim(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-latar px-4 py-6">
      <main className="flex w-full max-w-md flex-col gap-6">
        <section className="flex flex-col gap-6 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
          <div className="flex flex-col items-center gap-4">
            <img src="/logo.png" alt="Koreksi-in" className="h-16 w-auto" />
            <h1 className="text-2xl font-bold leading-8 text-teks">
              Lupa Password
            </h1>
          </div>

          {terkirim && (
            <PesanForm
              varian="sukses"
              pesan={PESAN_KODE.TAUTAN_RESET_TERKIRIM}
              kotak
            />
          )}

          {!terkirim && kesalahanServer && (
            <PesanForm varian="galat" pesan={kesalahanServer} kotak />
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
                type="email"
                autoComplete="email"
                value={email}
                onChange={(peristiwa) => setEmail(peristiwa.target.value)}
                aria-invalid={kesalahanEmail ? "true" : undefined}
                aria-describedby={kesalahanEmail ? "galat-email" : undefined}
                className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip"
              />
            </label>
            {kesalahanEmail && (
              <PesanForm
                varian="galat"
                id="galat-email"
                pesan={kesalahanEmail}
                className="-mt-2 text-sm leading-5"
              />
            )}
            <button
              type="submit"
              aria-disabled={sedangKirim ? "true" : undefined}
              onClick={(peristiwa) => {
                if (sedangKirim) peristiwa.preventDefault();
              }}
              className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan aria-disabled:opacity-50"
            >
              {sedangKirim && <Spinner ukuran="size-4" />}
              Kirim Tautan
            </button>
          </form>

          <Link
            to="/masuk"
            className="inline-flex min-h-11 items-center justify-center font-semibold text-biru-utama underline"
          >
            Kembali ke Masuk
          </Link>
        </section>
      </main>
    </div>
  );
}

export default LupaPassword;
