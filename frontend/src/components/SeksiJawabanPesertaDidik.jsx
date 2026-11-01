import { useState } from "react";
import { File, Upload } from "lucide-react";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";
import Lencana from "./Lencana.jsx";
import Spinner from "./Spinner.jsx";

function SeksiJawabanPesertaDidik({
  idBatch,
  adaSoal,
  daftarFileJawaban,
  kesalahanStatus,
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
    <section className="flex flex-col gap-4 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-teks">Jawaban Peserta Didik</h2>

      {!adaSoal && (
        <p className="text-teks-redup">{PESAN_KODE.BELUM_ADA_SOAL}</p>
      )}

      {adaSoal && (
        <div className="flex flex-col gap-4">
          {daftarFileJawaban.length === 0 && fileTerpilih.length === 0 && (
            <p className="text-sm leading-5 text-teks-redup">
              {PESAN_KODE.PERINGATAN_SEBELUM_UNGGAH}
            </p>
          )}

          {fileTerpilih.length === 0 && (
            <div>
              <label className="inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan focus-within:ring-2 focus-within:ring-biru-utama">
                <Upload className="size-4" aria-hidden="true" />
                Upload Jawaban Peserta Didik
                <input
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                  onChange={tanganiPilihFile}
                  className="sr-only"
                />
              </label>
            </div>
          )}

          {fileTerpilih.length > 0 && (
            <form
              onSubmit={tanganiUpload}
              noValidate
              className="flex flex-col gap-4"
            >
              {kesalahanUpload && (
                <p
                  role="alert"
                  className="rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
                >
                  {kesalahanUpload}
                </p>
              )}
              <ul className="flex flex-col gap-3">
                {fileTerpilih.map((item, index) => (
                  <li
                    key={index}
                    className="flex flex-col gap-3 rounded-lg border border-garis bg-permukaan p-4"
                  >
                    <span className="flex items-center gap-2 font-semibold text-teks">
                      <File
                        className="size-4 shrink-0 text-teks"
                        aria-hidden="true"
                      />
                      <span className="truncate">{item.file.name}</span>
                    </span>
                    <label className="flex flex-col gap-1.5">
                      <span className="text-sm font-semibold text-teks">
                        Nama peserta didik
                      </span>
                      <input
                        type="text"
                        required
                        maxLength={100}
                        value={item.nama}
                        onChange={(peristiwa) =>
                          ubahNama(index, peristiwa.target.value)
                        }
                        className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks"
                      />
                    </label>
                  </li>
                ))}
              </ul>

              <div className="flex flex-wrap gap-2">
                <button
                  type="submit"
                  disabled={sedangUpload}
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan disabled:opacity-50"
                >
                  {sedangUpload && <Spinner ukuran="size-4" />}
                  Upload
                </button>
                <button
                  type="button"
                  onClick={tanganiBatal}
                  disabled={sedangUpload}
                  className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks disabled:opacity-50"
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
                  </tr>
                </thead>
                <tbody role="rowgroup" className="max-lg:block">
                  {daftarFileJawaban.map((fileJawaban) => (
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
                        <Lencana varian={fileJawaban.status_proses} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default SeksiJawabanPesertaDidik;
