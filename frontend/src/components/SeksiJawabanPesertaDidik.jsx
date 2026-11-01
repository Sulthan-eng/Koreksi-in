import { useState } from "react";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";
import KeadaanData from "./KeadaanData.jsx";
import Lencana from "./Lencana.jsx";
import PesanForm from "./PesanForm.jsx";
import Spinner from "./Spinner.jsx";

function SeksiJawabanPesertaDidik({
  idBatch,
  adaSoal,
  daftarFileJawaban,
  onUploadSukses,
}) {
  const [fileTerpilih, setFileTerpilih] = useState([]);
  const [sedangUpload, setSedangUpload] = useState(false);
  const [kesalahanUpload, setKesalahanUpload] = useState(null);

  function tanganiPilihFile(peristiwa) {
    const fileBaru = Array.from(peristiwa.target.files).map((file) => ({
      file,
      nama: "",
    }));
    setFileTerpilih(fileBaru);
    setKesalahanUpload(null);
    peristiwa.target.value = "";
  }

  function ubahNama(index, nilai) {
    setFileTerpilih((sebelumnya) =>
      sebelumnya.map((item, i) =>
        i === index ? { ...item, nama: nilai } : item,
      ),
    );
  }

  function tanganiBatal() {
    setFileTerpilih([]);
    setKesalahanUpload(null);
  }

  async function tanganiUpload(peristiwa) {
    peristiwa.preventDefault();
    setSedangUpload(true);
    setKesalahanUpload(null);
    try {
      const formData = new FormData();
      fileTerpilih.forEach(({ file }) => formData.append("files", file));
      fileTerpilih.forEach(({ nama }) =>
        formData.append("nama_peserta_didik", nama),
      );
      const hasil = await batchApi.unggahFileJawaban(idBatch, formData);
      onUploadSukses(hasil);
      setFileTerpilih([]);
    } catch (error) {
      setKesalahanUpload(error.pesan);
    } finally {
      setSedangUpload(false);
    }
  }

  return (
    <div className="mt-8">
      <h2 className="mb-4 text-lg font-semibold text-teks">
        Jawaban Peserta Didik
      </h2>

      {!adaSoal && (
        <KeadaanData keadaan="kosong" pesan={PESAN_KODE.BELUM_ADA_SOAL} />
      )}

      {adaSoal && (
        <>
          {daftarFileJawaban.length === 0 && (
            <p className="mb-3 text-sm text-teks-redup">
              Pastikan semua soal sudah ditambahkan. Setelah jawaban diunggah,
              soal tidak dapat ditambah lagi.
            </p>
          )}

          {fileTerpilih.length === 0 && (
            <label className="inline-block cursor-pointer rounded-md bg-biru-utama px-4 py-2 text-permukaan focus-within:ring-2 focus-within:ring-biru-utama">
              Upload Jawaban Peserta Didik
              <input
                type="file"
                multiple
                accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                onChange={tanganiPilihFile}
                className="sr-only"
              />
            </label>
          )}

          {fileTerpilih.length > 0 && (
            <form
              onSubmit={tanganiUpload}
              className="rounded-lg border border-garis bg-permukaan p-6"
            >
              <ul className="mb-4 space-y-3">
                {fileTerpilih.map((item, index) => (
                  <li key={index} className="flex items-center gap-3">
                    <span className="flex-1 truncate text-teks">
                      {item.file.name}
                    </span>
                    <input
                      type="text"
                      required
                      maxLength={100}
                      placeholder="Nama peserta didik"
                      value={item.nama}
                      onChange={(peristiwa) =>
                        ubahNama(index, peristiwa.target.value)
                      }
                      className="w-48 rounded-md border border-garis bg-permukaan px-3 py-2 text-teks"
                    />
                  </li>
                ))}
              </ul>

              {kesalahanUpload && (
                <PesanForm
                  varian="galat"
                  pesan={kesalahanUpload}
                  className="mb-3"
                />
              )}

              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={sedangUpload}
                  className="flex items-center justify-center gap-2 rounded-md bg-biru-utama px-4 py-2 text-permukaan disabled:opacity-50"
                >
                  {sedangUpload && <Spinner ukuran="size-4" />}
                  Upload
                </button>
                <button
                  type="button"
                  onClick={tanganiBatal}
                  disabled={sedangUpload}
                  className="rounded-md border border-garis px-4 py-2 text-teks-redup disabled:opacity-50"
                >
                  Batal
                </button>
              </div>
            </form>
          )}
        </>
      )}

      {daftarFileJawaban.length > 0 && (
        <ul className="mt-6 space-y-2">
          {daftarFileJawaban.map((fileJawaban) => (
            <li
              key={fileJawaban.id_file}
              className="flex items-center justify-between rounded-lg border border-garis bg-permukaan p-3"
            >
              <div>
                <span className="text-teks">
                  {fileJawaban.nama_peserta_didik}
                </span>
                {fileJawaban.status_proses === "gagal" &&
                  fileJawaban.pesan_error && (
                    <p className="mt-1 text-sm text-kurang-mirip">
                      {fileJawaban.pesan_error}
                    </p>
                  )}
              </div>
              <Lencana varian={fileJawaban.status_proses} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default SeksiJawabanPesertaDidik;
