import { useEffect, useId, useRef, useState } from "react";
import { PESAN_KODE } from "../api/pesan.js";
import {
  apakahGalatJaringan,
  keTanggalInputWib,
  validasiMasaBerlakuPro,
} from "../lib/akunPengajar.js";
import PesanForm from "./PesanForm.jsx";
import Spinner from "./Spinner.jsx";

function DialogUbahLangganan({ akun, onBatal, onSimpan }) {
  const dialogRef = useRef(null);
  const idJudul = useId();
  const idGalat = useId();

  const [statusDipilih, setStatusDipilih] = useState(akun.status_langganan);
  const [masaBerlaku, setMasaBerlaku] = useState(
    akun.status_langganan === "pro"
      ? keTanggalInputWib(akun.masa_berlaku_pro)
      : "",
  );
  const [galat, setGalat] = useState(null);
  const [sedangSimpan, setSedangSimpan] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return undefined;
    if (!dialog.open) {
      dialog.showModal();
    }
    return () => {
      if (dialog.open) {
        dialog.close();
      }
    };
  }, []);

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    if (sedangSimpan) return;
    setGalat(null);

    if (statusDipilih === "pro" && !validasiMasaBerlakuPro(masaBerlaku)) {
      setGalat(PESAN_KODE.MASA_BERLAKU_TIDAK_VALID);
      return;
    }

    setSedangSimpan(true);
    try {
      await onSimpan(akun.id_pengguna, {
        status_langganan: statusDipilih,
        masa_berlaku_pro: statusDipilih === "pro" ? masaBerlaku : null,
      });
    } catch (error) {
      if (error?.kode === "MASA_BERLAKU_TIDAK_VALID") {
        setGalat(PESAN_KODE.MASA_BERLAKU_TIDAK_VALID);
      } else if (apakahGalatJaringan(error)) {
        setGalat(PESAN_KODE.KONEKSI_TERPUTUS_COBA_LAGI);
      } else {
        setGalat(PESAN_KODE.GAGAL_UBAH_LANGGANAN);
      }
      setSedangSimpan(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={idJudul}
      className="m-auto w-full max-w-md rounded-xl border border-garis bg-permukaan p-0 text-teks shadow-lg backdrop:bg-teks/40"
      onCancel={(peristiwa) => {
        peristiwa.preventDefault();
        if (!sedangSimpan) onBatal();
      }}
    >
      <form
        noValidate
        onSubmit={tanganiSubmit}
        className="flex flex-col gap-4 p-6"
      >
        <div className="flex flex-col gap-1">
          <h2 id={idJudul} className="text-lg font-semibold">
            Ubah Langganan
          </h2>
          <p className="wrap-anywhere text-sm leading-5 text-teks-redup">
            {akun.nama}
          </p>
        </div>

        <fieldset className="flex flex-col gap-2" disabled={sedangSimpan}>
          <legend className="text-sm font-semibold">Status langganan</legend>
          <label className="flex min-h-11 items-center gap-2">
            <input
              type="radio"
              name="langganan-dlg"
              value="free"
              checked={statusDipilih === "free"}
              onChange={() => {
                setStatusDipilih("free");
                setGalat(null);
              }}
              className="size-5 accent-biru-utama"
            />
            Free
          </label>
          <label className="flex min-h-11 items-center gap-2">
            <input
              type="radio"
              name="langganan-dlg"
              value="pro"
              checked={statusDipilih === "pro"}
              onChange={() => {
                setStatusDipilih("pro");
                setGalat(null);
              }}
              className="size-5 accent-biru-utama"
            />
            Pro
          </label>
        </fieldset>

        {statusDipilih === "pro" && (
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-semibold">Masa berlaku</span>
            <input
              type="date"
              value={masaBerlaku}
              disabled={sedangSimpan}
              onChange={(peristiwa) => {
                setMasaBerlaku(peristiwa.target.value);
                if (galat) setGalat(null);
              }}
              aria-invalid={
                galat === PESAN_KODE.MASA_BERLAKU_TIDAK_VALID
                  ? "true"
                  : undefined
              }
              aria-describedby={galat ? idGalat : undefined}
              className="h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip disabled:opacity-50"
            />
          </label>
        )}

        {galat && (
          <PesanForm
            varian="galat"
            id={idGalat}
            pesan={galat}
            className="text-sm leading-5"
          />
        )}

        <div className="mt-1 flex flex-wrap justify-end gap-3">
          <button
            type="button"
            aria-disabled={sedangSimpan ? "true" : undefined}
            onClick={() => {
              if (!sedangSimpan) onBatal();
            }}
            className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks aria-disabled:opacity-50"
          >
            Batal
          </button>
          <button
            type="submit"
            aria-disabled={sedangSimpan ? "true" : undefined}
            onClick={(peristiwa) => {
              if (sedangSimpan) peristiwa.preventDefault();
            }}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan aria-disabled:opacity-50"
          >
            {sedangSimpan && <Spinner ukuran="size-4" />}
            Simpan
          </button>
        </div>
      </form>
    </dialog>
  );
}

export default DialogUbahLangganan;
