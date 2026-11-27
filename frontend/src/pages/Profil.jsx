import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ChevronRight,
  CircleAlert,
  Crown,
  Lock,
  Pencil,
  User,
  UserCheck,
} from "lucide-react";
import * as auth from "../api/auth.js";
import { PESAN_KODE, pesanBerlakuHingga } from "../api/pesan.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatTanggalWib } from "../lib/akunPengajar.js";
import {
  validasiPanjangNama,
  validasiPanjangPassword,
} from "../lib/validasi.js";
import {
  fieldPertamaBermasalah,
  galatGantiPasswordDariKode,
  galatUbahProfilDariKode,
} from "../lib/galatAuth.js";
import { inisialDariNama } from "../lib/inisial.js";
import KeadaanData from "../components/KeadaanData.jsx";
import KolomIsian from "../components/KolomIsian.jsx";
import KolomPassword from "../components/KolomPassword.jsx";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";

const URUTAN_FIELD_GANTI_PASSWORD = [
  "passwordLama",
  "passwordBaru",
  "konfirmasiPasswordBaru",
];
const ID_KOLOM_GANTI_PASSWORD = {
  passwordLama: "password_lama",
  passwordBaru: "password_baru",
  konfirmasiPasswordBaru: "konfirmasi_password_baru",
};

