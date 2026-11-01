import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";
import { useAuth } from "../context/AuthContext.jsx";
import KeadaanData from "../components/KeadaanData.jsx";
import Spinner from "../components/Spinner.jsx";

function formatTanggal(iso) {
  return new Date(iso).toLocaleDateString("id-ID", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function Beranda() {
  const [daftarBatch, setDaftarBatch] = useState([]);
  const [status, setStatus] = useState("memuat");
  const [kesalahan, setKesalahan] = useState(null);
  const [formTerbuka, setFormTerbuka] = useState(false);
  const [namaBatch, setNamaBatch] = useState("");
  const [kesalahanForm, setKesalahanForm] = useState(null);
  const [sedangKirim, setSedangKirim] = useState(false);
  const navigate = useNavigate();
  const { nama } = useAuth();

  useEffect(() => {
    let dibatalkan = false;
    (async () => {
      try {
        const hasil = await batchApi.daftarBatch();
        if (!dibatalkan) {
          setDaftarBatch(hasil);
          setStatus("siap");
        }
      } catch (error) {
        if (!dibatalkan) {
          setKesalahan(error.pesan);
          setStatus("gagal");
        }
      }
    })();
    return () => {
      dibatalkan = true;
    };
  }, []);

  async function tanganiBuatBatch(peristiwa) {
    peristiwa.preventDefault();
    setKesalahanForm(null);

    if (namaBatch.trim() === "") {
      setKesalahanForm(PESAN_KODE.NAMA_BATCH_KOSONG);
      return;
    }

    setSedangKirim(true);
    try {
      const batch = await batchApi.buatBatch({ nama_batch: namaBatch });
      navigate(`/batch/${batch.id_batch}`);
    } catch (error) {
      setKesalahanForm(error.pesan || PESAN_KODE.GAGAL_BUAT_BATCH);
      setSedangKirim(false);
    }
  }

  if (status === "memuat") {
    return (
      <div className="min-h-screen bg-latar">
        <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-bold leading-8 text-teks">
              Selamat datang, {nama}
            </h1>
            <p className="text-teks-redup">
              Kelola batch koreksi esai Anda di sini.
            </p>
          </div>
          <KeadaanData keadaan="memuat" className="min-h-48" />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-latar">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold leading-8 text-teks">
            Selamat datang, {nama}
          </h1>
          <p className="text-teks-redup">
            Kelola batch koreksi esai Anda di sini.
          </p>
        </div>

        {status === "gagal" && (
          <KeadaanData
            keadaan="gagal"
            pesan={kesalahan || PESAN_KODE.KONEKSI_TERPUTUS}
          />
        )}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-teks">Batch Koreksi</h2>
          <button
            type="button"
            onClick={() => setFormTerbuka((sebelumnya) => !sebelumnya)}
            className="inline-flex min-h-11 items-center justify-center rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan"
          >
            Buat Batch Baru
          </button>
        </div>

        {formTerbuka && (
          <form
            onSubmit={tanganiBuatBatch}
            noValidate
            className="flex flex-col gap-4 rounded-lg border border-garis bg-permukaan p-6 shadow-sm"
          >
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-semibold text-teks">
                Nama Batch
              </span>
              <input
                type="text"
                maxLength={100}
                value={namaBatch}
                onChange={(peristiwa) => setNamaBatch(peristiwa.target.value)}
                aria-invalid={kesalahanForm ? "true" : undefined}
                aria-describedby={kesalahanForm ? "galat-nama" : undefined}
                className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip"
              />
            </label>
            {kesalahanForm && (
              <p
                id="galat-nama"
                role="alert"
                className="text-sm leading-5 text-kurang-mirip"
              >
                {kesalahanForm}
              </p>
            )}
            <div>
              <button
                type="submit"
                disabled={sedangKirim}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan disabled:opacity-50"
              >
                {sedangKirim && <Spinner ukuran="size-4" />}
                Buat
              </button>
            </div>
          </form>
        )}

        {status === "siap" && daftarBatch.length === 0 && (
          <KeadaanData keadaan="kosong" pesan={PESAN_KODE.BELUM_ADA_BATCH} />
        )}

        {status === "siap" && daftarBatch.length > 0 && (
          <ul className="flex flex-col rounded-lg border border-garis bg-permukaan shadow-sm">
            {daftarBatch.map((batch) => (
              <li
                key={batch.id_batch}
                className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-garis p-4 last:border-b-0"
              >
                <div className="flex min-w-0 flex-1 flex-col gap-1">
                  <Link
                    to={`/batch/${batch.id_batch}`}
                    className="font-semibold text-biru-utama underline"
                  >
                    {batch.nama_batch}
                  </Link>
                  <span className="text-sm leading-5 text-teks-redup">
                    {formatTanggal(batch.dibuat_pada)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}

export default Beranda;
