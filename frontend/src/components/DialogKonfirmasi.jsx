import { useEffect, useId, useRef } from "react";
import Spinner from "./Spinner.jsx";

const KELAS_UTAMA =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan disabled:opacity-50";
const KELAS_SEKUNDER =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-garis px-4 font-semibold text-teks disabled:opacity-50";
const KELAS_SEKUNDER_MERUSAK =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-garis px-4 font-semibold text-kurang-mirip disabled:opacity-50";

function DialogKonfirmasi({
  terbuka,
  judul,
  isi,
  labelBatal,
  labelYa,
  onBatal,
  onYa,
  tombolUtama = "batal",
  variasiYa,
  prosesBerjalan = false,
}) {
  const dialogRef = useRef(null);
  const tombolBatalRef = useRef(null);
  const idJudul = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (terbuka && !dialog.open) {
      dialog.showModal();
      tombolBatalRef.current?.focus();
    } else if (!terbuka && dialog.open) {
      dialog.close();
    }
  }, [terbuka]);

  const kelasBatal = tombolUtama === "batal" ? KELAS_UTAMA : KELAS_SEKUNDER;
  const kelasYa =
    tombolUtama === "ya"
      ? KELAS_UTAMA
      : variasiYa === "merusak"
        ? KELAS_SEKUNDER_MERUSAK
        : KELAS_SEKUNDER;

  // m-auto memulihkan pemusatan bawaan <dialog>: preflight Tailwind v4 menyetel margin semua elemen menjadi 0.
  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={idJudul}
      className="m-auto w-full max-w-md rounded-xl p-0 shadow-lg backdrop:bg-teks/40"
      onCancel={(peristiwa) => {
        peristiwa.preventDefault();
        if (!prosesBerjalan) onBatal();
      }}
    >
      <div className="flex flex-col gap-4 p-6">
        <h2 id={idJudul} className="text-lg font-bold text-teks">
          {judul}
        </h2>
        <p className="text-sm leading-5 text-teks-redup">{isi}</p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            ref={tombolBatalRef}
            onClick={onBatal}
            disabled={prosesBerjalan}
            className={kelasBatal}
          >
            {labelBatal}
          </button>
          <button
            type="button"
            onClick={onYa}
            disabled={prosesBerjalan}
            className={kelasYa}
          >
            {prosesBerjalan && <Spinner ukuran="size-4" />}
            {labelYa}
          </button>
        </div>
      </div>
    </dialog>
  );
}

export default DialogKonfirmasi;