function Profil() {
  const {
    nama,
    email,
    statusLangganan,
    masaBerlakuPro,
    dibuatPada,
    muatUlangProfil,
  } = useAuth();
  const [sedangMuatProfilAwal, setSedangMuatProfilAwal] = useState(true);

  const [ubahNamaTerbuka, setUbahNamaTerbuka] = useState(false);
  const [namaInput, setNamaInput] = useState("");
  const [galatNama, setGalatNama] = useState(null);
  const [kesalahanUmumNama, setKesalahanUmumNama] = useState(null);
  const [sedangSimpanNama, setSedangSimpanNama] = useState(false);
  const pensilRef = useRef(null);
  const sudahPernahDibukaRef = useRef(false);

  const [passwordLama, setPasswordLama] = useState("");
  const [passwordBaru, setPasswordBaru] = useState("");
  const [konfirmasiPasswordBaru, setKonfirmasiPasswordBaru] = useState("");
  const [galatPassword, setGalatPassword] = useState({
    passwordLama: null,
    passwordBaru: null,
    konfirmasiPasswordBaru: null,
  });
  const [kesalahanUmumPassword, setKesalahanUmumPassword] = useState(null);
  const [sedangKirimPassword, setSedangKirimPassword] = useState(false);
  const [passwordBerhasilDiubah, setPasswordBerhasilDiubah] = useState(false);

  useEffect(() => {
    let dibatalkan = false;
    muatUlangProfil({ pertahankanSaatGagal: true })
      .catch(() => {})
      .finally(() => {
        if (!dibatalkan) setSedangMuatProfilAwal(false);
      });
    return () => {
      dibatalkan = true;
    };
  }, [muatUlangProfil]);

  function bukaUbahNama() {
    setNamaInput(nama ?? "");
    setGalatNama(null);
    setKesalahanUmumNama(null);
    setUbahNamaTerbuka(true);
  }

  function tutupUbahNama() {
    setUbahNamaTerbuka(false);
  }

  useEffect(() => {
    if (!sudahPernahDibukaRef.current) {
      sudahPernahDibukaRef.current = true;
      return;
    }
    if (ubahNamaTerbuka) {
      document.getElementById("nama-baru")?.focus();
    } else {
      pensilRef.current?.focus();
    }
  }, [ubahNamaTerbuka]);

  async function tanganiSubmitNama(peristiwa) {
    peristiwa.preventDefault();
    if (sedangSimpanNama) return;

    if (namaInput.trim() === "") {
      setGalatNama(PESAN_KODE.NAMA_KOSONG);
      setKesalahanUmumNama(null);
      document.getElementById("nama-baru")?.focus();
      return;
    }
    const kodePanjang = validasiPanjangNama(namaInput);
    if (kodePanjang) {
      setGalatNama(PESAN_KODE[kodePanjang]);
      setKesalahanUmumNama(null);
      document.getElementById("nama-baru")?.focus();
      return;
    }

    setSedangSimpanNama(true);
    setGalatNama(null);
    setKesalahanUmumNama(null);
    try {
      await auth.ubahProfil({ nama: namaInput });
      await muatUlangProfil({ pertahankanSaatGagal: true });
      setUbahNamaTerbuka(false);
    } catch (error) {
      const hasil = galatUbahProfilDariKode(error?.kode, error?.pesan);
      setGalatNama(hasil.nama);
      setKesalahanUmumNama(hasil.umum);
      if (hasil.nama) document.getElementById("nama-baru")?.focus();
    } finally {
      setSedangSimpanNama(false);
    }
  }

  async function tanganiSubmitPassword(peristiwa) {
    peristiwa.preventDefault();
    if (sedangKirimPassword) return;

    const galatBaru = {
      passwordLama: null,
      passwordBaru: null,
      konfirmasiPasswordBaru: null,
    };

    if (passwordLama === "") {
      galatBaru.passwordLama = PESAN_KODE.PASSWORD_KOSONG;
    }
    if (passwordBaru === "") {
      galatBaru.passwordBaru = PESAN_KODE.PASSWORD_KOSONG;
    } else {
      const kodePanjang = validasiPanjangPassword(passwordBaru);
      if (kodePanjang) {
        galatBaru.passwordBaru = PESAN_KODE[kodePanjang];
      }
    }
    if (konfirmasiPasswordBaru === "") {
      galatBaru.konfirmasiPasswordBaru = PESAN_KODE.KONFIRMASI_PASSWORD_KOSONG;
    } else if (passwordBaru !== "" && konfirmasiPasswordBaru !== passwordBaru) {
      galatBaru.konfirmasiPasswordBaru =
        PESAN_KODE.KONFIRMASI_PASSWORD_TIDAK_SAMA;
    }

    const bermasalah = fieldPertamaBermasalah(
      galatBaru,
      URUTAN_FIELD_GANTI_PASSWORD,
    );
    if (bermasalah) {
      setGalatPassword(galatBaru);
      setKesalahanUmumPassword(null);
      setPasswordBerhasilDiubah(false);
      document.getElementById(ID_KOLOM_GANTI_PASSWORD[bermasalah])?.focus();
      return;
    }

    setSedangKirimPassword(true);
    setKesalahanUmumPassword(null);
    setPasswordBerhasilDiubah(false);
    setGalatPassword({
      passwordLama: null,
      passwordBaru: null,
      konfirmasiPasswordBaru: null,
    });

    try {
      await auth.gantiPassword({
        password_lama: passwordLama,
        password_baru: passwordBaru,
        konfirmasi_password_baru: konfirmasiPasswordBaru,
      });
      setPasswordLama("");
      setPasswordBaru("");
      setKonfirmasiPasswordBaru("");
      setPasswordBerhasilDiubah(true);
    } catch (error) {
      const hasil = galatGantiPasswordDariKode(error?.kode, error?.pesan);
      setGalatPassword({
        passwordLama: hasil.passwordLama,
        passwordBaru: hasil.passwordBaru,
        konfirmasiPasswordBaru: null,
      });
      setKesalahanUmumPassword(hasil.umum);
      const target = fieldPertamaBermasalah(hasil, [
        "passwordLama",
        "passwordBaru",
      ]);
      if (target) {
        document.getElementById(ID_KOLOM_GANTI_PASSWORD[target])?.focus();
      }
    } finally {
      setSedangKirimPassword(false);
    }
  }

  const tanggalBerlakuTeks =
    statusLangganan === "pro" && masaBerlakuPro
      ? formatTanggalWib(masaBerlakuPro)
      : "";

  return (
    <div className="min-h-screen bg-latar text-teks">
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6">
        <div className="flex items-center gap-4">
          <span
            className="inline-flex size-16 shrink-0 items-center justify-center rounded-full bg-biru-utama text-2xl font-bold text-permukaan"
            aria-hidden="true"
          >
            {inisialDariNama(nama)}
          </span>
          <div className="flex min-w-0 flex-col gap-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-teks-redup">
              Profil
            </p>
            <h1 className="wrap-anywhere text-2xl font-bold leading-8">
              {nama}
            </h1>
          </div>
        </div>

        {sedangMuatProfilAwal && !dibuatPada ? (
          <KeadaanData keadaan="memuat" className="py-12" />
        ) : !dibuatPada ? (
          <p
            role="alert"
            className="flex items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
          >
            <CircleAlert
              className="mt-0.5 size-4 shrink-0"
              aria-hidden="true"
            />
            <span>{PESAN_KODE.GAGAL_MUAT_PROFIL}</span>
          </p>
        ) : (
          <>
            <section className="flex flex-col gap-5 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
              <h2 className="text-lg font-semibold">Informasi akun</h2>
              <dl className="grid gap-5">
                {ubahNamaTerbuka ? (
                  <form
                    noValidate
                    onSubmit={tanganiSubmitNama}
                    className="flex flex-col gap-3"
                  >
                    {kesalahanUmumNama && (
                      <PesanForm
                        varian="galat"
                        pesan={kesalahanUmumNama}
                        id="pesan-ubah-nama"
                        kotak
                      />
                    )}
                    <KolomIsian
                      id="nama-baru"
                      label="Nama"
                      type="text"
                      autoComplete="name"
                      Ikon={User}
                      value={namaInput}
                      onChange={(peristiwa) => {
                        setNamaInput(peristiwa.target.value);
                        setGalatNama(null);
                      }}
                      galat={galatNama}
                      ariaDescribedby={
                        kesalahanUmumNama ? "pesan-ubah-nama" : undefined
                      }
                    />
                    <div className="flex flex-wrap gap-3">
                      <button
                        type="submit"
                        disabled={sedangSimpanNama}
                        className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-5 font-semibold text-permukaan disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
                      >
                        {sedangSimpanNama && <Spinner ukuran="size-4" />}
                        Simpan
                      </button>
                      <button
                        type="button"
                        disabled={sedangSimpanNama}
                        onClick={tutupUbahNama}
                        className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-5 font-semibold disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
                      >
                        Batal
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex min-w-0 flex-col gap-1">
                      <dt className="text-xs font-semibold uppercase tracking-wider text-teks-redup">
                        Nama
                      </dt>
                      <dd className="wrap-anywhere text-base leading-6">
                        {nama}
                      </dd>
                    </div>
                    <button
                      ref={pensilRef}
                      type="button"
                      onClick={bukaUbahNama}
                      aria-label="Ubah nama"
                      className="inline-flex size-11 shrink-0 items-center justify-center rounded-lg border border-garis bg-latar focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
                    >
                      <Pencil className="size-4" aria-hidden="true" />
                    </button>
                  </div>
                )}
                <div className="flex flex-col gap-1">
                  <dt className="text-xs font-semibold uppercase tracking-wider text-teks-redup">
                    Email
                  </dt>
                  <dd className="text-base leading-6">{email}</dd>
                  <p className="text-sm leading-5 text-teks-redup">
                    Email tidak dapat diubah.
                  </p>
                </div>
                <div className="flex flex-col gap-1">
                  <dt className="text-xs font-semibold uppercase tracking-wider text-teks-redup">
                    Bergabung sejak
                  </dt>
                  <dd className="text-base leading-6">
                    {formatTanggalWib(dibuatPada)}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="flex flex-col gap-4 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
              <h2 className="text-lg font-semibold">Paket</h2>
              <div className="flex flex-wrap items-center gap-3">
                {statusLangganan === "pro" ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-biru-utama px-2.5 py-0.5 text-sm font-semibold leading-5 whitespace-nowrap text-permukaan">
                    <Crown className="size-4" aria-hidden="true" />
                    PRO
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-garis bg-latar px-2.5 py-0.5 text-sm font-semibold leading-5 whitespace-nowrap text-teks-redup">
                    <UserCheck className="size-4" aria-hidden="true" />
                    FREE
                  </span>
                )}
                {statusLangganan === "pro" ? (
                  tanggalBerlakuTeks && (
                    <p className="text-base leading-6">
                      {pesanBerlakuHingga(tanggalBerlakuTeks)}
                    </p>
                  )
                ) : (
                  <p className="text-base leading-6">
                    {PESAN_KODE.AKUN_MEMAKAI_FREE}
                  </p>
                )}
              </div>
              <Link
                to="/langganan"
                className="inline-flex min-h-11 w-fit items-center gap-1 font-semibold text-biru-utama underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
              >
                Lihat riwayat pembayaran
                <ChevronRight className="size-4" aria-hidden="true" />
              </Link>
            </section>

            <section className="flex flex-col gap-5 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
              <h2 className="text-lg font-semibold">Ganti kata sandi</h2>
              {passwordBerhasilDiubah && (
                <PesanForm
                  varian="sukses"
                  pesan={PESAN_KODE.KATA_SANDI_BERHASIL_DIUBAH}
                  kotak
                />
              )}
              {kesalahanUmumPassword && (
                <PesanForm
                  varian="galat"
                  pesan={kesalahanUmumPassword}
                  id="pesan-ganti-password"
                  kotak
                />
              )}
              <form
                noValidate
                onSubmit={tanganiSubmitPassword}
                className="flex flex-col gap-4"
              >
                <KolomPassword
                  id="password_lama"
                  label="Kata sandi saat ini"
                  autoComplete="current-password"
                  placeholder="Masukkan kata sandi saat ini"
                  Ikon={Lock}
                  value={passwordLama}
                  onChange={(peristiwa) => {
                    setPasswordLama(peristiwa.target.value);
                    setGalatPassword((sebelumnya) =>
                      sebelumnya.passwordLama
                        ? { ...sebelumnya, passwordLama: null }
                        : sebelumnya,
                    );
                    setPasswordBerhasilDiubah(false);
                  }}
                  galat={galatPassword.passwordLama}
                  ariaDescribedby={
                    kesalahanUmumPassword ? "pesan-ganti-password" : undefined
                  }
                />
                <KolomPassword
                  id="password_baru"
                  label="Kata sandi baru"
                  autoComplete="new-password"
                  placeholder="Masukkan kata sandi baru"
                  Ikon={Lock}
                  petunjuk="Minimal 8 karakter."
                  value={passwordBaru}
                  onChange={(peristiwa) => {
                    setPasswordBaru(peristiwa.target.value);
                    setGalatPassword((sebelumnya) =>
                      sebelumnya.passwordBaru ||
                      sebelumnya.konfirmasiPasswordBaru
                        ? {
                            ...sebelumnya,
                            passwordBaru: null,
                            konfirmasiPasswordBaru: null,
                          }
                        : sebelumnya,
                    );
                    setPasswordBerhasilDiubah(false);
                  }}
                  galat={galatPassword.passwordBaru}
                  ariaDescribedby={
                    kesalahanUmumPassword ? "pesan-ganti-password" : undefined
                  }
                />
                <KolomPassword
                  id="konfirmasi_password_baru"
                  label="Ulangi kata sandi baru"
                  autoComplete="new-password"
                  placeholder="Ulangi kata sandi baru"
                  Ikon={Lock}
                  value={konfirmasiPasswordBaru}
                  onChange={(peristiwa) => {
                    setKonfirmasiPasswordBaru(peristiwa.target.value);
                    setGalatPassword((sebelumnya) =>
                      sebelumnya.konfirmasiPasswordBaru
                        ? { ...sebelumnya, konfirmasiPasswordBaru: null }
                        : sebelumnya,
                    );
                    setPasswordBerhasilDiubah(false);
                  }}
                  galat={galatPassword.konfirmasiPasswordBaru}
                  ariaDescribedby={
                    kesalahanUmumPassword ? "pesan-ganti-password" : undefined
                  }
                />
                <div>
                  <button
                    type="submit"
                    disabled={sedangKirimPassword}
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-5 font-semibold text-permukaan disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
                  >
                    {sedangKirimPassword && <Spinner ukuran="size-4" />}
                    Simpan
                  </button>
                </div>
              </form>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default Profil;
