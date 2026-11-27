import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  CircleAlert,
  CircleCheck,
  Printer,
  RotateCcw,
  SearchX,
} from "lucide-react";
import * as langgananApi from "../api/langganan.js";
import { PESAN_KODE } from "../api/pesan.js";
import {
  formatMetodePembayaran,
  formatRupiah,
  formatTanggalJamWib,
} from "../lib/langganan.js";
import Spinner from "../components/Spinner.jsx";

function Invoice() {
  const { idOrder } = useParams();
  const [keadaan, setKeadaan] = useState("memuat");
  const [invoice, setInvoice] = useState(null);
  const [hitunganMuat, setHitunganMuat] = useState(0);

  useEffect(() => {
    let dibatalkan = false;

    langgananApi
      .ambilInvoice(idOrder)
      .then((hasil) => {
        if (dibatalkan) return;
        setInvoice(hasil);
        setKeadaan("berhasil");
      })
      .catch((error) => {
        if (dibatalkan) return;
        if (error?.kode === "SESI_BERAKHIR") return;
        if (
          error?.kode === "INVOICE_TIDAK_DITEMUKAN" ||
          error?.status === 404
        ) {
          setInvoice(null);
          setKeadaan("tidak-ditemukan");
          return;
        }
        setInvoice(null);
        setKeadaan("gagal");
      });

    return () => {
      dibatalkan = true;
    };
  }, [idOrder, hitunganMuat]);

  function tanganiCobaLagi() {
    setKeadaan("memuat");
    setHitunganMuat((sebelumnya) => sebelumnya + 1);
  }

  function tanganiCetak() {
    window.print();
  }

  return (
    <div className="min-h-screen bg-latar text-teks print:min-h-0 print:bg-permukaan">
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6 print:max-w-none print:px-8 print:py-6">
        {keadaan === "berhasil" && invoice && (
          <>
            <article
              aria-labelledby="judul-invoice"
              className="flex break-inside-avoid flex-col gap-6 rounded-lg border border-garis bg-permukaan p-6 shadow-sm md:p-8 print:rounded-none print:border-0 print:p-0 print:shadow-none"
            >
              <header className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <img src="/logo-ikon.png" alt="" className="h-10 w-auto" />
                  <span className="text-lg font-bold">Koreksi-in</span>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <h1
                    id="judul-invoice"
                    className="text-2xl font-bold leading-8"
                  >
                    Invoice
                  </h1>
                  <span className="cetak-warna-persis inline-flex items-center gap-1.5 rounded-full bg-sangat-mirip-latar px-2.5 py-0.5 text-sm font-semibold leading-5 text-sangat-mirip">
                    <CircleCheck className="size-4" aria-hidden="true" />
                    LUNAS
                  </span>
                </div>
              </header>

              <dl className="grid gap-6 border-t border-garis pt-6 sm:grid-cols-2">
                <div className="flex min-w-0 flex-col gap-2">
                  <dt className="text-xs font-semibold uppercase tracking-wider text-teks-redup">
                    Ditagihkan kepada
                  </dt>
                  <dd className="flex min-w-0 flex-col gap-1">
                    <span className="wrap-anywhere text-base font-semibold leading-6">
                      {invoice.nama_pengajar}
                    </span>
                    <span className="wrap-anywhere text-sm leading-5 text-teks-redup">
                      {invoice.email_pengajar}
                    </span>
                  </dd>
                </div>
                <div className="flex min-w-0 flex-col gap-4">
                  <div className="flex flex-col gap-1">
                    <dt className="text-xs font-semibold uppercase tracking-wider text-teks-redup">
                      No. invoice
                    </dt>
                    <dd className="font-semibold">{invoice.nomor_invoice}</dd>
                  </div>
                  <div className="flex flex-col gap-1">
                    <dt className="text-xs font-semibold uppercase tracking-wider text-teks-redup">
                      Tanggal dibayar
                    </dt>
                    <dd>{formatTanggalJamWib(invoice.tanggal_dibayar)}</dd>
                  </div>
                  <div className="flex flex-col gap-1">
                    <dt className="text-xs font-semibold uppercase tracking-wider text-teks-redup">
                      Metode pembayaran
                    </dt>
                    <dd>{formatMetodePembayaran(invoice.metode_pembayaran)}</dd>
                  </div>
                </div>
              </dl>

              <table className="w-full border-collapse text-left text-base">
                <caption className="sr-only">Rincian pembayaran</caption>
                <thead>
                  <tr className="border-b border-garis text-xs font-semibold uppercase tracking-wider text-teks-redup">
                    <th scope="col" className="py-2 font-semibold">
                      Item
                    </th>
                    <th scope="col" className="py-2 text-right font-semibold">
                      Harga
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-garis">
                    <td className="py-3 pr-4">{invoice.paket}</td>
                    <td className="py-3 text-right whitespace-nowrap">
                      {formatRupiah(invoice.nominal)}
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <th scope="row" className="pt-4 text-left font-semibold">
                      Total
                    </th>
                    <td className="pt-4 text-right text-lg font-bold whitespace-nowrap">
                      {formatRupiah(invoice.nominal)}
                    </td>
                  </tr>
                </tfoot>
              </table>

              <p className="border-t border-garis pt-4 text-sm leading-5 text-teks-redup">
                Invoice ini dibuat otomatis oleh sistem.
              </p>
            </article>

            <div className="flex flex-col gap-3 sm:flex-row print:hidden">
              <button
                type="button"
                onClick={tanganiCetak}
                className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-5 font-semibold text-permukaan focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama sm:w-auto"
              >
                <Printer className="size-4" aria-hidden="true" />
                Cetak / Simpan PDF
              </button>
              <Link
                to="/langganan"
                className="inline-flex min-h-11 w-full items-center justify-center rounded-lg border border-garis bg-permukaan px-5 font-semibold no-underline hover:bg-latar focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama sm:w-auto"
              >
                Kembali ke Langganan
              </Link>
            </div>
          </>
        )}

        {keadaan === "memuat" && (
          <section
            role="status"
            className="flex min-h-64 items-center justify-center gap-2 rounded-lg border border-garis bg-permukaan p-6 shadow-sm"
          >
            <Spinner ukuran="size-5" />
            <span className="text-base leading-6 text-teks-redup">
              Memuat invoice
            </span>
          </section>
        )}

        {keadaan === "tidak-ditemukan" && (
          <section className="flex flex-col items-center gap-4 rounded-lg border border-garis bg-permukaan p-8 text-center shadow-sm">
            <SearchX className="size-8 text-teks-redup" aria-hidden="true" />
            <h1 className="text-xl font-semibold leading-7">
              {PESAN_KODE.INVOICE_TIDAK_DITEMUKAN}
            </h1>
            <Link
              to="/langganan"
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-biru-utama bg-biru-utama px-5 font-semibold text-permukaan no-underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
            >
              Kembali ke Langganan
            </Link>
          </section>
        )}

        {keadaan === "gagal" && (
          <section
            role="alert"
            className="flex flex-col items-center gap-4 rounded-lg border border-garis bg-permukaan p-8 text-center shadow-sm"
          >
            <CircleAlert
              className="size-8 text-kurang-mirip"
              aria-hidden="true"
            />
            <p className="text-base leading-6">
              {PESAN_KODE.INVOICE_GAGAL_DIMUAT}
            </p>
            <button
              type="button"
              onClick={tanganiCobaLagi}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-5 font-semibold text-permukaan focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
            >
              <RotateCcw className="size-4" aria-hidden="true" />
              Coba lagi
            </button>
          </section>
        )}
      </main>
    </div>
  );
}

export default Invoice;
