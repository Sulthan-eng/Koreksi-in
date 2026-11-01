import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as batchApi from "../api/batch.js";
import { useAuth } from "../context/AuthContext.jsx";
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
    setSedangKirim(true);
    setKesalahanForm(null);
    try {
      const batch = await batchApi.buatBatch({ nama_batch: namaBatch });
      navigate(`/batch/${batch.id_batch}`);
    } catch (error) {
      setKesalahanForm(error.pesan);
      setSedangKirim(false);
    }
  }

  return (
    <div className="min-h-screen bg-latar p-8">
      <div className="mx-auto max-w-3xl">
        {nama && (
          <div className="mb-6">
            <p className="text-lg font-medium text-teks">
              Selamat datang, {nama}
            </p>
            <p className="text-teks-redup">
              Kelola batch koreksi esai Anda di sini.
            </p>
          </div>
        )}

        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-teks">Batch Koreksi</h1>
          <button
            type="button"
            onClick={() => setFormTerbuka((sebelumnya) => !sebelumnya)}
            className="rounded-md bg-biru-utama px-4 py-2 text-white"
          >
            Buat Batch Baru
          </button>
        </div>

        {formTerbuka && (
          <form
            onSubmit={tanganiBuatBatch}
            className="mb-6 rounded-lg border border-garis bg-permukaan p-6"
          >
            <label
              htmlFor="nama_batch"
              className="mb-1 block text-sm text-teks-redup"
            >
              Nama Batch
            </label>
            <input
              id="nama_batch"
              type="text"
              required
              maxLength={100}
              value={namaBatch}
              onChange={(peristiwa) => setNamaBatch(peristiwa.target.value)}
              className="mb-3 w-full rounded-md border border-garis bg-permukaan px-3 py-2 text-teks"
            />
            {kesalahanForm && (
              <p role="alert" className="mb-3 text-kurang-mirip">
                {kesalahanForm}
              </p>
            )}
            <button
              type="submit"
              disabled={sedangKirim}
              className="flex items-center justify-center gap-2 rounded-md bg-biru-utama px-4 py-2 text-white disabled:opacity-50"
            >
              {sedangKirim && <Spinner ukuran="size-4" />}
              Buat
            </button>
          </form>
        )}

        {status === "memuat" && (
          <div className="flex justify-center py-12">
            <Spinner ukuran="size-5" />
          </div>
        )}

        {status === "gagal" && (
          <p role="alert" className="text-kurang-mirip">
            {kesalahan}
          </p>
        )}

        {status === "siap" && daftarBatch.length === 0 && (
          <p className="text-teks-redup">
            Belum ada batch. Buat batch pertama untuk mulai mengoreksi.
          </p>
        )}

        {status === "siap" && daftarBatch.length > 0 && (
          <ul className="divide-y divide-garis rounded-lg border border-garis bg-permukaan">
            {daftarBatch.map((batch) => (
              <li key={batch.id_batch}>
                <button
                  type="button"
                  onClick={() => navigate(`/batch/${batch.id_batch}`)}
                  className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-biru-muda"
                >
                  <span className="text-teks">{batch.nama_batch}</span>
                  <span className="text-sm text-teks-redup">
                    {formatTanggal(batch.dibuat_pada)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default Beranda;
