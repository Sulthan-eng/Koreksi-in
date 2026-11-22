import { pesanBerlakuHingga } from "../api/pesan.js";
import { formatTanggalWib } from "../lib/akunPengajar.js";
import Lencana from "./Lencana.jsx";

const KELAS_HEADER_KOLOM = "px-3 py-4 text-sm font-semibold leading-5";
const KELAS_TOMBOL_AKSI =
  "inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-3 py-2 text-sm font-semibold whitespace-nowrap";

function SelAkun({ label, className = "", children }) {
  return (
    <td
      className={`px-3 py-4 align-top max-lg:block max-lg:p-0 max-lg:py-1 ${className}`.trim()}
    >
      <span
        aria-hidden="true"
        className="hidden text-xs font-semibold text-teks-redup max-lg:block"
      >
        {label}
      </span>
      {children}
    </td>
  );
}

function TabelAkunPengajar({
  daftarAkun,
  onBukaUbahLangganan,
  onBukaNonaktifkan,
  onBukaAktifkan,
}) {
  return (
    <div className="rounded-lg border border-garis bg-permukaan shadow-sm">
      <table className="w-full text-left text-base leading-6 max-lg:block">
        <thead className="max-lg:sr-only">
          <tr className="border-b border-garis text-teks-redup">
            <th scope="col" className={KELAS_HEADER_KOLOM}>
              Nama
            </th>
            <th scope="col" className={KELAS_HEADER_KOLOM}>
              Email
            </th>
            <th scope="col" className={KELAS_HEADER_KOLOM}>
              Langganan
            </th>
            <th scope="col" className={KELAS_HEADER_KOLOM}>
              Status akun
            </th>
            <th scope="col" className={KELAS_HEADER_KOLOM}>
              Tanggal daftar
            </th>
            <th scope="col" className={KELAS_HEADER_KOLOM}>
              Jumlah batch
            </th>
            <th scope="col" className={KELAS_HEADER_KOLOM}>
              Aksi
            </th>
          </tr>
        </thead>
        <tbody className="max-lg:block">
          {daftarAkun.map((akun) => {
            const nonaktif = akun.dinonaktifkan_pada !== null;
            return (
              <tr
                key={akun.id_pengguna}
                className="border-b border-garis last:border-b-0 max-lg:block max-lg:p-4"
              >
                <th
                  scope="row"
                  className="px-3 py-4 align-top text-left font-semibold wrap-anywhere max-lg:block max-lg:p-0 max-lg:pb-2"
                >
                  {akun.nama}
                </th>
                <SelAkun label="Email" className="wrap-anywhere">
                  {akun.email}
                </SelAkun>
                <SelAkun label="Langganan">
                  <Lencana varian={akun.status_langganan} />
                  {akun.status_langganan === "pro" && akun.masa_berlaku_pro && (
                    <span className="mt-1 block text-sm leading-5 text-teks-redup">
                      {pesanBerlakuHingga(
                        formatTanggalWib(akun.masa_berlaku_pro),
                      )}
                    </span>
                  )}
                </SelAkun>
                <SelAkun label="Status akun">
                  <Lencana varian={nonaktif ? "nonaktif" : "aktif"} />
                </SelAkun>
                <SelAkun label="Tanggal daftar">
                  {formatTanggalWib(akun.dibuat_pada)}
                </SelAkun>
                <SelAkun label="Jumlah batch">{akun.jumlah_batch}</SelAkun>
                <SelAkun label="Aksi" className="max-lg:pt-2 max-lg:py-0">
                  <div className="flex flex-col items-start gap-2 max-lg:flex-row max-lg:flex-wrap">
                    <button
                      type="button"
                      aria-label={`Ubah Langganan ${akun.nama}`}
                      onClick={(peristiwa) =>
                        onBukaUbahLangganan(akun, peristiwa.currentTarget)
                      }
                      className={`${KELAS_TOMBOL_AKSI} text-teks`}
                    >
                      Ubah Langganan
                    </button>
                    {nonaktif ? (
                      <button
                        type="button"
                        aria-label={`Aktifkan ${akun.nama}`}
                        onClick={(peristiwa) =>
                          onBukaAktifkan(akun, peristiwa.currentTarget)
                        }
                        className={`${KELAS_TOMBOL_AKSI} text-teks`}
                      >
                        Aktifkan
                      </button>
                    ) : (
                      <button
                        type="button"
                        aria-label={`Nonaktifkan ${akun.nama}`}
                        onClick={(peristiwa) =>
                          onBukaNonaktifkan(akun, peristiwa.currentTarget)
                        }
                        className={`${KELAS_TOMBOL_AKSI} text-kurang-mirip`}
                      >
                        Nonaktifkan
                      </button>
                    )}
                  </div>
                </SelAkun>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default TabelAkunPengajar;
