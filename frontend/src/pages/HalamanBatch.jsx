import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Plus } from "lucide-react";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";
import KeadaanData from "../components/KeadaanData.jsx";
import PesanForm from "../components/PesanForm.jsx";
import SeksiJawabanPesertaDidik from "../components/SeksiJawabanPesertaDidik.jsx";
import Spinner from "../components/Spinner.jsx";
import TabHasilKoreksi from "../components/TabHasilKoreksi.jsx";

const JEDA_POLLING_MS = 5000;

const TAB_SOAL = "soal";
const TAB_DASHBOARD = "dashboard";
const BATAS_SOAL_PER_BATCH = 20;

const DAFTAR_TAB = [
  { id: TAB_SOAL, label: "Soal dan Jawaban" },
  { id: TAB_DASHBOARD, label: "Dashboard Hasil Koreksi" },
];

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

  const tabRefs = useRef([]);

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
        setKesalahanPolling(PESAN_KODE.GAGAL_STATUS_PEMROSESAN);
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
      setPesanSukses(PESAN_KODE.KUNCI_TERSIMPAN);
    } catch (error) {
      setKesalahanSoal(error.pesan);
    } finally {
      setSedangSimpan(false);
    }
  }

  function tanganiKeyDownTab(peristiwa, indeks) {
    let indeksTarget = null;
    if (peristiwa.key === "ArrowRight") {
      indeksTarget = (indeks + 1) % DAFTAR_TAB.length;
    } else if (peristiwa.key === "ArrowLeft") {
      indeksTarget = (indeks - 1 + DAFTAR_TAB.length) % DAFTAR_TAB.length;
    } else if (peristiwa.key === "Home") {
      indeksTarget = 0;
    } else if (peristiwa.key === "End") {
      indeksTarget = DAFTAR_TAB.length - 1;
    }

    if (indeksTarget !== null) {
      peristiwa.preventDefault();
      const target = DAFTAR_TAB[indeksTarget];
      setTabAktif(target.id);
      tabRefs.current[indeksTarget]?.focus();
    }
  }

  if (status === "memuat") {
    return (
      <div className="min-h-screen bg-latar">
        <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
          <Link
            to="/"
            className="inline-flex min-h-11 items-center gap-2 font-semibold text-biru-utama underline"
          >
            <ArrowLeft className="size-4 shrink-0" aria-hidden="true" />
            Batch Koreksi
          </Link>
          <KeadaanData keadaan="memuat" className="min-h-48" />
        </main>
      </div>
    );
  }

  if (status === "gagal") {
    return (
      <div className="min-h-screen bg-latar">
        <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
          <Link
            to="/"
            className="inline-flex min-h-11 items-center gap-2 font-semibold text-biru-utama underline"
          >
            <ArrowLeft className="size-4 shrink-0" aria-hidden="true" />
            Batch Koreksi
          </Link>
          <div
            role="alert"
            className="flex flex-col items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
          >
            <p>{kesalahan || PESAN_KODE.KONEKSI_TERPUTUS}</p>
            <Link to="/" className="font-semibold underline">
              Kembali ke Beranda
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-latar">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <Link
          to="/"
          className="inline-flex min-h-11 items-center gap-2 font-semibold text-biru-utama underline"
        >
          <ArrowLeft className="size-4 shrink-0" aria-hidden="true" />
          Batch Koreksi
        </Link>

        <header className="flex flex-col gap-4">
          <div className="flex items-start gap-3">
            <h1 className="min-w-0 break-words text-2xl font-bold leading-8 text-teks">
              {batch.nama_batch}
            </h1>
          </div>
        </header>

        <div
          role="tablist"
          aria-label="Bagian batch"
          className="grid grid-cols-2 gap-1 rounded-lg border border-garis bg-latar p-1 lg:flex lg:gap-2 lg:rounded-none lg:border-0 lg:border-b lg:border-garis lg:bg-transparent lg:p-0"
        >
          {DAFTAR_TAB.map((tab, indeks) => {
            const aktif = tabAktif === tab.id;
            return (
              <button
                key={tab.id}
                ref={(el) => {
                  tabRefs.current[indeks] = el;
                }}
                type="button"
                role="tab"
                id={`tab-${tab.id}`}
                aria-controls={`panel-${tab.id}`}
                aria-selected={aktif}
                tabIndex={aktif ? 0 : -1}
                onClick={() => setTabAktif(tab.id)}
                onKeyDown={(peristiwa) => tanganiKeyDownTab(peristiwa, indeks)}
                className="min-h-11 rounded-md px-2 text-sm font-semibold leading-5 text-teks-redup aria-[selected=true]:bg-permukaan aria-[selected=true]:text-biru-utama aria-[selected=true]:shadow-sm lg:-mb-px lg:rounded-none lg:border-b-2 lg:border-transparent lg:px-4 lg:text-base lg:leading-6 lg:shadow-none lg:aria-[selected=true]:border-biru-utama lg:aria-[selected=true]:bg-transparent"
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {tabAktif === TAB_SOAL && (
          <div
            id="panel-soal"
            role="tabpanel"
            aria-labelledby="tab-soal"
            tabIndex={0}
            className="flex flex-col gap-6 focus:outline-none"
          >
            <section className="flex flex-col gap-4 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-teks">
                Soal dan Kunci Jawaban
              </h2>

              {pesanSukses &&
                !formTerbuka &&
                daftarFileJawaban.length === 0 && (
                  <PesanForm
                    varian="sukses"
                    pesan={pesanSukses}
                    className="rounded-lg bg-sangat-mirip-latar px-4 py-3 text-sm leading-5"
                  />
                )}

              {daftarSoal.length === 0 && (
                <KeadaanData
                  keadaan="kosong"
                  pesan={PESAN_KODE.BELUM_ADA_SOAL_BATCH}
                />
              )}

              {daftarSoal.length > 0 && (
                <ol className="flex flex-col gap-4">
                  {daftarSoal.map((soal) => (
                    <li
                      key={soal.id_soal}
                      className="flex flex-col gap-1 rounded-lg border border-garis bg-permukaan p-4"
                    >
                      <h3 className="font-semibold text-teks">
                        Soal {soal.no_soal}
                      </h3>
                      <p className="whitespace-pre-wrap text-teks">
                        {soal.kunci_jawaban}
                      </p>
                    </li>
                  ))}
                </ol>
              )}

              {formTerbuka ? (
                <form
                  onSubmit={tanganiSimpanSoal}
                  noValidate
                  className="flex flex-col gap-4 border-t border-garis pt-4"
                >
                  <label className="flex flex-col gap-1.5">
                    <span className="text-sm font-semibold text-teks">
                      Soal {daftarSoal.length + 1}: Kunci Jawaban
                    </span>
                    <textarea
                      id="kunci_jawaban"
                      rows={4}
                      value={kunciJawaban}
                      onChange={(peristiwa) =>
                        setKunciJawaban(peristiwa.target.value)
                      }
                      aria-invalid={kesalahanSoal ? "true" : undefined}
                      aria-describedby={
                        kesalahanSoal ? "galat-kunci" : undefined
                      }
                      className="w-full rounded-lg border border-garis bg-permukaan p-3 text-teks aria-[invalid=true]:border-kurang-mirip"
                    />
                  </label>
                  {kesalahanSoal && (
                    <p
                      id="galat-kunci"
                      role="alert"
                      className="text-sm leading-5 text-kurang-mirip"
                    >
                      {kesalahanSoal}
                    </p>
                  )}
                  <div>
                    <button
                      type="submit"
                      disabled={sedangSimpan}
                      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan disabled:opacity-50"
                    >
                      {sedangSimpan && <Spinner ukuran="size-4" />}
                      Simpan Kunci Jawaban
                    </button>
                  </div>
                </form>
              ) : daftarFileJawaban.length > 0 ? (
                <p className="rounded-lg bg-biru-muda px-4 py-3 text-sm leading-5 text-teks">
                  {PESAN_KODE.SOAL_SETELAH_JAWABAN}
                </p>
              ) : daftarSoal.length >= BATAS_SOAL_PER_BATCH ? (
                <p className="rounded-lg bg-biru-muda px-4 py-3 text-sm leading-5 text-teks">
                  {PESAN_KODE.SUDAH_MAKSIMAL_SOAL}
                </p>
              ) : (
                <div>
                  <button
                    type="button"
                    onClick={bukaFormTambahSoal}
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks"
                  >
                    <Plus className="size-4" aria-hidden="true" />
                    Tambah Soal
                  </button>
                </div>
              )}
            </section>

            <SeksiJawabanPesertaDidik
              idBatch={id}
              adaSoal={daftarSoal.length > 0}
              daftarFileJawaban={daftarFileJawaban}
              kesalahanStatus={kesalahanPolling}
              onUploadSukses={(fileBaru) =>
                setDaftarFileJawaban((sebelumnya) => [
                  ...sebelumnya,
                  ...fileBaru,
                ])
              }
            />
          </div>
        )}

        {tabAktif === TAB_DASHBOARD && (
          <div
            id="panel-dashboard"
            role="tabpanel"
            aria-labelledby="tab-dashboard"
            tabIndex={0}
            className="focus:outline-none"
          >
            <TabHasilKoreksi idBatch={id} daftarSoal={daftarSoal} />
          </div>
        )}
      </main>
    </div>
  );
}

export default HalamanBatch;
