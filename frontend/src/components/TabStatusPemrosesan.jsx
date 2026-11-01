import Lencana from "./Lencana.jsx";

function TabStatusPemrosesan({ daftarFileJawaban, kesalahan }) {
  if (kesalahan) {
    return (
      <p role="alert" className="text-kurang-mirip">
        {kesalahan}
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {daftarFileJawaban.map((fileJawaban) => (
        <li
          key={fileJawaban.id_file}
          className="flex items-center justify-between rounded-lg border border-garis bg-permukaan p-3"
        >
          <div>
            <span className="text-teks">{fileJawaban.nama_peserta_didik}</span>
            {fileJawaban.status_proses === "gagal" && fileJawaban.pesan_error && (
              <p className="mt-1 text-sm text-kurang-mirip">{fileJawaban.pesan_error}</p>
            )}
          </div>
          <Lencana varian={fileJawaban.status_proses} />
        </li>
      ))}
    </ul>
  );
}

export default TabStatusPemrosesan;
