function KartuAngka({
  label,
  nilai,
  ikon: Ikon,
  warnaGaris,
  kelasIkon = "bg-biru-muda text-biru-utama",
  kelasIkonGambar = "",
  kelasNilai = "text-teks",
  kelasIsi = "gap-1",
  kelasKartu = "",
}) {
  return (
    <div
      className={`relative flex flex-col ${kelasIsi} overflow-hidden rounded-lg border border-garis bg-permukaan p-4 shadow-sm ${kelasKartu}`.trim()}
    >
      {warnaGaris && (
        <span
          className={`absolute inset-x-0 top-0 h-1 ${warnaGaris}`}
          aria-hidden="true"
        />
      )}
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm leading-5 text-teks-redup">{label}</p>
        {Ikon && (
          <span
            className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${kelasIkon}`}
            aria-hidden="true"
          >
            <Ikon className={`size-4 ${kelasIkonGambar}`.trim()} />
          </span>
        )}
      </div>
      <p
        className={`mt-auto text-3xl font-bold leading-9 ${kelasNilai}`.trim()}
      >
        {nilai}
      </p>
    </div>
  );
}

export default KartuAngka;
