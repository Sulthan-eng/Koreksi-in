import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";
import SeksiJawabanPesertaDidik from "../components/SeksiJawabanPesertaDidik.jsx";
import Spinner from "../components/Spinner.jsx";
import TabHasilKoreksi from "../components/TabHasilKoreksi.jsx";
import TabStatusPemrosesan from "../components/TabStatusPemrosesan.jsx";

const JEDA_POLLING_MS = 5000;

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
  const [daftarFileJawaban, setDaftarFileJawaban] = useState([]);
  const [kesalahanPolling, setKesalahanPolling] = useState(null);
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
        const [batchHasil, soalHasil, fileJawabanHasil] = await Promise.all([
          batchApi.ambilBatch(id),
          batchApi.daftarSoal(id),
          batchApi.daftarFileJawaban(id),
        ]);
        if (!dibatalkan) {
          setBatch(batchHasil);
          setDaftarSoal(soalHasil);
          setDaftarFileJawaban(fileJawabanHasil);
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

  const adaFileDiproses = daftarFileJawaban.some(
    (fileJawaban) => fileJawaban.status_proses === "diproses",
  );

  useEffect(() => {
    if (!adaFileDiproses) return;
    const interval = setInterval(async () => {
      try {
        const hasil = await batchApi.daftarFileJawaban(id);
        setDaftarFileJawaban(hasil);
      } catch {
        setKesalahanPolling("Gagal memuat status pemrosesan, coba muat ulang halaman");
        clearInterval(interval);
      }
    }, JEDA_POLLING_MS);
    return () => clearInterval(interval);
  }, [id, adaFileDiproses]);

  function bukaFormTambahSoal() {
    if (daftarSoal.length >= BATAS_SOAL_PER_BATCH) return;
    setKesalahanSoal(null);
    setPesanSukses(null);
    setKunciJawaban("");
    setFormTerbuka(true);
  }

  async function tanganiSimpanSoal(peristiwa) {
    peristiwa.preventDefault();
    if (kunciJawaban.trim() === "") {
      setKesalahanSoal(PESAN_KODE.KUNCI_KOSONG);
      return;
    }
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
            <h2 className="mb-4 text-lg font-semibold text-teks">
              Soal dan Kunci Jawaban
            </h2>

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

            {pesanSukses && !formTerbuka && daftarFileJawaban.length === 0 && (
              <p role="status" className="mb-4 text-sangat-mirip">
                {pesanSukses}
              </p>
            )}

            {formTerbuka ? (
              <form
                onSubmit={tanganiSimpanSoal}
                noValidate
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
            ) : daftarFileJawaban.length > 0 ? (
              <p className="text-teks-redup">{PESAN_KODE.SOAL_SETELAH_JAWABAN}</p>
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

            <SeksiJawabanPesertaDidik
              idBatch={id}
              adaSoal={daftarSoal.length > 0}
              daftarFileJawaban={daftarFileJawaban}
              onUploadSukses={(fileBaru) =>
                setDaftarFileJawaban((sebelumnya) => [...sebelumnya, ...fileBaru])
              }
            />
          </div>
        )}

        {tabAktif === TAB_STATUS && (
          <div role="tabpanel">
            <TabStatusPemrosesan
              daftarFileJawaban={daftarFileJawaban}
              kesalahan={kesalahanPolling}
            />
          </div>
        )}

        {tabAktif === TAB_DASHBOARD && (
          <div role="tabpanel">
            <TabHasilKoreksi idBatch={id} daftarSoal={daftarSoal} />
          </div>
        )}
      </div>
    </div>
  );
}

export default HalamanBatch;
