import {
  formatAngka,
  formatPersenPemakaian,
  labelTingkatKuota,
  lebarBilahKuota,
  sisaPanggilan,
  tingkatKuota,
} from "../lib/dashboardPantauan.js";

const KELAS_BILAH = {
  normal: "bg-biru-utama",
  "mendekati-batas": "bg-cukup-mirip",
  "hampir-habis": "bg-kurang-mirip",
  "batas-tercapai": "bg-kurang-mirip",
};

const KELAS_LENCANA = {
  "mendekati-batas": "bg-cukup-mirip-latar text-cukup-mirip",
  "hampir-habis": "bg-kurang-mirip-latar text-kurang-mirip",
  "batas-tercapai": "bg-kurang-mirip-latar text-kurang-mirip",
};

function KartuKuota({ kuota }) {
  const tingkat = tingkatKuota(kuota.terpakai, kuota.batas);
  const label = labelTingkatKuota(tingkat);
  const persen = formatPersenPemakaian(kuota.terpakai, kuota.batas);
  const lebar = lebarBilahKuota(kuota.terpakai, kuota.batas);
  const sisa = formatAngka(sisaPanggilan(kuota.terpakai, kuota.batas));

  return (
    <div className="relative flex flex-col gap-5 overflow-hidden rounded-lg border border-garis bg-permukaan p-6 shadow-sm">
      <span
        className="absolute inset-x-0 top-0 h-1 bg-merek-hijau"
        aria-hidden="true"
      />

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <p className="text-sm leading-5 text-teks-redup">Terpakai hari ini</p>
          <p className="text-3xl font-bold leading-9 text-teks">
            {formatAngka(kuota.terpakai)}
          </p>
        </div>
        <div className="flex flex-col gap-1 text-right">
          <p className="text-sm leading-5 text-teks-redup">Batas harian</p>
          <p className="text-3xl font-bold leading-9 text-teks">
            {formatAngka(kuota.batas)}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <div
          className="h-3 w-full overflow-hidden rounded-full bg-biru-muda"
          role="progressbar"
          aria-valuemin="0"
          aria-valuemax={kuota.batas}
          aria-valuenow={kuota.terpakai}
          aria-label="Pemakaian kuota API hari ini"
        >
          <div
            className={`h-full rounded-full ${KELAS_BILAH[tingkat]}`}
            style={{ width: lebar }}
          />
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm leading-5">
          <span className="flex flex-wrap items-center gap-2">
            <span>{persen} terpakai</span>
            {label && (
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 font-semibold whitespace-nowrap ${KELAS_LENCANA[tingkat]}`}
              >
                {label}
              </span>
            )}
          </span>
          <span>Sisa {sisa} panggilan</span>
        </div>
      </div>

      <div className="flex flex-col gap-1 text-sm leading-5 text-teks-redup">
        <p>Diatur ulang setiap hari pukul 00.00 waktu Pasifik (AS).</p>
        <p>Model: {kuota.nama_model}</p>
      </div>
    </div>
  );
}

export default KartuKuota;
