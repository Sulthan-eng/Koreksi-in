import { useEffect, useState } from "react";
import * as batchApi from "../api/batch.js";
import { LencanaKategori } from "./Lencana.jsx";
import Spinner from "./Spinner.jsx";

function TabHasilKoreksi({ idBatch, daftarSoal }) {
  const [status, setStatus] = useState("memuat");
  const [daftarHasil, setDaftarHasil] = useState([]);
  const [noSoalDipilih, setNoSoalDipilih] = useState(daftarSoal[0]?.no_soal ?? null);

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
    return (
      <div className="flex justify-center p-8">
        <Spinner className="h-6 w-6 text-biru-utama" />
      </div>
    );
  }

  if (status === "gagal") {
    return (
      <p role="alert" className="text-kurang-mirip">
        Koneksi internet terputus, coba muat ulang halaman.
      </p>
    );
  }

  const hasilSoalTerpilih = daftarHasil.filter((item) => item.no_soal === noSoalDipilih);

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {daftarSoal.map((soal) => (
          <button
            key={soal.id_soal}
            type="button"
            onClick={() => setNoSoalDipilih(soal.no_soal)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              noSoalDipilih === soal.no_soal
                ? "bg-biru-utama text-white"
                : "border border-garis text-teks-redup"
            }`}
          >
            Soal {soal.no_soal}
          </button>
        ))}
      </div>

      {hasilSoalTerpilih.length === 0 ? (
        <p className="text-teks-redup">
          Belum ada hasil koreksi untuk soal ini. Tunggu proses selesai.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-garis">
          <table className="w-full min-w-max text-left">
            <thead>
              <tr className="border-b border-garis">
                <th className="p-3 text-sm font-medium text-teks-redup">Peserta Didik</th>
                <th className="p-3 text-sm font-medium text-teks-redup">Teks OCR</th>
                <th className="p-3 text-sm font-medium text-teks-redup">Skor Kemiripan</th>
                <th className="p-3 text-sm font-medium text-teks-redup">Kategori Kualitatif</th>
              </tr>
            </thead>
            <tbody>
              {hasilSoalTerpilih.map((item) => (
                <tr key={item.id_file} className="border-b border-garis last:border-0">
                  <td className="p-3 text-teks">{item.nama_peserta_didik}</td>
                  <td className="whitespace-pre-wrap p-3 text-teks">
                    {item.teks_ocr || (
                      <span className="text-teks-redup">(jawaban tidak ditemukan)</span>
                    )}
                  </td>
                  <td className="p-3 text-teks">{item.skor_sistem}</td>
                  <td className="p-3">
                    <LencanaKategori kategori={item.kategori} />
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
