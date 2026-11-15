function KartuAngka({ label, nilai }) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-garis bg-permukaan p-4 shadow-sm">
      <p className="text-sm text-teks-redup">{label}</p>
      <p className="text-3xl font-bold leading-9 text-teks">{nilai}</p>
    </div>
  );
}

export default KartuAngka;
