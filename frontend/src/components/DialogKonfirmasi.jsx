import { useEffect, useId, useRef } from "react";

function DialogKonfirmasi({
  terbuka,
  judul,
  isi,
  labelBatal,
  labelYa,
  onBatal,
  onYa,
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

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={idJudul}
      className="w-full max-w-md rounded-xl p-0 shadow-lg backdrop:bg-teks/40"
      onCancel={(peristiwa) => {
        peristiwa.preventDefault();
        onBatal();
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
            className="inline-flex min-h-11 items-center justify-center rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan"
          >
            {labelBatal}
          </button>
          <button
            type="button"
            onClick={onYa}
            className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis px-4 font-semibold text-teks"
          >
            {labelYa}
          </button>
        </div>
      </div>
    </dialog>
  );
}

export default DialogKonfirmasi;
