import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Check, Download, Gauge, Pencil, ScanText, X } from "lucide-react";
import BilahAtas from "../components/BilahAtas.jsx";

const ID_SEKSI = ["cara-kerja", "fitur-utama", "free-dan-pro"];

const CONTOH_HASIL_KOREKSI = [
  {
    nama: "Andi Pratama",
    skor: 92,
    kategori: "Sangat Mirip",
    kelasKategori: "bg-sangat-mirip-latar text-sangat-mirip",
  },
  {
    nama: "Budi Hartono",
    skor: 74,
    kategori: "Cukup Mirip",
    kelasKategori: "bg-cukup-mirip-latar text-cukup-mirip",
  },
  {
    nama: "Citra Dewi",
    skor: 48,
    kategori: "Kurang Mirip",
    kelasKategori: "bg-kurang-mirip-latar text-kurang-mirip",
  },
];

const LANGKAH_CARA_KERJA = [
  "Buat batch dan ketik kunci jawaban.",
  "Unggah lembar jawaban berupa foto atau PDF, beserta nama peserta didik.",
  "Sistem membaca tulisan dan memberi skor kemiripan.",
  "Tinjau hasil, koreksi nilai bila perlu, lalu ekspor (akun Pro).",
];

const BARIS_PERBANDINGAN = [
  { fitur: "Batch aktif", free: "1", pro: "Tidak dibatasi" },
  { fitur: "Soal per batch", free: "15", pro: "30" },
  { fitur: "Jawaban peserta didik per batch", free: "15", pro: "50" },
  { fitur: "File per sekali unggah", free: "10", pro: "10" },
];

const KELAS_KARTU_FITUR =
  "group relative flex flex-col gap-3 overflow-hidden rounded-xl border border-garis bg-permukaan p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-lg motion-reduce:transition-none motion-reduce:hover:translate-y-0";

