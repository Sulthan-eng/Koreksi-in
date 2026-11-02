import { useEffect, useRef, useState } from "react";
import { BadgeCheck, Pencil } from "lucide-react";
import * as batchApi from "../api/batch.js";
import { PESAN_KODE } from "../api/pesan.js";
import KeadaanData from "./KeadaanData.jsx";
import Lencana from "./Lencana.jsx";
import PesanForm from "./PesanForm.jsx";
import Spinner from "./Spinner.jsx";

const BATAS_PANJANG_TEKS_OCR = 10000;

function TeksOcr({ teks }) {
  const refTeks = useRef(null);
  const [dibuka, setDibuka] = useState(false);
  const [terpotong, setTerpotong] = useState(false);

  useEffect(() => {
    const elemen = refTeks.current;
    if (!elemen || dibuka) return undefined;

    function periksaTerpotong() {
      setTerpotong(elemen.scrollHeight > elemen.clientHeight);
    }

    periksaTerpotong();
    const observer = new ResizeObserver(periksaTerpotong);
    observer.observe(elemen);
    return () => observer.disconnect();
  }, [teks, dibuka]);

  if (!teks) {
    return <span className="text-teks-redup">(jawaban tidak ditemukan)</span>;
  }

  return (
    <div>
      <p
        ref={refTeks}
        className={`whitespace-pre-wrap text-teks ${dibuka ? "" : "line-clamp-3"}`}
      >
        {teks}
      </p>
      {(terpotong || dibuka) && (
        <button
          type="button"
          aria-expanded={dibuka}
          onClick={() => setDibuka((sebelumnya) => !sebelumnya)}
          className="mt-1 inline-flex min-h-11 items-center text-sm font-semibold text-biru-utama underline"
        >
          {dibuka ? "Tampilkan ringkas" : "Tampilkan lengkap"}
        </button>
      )}
    </div>
  );
}

