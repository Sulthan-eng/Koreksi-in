import { useEffect, useRef, useState } from "react";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";
import KeadaanData from "./KeadaanData.jsx";
import Lencana from "./Lencana.jsx";

function TeksOcr({ teks }) {
  const refTeks = useRef(null);
  const [dibuka, setDibuka] = useState(false);
  const [terpotong, setTerpotong] = useState(false);

  useEffect(() => {
    const elemen = refTeks.current;
    if (!elemen || dibuka) return undefined;

    function periksaTerpotong() {
      setTerpotong(elemen.scrollHeight > elemen.clientHeight);
    }

    periksaTerpotong();
    const observer = new ResizeObserver(periksaTerpotong);
    observer.observe(elemen);
    return () => observer.disconnect();
  }, [teks, dibuka]);

  if (!teks) {
    return <span className="text-teks-redup">(jawaban tidak ditemukan)</span>;
  }

  return (
    <div>
      <p
        ref={refTeks}
        className={`whitespace-pre-wrap text-teks ${dibuka ? "" : "line-clamp-3"}`}
      >
        {teks}
      </p>
      {(terpotong || dibuka) && (
        <button
          type="button"
          aria-expanded={dibuka}
          onClick={() => setDibuka((sebelumnya) => !sebelumnya)}
          className="mt-1 inline-flex min-h-11 items-center text-sm font-semibold text-biru-utama underline"
        >
          {dibuka ? "Tampilkan ringkas" : "Tampilkan lengkap"}
        </button>
      )}
    </div>
  );
}

function TabHasilKoreksi({ idBatch, daftarSoal }) {
  const [status, setStatus] = useState("memuat");
  const [daftarHasil, setDaftarHasil] = useState([]);
  const [noSoalDipilih, setNoSoalDipilih] = useState(
    daftarSoal[0]?.no_soal ?? null,
  );

  useEffect(() => {
    let dibatalkan = false;
    (async () => {
      try {
        const hasil = await batchApi.daftarHasilKoreksi(idBatch);
        if (!dibatalkan) {
          setDaftarHasil(hasil);
          setStatus("siap");
        }
      } catch {
        if (!dibatalkan) setStatus("gagal");
      }
    })();
    return () => {
      dibatalkan = true;
    };
  }, [idBatch]);

  if (status === "memuat") {
    return <KeadaanData keadaan="memuat" className="p-8" />;
  }

  if (status === "gagal") {
    return <KeadaanData keadaan="gagal" pesan={PESAN_KODE.KONEKSI_TERPUTUS} />;
  }

  const hasilSoalTerpilih = daftarHasil.filter(
    (item) => item.no_soal === noSoalDipilih,
  );

  return (
    <div>
      <select
        aria-label="Soal"
        value={noSoalDipilih ?? ""}
        onChange={(peristiwa) =>
          setNoSoalDipilih(Number(peristiwa.target.value))
        }
        className="mb-4 h-11 w-fit min-w-40 rounded-lg border border-garis bg-permukaan px-3 text-teks"
      >
        {daftarSoal.map((soal) => (
          <option key={soal.id_soal} value={soal.no_soal}>
            Soal {soal.no_soal}
          </option>
        ))}
      </select>

      {hasilSoalTerpilih.length === 0 ? (
        <KeadaanData keadaan="kosong" pesan={PESAN_KODE.BELUM_ADA_HASIL_SOAL} />
      ) : (
        <div className="overflow-hidden rounded-lg border border-garis bg-permukaan max-lg:overflow-visible max-lg:border-0 max-lg:bg-transparent">
          <table role="table" className="w-full border-collapse max-lg:block">
            <thead role="rowgroup" className="max-lg:hidden">
              <tr role="row">
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-3 text-left text-sm font-semibold text-teks-redup"
                >
                  Peserta Didik
                </th>
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-3 text-left text-sm font-semibold text-teks-redup"
                >
                  Teks OCR
                </th>
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-3 text-left text-sm font-semibold text-teks-redup"
                >
                  Skor Kemiripan
                </th>
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-3 text-left text-sm font-semibold text-teks-redup"
                >
                  Kategori Kualitatif
                </th>
              </tr>
            </thead>
            <tbody role="rowgroup" className="max-lg:block">
              {hasilSoalTerpilih.map((item) => (
                <tr
                  key={item.id_file}
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
                    <span className="text-teks">{item.nama_peserta_didik}</span>
                  </td>
                  <td
                    role="cell"
                    className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                  >
                    <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                      Teks OCR
                    </span>
                    <TeksOcr teks={item.teks_ocr} />
                  </td>
                  <td
                    role="cell"
                    className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                  >
                    <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                      Skor Kemiripan
                    </span>
                    <span className="text-teks">{item.skor_sistem}</span>
                  </td>
                  <td
                    role="cell"
                    className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                  >
                    <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                      Kategori Kualitatif
                    </span>
                    <Lencana varian={item.kategori} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default TabHasilKoreksi;