function Pemasaran() {
  const [seksiAktif, setSeksiAktif] = useState(null);
  const { hash } = useLocation();

  useEffect(() => {
    const pengamat = new IntersectionObserver(
      (entri) => {
        entri.forEach((item) => {
          if (!item.isIntersecting) return;
          setSeksiAktif(item.target.id);
        });
      },
      { rootMargin: "-40% 0px -55% 0px" },
    );

    ID_SEKSI.forEach((id) => {
      const elemen = document.getElementById(id);
      if (elemen) pengamat.observe(elemen);
    });

    return () => pengamat.disconnect();
  }, []);

  useEffect(() => {
    if (!hash) return;
    const idSeksi = decodeURIComponent(hash.slice(1));
    const elemen = document.getElementById(idSeksi);
    if (!elemen) return;
    const gerakKurang = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    elemen.scrollIntoView({
      behavior: gerakKurang ? "auto" : "smooth",
      block: "start",
    });
  }, [hash]);

  return (
    <div className="min-h-screen bg-latar text-teks">
      <BilahAtas varian="publik" seksiAktif={seksiAktif} />

      <main>
        <section className="bg-latar">
          <div className="mx-auto grid w-full max-w-5xl items-center gap-8 px-4 py-12 lg:grid-cols-2 lg:py-16">
            <div className="flex flex-col gap-4">
              <div
                className="h-1 w-16 rounded-full bg-merek-hijau"
                aria-hidden="true"
              ></div>
              <h1 className="text-2xl font-bold leading-8">
                Koreksi esai lebih cepat, nilai akhir tetap di tangan Anda
              </h1>
              <p className="text-base leading-6 text-teks-redup">
                Unggah lembar jawaban peserta didik. Koreksi-in membaca tulisan
                tangan dan memberi skor kemiripan sebagai rekomendasi.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link
                  to="/daftar"
                  className="inline-flex min-h-11 items-center justify-center rounded-lg border border-biru-utama bg-biru-utama px-5 font-semibold text-permukaan no-underline hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
                >
                  Daftar
                </Link>
                <Link
                  to="/masuk"
                  className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-5 font-semibold text-teks no-underline hover:bg-latar focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
                >
                  Masuk
                </Link>
              </div>
            </div>

            <div
              aria-hidden="true"
              className="relative overflow-hidden rounded-xl border border-garis bg-permukaan shadow-sm"
            >
              <span className="absolute inset-x-0 top-0 h-1 bg-merek-hijau"></span>
              <div className="flex flex-col gap-4 p-4 lg:p-6">
                <p className="text-sm font-semibold leading-5 text-teks-redup">
                  Dashboard Hasil Koreksi
                </p>
                <table className="w-full text-left text-sm leading-5">
                  <thead>
                    <tr className="border-b border-garis">
                      <th
                        scope="col"
                        className="py-2 pr-3 font-semibold text-teks-redup"
                      >
                        Peserta Didik
                      </th>
                      <th
                        scope="col"
                        className="py-2 pr-3 text-center font-semibold text-teks-redup"
                      >
                        Skor Kemiripan
                      </th>
                      <th
                        scope="col"
                        className="py-2 font-semibold text-teks-redup"
                      >
                        Kategori Kualitatif
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {CONTOH_HASIL_KOREKSI.map((baris) => (
                      <tr
                        key={baris.nama}
                        className="border-b border-garis last:border-b-0"
                      >
                        <td className="py-3 pr-3 font-semibold text-teks">
                          {baris.nama}
                        </td>
                        <td className="py-3 pr-3 text-center text-teks">
                          {baris.skor}
                        </td>
                        <td className="py-3">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 font-semibold ${baris.kelasKategori}`}
                          >
                            {baris.kategori}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <section id="cara-kerja" className="scroll-mt-24 bg-permukaan">
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-12">
            <h2 className="text-lg font-semibold">Cara kerja</h2>
            <ol className="flex flex-col gap-4 lg:grid lg:grid-cols-4">
              {LANGKAH_CARA_KERJA.map((langkah, indeks) => (
                <li
                  key={indeks}
                  className="group relative flex items-start gap-4 lg:flex-col"
                >
                  <span
                    aria-hidden="true"
                    className="absolute left-4 top-8 -bottom-4 w-0.5 -translate-x-1/2 bg-merek-hijau group-last:hidden lg:hidden"
                  ></span>
                  <span className="relative flex size-8 shrink-0 items-center justify-center rounded-full border-2 border-merek-hijau bg-permukaan text-sm font-semibold leading-5 text-biru-utama lg:self-center">
                    {indeks + 1}
                  </span>
                  <p className="flex-1 pt-1 text-base leading-6 lg:pt-0 lg:text-center">
                    {langkah}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="fitur-utama" className="scroll-mt-24 bg-latar">
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-12">
            <h2 className="text-lg font-semibold">Fitur utama</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <article className={KELAS_KARTU_FITUR}>
                <span
                  className="absolute inset-x-0 top-0 h-1 bg-merek-hijau"
                  aria-hidden="true"
                ></span>
                <span className="flex size-11 items-center justify-center rounded-lg bg-biru-muda text-biru-utama">
                  <ScanText className="size-5" aria-hidden="true" />
                </span>
                <h3 className="font-semibold">Membaca tulisan tangan</h3>
                <p className="text-sm leading-5 text-teks-redup">
                  Lembar jawaban foto atau PDF dibaca menjadi teks.
                </p>
              </article>

              <article className={KELAS_KARTU_FITUR}>
                <span
                  className="absolute inset-x-0 top-0 h-1 bg-merek-biru"
                  aria-hidden="true"
                ></span>
                <span className="flex size-11 items-center justify-center rounded-lg bg-biru-muda text-biru-utama">
                  <Gauge className="size-5" aria-hidden="true" />
                </span>
                <h3 className="font-semibold">Skor kemiripan dan kategori</h3>
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex items-center rounded-full bg-sangat-mirip-latar px-2.5 py-0.5 text-sm font-semibold leading-5 text-sangat-mirip">
                    Sangat Mirip
                  </span>
                  <span className="inline-flex items-center rounded-full bg-cukup-mirip-latar px-2.5 py-0.5 text-sm font-semibold leading-5 text-cukup-mirip">
                    Cukup Mirip
                  </span>
                  <span className="inline-flex items-center rounded-full bg-kurang-mirip-latar px-2.5 py-0.5 text-sm font-semibold leading-5 text-kurang-mirip">
                    Kurang Mirip
                  </span>
                </div>
                <p className="text-sm leading-5 text-teks-redup">
                  Skor sebagai rekomendasi, bukan nilai akhir.
                </p>
              </article>

              <article className={KELAS_KARTU_FITUR}>
                <span
                  className="absolute inset-x-0 top-0 h-1 bg-merek-hijau"
                  aria-hidden="true"
                ></span>
                <span className="flex size-11 items-center justify-center rounded-lg bg-biru-muda text-biru-utama">
                  <Pencil className="size-5" aria-hidden="true" />
                </span>
                <h3 className="font-semibold">Koreksi manual</h3>
                <p className="text-sm leading-5 text-teks-redup">
                  Edit teks hasil baca dan nilai akhir.
                </p>
              </article>

              <article className={KELAS_KARTU_FITUR}>
                <span
                  className="absolute inset-x-0 top-0 h-1 bg-merek-biru"
                  aria-hidden="true"
                ></span>
                <span className="flex size-11 items-center justify-center rounded-lg bg-biru-muda text-biru-utama">
                  <Download className="size-5" aria-hidden="true" />
                </span>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-semibold">Ekspor rekap nilai</h3>
                  <span className="inline-flex items-center rounded-full bg-biru-utama px-2.5 py-0.5 text-sm font-semibold leading-5 text-permukaan">
                    Pro
                  </span>
                </div>
                <p className="text-sm leading-5 text-teks-redup">
                  Unduh rekap nilai dalam file .xlsx.
                </p>
              </article>
            </div>
          </div>
        </section>

        <section id="free-dan-pro" className="scroll-mt-24 bg-permukaan">
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-12">
            <h2 className="text-lg font-semibold">Free dan Pro</h2>
            <div className="overflow-hidden rounded-xl border border-garis bg-permukaan shadow-sm">
              <table className="w-full text-left text-base leading-6">
                <thead>
                  <tr className="border-b border-garis bg-latar">
                    <th scope="col" className="p-4">
                      <span className="sr-only">Fitur</span>
                    </th>
                    <th
                      scope="col"
                      className="p-4 text-center text-sm font-semibold leading-5 text-teks-redup"
                    >
                      Free
                    </th>
                    <th
                      scope="col"
                      className="bg-biru-utama p-4 text-center text-sm font-semibold leading-5 text-permukaan"
                    >
                      Pro
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {BARIS_PERBANDINGAN.map((baris) => (
                    <tr
                      key={baris.fitur}
                      className="border-b border-garis last:border-b-0"
                    >
                      <th scope="row" className="p-4 text-left font-semibold">
                        {baris.fitur}
                      </th>
                      <td className="p-4 text-center text-teks-redup">
                        {baris.free}
                      </td>
                      <td className="bg-biru-muda p-4 text-center font-bold text-biru-utama">
                        {baris.pro}
                      </td>
                    </tr>
                  ))}

                  <tr className="border-b border-garis last:border-b-0">
                    <th scope="row" className="p-4 text-left font-semibold">
                      Ekspor rekap nilai
                    </th>
                    <td className="p-4 text-center text-teks-redup">
                      <span className="inline-flex items-center justify-center gap-1.5">
                        <X className="size-4 shrink-0" aria-hidden="true" />
                        Tidak
                      </span>
                    </td>
                    <td className="bg-biru-muda p-4 text-center font-bold text-biru-utama">
                      <span className="inline-flex items-center justify-center gap-1.5">
                        <Check className="size-4 shrink-0" aria-hidden="true" />
                        Ya
                      </span>
                    </td>
                  </tr>

                  <tr className="border-b border-garis last:border-b-0">
                    <th scope="row" className="p-4 text-left font-semibold">
                      Harga
                    </th>
                    <td className="p-4 text-center text-teks-redup">Gratis</td>
                    <td className="bg-biru-muda p-4 text-center">
                      <span className="font-bold text-biru-utama">
                        Rp 30.000 (1 bulan), Rp 80.000 (3 bulan)
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-sm leading-5 text-teks-redup">
              Langganan Pro tidak diperpanjang otomatis.
            </p>
          </div>
        </section>

        <section className="bg-biru-utama">
          <div className="mx-auto flex w-full max-w-5xl flex-col items-center gap-4 px-4 py-12 text-center">
            <h2 className="text-lg font-semibold text-permukaan">
              Siap mulai mengoreksi lebih cepat?
            </h2>
            <Link
              to="/daftar"
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-permukaan bg-permukaan px-5 font-semibold text-biru-utama no-underline hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-permukaan"
            >
              Daftar
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

export default Pemasaran;