function TabHasilKoreksi({ idBatch, daftarSoal, bacaSaja }) {
  const [status, setStatus] = useState("memuat");
  const [daftarHasil, setDaftarHasil] = useState([]);
  const [noSoalDipilih, setNoSoalDipilih] = useState(
    daftarSoal[0]?.no_soal ?? null,
  );

  const [idKoreksiDiedit, setIdKoreksiDiedit] = useState(null);
  const [modeEdit, setModeEdit] = useState(null); // 'teks' | 'nilai'
  const [teksDraft, setTeksDraft] = useState("");
  const [nilaiDraft, setNilaiDraft] = useState("");
  const [sedangSimpan, setSedangSimpan] = useState(false);
  const [kesalahanEdit, setKesalahanEdit] = useState(null);
  const [kesalahanNilai, setKesalahanNilai] = useState(null);
  const [idBaruGagalHitungUlang, setIdBaruGagalHitungUlang] = useState(null);

  const refTeksarea = useRef(null);
  const refInputNilai = useRef(null);
  const refTombolEdit = useRef({});
  const refTombolNilai = useRef({});

  useEffect(() => {
    let dibatalkan = false;
    (async () => {
      try {
        const hasil = await batchApi.daftarHasilKoreksi(idBatch);
        if (!dibatalkan) {
          setDaftarHasil(hasil);
          setStatus("siap");
        }
      } catch {
        if (!dibatalkan) setStatus("gagal");
      }
    })();
    return () => {
      dibatalkan = true;
    };
  }, [idBatch]);

  useEffect(() => {
    if (idKoreksiDiedit && modeEdit === "teks") refTeksarea.current?.focus();
    if (idKoreksiDiedit && modeEdit === "nilai") refInputNilai.current?.focus();
  }, [idKoreksiDiedit, modeEdit]);

  function mulaiEdit(item) {
    setIdKoreksiDiedit(item.id_koreksi);
    setModeEdit("teks");
    setTeksDraft(item.teks_ocr);
    setKesalahanEdit(null);
  }

  function batalEdit(item) {
    setIdKoreksiDiedit(null);
    setModeEdit(null);
    setTeksDraft("");
    setKesalahanEdit(null);
    refTombolEdit.current[item.id_koreksi]?.focus();
  }

  function mulaiEditNilai(item) {
    setIdKoreksiDiedit(item.id_koreksi);
    setModeEdit("nilai");
    setNilaiDraft(String(item.skor_revisi ?? item.skor_sistem ?? ""));
    setKesalahanNilai(null);
  }

  function batalEditNilai(item) {
    setIdKoreksiDiedit(null);
    setModeEdit(null);
    setNilaiDraft("");
    setKesalahanNilai(null);
    refTombolNilai.current[item.id_koreksi]?.focus();
  }

  async function tanganiSimpan(item) {
    if (!teksDraft.trim()) {
      setKesalahanEdit(PESAN_KODE.TEKS_OCR_KOSONG);
      return;
    }
    if (Array.from(teksDraft.trim()).length > BATAS_PANJANG_TEKS_OCR) {
      setKesalahanEdit(PESAN_KODE.TEKS_OCR_TERLALU_PANJANG);
      return;
    }

    setSedangSimpan(true);
    setKesalahanEdit(null);
    try {
      const hasilBaru = await batchApi.ubahTeksOcr(idBatch, item.id_koreksi, {
        teks_ocr: teksDraft,
      });
      setDaftarHasil((sebelumnya) =>
        sebelumnya.map((baris) =>
          baris.id_koreksi === hasilBaru.id_koreksi
            ? {
                ...baris,
                teks_ocr: hasilBaru.teks_ocr,
                skor_sistem: hasilBaru.skor_sistem,
                kategori: hasilBaru.kategori,
                skor_hitung_ulang: hasilBaru.skor_hitung_ulang,
              }
            : baris,
        ),
      );
      setIdBaruGagalHitungUlang(
        hasilBaru.skor_hitung_ulang ? hasilBaru.id_koreksi : null,
      );
      setIdKoreksiDiedit(null);
      setModeEdit(null);
      setTeksDraft("");
      refTombolEdit.current[item.id_koreksi]?.focus();
    } catch (error) {
      setKesalahanEdit(error.pesan);
    } finally {
      setSedangSimpan(false);
    }
  }

  async function tanganiSimpanNilai(item) {
    const teks = nilaiDraft.trim();
    const n = Number(teks);
    const valid =
      teks !== "" &&
      !Number.isNaN(n) &&
      Number.isInteger(n) &&
      String(n) === teks;
    if (!valid || n < 0 || n > 100) {
      setKesalahanNilai(PESAN_KODE.NILAI_AKHIR_TIDAK_VALID);
      return;
    }

    setSedangSimpan(true);
    setKesalahanNilai(null);
    try {
      const hasilBaru = await batchApi.ubahNilaiAkhir(
        idBatch,
        item.id_koreksi,
        {
          skor_revisi: n,
        },
      );
      setDaftarHasil((sebelumnya) =>
        sebelumnya.map((baris) =>
          baris.id_koreksi === hasilBaru.id_koreksi
            ? { ...baris, skor_revisi: hasilBaru.skor_revisi }
            : baris,
        ),
      );
      setIdKoreksiDiedit(null);
      setModeEdit(null);
      setNilaiDraft("");
      refTombolNilai.current[item.id_koreksi]?.focus();
    } catch (error) {
      setKesalahanNilai(error.pesan);
    } finally {
      setSedangSimpan(false);
    }
  }

  if (status === "memuat") {
    return <KeadaanData keadaan="memuat" className="p-8" />;
  }

  if (status === "gagal") {
    return <KeadaanData keadaan="gagal" pesan={PESAN_KODE.KONEKSI_TERPUTUS} />;
  }

  const hasilSoalTerpilih = daftarHasil.filter(
    (item) => item.no_soal === noSoalDipilih,
  );

  return (
    <div>
      {daftarSoal.length > 0 && (
        <select
          aria-label="Soal"
          disabled={idKoreksiDiedit !== null}
          value={noSoalDipilih ?? ""}
          onChange={(peristiwa) =>
            setNoSoalDipilih(Number(peristiwa.target.value))
          }
          className="mb-4 h-11 w-fit min-w-40 rounded-lg border border-garis bg-permukaan px-3 text-teks disabled:opacity-50"
        >
          {daftarSoal.map((soal) => (
            <option key={soal.id_soal} value={soal.no_soal}>
              Soal {soal.no_soal}
            </option>
          ))}
        </select>
      )}

      {hasilSoalTerpilih.length === 0 ? (
        <KeadaanData keadaan="kosong" pesan={PESAN_KODE.BELUM_ADA_HASIL_SOAL} />
      ) : (
        <div className="overflow-hidden rounded-lg border border-garis bg-permukaan max-lg:overflow-visible max-lg:border-0 max-lg:bg-transparent">
          <table role="table" className="w-full border-collapse max-lg:block">
            <thead role="rowgroup" className="max-lg:hidden">
              <tr role="row">
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                >
                  Peserta Didik
                </th>
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                >
                  Teks OCR
                </th>
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                >
                  Skor Kemiripan
                </th>
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                >
                  Kategori Kualitatif
                </th>
                <th
                  role="columnheader"
                  scope="col"
                  className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                >
                  Nilai Akhir
                </th>
                {!bacaSaja && (
                  <th
                    role="columnheader"
                    scope="col"
                    className="border-b border-garis p-4 text-left text-sm font-semibold text-teks-redup"
                  >
                    Aksi
                  </th>
                )}
              </tr>
            </thead>
            <tbody role="rowgroup" className="max-lg:block">
              {hasilSoalTerpilih.map((item) => {
                const sedangDiedit =
                  !bacaSaja &&
                  idKoreksiDiedit === item.id_koreksi &&
                  modeEdit === "teks";
                const sedangEditNilai =
                  !bacaSaja &&
                  idKoreksiDiedit === item.id_koreksi &&
                  modeEdit === "nilai";
                const kunciBarisLain =
                  idKoreksiDiedit !== null &&
                  idKoreksiDiedit !== item.id_koreksi;
                const kunciEdit = kunciBarisLain || sedangEditNilai;
                const kunciNilai = kunciBarisLain || sedangDiedit;

                return (
                  <tr
                    key={item.id_koreksi}
                    role="row"
                    className="border-b border-garis last:border-b-0 max-lg:mb-3 max-lg:block max-lg:rounded-lg max-lg:border max-lg:border-garis max-lg:bg-permukaan max-lg:p-4"
                  >
                    <td
                      role="cell"
                      className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                    >
                      <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                        Peserta Didik
                      </span>
                      <span className="text-teks">
                        {item.nama_peserta_didik}
                      </span>
                    </td>
                    <td
                      role="cell"
                      className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                    >
                      <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                        Teks OCR
                      </span>
                      {sedangDiedit ? (
                        <form
                          onSubmit={(peristiwa) => {
                            peristiwa.preventDefault();
                            tanganiSimpan(item);
                          }}
                          noValidate
                          className="flex flex-col gap-2"
                        >
                          <label className="flex flex-col gap-1.5">
                            <span className="sr-only">
                              Teks OCR untuk {item.nama_peserta_didik}
                            </span>
                            <textarea
                              ref={refTeksarea}
                              rows={4}
                              value={teksDraft}
                              onChange={(peristiwa) =>
                                setTeksDraft(peristiwa.target.value)
                              }
                              onKeyDown={(peristiwa) => {
                                if (
                                  peristiwa.key === "Escape" &&
                                  !sedangSimpan
                                ) {
                                  peristiwa.preventDefault();
                                  batalEdit(item);
                                }
                              }}
                              aria-invalid={kesalahanEdit ? "true" : undefined}
                              aria-describedby={
                                kesalahanEdit
                                  ? `galat-edit-${item.id_koreksi}`
                                  : undefined
                              }
                              className="w-full rounded-lg border border-garis bg-permukaan p-3 text-teks aria-invalid:border-kurang-mirip"
                            />
                          </label>
                          {kesalahanEdit && (
                            <PesanForm
                              varian="galat"
                              id={`galat-edit-${item.id_koreksi}`}
                              pesan={kesalahanEdit}
                              className="text-sm leading-5"
                            />
                          )}
                          <div className="flex flex-wrap gap-2">
                            <button
                              type="submit"
                              aria-disabled={sedangSimpan ? "true" : undefined}
                              onClick={(peristiwa) => {
                                if (sedangSimpan) peristiwa.preventDefault();
                              }}
                              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 text-sm font-semibold text-permukaan aria-disabled:opacity-50"
                            >
                              {sedangSimpan && <Spinner ukuran="size-4" />}
                              Simpan
                            </button>
                            <button
                              type="button"
                              aria-disabled={sedangSimpan ? "true" : undefined}
                              onClick={() => {
                                if (sedangSimpan) return;
                                batalEdit(item);
                              }}
                              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-4 text-sm font-semibold text-teks aria-disabled:opacity-50"
                            >
                              Batal
                            </button>
                          </div>
                        </form>
                      ) : (
                        <TeksOcr teks={item.teks_ocr} />
                      )}
                    </td>
                    <td
                      role="cell"
                      className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                    >
                      <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                        Skor Kemiripan
                      </span>
                      <span className="text-teks">{item.skor_sistem}</span>
                    </td>
                    <td
                      role="cell"
                      className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                    >
                      <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                        Kategori Kualitatif
                      </span>
                      <Lencana varian={item.kategori} />
                      {item.skor_hitung_ulang &&
                        (idBaruGagalHitungUlang === item.id_koreksi ? (
                          <PesanForm
                            varian="galat"
                            pesan="Teks tersimpan, tetapi skor belum berhasil dihitung ulang. Coba lagi."
                            className="mt-1 text-sm leading-5"
                          />
                        ) : (
                          <p className="mt-1 text-sm leading-5 text-kurang-mirip">
                            Teks tersimpan, tetapi skor belum berhasil dihitung
                            ulang. Coba lagi.
                          </p>
                        ))}
                    </td>
                    <td
                      role="cell"
                      className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                    >
                      <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                        Nilai Akhir
                      </span>
                      {sedangEditNilai ? (
                        <form
                          onSubmit={(peristiwa) => {
                            peristiwa.preventDefault();
                            tanganiSimpanNilai(item);
                          }}
                          noValidate
                          className="flex flex-col gap-2"
                        >
                          <label className="flex flex-col gap-1.5">
                            <span className="sr-only">
                              Nilai Akhir untuk {item.nama_peserta_didik}
                            </span>
                            <input
                              ref={refInputNilai}
                              type="number"
                              inputMode="numeric"
                              min={0}
                              max={100}
                              step={1}
                              value={nilaiDraft}
                              onChange={(peristiwa) =>
                                setNilaiDraft(peristiwa.target.value)
                              }
                              onKeyDown={(peristiwa) => {
                                if (
                                  peristiwa.key === "Escape" &&
                                  !sedangSimpan
                                ) {
                                  peristiwa.preventDefault();
                                  batalEditNilai(item);
                                }
                              }}
                              aria-invalid={kesalahanNilai ? "true" : undefined}
                              aria-describedby={
                                kesalahanNilai
                                  ? `galat-nilai-${item.id_koreksi}`
                                  : undefined
                              }
                              className="w-24 rounded-lg border border-garis bg-permukaan p-2 text-teks aria-invalid:border-kurang-mirip"
                            />
                          </label>
                          {kesalahanNilai && (
                            <PesanForm
                              varian="galat"
                              id={`galat-nilai-${item.id_koreksi}`}
                              pesan={kesalahanNilai}
                              className="text-sm leading-5"
                            />
                          )}
                          <div className="flex flex-wrap gap-2">
                            <button
                              type="submit"
                              aria-disabled={sedangSimpan ? "true" : undefined}
                              onClick={(peristiwa) => {
                                if (sedangSimpan) peristiwa.preventDefault();
                              }}
                              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-biru-utama bg-biru-utama px-4 text-sm font-semibold text-permukaan aria-disabled:opacity-50"
                            >
                              {sedangSimpan && <Spinner ukuran="size-4" />}
                              Simpan
                            </button>
                            <button
                              type="button"
                              aria-disabled={sedangSimpan ? "true" : undefined}
                              onClick={() => {
                                if (sedangSimpan) return;
                                batalEditNilai(item);
                              }}
                              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-4 text-sm font-semibold text-teks aria-disabled:opacity-50"
                            >
                              Batal
                            </button>
                          </div>
                        </form>
                      ) : item.skor_revisi != null ? (
                        <span className="font-semibold text-teks">
                          {item.skor_revisi}
                        </span>
                      ) : (
                        <>
                          <span aria-hidden="true">—</span>
                          <span className="sr-only">Belum diisi</span>
                        </>
                      )}
                    </td>
                    {!bacaSaja && (
                      <td
                        role="cell"
                        className="p-4 align-top max-lg:block max-lg:p-0 max-lg:py-1"
                      >
                        <span className="hidden text-xs font-semibold text-teks-redup max-lg:block">
                          Aksi
                        </span>
                        <div className="flex flex-col gap-2">
                          <button
                            type="button"
                            ref={(el) => {
                              refTombolEdit.current[item.id_koreksi] = el;
                            }}
                            aria-label={`Edit jawaban ${item.nama_peserta_didik}`}
                            aria-disabled={kunciEdit ? "true" : undefined}
                            onClick={() => {
                              if (kunciEdit) return;
                              mulaiEdit(item);
                            }}
                            className="inline-flex min-h-11 items-center gap-1.5 rounded-lg border border-garis bg-permukaan px-3 text-sm font-semibold text-teks aria-disabled:opacity-50"
                          >
                            <Pencil className="size-4" aria-hidden="true" />
                            Edit
                          </button>
                          <button
                            type="button"
                            ref={(el) => {
                              refTombolNilai.current[item.id_koreksi] = el;
                            }}
                            aria-label={`Ubah Nilai Akhir ${item.nama_peserta_didik}`}
                            aria-disabled={kunciNilai ? "true" : undefined}
                            onClick={() => {
                              if (kunciNilai) return;
                              mulaiEditNilai(item);
                            }}
                            className="inline-flex min-h-11 items-center gap-1.5 rounded-lg border border-garis bg-permukaan px-3 text-sm font-semibold text-teks aria-disabled:opacity-50"
                          >
                            <BadgeCheck className="size-4" aria-hidden="true" />
                            Ubah Nilai Akhir
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default TabHasilKoreksi;
