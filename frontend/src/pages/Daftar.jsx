import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as auth from "../api/auth.js";
import { PESAN_KODE } from "../api/pesan.js";
import { REGEX_EMAIL } from "../lib/validasi.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";

function Daftar() {
  const [nama, setNama] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [kesalahan, setKesalahan] = useState(null);
  const [kolomTidakValid, setKolomTidakValid] = useState(new Set());
  const [sedangKirim, setSedangKirim] = useState(false);
  const navigate = useNavigate();

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    const tidakValid = new Set();

    if (nama.trim() === "") {
      tidakValid.add("nama");
    }
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
      await auth.daftar({ nama, email, password });
      navigate("/masuk", {
        state: { pesan: "Akun berhasil dibuat, silakan masuk" },
      });
    } catch (error) {
      const tidakValidServer = new Set();
      if (error.kode === "EMAIL_SUDAH_TERDAFTAR") {
        tidakValidServer.add("email");
      } else if (
        error.kode === "PASSWORD_TERLALU_PENDEK" ||
        error.kode === "PASSWORD_TERLALU_PANJANG"
      ) {
        tidakValidServer.add("password");
      }
      setKolomTidakValid(tidakValidServer);
      setKesalahan(error.pesan);
      setSedangKirim(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-latar px-4 py-6">
      <div className="flex w-full max-w-md flex-col gap-6">
        <section className="flex flex-col gap-6 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
          <div className="flex flex-col items-center gap-4">
            <img src="/logo.png" alt="Koreksi-in" className="h-16 w-auto" />
            <h1 className="text-2xl font-bold leading-8 text-teks">Daftar</h1>
          </div>

          {kesalahan && (
            <PesanForm
              varian="galat"
              pesan={kesalahan}
              id="pesan-daftar"
              kotak
            />
          )}

          <form
            noValidate
            onSubmit={tanganiSubmit}
            className="flex flex-col gap-4"
          >
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-semibold text-teks">Nama</span>
              <input
                id="nama"
                type="text"
                autoComplete="name"
                value={nama}
                onChange={(peristiwa) => setNama(peristiwa.target.value)}
                aria-invalid={kolomTidakValid.has("nama") ? "true" : undefined}
                aria-describedby={kesalahan ? "pesan-daftar" : undefined}
                className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip"
              />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-semibold text-teks">Email</span>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(peristiwa) => setEmail(peristiwa.target.value)}
                aria-invalid={kolomTidakValid.has("email") ? "true" : undefined}
                aria-describedby={kesalahan ? "pesan-daftar" : undefined}
                className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip"
              />
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-semibold text-teks">Password</span>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(peristiwa) => setPassword(peristiwa.target.value)}
                aria-invalid={
                  kolomTidakValid.has("password") ? "true" : undefined
                }
                aria-describedby={
                  kolomTidakValid.has("password")
                    ? "petunjuk-password pesan-daftar"
                    : "petunjuk-password"
                }
                className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip"
              />
              <span
                id="petunjuk-password"
                className="text-sm leading-5 text-teks-redup"
              >
                Minimal 8 karakter.
              </span>
            </label>
            <button
              type="submit"
              disabled={sedangKirim}
              className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan disabled:opacity-50"
            >
              {sedangKirim && <Spinner ukuran="size-4" />}
              Daftar
            </button>
          </form>
        </section>

        <p className="text-center text-sm text-teks-redup">
          Sudah punya akun?{" "}
          <Link
            to="/masuk"
            className="inline-flex min-h-11 items-center font-semibold text-biru-utama underline"
          >
            Masuk
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Daftar;
