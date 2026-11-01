import Spinner from "./Spinner.jsx";

function KeadaanData({ keadaan, pesan, className = "" }) {
  if (keadaan === "memuat") {
    return (
      <div
        role="status"
        className={`flex items-center justify-center gap-2 ${className || "py-12"}`.trim()}
      >
        <Spinner ukuran="size-5" />
        <span className="sr-only">Memuat</span>
      </div>
    );
  }

  if (keadaan === "kosong") {
    if (!pesan) return null;
    return <p className={`text-teks-redup ${className}`.trim()}>{pesan}</p>;
  }

  if (keadaan === "gagal") {
    if (!pesan) return null;
    return (
      <p role="alert" className={`text-kurang-mirip ${className}`.trim()}>
        {pesan}
      </p>
    );
  }

  return null;
}

export default KeadaanData;
