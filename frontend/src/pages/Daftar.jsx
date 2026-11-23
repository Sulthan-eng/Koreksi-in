import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as auth from "../api/auth.js";
import { PESAN_KODE } from "../api/pesan.js";
import {
  REGEX_EMAIL,
  validasiPanjangEmail,
  validasiPanjangNama,
  validasiPanjangPassword,
} from "../lib/validasi.js";
import {
  fieldPertamaBermasalah,
  galatDaftarDariKode,
} from "../lib/galatAuth.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";
import KolomIsian from "../components/KolomIsian.jsx";
import KolomPassword from "../components/KolomPassword.jsx";

const URUTAN_FIELD_DAFTAR = ["nama", "email", "password"];

function Daftar() {
  const [nama, setNama] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [galat, setGalat] = useState({
    nama: null,
    email: null,
    password: null,
  });
  const [kesalahanUmum, setKesalahanUmum] = useState(null);
  const [sedangKirim, setSedangKirim] = useState(false);
  const navigate = useNavigate();

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    const galatBaru = { nama: null, email: null, password: null };

    if (nama.trim() === "") {
      galatBaru.nama = PESAN_KODE.NAMA_KOSONG;
    } else {
      const kodePanjangNama = validasiPanjangNama(nama);
      if (kodePanjangNama) {
        galatBaru.nama = PESAN_KODE[kodePanjangNama];
      }
    }
    if (email.trim() === "") {
      galatBaru.email = PESAN_KODE.EMAIL_KOSONG;
    } else {
      const kodePanjangEmail = validasiPanjangEmail(email);
      if (kodePanjangEmail) {
        galatBaru.email = PESAN_KODE[kodePanjangEmail];
      } else if (!REGEX_EMAIL.test(email.trim())) {
        galatBaru.email = PESAN_KODE.FORMAT_EMAIL_TIDAK_VALID;
      }
    }
    if (password === "") {
      galatBaru.password = PESAN_KODE.PASSWORD_KOSONG;
    } else {
      const kodePanjang = validasiPanjangPassword(password);
      if (kodePanjang) {
        galatBaru.password = PESAN_KODE[kodePanjang];
      }
    }

    const bermasalah = fieldPertamaBermasalah(galatBaru, URUTAN_FIELD_DAFTAR);
    if (bermasalah) {
      setGalat(galatBaru);
      setKesalahanUmum(null);
      document.getElementById(bermasalah)?.focus();
      return;
    }

    setSedangKirim(true);
    setKesalahanUmum(null);
    setGalat({ nama: null, email: null, password: null });

    try {
      await auth.daftar({ nama, email, password });
      navigate("/masuk", {
        state: { pesan: "Akun berhasil dibuat, silakan masuk" },
      });
    } catch (error) {
      const hasil = galatDaftarDariKode(error.kode, error.pesan);
      setGalat({
        nama: hasil.nama,
        email: hasil.email,
        password: hasil.password,
      });
      setKesalahanUmum(hasil.umum);
      setSedangKirim(false);
      const target = fieldPertamaBermasalah(hasil, URUTAN_FIELD_DAFTAR);
      if (target) document.getElementById(target)?.focus();
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

          {kesalahanUmum && (
            <PesanForm
              varian="galat"
              pesan={kesalahanUmum}
              id="pesan-daftar"
              kotak
            />
          )}

          <form
            noValidate
            onSubmit={tanganiSubmit}
            className="flex flex-col gap-4"
          >
            <KolomIsian
              id="nama"
              label="Nama"
              type="text"
              autoComplete="name"
              value={nama}
              onChange={(peristiwa) => {
                setNama(peristiwa.target.value);
                setGalat((sebelumnya) =>
                  sebelumnya.nama ? { ...sebelumnya, nama: null } : sebelumnya,
                );
              }}
              galat={galat.nama}
              ariaDescribedby={kesalahanUmum ? "pesan-daftar" : undefined}
            />
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
              }}
              galat={galat.email}
              ariaDescribedby={kesalahanUmum ? "pesan-daftar" : undefined}
            />
            <KolomPassword
              id="password"
              label="Password"
              autoComplete="new-password"
              value={password}
              onChange={(peristiwa) => {
                setPassword(peristiwa.target.value);
                setGalat((sebelumnya) =>
                  sebelumnya.password
                    ? { ...sebelumnya, password: null }
                    : sebelumnya,
                );
              }}
              petunjuk="Minimal 8 karakter."
              galat={galat.password}
              ariaDescribedby={kesalahanUmum ? "pesan-daftar" : undefined}
            />
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
