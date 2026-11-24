import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Crown,
  FileCheck,
  FileX,
  Gauge,
  Layers,
  LoaderCircle,
  RefreshCw,
  UserCheck,
  Users,
} from "lucide-react";
import * as adminApi from "../api/admin.js";
import { PESAN_KODE } from "../api/pesan.js";
import { formatAngka, formatJamDiperbarui } from "../lib/dashboardPantauan.js";
import KartuAngka from "../components/KartuAngka.jsx";
import KartuKuota from "../components/KartuKuota.jsx";
import KeadaanData from "../components/KeadaanData.jsx";
import PesanForm from "../components/PesanForm.jsx";

function DashboardPantauan() {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("memuat"); // memuat | siap | gagal
  const [sedangMuatUlang, setSedangMuatUlang] = useState(false);
  const [galatMuatUlang, setGalatMuatUlang] = useState(false);
  const [waktuDiperbarui, setWaktuDiperbarui] = useState(null);
  const idPermintaanRef = useRef(0);
  const sedangMemuatRef = useRef(false);

  const ambilData = useCallback((muatUlang = false) => {
    if (sedangMemuatRef.current) return;
    const id = (idPermintaanRef.current += 1);
    sedangMemuatRef.current = true;

    return adminApi
      .ambilRingkasanDashboard()
      .then((hasil) => {
        if (id !== idPermintaanRef.current) return;
        setData(hasil);
        setWaktuDiperbarui(new Date());
        setStatus("siap");
        setGalatMuatUlang(false);
      })
      .catch(() => {
        if (id !== idPermintaanRef.current) return;
        if (muatUlang) {
          setGalatMuatUlang(true);
        } else {
          setStatus("gagal");
        }
      })
      .finally(() => {
        if (id === idPermintaanRef.current) {
          sedangMemuatRef.current = false;
          setSedangMuatUlang(false);
        }
      });
  }, []);

  useEffect(() => {
    ambilData();
  }, [ambilData]);

  const nonaktif = status === "memuat" || sedangMuatUlang;

  function tanganiMuatUlang() {
    if (status === "memuat" || sedangMemuatRef.current) return;
    const muatUlang = data !== null;
    if (muatUlang) {
      setSedangMuatUlang(true);
    } else {
      setStatus("memuat");
    }
    setGalatMuatUlang(false);
    ambilData(muatUlang);
  }

  const kartuAkun = data
    ? [
        {
          label: "Total akun Pengajar",
          nilai: formatAngka(data.jumlah_akun_pengajar),
          ikon: Users,
          warnaGaris: "bg-merek-biru",
        },
        {
          label: "Akun Free",
          nilai: formatAngka(data.jumlah_akun_free),
          ikon: UserCheck,
          warnaGaris: "bg-merek-hijau",
        },
        {
          label: "Akun Pro",
          nilai: formatAngka(data.jumlah_akun_pro),
          ikon: Crown,
          warnaGaris: "bg-merek-biru",
          kelasIkon: "bg-biru-utama text-permukaan",
          kelasKartu: "max-lg:col-span-2",
        },
      ]
    : [];

  const kartuAktivitas = data
    ? [
        {
          label: "Jumlah batch",
          nilai: formatAngka(data.jumlah_batch),
          ikon: Layers,
          warnaGaris: "bg-merek-biru",
        },
        {
          label: "File Diproses",
          nilai: formatAngka(data.jumlah_file_diproses),
          ikon: LoaderCircle,
          warnaGaris: "bg-biru-utama",
          kelasIkonGambar:
            data.jumlah_file_diproses > 0
              ? "animate-spin motion-reduce:animate-none"
              : "",
        },
        {
          label: "File Selesai",
          nilai: formatAngka(data.jumlah_file_selesai),
          ikon: FileCheck,
          warnaGaris: "bg-merek-hijau",
          kelasIkon: "bg-sangat-mirip-latar text-sangat-mirip",
        },
        {
          label: "File Gagal",
          nilai: formatAngka(data.jumlah_file_gagal),
          ikon: FileX,
          warnaGaris: "bg-kurang-mirip",
          kelasIkon: "bg-kurang-mirip-latar text-kurang-mirip",
          kelasNilai: "text-kurang-mirip",
        },
      ]
    : [];

  return (
    <div className="min-h-screen bg-latar text-teks">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-bold leading-8 text-teks">
              Dashboard Pantauan
            </h1>
            <p className="text-sm leading-5 text-teks-redup">
              Ringkasan akun, aktivitas koreksi, dan pemakaian kuota API.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 lg:shrink-0">
            {data && waktuDiperbarui && (
              <p className="text-sm leading-5 text-teks-redup">
                Diperbarui pukul {formatJamDiperbarui(waktuDiperbarui)}
              </p>
            )}
            <button
              type="button"
              aria-disabled={nonaktif}
              onClick={tanganiMuatUlang}
              className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-garis bg-permukaan px-4 text-sm font-medium text-teks focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama aria-disabled:opacity-60"
            >
              <RefreshCw
                className={`size-4 ${sedangMuatUlang ? "animate-spin motion-reduce:animate-none" : ""}`.trim()}
                aria-hidden="true"
              />
              Muat ulang
            </button>
          </div>
        </div>

        {status === "memuat" && (
          <KeadaanData keadaan="memuat" className="min-h-48" />
        )}

        {status === "gagal" && (
          <PesanForm
            varian="galat"
            pesan={PESAN_KODE.GAGAL_MUAT_DASHBOARD_PANTAUAN}
            kotak
          />
        )}

        {status === "siap" && data && (
          <>
            {galatMuatUlang && (
              <PesanForm
                varian="galat"
                pesan={PESAN_KODE.GAGAL_MUAT_DASHBOARD_PANTAUAN}
                kotak
              />
            )}

            <section className="flex flex-col gap-3">
              <div className="flex items-center justify-between gap-2">
                <h2 className="flex items-center gap-2 text-sm font-semibold leading-5 text-teks-redup">
                  <Users className="size-4" aria-hidden="true" />
                  Akun
                </h2>
                <Link
                  to="/admin/akun-pengajar"
                  className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-biru-utama focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
                >
                  Kelola akun Pengajar
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </div>
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
                {kartuAkun.map((kartu) => (
                  <KartuAngka key={kartu.label} {...kartu} kelasIsi="gap-2" />
                ))}
              </div>
            </section>

            <section className="flex flex-col gap-3">
              <h2 className="flex items-center gap-2 text-sm font-semibold leading-5 text-teks-redup">
                <Layers className="size-4" aria-hidden="true" />
                Aktivitas
              </h2>
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                {kartuAktivitas.map((kartu) => (
                  <KartuAngka key={kartu.label} {...kartu} kelasIsi="gap-2" />
                ))}
              </div>
            </section>

            <section className="flex flex-col gap-3">
              <h2 className="flex items-center gap-2 text-sm font-semibold leading-5 text-teks-redup">
                <Gauge className="size-4" aria-hidden="true" />
                Kuota API
              </h2>
              <KartuKuota kuota={data.kuota} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default DashboardPantauan;
