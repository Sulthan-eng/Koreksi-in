import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Check,
  ChevronRight,
  CircleAlert,
  Crown,
  MessageCircle,
  UserCheck,
} from "lucide-react";
import * as langgananApi from "../api/langganan.js";
import { PESAN_KODE, pesanBerlakuHingga } from "../api/pesan.js";
import { useAuth } from "../context/AuthContext.jsx";
import { apakahGalatJaringan, formatTanggalWib } from "../lib/akunPengajar.js";
import {
  buatPesanKendalaPembayaran,
  buatTautanWhatsAppAdmin,
} from "../lib/kontakAdmin.js";
import {
  DAFTAR_MANFAAT_PRO,
  DAFTAR_PAKET_PRO,
  JEDA_POLLING_TRANSAKSI_MS,
  ambilTransaksiTerakhir,
  formatRingkasanPaket,
  formatRingkasanTransaksi,
  formatRupiah,
  formatTanggalSingkatWib,
  labelTombolLangganan,
  langkahPollingTransaksi,
  namaPaketTransaksi,
} from "../lib/langganan.js";
import KeadaanData from "../components/KeadaanData.jsx";
import Lencana from "../components/Lencana.jsx";
import Spinner from "../components/Spinner.jsx";

const NOMOR_WA_ADMIN = import.meta.env.VITE_NOMOR_WA_ADMIN;

