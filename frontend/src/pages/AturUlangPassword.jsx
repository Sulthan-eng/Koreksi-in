import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Lock } from "lucide-react";
import * as auth from "../api/auth.js";
import { PESAN_KODE } from "../api/pesan.js";
import { useAuth } from "../context/AuthContext.jsx";
import { validasiPanjangPassword } from "../lib/validasi.js";
import {
  fieldPertamaBermasalah,
  galatAturUlangPasswordDariKode,
} from "../lib/galatAuth.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";
import KolomPassword from "../components/KolomPassword.jsx";

const URUTAN_FIELD_ATUR_ULANG = ["passwordBaru", "konfirmasiPassword"];
const ID_KOLOM_ATUR_ULANG = {
  passwordBaru: "password_baru",
  konfirmasiPassword: "konfirmasi_password",
};

function AturUlangPassword() {
  const [token] = useState(() => {
    const nilai = new URLSearchParams(window.location.search).get("token");
    return nilai && nilai.trim() !== "" ? nilai.trim() : null;
  });
  const [tokenTidakSah, setTokenTidakSah] = useState(() => token === null);
  const [passwordBaru, setPasswordBaru] = useState("");
  const [konfirmasiPassword, setKonfirmasiPassword] = useState("");
  const [galat, setGalat] = useState({
    passwordBaru: null,
    konfirmasiPassword: null,
  });
  const [kesalahanUmum, setKesalahanUmum] = useState(null);
  const [sedangKirim, setSedangKirim] = useState(false);

  const { status, keluar } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.search) {
      navigate(location.pathname, { replace: true });
    }
  }, [location.pathname, location.search, navigate]);

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    if (sedangKirim) return;

    const galatBaru = { passwordBaru: null, konfirmasiPassword: null };

    if (passwordBaru === "") {
      galatBaru.passwordBaru = PESAN_KODE.PASSWORD_KOSONG;
    } else {
      const kodePanjang = validasiPanjangPassword(passwordBaru);
      if (kodePanjang) {
        galatBaru.passwordBaru = PESAN_KODE[kodePanjang];
      }
    }
    if (konfirmasiPassword === "") {
      galatBaru.konfirmasiPassword = PESAN_KODE.KONFIRMASI_PASSWORD_KOSONG;
    } else if (passwordBaru !== "" && konfirmasiPassword !== passwordBaru) {
      galatBaru.konfirmasiPassword = PESAN_KODE.KONFIRMASI_PASSWORD_TIDAK_SAMA;
    }

    const bermasalah = fieldPertamaBermasalah(
      galatBaru,
      URUTAN_FIELD_ATUR_ULANG,
    );
    if (bermasalah) {
      setGalat(galatBaru);
      setKesalahanUmum(null);
      document.getElementById(ID_KOLOM_ATUR_ULANG[bermasalah])?.focus();
      return;
    }

    setSedangKirim(true);
    setKesalahanUmum(null);
    setGalat({ passwordBaru: null, konfirmasiPassword: null });

    try {
      await auth.aturUlangPassword({
        token,
        password_baru: passwordBaru,
      });
    } catch (error) {
      if (error?.kode === "TOKEN_RESET_TIDAK_VALID") {
        setTokenTidakSah(true);
      } else {
        const hasil = galatAturUlangPasswordDariKode(
          error?.kode,
          error?.pesan || PESAN_KODE.GAGAL_UBAH_PASSWORD,
        );
        setGalat({
          passwordBaru: hasil.passwordBaru,
          konfirmasiPassword: hasil.konfirmasiPassword,
        });
        setKesalahanUmum(hasil.umum);
        const target = fieldPertamaBermasalah(hasil, URUTAN_FIELD_ATUR_ULANG);
        if (target) {
          document.getElementById(ID_KOLOM_ATUR_ULANG[target])?.focus();
        }
      }
      setSedangKirim(false);
      return;
    }

    if (status === "terautentikasi") {
      try {
        await keluar();
      } catch {
        // Kegagalan membersihkan sesi diabaikan karena password sudah berhasil diganti.
      }
    }

    navigate("/masuk", {
      replace: true,
      state: { pesan: PESAN_KODE.PASSWORD_BERHASIL_DIUBAH },
    });
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-latar px-4 py-6">
      <main className="flex w-full max-w-md flex-col gap-6">
        <section className="flex flex-col gap-6 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
          <div className="flex flex-col items-center gap-4">
            <img src="/logo.png" alt="Koreksi-in" className="h-16 w-auto" />
            <h1 className="text-2xl font-bold leading-8 text-teks">
              Atur Ulang Password
            </h1>
            <p className="text-center text-sm leading-5 text-teks-redup">
              Buat password baru untuk akunmu. Minimal 8 karakter.
            </p>
          </div>

          {tokenTidakSah ? (
            <div className="flex flex-col gap-4">
              <PesanForm
                varian="galat"
                pesan={PESAN_KODE.TOKEN_RESET_TIDAK_VALID}
                kotak
              />
              <Link
                to="/lupa-password"
                className="inline-flex min-h-11 items-center justify-center font-semibold text-biru-utama underline"
              >
                Lupa Password
              </Link>
            </div>
          ) : (
            <>
              {kesalahanUmum && (
                <PesanForm
                  varian="galat"
                  pesan={kesalahanUmum}
                  id="pesan-atur-ulang"
                  kotak
                />
              )}

              <form
                noValidate
                onSubmit={tanganiSubmit}
                className="flex flex-col gap-4"
              >
                <KolomPassword
                  id="password_baru"
                  label="Password baru"
                  autoComplete="new-password"
                  placeholder="Password baru"
                  Ikon={Lock}
                  value={passwordBaru}
                  onChange={(peristiwa) => {
                    setPasswordBaru(peristiwa.target.value);
                    setGalat((sebelumnya) =>
                      sebelumnya.passwordBaru || sebelumnya.konfirmasiPassword
                        ? {
                            ...sebelumnya,
                            passwordBaru: null,
                            konfirmasiPassword: null,
                          }
                        : sebelumnya,
                    );
                  }}
                  galat={galat.passwordBaru}
                  ariaDescribedby={
                    kesalahanUmum ? "pesan-atur-ulang" : undefined
                  }
                />

                <KolomPassword
                  id="konfirmasi_password"
                  label="Konfirmasi password"
                  autoComplete="new-password"
                  placeholder="Ulangi password baru"
                  Ikon={Lock}
                  value={konfirmasiPassword}
                  onChange={(peristiwa) => {
                    setKonfirmasiPassword(peristiwa.target.value);
                    setGalat((sebelumnya) =>
                      sebelumnya.konfirmasiPassword
                        ? { ...sebelumnya, konfirmasiPassword: null }
                        : sebelumnya,
                    );
                  }}
                  galat={galat.konfirmasiPassword}
                  ariaDescribedby={
                    kesalahanUmum ? "pesan-atur-ulang" : undefined
                  }
                />

                <button
                  type="submit"
                  aria-disabled={sedangKirim ? "true" : undefined}
                  onClick={(peristiwa) => {
                    if (sedangKirim) peristiwa.preventDefault();
                  }}
                  className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan aria-disabled:opacity-50"
                >
                  {sedangKirim && <Spinner ukuran="size-4" />}
                  Simpan Password
                </button>
              </form>
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default AturUlangPassword;
