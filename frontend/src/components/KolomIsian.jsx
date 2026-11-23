function KolomIsian({
  id,
  label,
  value,
  onChange,
  petunjuk,
  galat,
  ariaInvalid,
  ariaDescribedby,
  kelasInputTambahan = "",
  anak,
  ...sisaProps
}) {
  const invalid = ariaInvalid ?? Boolean(galat);
  const describedBy =
    [
      ariaDescribedby,
      petunjuk ? `${id}-petunjuk` : null,
      galat ? `${id}-galat` : null,
    ]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-teks">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          value={value}
          onChange={onChange}
          aria-invalid={invalid ? "true" : undefined}
          aria-describedby={describedBy}
          className={`h-11 w-full rounded-lg border border-garis bg-permukaan px-3 text-teks aria-invalid:border-kurang-mirip ${kelasInputTambahan}`}
          {...sisaProps}
        />
        {anak}
      </div>
      {petunjuk && (
        <span
          id={`${id}-petunjuk`}
          className="text-sm leading-5 text-teks-redup"
        >
          {petunjuk}
        </span>
      )}
      {galat && (
        <span
          id={`${id}-galat`}
          role="alert"
          className="text-sm leading-5 text-kurang-mirip"
        >
          {galat}
        </span>
      )}
    </div>
  );
}

export default KolomIsian;
