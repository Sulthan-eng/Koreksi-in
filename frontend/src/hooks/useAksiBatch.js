import { useState } from "react";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";

/**
 * Alur aksi batch yang dipakai bersama: periksa keadaan dahulu, tampilkan
 * dialog konfirmasi, panggil API, lalu tangani hasil atau galatnya.
 * Halaman menyediakan respons keberhasilan lewat callback (memperbarui
 * daftar di Beranda, baca-saja dan berpindah halaman di Halaman Batch).
 */
export function useAksiBatch({
  cekPilihanBelumUnggah,
  onSelesaiSukses,
  onHapusSukses,
}) {
  const [dialog, setDialog] = useState(null); // { jenis, batch }
  const [sedangMemproses, setSedangMemproses] = useState(false);
  const [idBatchMemeriksa, setIdBatchMemeriksa] = useState(null);
  const [pesanAksi, setPesanAksi] = useState(null);

  async function pilihSelesaikan(batch) {
    if (sedangMemproses || idBatchMemeriksa !== null) return;
    setPesanAksi(null);
    if (cekPilihanBelumUnggah?.()) {
      setPesanAksi({
        varian: "galat",
        teks: PESAN_KODE.ADA_FILE_BELUM_UNGGAH,
      });
      return;
    }
    setIdBatchMemeriksa(batch.id_batch);
    try {
      const daftarFile = await batchApi.daftarFileJawaban(batch.id_batch);
      const adaFileDiproses = daftarFile.some(
        (fileJawaban) => fileJawaban.status_proses === "diproses",
      );
      if (adaFileDiproses) {
        setPesanAksi({
          varian: "galat",
          teks: PESAN_KODE.MASIH_ADA_FILE_DIPROSES,
        });
      } else {
        setDialog({ jenis: "selesaikan", batch });
      }
    } catch (error) {
      setPesanAksi({ varian: "galat", teks: error.pesan });
    } finally {
      setIdBatchMemeriksa(null);
    }
  }

  function pilihHapus(batch) {
    setPesanAksi(null);
    setDialog({ jenis: "hapus", batch });
  }
  async function konfirmasi() {
    const { jenis, batch } = dialog;
    setSedangMemproses(true);
    try {
      if (jenis === "selesaikan") {
        const hasil = await batchApi.selesaikanBatch(batch.id_batch);
        setPesanAksi({
          varian: "sukses",
          teks: PESAN_KODE.BATCH_SELESAI_SUKSES,
        });
        onSelesaiSukses?.(hasil);
      } else {
        await batchApi.hapusBatch(batch.id_batch);
        onHapusSukses?.(batch);
      }
    } catch (error) {
      setPesanAksi({ varian: "galat", teks: error.pesan });
    } finally {
      setSedangMemproses(false);
      setDialog(null);
    }
  }

  function batalkan() {
    if (sedangMemproses) return;
    setDialog(null);
  }

  // Kosongkan pesan tertentu tanpa menyentuh pesan lain, misalnya saat
  // pilihan file berubah sehingga pesan itu sudah tidak berlaku.
  function bersihkanPesan(teks) {
    setPesanAksi((sebelumnya) =>
      sebelumnya?.teks === teks ? null : sebelumnya,
    );
  }

  return {
    dialog,
    sedangMemproses,
    idBatchMemeriksa,
    pesanAksi,
    pilihSelesaikan,
    pilihHapus,
    konfirmasi,
    batalkan,
    bersihkanPesan,
  };
}

export default useAksiBatch;