function Langganan() {
  const { nama, email, statusLangganan, masaBerlakuPro, muatUlangProfil } =
    useAuth();
  const [sedangMuatProfilAwal, setSedangMuatProfilAwal] = useState(true);
  const [paketTerpilih, setPaketTerpilih] = useState(DAFTAR_PAKET_PRO[0].kode);
  const [ringkasanTerbuka, setRingkasanTerbuka] = useState(false);
  const [sedangMembuatTransaksi, setSedangMembuatTransaksi] = useState(false);
  const [galatTransaksi, setGalatTransaksi] = useState(null);

  const [statusMuatTransaksi, setStatusMuatTransaksi] = useState("memuat");
  const [daftarTransaksi, setDaftarTransaksi] = useState([]);
  const [pollingBerhentiMenunggu, setPollingBerhentiMenunggu] = useState(false);
  const [sedangPeriksaStatus, setSedangPeriksaStatus] = useState(false);

  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    let dibatalkan = false;

    muatUlangProfil({ pertahankanSaatGagal: false })
      .catch(() => {})
      .finally(() => {
        if (!dibatalkan) {
          setSedangMuatProfilAwal(false);
        }
      });

    langgananApi
      .daftarTransaksi()
      .then((hasil) => {
        if (dibatalkan) return;
        setDaftarTransaksi(hasil);
        setPollingBerhentiMenunggu(false);
        setStatusMuatTransaksi("siap");
      })
      .catch((error) => {
        if (dibatalkan) return;
        setStatusMuatTransaksi(
          apakahGalatJaringan(error) ? "offline" : "gagal",
        );
      });

    return () => {
      dibatalkan = true;
    };
  }, [muatUlangProfil]);

  const transaksiTerakhir = ambilTransaksiTerakhir(daftarTransaksi);
  const idTransaksiTerakhir = transaksiTerakhir?.id_transaksi ?? null;
  const statusTransaksiTerakhir = transaksiTerakhir?.status ?? null;

  useEffect(() => {
    if (
      statusMuatTransaksi !== "siap" ||
      !idTransaksiTerakhir ||
      statusTransaksiTerakhir !== "menunggu" ||
      pollingBerhentiMenunggu
    ) {
      return;
    }

    let dibatalkan = false;
    let timerId = null;
    let percobaan = 0;
    let gagalBeruntun = 0;

    function jadwalkanBerikutnya() {
      timerId = setTimeout(async () => {
        try {
          const hasil = await langgananApi.daftarTransaksi();
          if (dibatalkan) return;
          setDaftarTransaksi(hasil);
          const terbaru = ambilTransaksiTerakhir(hasil);
          const statusTerbaru = terbaru?.status ?? null;
          const langkah = langkahPollingTransaksi({
            statusTransaksi: statusTerbaru,
            percobaanSaatIni: percobaan,
            gagalBeruntunSaatIni: gagalBeruntun,
            berhasil: true,
          });
          percobaan = langkah.percobaan;
          gagalBeruntun = langkah.gagalBeruntun;

          if (langkah.perluMuatUlangProfil) {
            muatUlangProfil({ pertahankanSaatGagal: true }).catch(() => {});
          }
          if (langkah.belumTerkonfirmasi) {
            setPollingBerhentiMenunggu(true);
            return;
          }
          if (!langkah.berhenti) {
            jadwalkanBerikutnya();
          }
        } catch {
          if (dibatalkan) return;
          const langkah = langkahPollingTransaksi({
            statusTransaksi: "menunggu",
            percobaanSaatIni: percobaan,
            gagalBeruntunSaatIni: gagalBeruntun,
            berhasil: false,
          });
          percobaan = langkah.percobaan;
          gagalBeruntun = langkah.gagalBeruntun;
          if (langkah.belumTerkonfirmasi) {
            setPollingBerhentiMenunggu(true);
            return;
          }
          if (!langkah.berhenti) {
            jadwalkanBerikutnya();
          }
        }
      }, JEDA_POLLING_TRANSAKSI_MS);
    }

    jadwalkanBerikutnya();

    return () => {
      dibatalkan = true;
      clearTimeout(timerId);
    };
  }, [
    statusMuatTransaksi,
    idTransaksiTerakhir,
    statusTransaksiTerakhir,
    pollingBerhentiMenunggu,
    muatUlangProfil,
  ]);

  function tanganiPilihPaket(kodePaket) {
    if (sedangMembuatTransaksi) return;
    setPaketTerpilih(kodePaket);
    setGalatTransaksi(null);
  }

  function tanganiBukaRingkasan() {
    if (sedangMembuatTransaksi) return;
    setGalatTransaksi(null);
    setRingkasanTerbuka(true);
  }

  async function tanganiLanjutkanPembayaran() {
    if (sedangMembuatTransaksi) return;
    setGalatTransaksi(null);
    setSedangMembuatTransaksi(true);
    try {
      const hasil = await langgananApi.buatTransaksi({ paket: paketTerpilih });
      window.location.assign(hasil.redirect_url);
    } catch (error) {
      if (!mountedRef.current) return;
      if (error?.kode !== "SESI_BERAKHIR") {
        if (error?.kode === "TRANSAKSI_GAGAL_DIBUAT") {
          setGalatTransaksi(PESAN_KODE.TRANSAKSI_GAGAL_DIBUAT);
        } else if (error?.kode === "GAGAL_MENCATAT_TRANSAKSI") {
          setGalatTransaksi(PESAN_KODE.GAGAL_MENCATAT_TRANSAKSI);
        } else if (apakahGalatJaringan(error)) {
          setGalatTransaksi(PESAN_KODE.KONEKSI_TERPUTUS_COBA_LAGI);
        } else {
          setGalatTransaksi(error?.pesan || PESAN_KODE.TRANSAKSI_GAGAL_DIBUAT);
        }
      }
      setSedangMembuatTransaksi(false);
    }
  }

  async function tanganiPeriksaStatus() {
    if (sedangPeriksaStatus) return;
    setSedangPeriksaStatus(true);
    try {
      const [hasilTransaksi] = await Promise.all([
        langgananApi.daftarTransaksi(),
        muatUlangProfil({ pertahankanSaatGagal: true }).catch(() => null),
      ]);
      if (!mountedRef.current) return;
      setDaftarTransaksi(hasilTransaksi);
      const terbaru = ambilTransaksiTerakhir(hasilTransaksi);
      if (!terbaru || terbaru.status !== "menunggu") {
        setPollingBerhentiMenunggu(false);
      }
    } catch {
      // Gagal sementara saat periksa manual: pertahankan tampilan transaksi dan
      // tombol Periksa Status agar Pengajar dapat mencoba kembali.
    } finally {
      if (mountedRef.current) {
        setSedangPeriksaStatus(false);
      }
    }
  }

  const tanggalBerlakuTeks =
    statusLangganan === "pro" && masaBerlakuPro
      ? formatTanggalWib(masaBerlakuPro)
      : "";

  const tautanWhatsAppAdmin = buatTautanWhatsAppAdmin({
    nomor: NOMOR_WA_ADMIN,
    pesan: buatPesanKendalaPembayaran({
      nama,
      email,
      transaksi: transaksiTerakhir,
    }),
  });

  return (
    <div className="min-h-screen bg-latar text-teks">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold leading-8">Langganan</h1>
          <p className="text-sm leading-5 text-teks-redup">
            Kelola paket Pro dan pantau status pembayaran.
          </p>
        </div>

        <section className="flex flex-col gap-4 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
          {sedangMuatProfilAwal && !statusLangganan ? (
            <KeadaanData keadaan="memuat" className="py-2" />
          ) : statusLangganan ? (
            <div className="flex flex-wrap items-center gap-3">
              {statusLangganan === "pro" ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-biru-utama px-2.5 py-0.5 text-sm font-semibold leading-5 whitespace-nowrap text-permukaan">
                  <Crown className="size-4" aria-hidden="true" />
                  PRO
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-garis bg-latar px-2.5 py-0.5 text-sm font-semibold leading-5 whitespace-nowrap text-teks-redup">
                  <UserCheck className="size-4" aria-hidden="true" />
                  FREE
                </span>
              )}
              {statusLangganan === "pro" ? (
                tanggalBerlakuTeks && (
                  <p className="text-base leading-6">
                    {pesanBerlakuHingga(tanggalBerlakuTeks)}
                  </p>
                )
              ) : (
                <p className="text-base leading-6">
                  {PESAN_KODE.AKUN_MEMAKAI_FREE}
                </p>
              )}
            </div>
          ) : (
            <p
              role="alert"
              className="flex items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
            >
              <CircleAlert
                className="mt-0.5 size-4 shrink-0"
                aria-hidden="true"
              />
              <span>{PESAN_KODE.GAGAL_MUAT_LANGGANAN}</span>
            </p>
          )}
        </section>

        <section className="rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
          <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
            <fieldset className="flex flex-col gap-4">
              <legend className="text-lg font-semibold">Paket Pro</legend>
              <div className="grid gap-3">
                {DAFTAR_PAKET_PRO.map((paket) => (
                  <label
                    key={paket.kode}
                    className="flex min-h-11 cursor-pointer items-center gap-3 rounded-lg border border-garis bg-permukaan p-4 has-[:checked]:border-biru-utama has-[:checked]:bg-biru-muda focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-biru-utama"
                  >
                    <input
                      type="radio"
                      name="paket-pro"
                      value={paket.kode}
                      checked={paketTerpilih === paket.kode}
                      onChange={() => tanganiPilihPaket(paket.kode)}
                      className="size-5 accent-biru-utama"
                    />
                    <span className="text-base leading-6">
                      {paket.labelDurasi},{" "}
                      <span className="text-lg font-bold leading-7">
                        {paket.hargaTeks}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
            <div className="flex flex-col gap-3 lg:border-l lg:border-garis lg:pl-8">
              <h3 className="text-base font-semibold leading-6">Manfaat</h3>
              <ul className="grid gap-2 text-base leading-6">
                {DAFTAR_MANFAAT_PRO.map((manfaat) => (
                  <li key={manfaat} className="flex items-center gap-2">
                    <Check
                      className="size-4 shrink-0 text-biru-utama"
                      aria-hidden="true"
                    />
                    {manfaat}
                  </li>
                ))}
              </ul>
              <p className="mt-auto border-t border-garis pt-4 text-sm leading-5 text-teks-redup lg:border-t-0 lg:pt-0">
                Langganan Pro tidak diperpanjang otomatis.
              </p>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              aria-disabled={sedangMembuatTransaksi ? "true" : undefined}
              onClick={tanganiBukaRingkasan}
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-biru-utama bg-biru-utama px-5 font-semibold text-permukaan focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama aria-disabled:opacity-50"
            >
              {labelTombolLangganan(statusLangganan)}
            </button>
          </div>

          {ringkasanTerbuka && (
            <div className="grid gap-4 rounded-lg border border-garis bg-latar p-6 lg:grid-cols-2 lg:gap-8">
              <div className="flex flex-col gap-4">
                <p className="text-lg font-semibold leading-7">
                  {formatRingkasanPaket(paketTerpilih)}
                </p>
                {galatTransaksi && (
                  <p
                    role="alert"
                    className="flex items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
                  >
                    <CircleAlert
                      className="mt-0.5 size-4 shrink-0"
                      aria-hidden="true"
                    />
                    <span>{galatTransaksi}</span>
                  </p>
                )}
                <div>
                  <button
                    type="button"
                    aria-disabled={sedangMembuatTransaksi ? "true" : undefined}
                    onClick={tanganiLanjutkanPembayaran}
                    className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-5 font-semibold text-permukaan focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama aria-disabled:opacity-50"
                  >
                    {sedangMembuatTransaksi && <Spinner ukuran="size-4" />}
                    Lanjutkan ke Pembayaran
                  </button>
                </div>
              </div>
              <ul className="grid content-start gap-2 self-start text-sm leading-5 text-teks-redup">
                {DAFTAR_MANFAAT_PRO.map((manfaat) => (
                  <li key={manfaat} className="flex items-center gap-2">
                    <Check
                      className="size-4 shrink-0 text-biru-utama"
                      aria-hidden="true"
                    />
                    {manfaat}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {statusMuatTransaksi === "memuat" && (
          <KeadaanData keadaan="memuat" className="py-6" />
        )}

        {(statusMuatTransaksi === "gagal" ||
          statusMuatTransaksi === "offline") && (
          <p
            role="alert"
            className="flex items-start gap-2 rounded-lg bg-kurang-mirip-latar px-4 py-3 text-sm leading-5 text-kurang-mirip"
          >
            <CircleAlert
              className="mt-0.5 size-4 shrink-0"
              aria-hidden="true"
            />
            <span>
              {statusMuatTransaksi === "offline"
                ? PESAN_KODE.KONEKSI_TERPUTUS
                : PESAN_KODE.GAGAL_MUAT_LANGGANAN}
            </span>
          </p>
        )}

        {statusMuatTransaksi === "siap" && transaksiTerakhir && (
          <section className="flex flex-col gap-4 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <h2 className="text-lg font-semibold">
                Status transaksi terakhir
              </h2>
              <div className="flex flex-wrap items-center gap-3">
                <Lencana varian={transaksiTerakhir.status} />
                <p className="text-base leading-6">
                  {formatRingkasanTransaksi(transaksiTerakhir)}
                </p>
              </div>
            </div>

            {transaksiTerakhir.status === "menunggu" &&
              pollingBerhentiMenunggu && (
                <div className="flex flex-col gap-3 border-t border-garis pt-4 lg:flex-row lg:items-center lg:justify-between">
                  <p className="text-sm leading-5 text-teks-redup">
                    {PESAN_KODE.PEMBAYARAN_BELUM_TERKONFIRMASI}
                    {tautanWhatsAppAdmin && (
                      <>
                        {" "}
                        <a
                          href={tautanWhatsAppAdmin}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-semibold text-biru-utama underline"
                        >
                          Hubungi Admin
                        </a>
                      </>
                    )}
                  </p>
                  <div>
                    <button
                      type="button"
                      aria-disabled={sedangPeriksaStatus ? "true" : undefined}
                      onClick={tanganiPeriksaStatus}
                      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-garis bg-permukaan px-4 text-sm font-semibold text-teks focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama aria-disabled:opacity-50"
                    >
                      {sedangPeriksaStatus && <Spinner ukuran="size-4" />}
                      Periksa Status
                    </button>
                  </div>
                </div>
              )}

            {(transaksiTerakhir.status === "gagal" ||
              transaksiTerakhir.status === "kedaluwarsa") &&
              tautanWhatsAppAdmin && (
                <p className="border-t border-garis pt-4 text-sm leading-5 text-teks-redup">
                  Pembayaran belum berhasil. Jika saldo Anda sudah terpotong,{" "}
                  <a
                    href={tautanWhatsAppAdmin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-semibold text-biru-utama underline"
                  >
                    hubungi Admin
                  </a>
                  .
                </p>
              )}
          </section>
        )}

        {statusMuatTransaksi === "siap" && daftarTransaksi.length > 0 && (
          <section className="flex flex-col gap-4 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
            <h2 className="text-lg font-semibold">Riwayat transaksi</h2>
            <ul className="flex flex-col">
              {daftarTransaksi.map((item) => (
                <li
                  key={item.id_transaksi}
                  className="flex flex-col gap-3 border-t border-garis py-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex flex-col gap-1">
                    <p className="text-sm leading-5 text-teks-redup">
                      {formatTanggalSingkatWib(item.dibuat_pada)}
                    </p>
                    <p className="text-base font-semibold leading-6">
                      {namaPaketTransaksi(item.paket)}
                    </p>
                    <p className="text-sm leading-5 text-teks-redup">
                      {formatRupiah(item.nominal)}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 sm:justify-end">
                    <Lencana varian={item.status} />
                    {item.status === "berhasil" && item.id_order && (
                      <Link
                        to={`/invoice/${item.id_order}`}
                        className="inline-flex min-h-11 items-center gap-1 font-semibold text-biru-utama underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
                      >
                        Lihat invoice
                        <ChevronRight className="size-4" aria-hidden="true" />
                      </Link>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}

        {tautanWhatsAppAdmin && (
          <section className="flex flex-col gap-3 rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
            <h2 className="text-lg font-semibold">Ada kendala pembayaran?</h2>
            <div>
              <a
                href={tautanWhatsAppAdmin}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-garis bg-permukaan px-5 font-semibold text-teks focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
              >
                <MessageCircle className="size-4" aria-hidden="true" />
                Hubungi Admin via WhatsApp
              </a>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default Langganan;
