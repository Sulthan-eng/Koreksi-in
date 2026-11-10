import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import * as auth from "../api/auth.js";
import { PESAN_KODE, pesanUntukKode } from "../api/pesan.js";
import { useAuth } from "../context/AuthContext.jsx";
import { validasiPasswordBaru } from "../lib/validasi.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";

function AturUlangPassword() {
  const [token] = useState(() => {
    const nilai = new URLSearchParams(window.location.search).get("token");
    return nilai && nilai.trim() !== "" ? nilai.trim() : null;
  });
  const [tokenTidakSah, setTokenTidakSah] = useState(() => token === null);
  const [passwordBaru, setPasswordBaru] = useState("");
  const [konfirmasiPassword, setKonfirmasiPassword] = useState("");
  const [kesalahan, setKesalahan] = useState(null);
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

    setKesalahan(null);

    const kodeGalat = validasiPasswordBaru(passwordBaru, konfirmasiPassword);
    if (kodeGalat) {
      setKesalahan(pesanUntukKode(kodeGalat));
      return;
    }

    setSedangKirim(true);
    try {
      await auth.aturUlangPassword({
        token,
        password_baru: passwordBaru,
      });
    } catch (error) {
      if (error?.kode === "TOKEN_RESET_TIDAK_VALID") {
        setTokenTidakSah(true);
      } else if (
        error?.kode === "PASSWORD_TERLALU_PENDEK" ||
        error?.kode === "PASSWORD_TERLALU_PANJANG"
      ) {
        setKesalahan(pesanUntukKode(error.kode));
      } else {
        setKesalahan(PESAN_KODE.GAGAL_UBAH_PASSWORD);
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
            <form
              noValidate
              onSubmit={tanganiSubmit}
              className="flex flex-col gap-4"
            >
              {kesalahan && (
                <PesanForm varian="galat" pesan={kesalahan} kotak />
              )}

              <label className="flex flex-col gap-1.5">
                <span className="text-sm font-semibold text-teks">
                  Password baru
                </span>
                <input
                  id="password_baru"
                  type="password"
                  autoComplete="new-password"
                  value={passwordBaru}
                  onChange={(peristiwa) =>
                    setPasswordBaru(peristiwa.target.value)
                  }
                  className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks"
                />
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-sm font-semibold text-teks">
                  Konfirmasi password
                </span>
                <input
                  id="konfirmasi_password"
                  type="password"
                  autoComplete="new-password"
                  value={konfirmasiPassword}
                  onChange={(peristiwa) =>
                    setKonfirmasiPassword(peristiwa.target.value)
                  }
                  className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks"
                />
              </label>

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
          )}
        </section>
      </main>
    </div>
  );
}

export default AturUlangPassword;
