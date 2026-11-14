import { useEffect, useRef, useState } from "react";
import {
  CircleAlert,
  File,
  Plus,
  RotateCcw,
  Trash2,
  Upload,
} from "lucide-react";
import * as batchApi from "../api/batch.js";
import {
  BATAS_PER_AKUN,
  PESAN_KODE,
  pesanDipilihDariSlot,
  pesanGagalTengahUnggah,
  pesanLabelHapusFile,
  pesanMelebihiSisaSlot,
  pesanMengirimFile,
  pesanSisaSlotJawaban,
  pesanUntukKode,
} from "../api/pesan.js";
import { useKonfirmasiTinggalkan } from "../hooks/useKonfirmasiTinggalkan.js";
import {
  pecahKiriman,
  periksaFileDiBrowser,
  petakanFileBermasalah,
} from "../lib/unggahJawaban.js";
import DialogKonfirmasi from "./DialogKonfirmasi.jsx";
import Lencana from "./Lencana.jsx";
import PesanForm from "./PesanForm.jsx";
import Spinner from "./Spinner.jsx";

const MAKS_PANJANG_NAMA = 100;

function SeksiJawabanPesertaDidik({
  idBatch,
  adaSoal,
  bacaSaja = false,
  batasJawaban = BATAS_PER_AKUN.free.jawabanPerBatch,
  daftarFileJawaban,
  kesalahanStatus,
  bolehLewatRef,
  onPilihanBelumUnggah,
  onUnggahBerjalan,
  onUploadSukses,
  onCobaLagiSukses,
  onMuatUlangDaftarFileJawaban,
}) {
  const [fileTerpilih, setFileTerpilih] = useState([]);
  const [sedangUpload, setSedangUpload] = useState(false);
  const [kemajuanKirim, setKemajuanKirim] = useState(null);
  const [galatSlot, setGalatSlot] = useState(null);
  const [kesalahanUpload, setKesalahanUpload] = useState(null);
  const [pesanGagalTengah, setPesanGagalTengah] = useState(null);
  const [dialogBatalTerbuka, setDialogBatalTerbuka] = useState(false);

  const [idFileSedangDicobaLagi, setIdFileSedangDicobaLagi] = useState(
    () => new Set(),
  );
  const [kesalahanCobaLagi, setKesalahanCobaLagi] = useState({});

  const idBarisCounter = useRef(0);
  const refInputFile = useRef(null);
  const refTombolUploadAwal = useRef(null);
  const refTombolTambahFile = useRef(null);
  const refTombolHapus = useRef({});
  const refGalatNama = useRef({});
  const refGalatSlot = useRef(null);
  const refGalatBermasalah = useRef(null);
  const refGalatUmum = useRef(null);
  const refGalatTengah = useRef(null);
  const fokusTertundaRef = useRef(null);

  const refTombolCobaLagi = useRef({});
  const refStatusCobaLagi = useRef({});
  const fokusStatusTertunda = useRef(null);

  const sisaSlot = Math.max(0, batasJawaban - daftarFileJawaban.length);
  const adaBarisBermasalah = fileTerpilih.some((item) =>
    Boolean(item.galatFile),
  );

  // Tombol "Coba Lagi" hilang begitu baris berpindah dari Gagal: pindahkan
  // fokus ke lencana Status baris itu (tabIndex={-1}) agar tidak jatuh ke
  // tubuh halaman, mirip pola fokusJudulTertunda di HalamanBatch.jsx.
  useEffect(() => {
    const idTertunda = fokusStatusTertunda.current;
    if (!idTertunda) return;
    const fileJawaban = daftarFileJawaban.find(
      (fj) => fj.id_file === idTertunda,
    );
    if (fileJawaban && fileJawaban.status_proses !== "gagal") {
      fokusStatusTertunda.current = null;
      refStatusCobaLagi.current[idTertunda]?.focus();
    }
  }, [daftarFileJawaban]);

  useEffect(() => {
    const target = fokusTertundaRef.current;
    if (!target) return;
    fokusTertundaRef.current = null;

    if (target.jenis === "hapus-baris") {
      refTombolHapus.current[target.idBaris]?.focus();
    } else if (target.jenis === "tambah-file") {
      refTombolTambahFile.current?.focus();
    } else if (target.jenis === "upload-awal") {
      refTombolUploadAwal.current?.focus();
    } else if (target.jenis === "galat-slot") {
      refGalatSlot.current?.focus();
    } else if (target.jenis === "galat-bermasalah") {
      refGalatBermasalah.current?.focus();
    } else if (target.jenis === "galat-umum") {
      refGalatUmum.current?.focus();
    } else if (target.jenis === "galat-tengah") {
      refGalatTengah.current?.focus();
    } else if (target.jenis === "galat-nama") {
      refGalatNama.current[target.idBaris]?.focus();
    }
  }, [
    fileTerpilih,
    galatSlot,
    kesalahanUpload,
    pesanGagalTengah,
    adaBarisBermasalah,
  ]);

  async function tanganiCobaLagi(fileJawaban) {
    const idFile = fileJawaban.id_file;
    setIdFileSedangDicobaLagi((sebelumnya) => new Set(sebelumnya).add(idFile));
    setKesalahanCobaLagi((sebelumnya) => ({ ...sebelumnya, [idFile]: null }));
    try {
      const fileBaru = await batchApi.cobaLagiFileJawaban(idBatch, idFile);
      fokusStatusTertunda.current = idFile;
      onCobaLagiSukses?.(fileBaru);
    } catch (error) {
      if (error.kode === "FILE_BUKAN_GAGAL") {
        try {
          const daftarBaru = await batchApi.daftarFileJawaban(idBatch);
          onMuatUlangDaftarFileJawaban?.(daftarBaru);
        } catch {
          // Pemuatan ulang gagal: pesan galat di bawah tetap tampil dari error asli.
        }
      }
      setKesalahanCobaLagi((sebelumnya) => ({
        ...sebelumnya,
        [idFile]: error.pesan,
      }));
    } finally {
      setIdFileSedangDicobaLagi((sebelumnya) => {
        const baru = new Set(sebelumnya);
        baru.delete(idFile);
        return baru;
      });
    }
  }

  const blocker = useKonfirmasiTinggalkan(
    fileTerpilih.length > 0,
    bolehLewatRef,
  );

  async function tanganiPilihFile(peristiwa) {
    const daftarFileInput = Array.from(peristiwa.target.files);
    peristiwa.target.value = "";
    if (daftarFileInput.length === 0 || sedangUpload) return;

    if (fileTerpilih.length + daftarFileInput.length > sisaSlot) {
      setGalatSlot(pesanMelebihiSisaSlot(sisaSlot));
      fokusTertundaRef.current = { jenis: "galat-slot" };
      return;
    }

    setGalatSlot(null);
    setKesalahanUpload(null);
    setPesanGagalTengah(null);

    const barisBaru = await Promise.all(
      daftarFileInput.map(async (file) => {
        const kodeGalat = await periksaFileDiBrowser(file);
        idBarisCounter.current += 1;
        return {
          id: idBarisCounter.current,
          file,
          nama: "",
          galatFile: kodeGalat ? pesanUntukKode(kodeGalat) : null,
          galatNama: null,
        };
      }),
    );

    const adaBaruBermasalah = barisBaru.some((item) => Boolean(item.galatFile));
    if (adaBaruBermasalah) {
      fokusTertundaRef.current = { jenis: "galat-bermasalah" };
    }

    setFileTerpilih((sebelumnya) => [...sebelumnya, ...barisBaru]);
    onPilihanBelumUnggah?.(true);
  }

  function ubahNama(idBaris, nilai) {
    setFileTerpilih((sebelumnya) =>
      sebelumnya.map((item) =>
        item.id === idBaris
          ? {
              ...item,
              nama: nilai,
              galatNama: nilai.trim() !== "" ? null : item.galatNama,
            }
          : item,
      ),
    );
  }

  function hapusBaris(index) {
    const daftarBaru = fileTerpilih.filter((_, i) => i !== index);
    setFileTerpilih(daftarBaru);
    setGalatSlot(null);

    if (daftarBaru.length === 0) {
      setKesalahanUpload(null);
      setPesanGagalTengah(null);
      onPilihanBelumUnggah?.(false);
      fokusTertundaRef.current = { jenis: "upload-awal" };
    } else if (index < daftarBaru.length) {
      fokusTertundaRef.current = {
        jenis: "hapus-baris",
        idBaris: daftarBaru[index].id,
      };
    } else {
      fokusTertundaRef.current = { jenis: "tambah-file" };
    }
  }

  function konfirmasiBatalPilihan() {
    setDialogBatalTerbuka(false);
    setFileTerpilih([]);
    setGalatSlot(null);
    setKesalahanUpload(null);
    setPesanGagalTengah(null);
    onPilihanBelumUnggah?.(false);
    fokusTertundaRef.current = { jenis: "upload-awal" };
  }

  async function tanganiUpload(peristiwa) {
    peristiwa.preventDefault();
    if (sedangUpload || adaBarisBermasalah || fileTerpilih.length === 0) return;

    setGalatSlot(null);
    setKesalahanUpload(null);
    setPesanGagalTengah(null);

    const hasilPeriksa = await Promise.all(
      fileTerpilih.map(async (item) => {
        const namaBersih = item.nama.trim();
        let galatNama = null;
        if (namaBersih === "") {
          galatNama = PESAN_KODE.NAMA_PESERTA_KOSONG;
        } else if (namaBersih.length > MAKS_PANJANG_NAMA) {
          galatNama = PESAN_KODE.NAMA_PESERTA_TERLALU_PANJANG;
        }
        const kodeGalatFile = await periksaFileDiBrowser(item.file);
        const galatFile = kodeGalatFile
          ? pesanUntukKode(kodeGalatFile)
          : item.galatFile;
        return {
          ...item,
          galatFile,
          galatNama,
        };
      }),
    );

    const adaFileGagal = hasilPeriksa.some((item) => Boolean(item.galatFile));
    const barisPertamaNamaGagal = hasilPeriksa.find((item) =>
      Boolean(item.galatNama),
    );

    if (adaFileGagal || barisPertamaNamaGagal) {
      setFileTerpilih(hasilPeriksa);
      if (adaFileGagal) {
        fokusTertundaRef.current = { jenis: "galat-bermasalah" };
      } else if (barisPertamaNamaGagal) {
        fokusTertundaRef.current = {
          jenis: "galat-nama",
          idBaris: barisPertamaNamaGagal.id,
        };
      }
      return;
    }

    const daftarKiriman = pecahKiriman(hasilPeriksa);
    const totalFile = hasilPeriksa.length;
    let jumlahTersimpan = 0;
    let sisaBaris = [...hasilPeriksa];

    setSedangUpload(true);
    onUnggahBerjalan?.(true);

    try {
      for (const kiriman of daftarKiriman) {
        setKemajuanKirim({
          k: jumlahTersimpan + kiriman.length,
          n: totalFile,
        });

        const formData = new FormData();
        kiriman.forEach(({ file }) => formData.append("files", file));
        kiriman.forEach(({ nama }) =>
          formData.append("nama_peserta_didik", nama.trim()),
        );

        try {
          const hasil = await batchApi.unggahFileJawaban(idBatch, formData);
          jumlahTersimpan += kiriman.length;
          sisaBaris = sisaBaris.slice(kiriman.length);
          setFileTerpilih(sisaBaris);
          onUploadSukses(hasil);
        } catch (error) {
          if (jumlahTersimpan > 0) {
            setPesanGagalTengah(
              pesanGagalTengahUnggah(jumlahTersimpan, sisaBaris.length),
            );
          }

          if (
            Array.isArray(error.file_bermasalah) &&
            error.file_bermasalah.length > 0
          ) {
            const barisTerpetakan = petakanFileBermasalah(
              sisaBaris,
              error.file_bermasalah,
              (kode) => pesanUntukKode(kode),
              0,
            );
            setFileTerpilih(barisTerpetakan);
            fokusTertundaRef.current = {
              jenis: jumlahTersimpan > 0 ? "galat-tengah" : "galat-bermasalah",
            };
          } else {
            setKesalahanUpload(error.pesan);
            fokusTertundaRef.current = {
              jenis: jumlahTersimpan > 0 ? "galat-tengah" : "galat-umum",
            };
          }
          break;
        }
      }

      if (sisaBaris.length === 0) {
        onPilihanBelumUnggah?.(false);
        fokusTertundaRef.current = { jenis: "upload-awal" };
      }
    } finally {
      setSedangUpload(false);
      setKemajuanKirim(null);
      onUnggahBerjalan?.(false);
    }
  }

  const persenKemajuan = kemajuanKirim
    ? Math.min(100, Math.round((kemajuanKirim.k / kemajuanKirim.n) * 100))
    : 0;

  return (
    <section className="flex flex-col gap-4 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-teks">Jawaban Peserta Didik</h2>

      {!adaSoal && (
        <p className="text-teks-redup">{PESAN_KODE.BELUM_ADA_SOAL}</p>
      )}

      {adaSoal && (
        <div className="flex flex-col gap-4">
          {!bacaSaja && (
            <input
              ref={refInputFile}
              type="file"
              multiple
              accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
              onChange={tanganiPilihFile}
              className="sr-only"
              tabIndex={-1}
              aria-label="Pilih file jawaban peserta didik"
            />
          )}

          {!bacaSaja && fileTerpilih.length === 0 && (
            <div className="flex flex-col gap-2">
              {daftarFileJawaban.length === 0 && (
                <p className="text-sm leading-5 text-teks-redup">
                  {PESAN_KODE.PERINGATAN_SEBELUM_UNGGAH}
                </p>
              )}
              <p className="text-sm leading-5 text-teks-redup">
                {pesanSisaSlotJawaban(sisaSlot)}
              </p>
              {galatSlot && (
                <p
                  id="galat-slot"
                  ref={refGalatSlot}
                  tabIndex={-1}
                  role="alert"
                  className="flex items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
                >
                  <CircleAlert
                    className="mt-0.5 size-4 shrink-0"
                    aria-hidden="true"
                  />
                  <span>{galatSlot}</span>
                </p>
              )}
              <div>
                <button
                  type="button"
                  ref={refTombolUploadAwal}
                  aria-describedby={galatSlot ? "galat-slot" : undefined}
                  onClick={() => refInputFile.current?.click()}
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan"
                >
                  <Upload className="size-4" aria-hidden="true" />
                  Upload Jawaban Peserta Didik
                </button>
              </div>
            </div>
          )}

          {!bacaSaja && fileTerpilih.length > 0 && (
            <form
              onSubmit={tanganiUpload}
              noValidate
              className="flex flex-col gap-4"
            >
              <p className="text-sm leading-5 text-teks-redup">
                {pesanDipilihDariSlot(fileTerpilih.length, sisaSlot)}
              </p>

              {pesanGagalTengah && (
                <p
                  ref={refGalatTengah}
                  tabIndex={-1}
                  role="alert"
                  className="rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
                >
                  {pesanGagalTengah}
                </p>
              )}

              {kesalahanUpload && (
                <p
                  ref={refGalatUmum}
                  tabIndex={-1}
                  role="alert"
                  className="flex items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
                >
                  <CircleAlert
                    className="mt-0.5 size-4 shrink-0"
                    aria-hidden="true"
                  />
                  <span>{kesalahanUpload}</span>
                </p>
              )}

              {sedangUpload && kemajuanKirim && (
                <div
                  role="status"
                  className="flex flex-col gap-2 rounded-lg border border-garis bg-permukaan p-4"
                >
                  <p className="flex items-center gap-2 text-sm font-semibold leading-5 text-biru-utama">
                    <Spinner ukuran="size-4" />
                    <span id="kemajuan-kirim">
                      {pesanMengirimFile(kemajuanKirim.k, kemajuanKirim.n)}
                    </span>
                  </p>
                  <div
                    role="progressbar"
                    aria-labelledby="kemajuan-kirim"
                    aria-valuemin={0}
                    aria-valuemax={kemajuanKirim.n}
                    aria-valuenow={kemajuanKirim.k}
                    className="h-2 overflow-hidden rounded-full bg-biru-muda"
                  >
                    <div
                      className="h-full bg-biru-utama"
                      style={{ width: `${persenKemajuan}%` }}
                    />
                  </div>
                </div>
              )}

              <ul className="flex flex-col gap-3">
                {fileTerpilih.map((item, index) => (
                  <li
                    key={item.id}
                    className={`grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 rounded-lg border bg-permukaan p-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] lg:gap-4 ${
                      item.galatFile ? "border-kurang-mirip" : "border-garis"
                    }`}
                  >
                    <div className="max-lg:contents lg:col-start-1 lg:row-start-1 lg:flex lg:min-w-0 lg:flex-col lg:gap-2 lg:pt-7">
                      <span className="flex min-h-11 min-w-0 items-center gap-2 font-semibold text-teks max-lg:col-start-1 max-lg:row-start-1">
                        <File
                          className="size-4 shrink-0 text-teks"
                          aria-hidden="true"
                        />
                        <span
                          className="min-w-0 flex-1 truncate"
                          title={item.file.name}
                        >
                          {item.file.name}
                        </span>
                      </span>
                      {item.galatFile && (
                        <span className="flex items-start gap-2 text-sm leading-5 text-kurang-mirip max-lg:col-span-2 max-lg:row-start-2">
                          <CircleAlert
                            className="mt-0.5 size-4 shrink-0"
                            aria-hidden="true"
                          />
                          <span>{item.galatFile}</span>
                        </span>
                      )}
                    </div>

                    <div className="col-span-2 flex min-w-0 flex-col gap-2 lg:col-span-1 lg:col-start-2 lg:row-start-1">
                      <label className="flex min-w-0 flex-col gap-2">
                        <span className="text-sm font-semibold leading-5 text-teks">
                          Nama peserta didik
                        </span>
                        <input
                          type="text"
                          maxLength={MAKS_PANJANG_NAMA}
                          value={item.nama}
                          readOnly={sedangUpload}
                          aria-disabled={sedangUpload ? "true" : undefined}
                          aria-invalid={item.galatNama ? "true" : undefined}
                          aria-describedby={
                            item.galatNama ? `galat-nama-${item.id}` : undefined
                          }
                          onChange={(peristiwa) =>
                            ubahNama(item.id, peristiwa.target.value)
                          }
                          className={`h-11 w-full min-w-0 rounded-lg border bg-permukaan px-3 text-teks aria-disabled:bg-latar aria-disabled:text-teks-redup ${
                            item.galatNama
                              ? "border-kurang-mirip"
                              : "border-garis"
                          }`}
                        />
                      </label>
                      {item.galatNama && (
                        <p
                          id={`galat-nama-${item.id}`}
                          ref={(el) => {
                            refGalatNama.current[item.id] = el;
                          }}
                          tabIndex={-1}
                          className="text-sm leading-5 text-kurang-mirip"
                        >
                          {item.galatNama}
                        </p>
                      )}
                    </div>

                    <button
                      type="button"
                      ref={(el) => {
                        refTombolHapus.current[item.id] = el;
                      }}
                      aria-label={pesanLabelHapusFile(item.file.name)}
                      aria-disabled={sedangUpload ? "true" : undefined}
                      onClick={() => {
                        if (sedangUpload) return;
                        hapusBaris(index);
                      }}
                      className="inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-lg border border-garis bg-permukaan text-kurang-mirip aria-disabled:cursor-not-allowed aria-disabled:opacity-60 max-lg:col-start-2 max-lg:row-start-1 lg:col-start-3 lg:row-start-1 lg:mt-7"
                    >
                      <Trash2 className="size-5" aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>

              {galatSlot && (
                <p
                  id="galat-slot"
                  ref={refGalatSlot}
                  tabIndex={-1}
                  role="alert"
                  className="flex items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
                >
                  <CircleAlert
                    className="mt-0.5 size-4 shrink-0"
                    aria-hidden="true"
                  />
                  <span>{galatSlot}</span>
                </p>
              )}

              {adaBarisBermasalah && (
                <p
                  id="galat-bermasalah"
                  ref={refGalatBermasalah}
                  tabIndex={-1}
                  role="alert"
                  className="flex items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
                >
                  <CircleAlert
                    className="mt-0.5 size-4 shrink-0"
                    aria-hidden="true"
                  />
                  <span>{PESAN_KODE.HAPUS_FILE_BERMASALAH}</span>
                </p>
              )}

              <div className="flex flex-col gap-2 lg:flex-row lg:flex-wrap">
                <button
                  type="submit"
                  aria-disabled={
                    sedangUpload || adaBarisBermasalah ? "true" : undefined
                  }
                  aria-describedby={
                    adaBarisBermasalah ? "galat-bermasalah" : undefined
                  }
                  className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan aria-disabled:cursor-not-allowed aria-disabled:opacity-60 lg:w-auto"
                >
                  Mulai Penilaian
                </button>
                <button
                  type="button"
                  ref={refTombolTambahFile}
                  aria-disabled={sedangUpload ? "true" : undefined}
                  aria-describedby={galatSlot ? "galat-slot" : undefined}
                  onClick={() => {
                    if (sedangUpload) return;
                    refInputFile.current?.click();
                  }}
                  className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks aria-disabled:cursor-not-allowed aria-disabled:opacity-60 lg:w-auto"
                >
                  <Plus className="size-4" aria-hidden="true" />
                  Tambah File
                </button>
                <button
                  type="button"
                  aria-disabled={sedangUpload ? "true" : undefined}
                  onClick={() => {
                    if (sedangUpload) return;
                    setDialogBatalTerbuka(true);
                  }}
                  className="inline-flex min-h-11 w-full items-center justify-center rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks aria-disabled:cursor-not-allowed aria-disabled:opacity-60 lg:w-auto"
                >
                  Batal
                </button>
              </div>
            </form>
          )}

          {kesalahanStatus && (
            <p role="alert" className="text-sm leading-5 text-kurang-mirip">
              {kesalahanStatus}
            </p>
          )}

          {!kesalahanStatus && daftarFileJawaban.length > 0 && (
            <div className="overflow-hidden rounded-lg border border-garis bg-permukaan max-lg:overflow-visible max-lg:border-0 max-lg:bg-transparent">
              <table
                role="table"
                className="w-full border-collapse max-lg:block"
              >
                <thead role="rowgroup" className="max-lg:hidden">
                  <tr role="row">
                    <th
                      role="columnheader"
                      scope="col"
                      className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                    >
                      Peserta Didik
                    </th>
                    <th
                      role="columnheader"
                      scope="col"
                      className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                    >
                      Status
                    </th>
                    {!bacaSaja && (
                      <th
                        role="columnheader"
                        scope="col"
                        className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                      >
                        Aksi
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody role="rowgroup" className="max-lg:block">
                  {daftarFileJawaban.map((fileJawaban) => {
                    const sedangDicobaLagi = idFileSedangDicobaLagi.has(
                      fileJawaban.id_file,
                    );
                    return (
                      <tr
                        key={fileJawaban.id_file}
                        role="row"
                        className="border-b border-garis last:border-b-0 max-lg:mb-3 max-lg:block max-lg:rounded-lg max-lg:border max-lg:border-garis max-lg:bg-permukaan max-lg:p-4"
                      >
                        <td
                          role="cell"
                          className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                        >
                          <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                            Peserta Didik
                          </span>
                          <span className="text-teks">
                            {fileJawaban.nama_peserta_didik}
                          </span>
                          {fileJawaban.status_proses === "gagal" &&
                            fileJawaban.pesan_error && (
                              <span className="block text-sm leading-5 text-kurang-mirip">
                                {fileJawaban.pesan_error}
                              </span>
                            )}
                        </td>
                        <td
                          role="cell"
                          className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                        >
                          <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                            Status
                          </span>
                          <span
                            ref={(el) => {
                              refStatusCobaLagi.current[fileJawaban.id_file] =
                                el;
                            }}
                            tabIndex={-1}
                          >
                            <Lencana varian={fileJawaban.status_proses} />
                          </span>
                        </td>
                        {!bacaSaja && (
                          <td
                            role="cell"
                            className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                          >
                            {fileJawaban.status_proses === "gagal" && (
                              <>
                                <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                                  Aksi
                                </span>
                                <button
                                  type="button"
                                  ref={(el) => {
                                    refTombolCobaLagi.current[
                                      fileJawaban.id_file
                                    ] = el;
                                  }}
                                  aria-label={`Coba Lagi untuk ${fileJawaban.nama_peserta_didik}`}
                                  aria-disabled={
                                    sedangDicobaLagi ? "true" : undefined
                                  }
                                  onClick={() => {
                                    if (sedangDicobaLagi) return;
                                    tanganiCobaLagi(fileJawaban);
                                  }}
                                  className="inline-flex min-h-11 items-center gap-1.5 rounded-lg border border-garis bg-permukaan px-3 text-sm font-semibold text-teks aria-disabled:opacity-50"
                                >
                                  {sedangDicobaLagi ? (
                                    <Spinner ukuran="size-4" />
                                  ) : (
                                    <RotateCcw
                                      className="size-4"
                                      aria-hidden="true"
                                    />
                                  )}
                                  Coba Lagi
                                </button>
                                {kesalahanCobaLagi[fileJawaban.id_file] && (
                                  <PesanForm
                                    varian="galat"
                                    pesan={
                                      kesalahanCobaLagi[fileJawaban.id_file]
                                    }
                                    className="mt-1 text-sm leading-5"
                                  />
                                )}
                              </>
                            )}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <DialogKonfirmasi
        terbuka={dialogBatalTerbuka}
        judul={PESAN_KODE.JUDUL_BATALKAN_PILIHAN_FILE}
        isi={PESAN_KODE.PESAN_BATALKAN_PILIHAN_FILE}
        labelBatal="Kembali"
        labelYa="Ya"
        onBatal={() => setDialogBatalTerbuka(false)}
        onYa={konfirmasiBatalPilihan}
      />

      <DialogKonfirmasi
        terbuka={blocker.state === "blocked"}
        judul={PESAN_KODE.JUDUL_TINGGALKAN_HALAMAN}
        isi={PESAN_KODE.PESAN_TINGGALKAN_HALAMAN}
        labelBatal="Tetap di Halaman"
        labelYa="Tinggalkan"
        onBatal={() => blocker.reset?.()}
        onYa={() => blocker.proceed?.()}
      />
    </section>
  );
}

export default SeksiJawabanPesertaDidik;
