import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as batchApi from "../api/batch.js";
import Spinner from "../components/Spinner.jsx";

const TAB_SOAL = "soal";
const TAB_STATUS = "status";
const TAB_DASHBOARD = "dashboard";
const BATAS_SOAL_PER_BATCH = 20;

const KELAS_TAB_AKTIF = "border-b-2 border-biru-utama text-biru-utama";
const KELAS_TAB_NONAKTIF = "text-teks-redup";

function HalamanBatch() {
  const { id } = useParams();
  const [status, setStatus] = useState("memuat");
  const [kesalahan, setKesalahan] = useState(null);
  const [batch, setBatch] = useState(null);
  const [daftarSoal, setDaftarSoal] = useState([]);
  const [tabAktif, setTabAktif] = useState(TAB_SOAL);

  const [formTerbuka, setFormTerbuka] = useState(false);
  const [kunciJawaban, setKunciJawaban] = useState("");
  const [kesalahanSoal, setKesalahanSoal] = useState(null);
  const [sedangSimpan, setSedangSimpan] = useState(false);
  const [pesanSukses, setPesanSukses] = useState(null);

  useEffect(() => {
    let dibatalkan = false;
    (async () => {
      try {
        const [batchHasil, soalHasil] = await Promise.all([
          batchApi.ambilBatch(id),
          batchApi.daftarSoal(id),
        ]);
        if (!dibatalkan) {
          setBatch(batchHasil);
          setDaftarSoal(soalHasil);
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
  }, [id]);

  function bukaFormTambahSoal() {
    if (daftarSoal.length >= BATAS_SOAL_PER_BATCH) return;
    setKesalahanSoal(null);
    setPesanSukses(null);
    setKunciJawaban("");
    setFormTerbuka(true);
  }

  async function tanganiSimpanSoal(peristiwa) {
    peristiwa.preventDefault();
    setSedangSimpan(true);
    setKesalahanSoal(null);
    try {
      const soal = await batchApi.tambahSoal(id, {
        kunci_jawaban: kunciJawaban,
      });
      setDaftarSoal((sebelumnya) => [...sebelumnya, soal]);
      setFormTerbuka(false);
      setKunciJawaban("");
      setPesanSukses("Kunci jawaban tersimpan.");
    } catch (error) {
      setKesalahanSoal(error.pesan);
    } finally {
      setSedangSimpan(false);
    }
  }

  if (status === "memuat") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-latar">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (status === "gagal") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-latar p-8">
        <div className="text-center">
          <p role="alert" className="mb-4 text-kurang-mirip">
            {kesalahan}
          </p>
          <Link to="/" className="text-biru-utama">
            Kembali ke Beranda
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-latar p-8">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-6 text-xl font-semibold text-teks">
          {batch.nama_batch}
        </h1>

        <div role="tablist" className="mb-6 flex gap-4 border-b border-garis">
          <button
            type="button"
            role="tab"
            aria-selected={tabAktif === TAB_SOAL}
            onClick={() => setTabAktif(TAB_SOAL)}
            className={`px-3 py-2 ${tabAktif === TAB_SOAL ? KELAS_TAB_AKTIF : KELAS_TAB_NONAKTIF}`}
          >
            Soal dan Jawaban
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tabAktif === TAB_STATUS}
            onClick={() => setTabAktif(TAB_STATUS)}
            className={`px-3 py-2 ${tabAktif === TAB_STATUS ? KELAS_TAB_AKTIF : KELAS_TAB_NONAKTIF}`}
          >
            Status Pemrosesan
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tabAktif === TAB_DASHBOARD}
            onClick={() => setTabAktif(TAB_DASHBOARD)}
            className={`px-3 py-2 ${tabAktif === TAB_DASHBOARD ? KELAS_TAB_AKTIF : KELAS_TAB_NONAKTIF}`}
          >
            Dashboard Hasil Koreksi
          </button>
        </div>

        {tabAktif === TAB_SOAL && (
          <div role="tabpanel">
            {daftarSoal.length === 0 && (
              <p className="mb-4 text-teks-redup">
                Belum ada soal pada batch ini.
              </p>
            )}

            {daftarSoal.length > 0 && (
              <ul className="mb-6 space-y-3">
                {daftarSoal.map((soal) => (
                  <li
                    key={soal.id_soal}
                    className="rounded-lg border border-garis bg-permukaan p-4"
                  >
                    <p className="mb-1 font-medium text-teks">
                      Soal {soal.no_soal}
                    </p>
                    <p className="whitespace-pre-wrap text-teks-redup">
                      {soal.kunci_jawaban}
                    </p>
                  </li>
                ))}
              </ul>
            )}

            {pesanSukses && !formTerbuka && (
              <p role="status" className="mb-4 text-sangat-mirip">
                {pesanSukses}
              </p>
            )}

            {formTerbuka ? (
              <form
                onSubmit={tanganiSimpanSoal}
                className="rounded-lg border border-garis bg-permukaan p-6"
              >
                <label
                  htmlFor="kunci_jawaban"
                  className="mb-1 block text-sm text-teks-redup"
                >
                  Soal {daftarSoal.length + 1} — Kunci Jawaban
                </label>
                <textarea
                  id="kunci_jawaban"
                  required
                  rows={4}
                  value={kunciJawaban}
                  onChange={(peristiwa) => setKunciJawaban(peristiwa.target.value)}
                  className="mb-3 w-full rounded-md border border-garis bg-permukaan px-3 py-2 text-teks"
                />
                {kesalahanSoal && (
                  <p role="alert" className="mb-3 text-kurang-mirip">
                    {kesalahanSoal}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={sedangSimpan}
                  className="flex items-center justify-center gap-2 rounded-md bg-biru-utama px-4 py-2 text-white disabled:opacity-50"
                >
                  {sedangSimpan && <Spinner className="h-4 w-4 text-white" />}
                  Simpan Kunci Jawaban
                </button>
              </form>
            ) : daftarSoal.length >= BATAS_SOAL_PER_BATCH ? (
              <p className="text-teks-redup">
                Sudah mencapai jumlah maksimal 20 soal per batch.
              </p>
            ) : (
              <button
                type="button"
                onClick={bukaFormTambahSoal}
                className="rounded-md bg-biru-utama px-4 py-2 text-white"
              >
                Tambah Soal
              </button>
            )}
          </div>
        )}

        {tabAktif === TAB_STATUS && (
          <div role="tabpanel" className="text-teks-redup">
            Fitur ini belum tersedia di prototipe ini.
          </div>
        )}

        {tabAktif === TAB_DASHBOARD && (
          <div role="tabpanel" className="text-teks-redup">
            Fitur ini belum tersedia di prototipe ini.
          </div>
        )}
      </div>
    </div>
  );
}

export default HalamanBatch;
