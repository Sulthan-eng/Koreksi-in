import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import * as adminApi from "../api/admin.js";
import {
  PESAN_KODE,
  pesanAktifkanAkun,
  pesanNonaktifkanAkun,
} from "../api/pesan.js";
import {
  apakahGalatJaringan,
  terapkanPerubahanAkun,
} from "../lib/akunPengajar.js";
import DialogKonfirmasi from "../components/DialogKonfirmasi.jsx";
import DialogUbahLangganan from "../components/DialogUbahLangganan.jsx";
import KeadaanData from "../components/KeadaanData.jsx";
import PesanForm from "../components/PesanForm.jsx";
import TabelAkunPengajar from "../components/TabelAkunPengajar.jsx";

const DEBOUNCE_CARI_MS = 300;

function AkunPengajar() {
  const [cari, setCari] = useState("");
  const [cariAktif, setCariAktif] = useState("");
  const [statusLangganan, setStatusLangganan] = useState("");
  const [statusAkun, setStatusAkun] = useState("");

  const [statusMuat, setStatusMuat] = useState("memuat"); // memuat | siap | gagal | offline
  const [daftarAkun, setDaftarAkun] = useState([]);
  const [pernahAdaAkun, setPernahAdaAkun] = useState(false);

  const [pesanAksi, setPesanAksi] = useState(null);
  const [dialogLangganan, setDialogLangganan] = useState(null);
  const [dialogStatus, setDialogStatus] = useState(null); // { jenis: 'nonaktifkan'|'aktifkan', akun }
  const [sedangUbahStatus, setSedangUbahStatus] = useState(false);
  const [galatDialogStatus, setGalatDialogStatus] = useState(null);

  const idPermintaanRef = useRef(0);
  const pemicuDialogRef = useRef(null);
  const judulHalamanRef = useRef(null);

  useEffect(() => {
    const pengatur = setTimeout(() => {
      setCariAktif(cari);
    }, DEBOUNCE_CARI_MS);
    return () => clearTimeout(pengatur);
  }, [cari]);

  useEffect(() => {
    const idPermintaan = (idPermintaanRef.current += 1);
    const adaFilter =
      cariAktif.trim() !== "" || statusLangganan !== "" || statusAkun !== "";

    adminApi
      .daftarAkunPengajar({
        cari: cariAktif,
        status_langganan: statusLangganan,
        status_akun: statusAkun,
      })
      .then((hasil) => {
        if (idPermintaan !== idPermintaanRef.current) return;
        setDaftarAkun(hasil);
        if (hasil.length > 0 || adaFilter) {
          setPernahAdaAkun((sebelumnya) => sebelumnya || hasil.length > 0);
        }
        setStatusMuat("siap");
      })
      .catch((error) => {
        if (idPermintaan !== idPermintaanRef.current) return;
        setStatusMuat(apakahGalatJaringan(error) ? "offline" : "gagal");
      });
  }, [cariAktif, statusLangganan, statusAkun]);

  function pulihkanFokusSetelahDialog() {
    requestAnimationFrame(() => {
      const pemicu = pemicuDialogRef.current;
      pemicuDialogRef.current = null;
      if (pemicu && document.contains(pemicu)) {
        pemicu.focus();
      } else {
        judulHalamanRef.current?.focus();
      }
    });
  }

  function bukaDialogLangganan(akun, pemicu) {
    pemicuDialogRef.current = pemicu;
    setPesanAksi(null);
    setDialogLangganan(akun);
  }

  function tutupDialogLangganan() {
    setDialogLangganan(null);
    pulihkanFokusSetelahDialog();
  }

  async function simpanLangganan(idPengguna, payload) {
    const akunBaru = await adminApi.ubahLanggananPengajar(idPengguna, payload);
    setDaftarAkun((sebelumnya) =>
      terapkanPerubahanAkun(sebelumnya, akunBaru, {
        statusLangganan,
        statusAkun,
      }),
    );
    setDialogLangganan(null);
    setPesanAksi({
      varian: "sukses",
      teks: PESAN_KODE.LANGGANAN_BERHASIL_DIUBAH,
    });
    pulihkanFokusSetelahDialog();
  }

  function bukaDialogStatus(jenis, akun, pemicu) {
    pemicuDialogRef.current = pemicu;
    setPesanAksi(null);
    setGalatDialogStatus(null);
    setDialogStatus({ jenis, akun });
  }

  function tutupDialogStatus() {
    if (sedangUbahStatus) return;
    setDialogStatus(null);
    setGalatDialogStatus(null);
    pulihkanFokusSetelahDialog();
  }

  async function konfirmasiUbahStatus() {
    if (!dialogStatus || sedangUbahStatus) return;
    const { jenis, akun } = dialogStatus;
    setSedangUbahStatus(true);
    setGalatDialogStatus(null);
    try {
      const akunBaru =
        jenis === "nonaktifkan"
          ? await adminApi.nonaktifkanPengajar(akun.id_pengguna)
          : await adminApi.aktifkanPengajar(akun.id_pengguna);
      setDaftarAkun((sebelumnya) =>
        terapkanPerubahanAkun(sebelumnya, akunBaru, {
          statusLangganan,
          statusAkun,
        }),
      );
      setDialogStatus(null);
      setPesanAksi({
        varian: "sukses",
        teks:
          jenis === "nonaktifkan"
            ? PESAN_KODE.AKUN_BERHASIL_DINONAKTIFKAN
            : PESAN_KODE.AKUN_BERHASIL_DIAKTIFKAN,
      });
      pulihkanFokusSetelahDialog();
    } catch {
      setGalatDialogStatus(PESAN_KODE.GAGAL_UBAH_STATUS_AKUN);
    } finally {
      setSedangUbahStatus(false);
    }
  }

  const adaFilterAktif =
    cariAktif.trim() !== "" || statusLangganan !== "" || statusAkun !== "";
  const tampilkanBilahAlat = pernahAdaAkun;

  return (
    <div className="min-h-screen bg-latar text-teks">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <h1
          ref={judulHalamanRef}
          tabIndex={-1}
          className="text-2xl font-bold leading-8 text-teks"
        >
          Akun Pengajar
        </h1>

        {pesanAksi && (
          <PesanForm varian={pesanAksi.varian} pesan={pesanAksi.teks} kotak />
        )}

        {tampilkanBilahAlat && (
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
            <label className="flex flex-col gap-1.5 lg:flex-1">
              <span className="text-sm font-semibold">Cari</span>
              <div className="relative flex items-center">
                <Search
                  aria-hidden="true"
                  className="pointer-events-none absolute left-3 size-4 text-teks-redup"
                />
                <input
                  type="search"
                  placeholder="Cari berdasarkan nama atau email"
                  value={cari}
                  onChange={(peristiwa) => {
                    setCari(peristiwa.target.value);
                    setStatusMuat("memuat");
                  }}
                  className="h-11 w-full rounded-lg border border-garis bg-permukaan pl-9 pr-3 text-teks placeholder:text-teks-redup"
                />
              </div>
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-semibold">Status langganan</span>
              <select
                value={statusLangganan}
                onChange={(peristiwa) => {
                  setStatusLangganan(peristiwa.target.value);
                  setStatusMuat("memuat");
                }}
                className="h-11 rounded-lg border border-garis bg-permukaan px-3 text-teks"
              >
                <option value="">Semua</option>
                <option value="free">Free</option>
                <option value="pro">Pro</option>
              </select>
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-semibold">Status akun</span>
              <select
                value={statusAkun}
                onChange={(peristiwa) => {
                  setStatusAkun(peristiwa.target.value);
                  setStatusMuat("memuat");
                }}
                className="h-11 rounded-lg border border-garis bg-permukaan px-3 text-teks"
              >
                <option value="">Semua</option>
                <option value="aktif">Aktif</option>
                <option value="nonaktif">Nonaktif</option>
              </select>
            </label>
          </div>
        )}

        {statusMuat === "memuat" && (
          <KeadaanData keadaan="memuat" className="min-h-48" />
        )}

        {statusMuat === "gagal" && (
          <PesanForm
            varian="galat"
            pesan={PESAN_KODE.GAGAL_MUAT_AKUN_PENGAJAR}
            kotak
          />
        )}

        {statusMuat === "offline" && (
          <PesanForm varian="galat" pesan={PESAN_KODE.KONEKSI_TERPUTUS} kotak />
        )}

        {statusMuat === "siap" &&
          daftarAkun.length === 0 &&
          !adaFilterAktif && (
            <div className="rounded-lg border border-garis bg-permukaan p-6 text-center shadow-sm">
              <p>{PESAN_KODE.BELUM_ADA_AKUN_PENGAJAR}</p>
            </div>
          )}

        {statusMuat === "siap" && daftarAkun.length === 0 && adaFilterAktif && (
          <div className="rounded-lg border border-garis bg-permukaan p-6 text-center shadow-sm">
            <p>{PESAN_KODE.PENCARIAN_AKUN_KOSONG}</p>
          </div>
        )}

        {statusMuat === "siap" && daftarAkun.length > 0 && (
          <TabelAkunPengajar
            daftarAkun={daftarAkun}
            onBukaUbahLangganan={bukaDialogLangganan}
            onBukaNonaktifkan={(akun, pemicu) =>
              bukaDialogStatus("nonaktifkan", akun, pemicu)
            }
            onBukaAktifkan={(akun, pemicu) =>
              bukaDialogStatus("aktifkan", akun, pemicu)
            }
          />
        )}
      </main>

      {dialogLangganan && (
        <DialogUbahLangganan
          key={dialogLangganan.id_pengguna}
          akun={dialogLangganan}
          onBatal={tutupDialogLangganan}
          onSimpan={simpanLangganan}
        />
      )}

      <DialogKonfirmasi
        terbuka={dialogStatus?.jenis === "nonaktifkan"}
        judul={PESAN_KODE.JUDUL_NONAKTIFKAN_AKUN}
        isi={
          dialogStatus?.akun ? pesanNonaktifkanAkun(dialogStatus.akun.nama) : ""
        }
        labelBatal="Batal"
        labelYa="Ya"
        tombolUtama="tidak"
        variasiYa="merusak"
        prosesBerjalan={sedangUbahStatus}
        pesanGalat={galatDialogStatus}
        onBatal={tutupDialogStatus}
        onYa={konfirmasiUbahStatus}
      />

      <DialogKonfirmasi
        terbuka={dialogStatus?.jenis === "aktifkan"}
        judul={PESAN_KODE.JUDUL_AKTIFKAN_AKUN}
        isi={
          dialogStatus?.akun ? pesanAktifkanAkun(dialogStatus.akun.nama) : ""
        }
        labelBatal="Batal"
        labelYa="Ya"
        tombolUtama="ya"
        prosesBerjalan={sedangUbahStatus}
        pesanGalat={galatDialogStatus}
        onBatal={tutupDialogStatus}
        onYa={konfirmasiUbahStatus}
      />
    </div>
  );
}

export default AkunPengajar;
