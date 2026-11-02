import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";
import { useAksiBatch } from "../hooks/useAksiBatch.js";
import DialogKonfirmasi from "../components/DialogKonfirmasi.jsx";
import KeadaanData from "../components/KeadaanData.jsx";
import Lencana from "../components/Lencana.jsx";
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
  const [pilihanBelumUnggah, setPilihanBelumUnggah] = useState(false);
  const [sedangUnggah, setSedangUnggah] = useState(false);

  const navigate = useNavigate();
  const tabRefs = useRef([]);
  const judulRef = useRef(null);
  const fokusJudulTertunda = useRef(false);
  const bolehLewatRef = useRef(false);

  const bacaSaja = batch?.status === "selesai";

  const aksi = useAksiBatch({
    cekPilihanBelumUnggah: () => pilihanBelumUnggah,
    onSelesaiSukses: (batchHasil) => {
      setBatch(batchHasil);
      // Pilihan yang belum diunggah tidak lolos ke server; halaman tidak perlu
      // diblokir lagi setelah batch berubah Selesai.
      bolehLewatRef.current = true;
      fokusJudulTertunda.current = true;
    },
    onBatchSudahSelesai: async (batchSelesai) => {
      const hasil = await batchApi.ambilBatch(batchSelesai.id_batch);
      setBatch(hasil);
      // Tombol Selesaikan hilang setelah batch Selesai: arahkan fokus ke
      // judul agar tidak jatuh ke tubuh halaman (pola onSelesaiSukses).
      fokusJudulTertunda.current = true;
    },
    onHapusSukses: () => {
      bolehLewatRef.current = true;
      navigate("/");
    },
  });

  // Pola fokusJudulTertunda (sama seperti Beranda): tandai saat aksi sukses,
  // lalu fokus ke judul begitu dialog tertutup (tombol pemicunya sudah tidak
  // ada, bila tidak diarahkan fokus akan jatuh ke tubuh halaman).
  useEffect(() => {
    if (aksi.dialog === null && fokusJudulTertunda.current) {
      fokusJudulTertunda.current = false;
      judulRef.current?.focus();
    }
  }, [aksi.dialog]);

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

  // Pilihan file berubah: pesan "file belum diunggah" sudah tidak berlaku.
  function tanganiPilihanBelumUnggah(ada) {
    setPilihanBelumUnggah(ada);
    aksi.bersihkanPesan(PESAN_KODE.ADA_FILE_BELUM_UNGGAH);
  }

  function tanganiUnggahBerjalan(berjalan) {
    setSedangUnggah(berjalan);
  }

  // Tombol aksi memakai aria-disabled (bukan disabled) supaya fokus tetap ada:
  // klik diabaikan selama pemeriksaan/request atau unggahan sedang berjalan.
  const tahanTombolAksi =
    sedangUnggah || aksi.sedangMemproses || aksi.idBatchMemeriksa !== null;

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
            <h1
              ref={judulRef}
              tabIndex={-1}
              className="min-w-0 wrap-break-word text-2xl font-bold leading-8 text-teks"
            >
              {batch.nama_batch}
            </h1>
            <span className="mt-1.5 shrink-0">
              <Lencana varian={bacaSaja ? "batch_selesai" : "batch_aktif"} />
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {!bacaSaja && (
              <button
                type="button"
                aria-disabled={tahanTombolAksi ? "true" : undefined}
                onClick={() => {
                  if (tahanTombolAksi) return;
                  aksi.pilihSelesaikan(batch);
                }}
                className="inline-flex min-h-11 items-center justify-center rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan aria-disabled:opacity-50"
              >
                Selesaikan Batch
              </button>
            )}
            <button
              type="button"
              aria-disabled={tahanTombolAksi ? "true" : undefined}
              onClick={() => {
                if (tahanTombolAksi) return;
                aksi.pilihHapus(batch);
              }}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-garis bg-permukaan px-4 font-semibold text-kurang-mirip aria-disabled:opacity-50"
            >
              <Trash2 className="size-4" aria-hidden="true" />
              Hapus Batch
            </button>
          </div>

          {bacaSaja && (
            <p className="rounded-lg bg-biru-muda px-4 py-3 text-sm leading-5 text-teks">
              Batch ini sudah selesai dan tidak dapat diubah.
            </p>
          )}

          {aksi.pesanAksi && (
            <PesanForm
              varian={aksi.pesanAksi.varian}
              pesan={aksi.pesanAksi.teks}
              kotak
            />
          )}
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
                className="min-h-11 rounded-md px-2 text-sm font-semibold leading-5 text-teks-redup aria-selected:bg-permukaan aria-selected:text-biru-utama aria-selected:shadow-sm lg:-mb-px lg:rounded-none lg:border-b-2 lg:border-transparent lg:px-4 lg:text-base lg:leading-6 lg:shadow-none lg:aria-selected:border-biru-utama lg:aria-selected:bg-transparent"
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
            className="flex flex-col gap-6"
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

              {!bacaSaja &&
                (formTerbuka ? (
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
                        className="w-full rounded-lg border border-garis bg-permukaan p-3 text-teks aria-invalid:border-kurang-mirip"
                      />
                    </label>
                    {kesalahanSoal && (
                      <PesanForm
                        varian="galat"
                        id="galat-kunci"
                        pesan={kesalahanSoal}
                        className="text-sm leading-5"
                      />
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
                ))}
            </section>

            <SeksiJawabanPesertaDidik
              idBatch={id}
              adaSoal={daftarSoal.length > 0}
              bacaSaja={bacaSaja}
              daftarFileJawaban={daftarFileJawaban}
              kesalahanStatus={kesalahanPolling}
              bolehLewatRef={bolehLewatRef}
              onPilihanBelumUnggah={tanganiPilihanBelumUnggah}
              onUnggahBerjalan={tanganiUnggahBerjalan}
              onUploadSukses={(fileBaru) =>
                setDaftarFileJawaban((sebelumnya) => [
                  ...sebelumnya,
                  ...fileBaru,
                ])
              }
              onCobaLagiSukses={(fileBaru) =>
                setDaftarFileJawaban((sebelumnya) =>
                  sebelumnya.map((fj) =>
                    fj.id_file === fileBaru.id_file ? fileBaru : fj,
                  ),
                )
              }
              onMuatUlangDaftarFileJawaban={setDaftarFileJawaban}
            />
          </div>
        )}

        {tabAktif === TAB_DASHBOARD && (
          <div
            id="panel-dashboard"
            role="tabpanel"
            aria-labelledby="tab-dashboard"
          >
            <TabHasilKoreksi
              idBatch={id}
              daftarSoal={daftarSoal}
              bacaSaja={bacaSaja}
            />
          </div>
        )}
      </main>

      <DialogKonfirmasi
        terbuka={aksi.dialog?.jenis === "selesaikan"}
        judul={PESAN_KODE.JUDUL_SELESAIKAN_BATCH}
        isi={PESAN_KODE.PESAN_SELESAIKAN_BATCH}
        labelBatal="Batal"
        labelYa="Ya"
        tombolUtama="ya"
        prosesBerjalan={aksi.sedangMemproses}
        onBatal={aksi.batalkan}
        onYa={aksi.konfirmasi}
      />

      <DialogKonfirmasi
        terbuka={aksi.dialog?.jenis === "hapus"}
        judul={PESAN_KODE.JUDUL_HAPUS_BATCH}
        isi={PESAN_KODE.PESAN_HAPUS_BATCH}
        labelBatal="Batal"
        labelYa="Ya"
        variasiYa="merusak"
        prosesBerjalan={aksi.sedangMemproses}
        onBatal={aksi.batalkan}
        onYa={aksi.konfirmasi}
      />
    </div>
  );
}

export default HalamanBatch;
