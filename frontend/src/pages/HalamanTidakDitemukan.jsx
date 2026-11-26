import { useAuth } from "../context/AuthContext.jsx";
import { berandaUntukPeran } from "../lib/peran.js";
import { SearchX, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

function HalamanTidakDitemukan() {
  const { status, peran } = useAuth();

  const tujuan = berandaUntukPeran(peran);
  let label;
  if (status !== "terautentikasi") {
    label = "Kembali ke beranda";
  } else if (peran === "admin") {
    label = "Kembali ke Dashboard Pantauan";
  } else {
    label = "Kembali ke Beranda";
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-latar px-4 py-6">
      <main className="flex w-full max-w-md flex-col items-center gap-6 text-center">
        <SearchX className="size-6 text-teks-redup" aria-hidden="true" />
        <h1 className="text-2xl font-bold leading-8 text-teks">
          Halaman tidak ditemukan
        </h1>
        <p className="text-base leading-6 text-teks-redup">
          Halaman yang Anda cari tidak tersedia.
        </p>
        <Link
          to={tujuan}
          className="inline-flex min-h-11 items-center justify-center gap-1.5 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan no-underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
          aria-label={label}
        >
          <ArrowLeft className="size-4" aria-hidden="true" />
          {label}
        </Link>
      </main>
    </div>
  );
}

export default HalamanTidakDitemukan;
