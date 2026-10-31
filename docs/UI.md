# UI Koreksi-in

Aturan tampilan untuk frontend. Warna diambil dari logo (biru dan hijau). Frontend memakai Tailwind CSS v4 lewat plugin Vite.

## Aturan wajib

- Warna HANYA lewat token di bawah. TIDAK BOLEH ada HEX, `rgb()`, atau nilai arbitrer seperti `bg-[#123456]` di komponen.
- Token didefinisikan sekali di `frontend/src/index.css` dengan `@theme`. Menambah atau mengubah token adalah perubahan dokumen ini, bukan keputusan agent.
- Teks biasa HARUS memenuhi kontras WCAG AA (minimal 4,5 : 1). Kombinasi yang sudah dicek ada di tabel kontras.
- Warna tidak boleh menjadi satu-satunya penanda. Kategori dan status SELALU memakai teks ("Sangat Mirip", "Gagal"), bukan hanya warna.
- Teks UI Bahasa Indonesia. Desktop dulu, tetap responsif sampai lebar ponsel.
- Pesan validasi form berasal dari aplikasi dan tertulis persis seperti di SPEC, tampil di bawah form atau di dekat kolomnya. TIDAK BOLEH memakai bubble validasi bawaan browser (pakai `noValidate` pada form).
- Font: font sans-serif sistem bawaan Tailwind. Tidak ada font tambahan.

## Token warna

Nilai `--color-merek-biru` dan `--color-merek-hijau` diukur langsung dari logo. Sisanya diturunkan dan sudah dicek kontrasnya.

```css
@import "tailwindcss";

@theme {
  /* merek, dari logo */
  --color-merek-biru: #1385D7;
  --color-merek-hijau: #3EC68B;

  /* antarmuka */
  --color-biru-utama: #0F6DB5;   /* tombol utama, tautan, tab aktif */
  --color-biru-muda: #E8F3FC;    /* latar lembut, baris terpilih */
  --color-teks: #0F2A43;         /* teks utama */
  --color-teks-redup: #475569;   /* teks pendukung */
  --color-latar: #F4F8FB;        /* latar halaman */
  --color-permukaan: #FFFFFF;    /* kartu, tabel, form */
  --color-garis: #D5E1EB;        /* garis pembatas, border */

  /* kategori dan status */
  --color-sangat-mirip: #166534;
  --color-sangat-mirip-latar: #DCFCE7;
  --color-cukup-mirip: #92400E;
  --color-cukup-mirip-latar: #FEF3C7;
  --color-kurang-mirip: #991B1B;
  --color-kurang-mirip-latar: #FEE2E2;
}
```

Kelas Tailwind yang dihasilkan, misalnya `bg-biru-utama`, `text-teks`, `bg-latar`, `border-garis`, `text-sangat-mirip`, `bg-sangat-mirip-latar`.

## Pemakaian

| Elemen | Warna |
|---|---|
| Latar halaman | `bg-latar` |
| Kartu, tabel, form | `bg-permukaan`, border `border-garis` |
| Teks utama | `text-teks` |
| Teks pendukung (keterangan, label kecil) | `text-teks-redup` |
| Tombol utama | `bg-biru-utama` dengan teks putih |
| Tautan dan tab aktif | `text-biru-utama` |
| Baris atau item terpilih | `bg-biru-muda` |
| Aksen dekoratif (garis, ikon besar, ilustrasi) | `merek-hijau` atau `merek-biru` |
| Teks di atas `merek-hijau` | `text-teks` (jangan putih) |
| Teks putih di atas `merek-biru` | hanya untuk teks besar (24 px, atau 19 px tebal). Untuk tombol pakai `biru-utama` |

### Kategori Kualitatif (tabel Dashboard Hasil Koreksi)

Tampil sebagai lencana kecil: teks kategori di atas warna latar lembut. Pemetaan dari `kategori`:

| `kategori` | Teks lencana | Kelas |
|---|---|---|
| `sangat_mirip` | Sangat Mirip | `bg-sangat-mirip-latar text-sangat-mirip` |
| `cukup_mirip` | Cukup Mirip | `bg-cukup-mirip-latar text-cukup-mirip` |
| `kurang_mirip` | Kurang Mirip | `bg-kurang-mirip-latar text-kurang-mirip` |

### Status Pemrosesan (lencana di daftar file jawaban)

| `status_proses` | Teks lencana | Kelas |
|---|---|---|
| `diproses` | Diproses | `bg-biru-muda text-biru-utama` (beri indikator berputar) |
| `selesai` | Selesai | `bg-sangat-mirip-latar text-sangat-mirip` |
| `gagal` | Gagal | `bg-kurang-mirip-latar text-kurang-mirip`, tampilkan `pesan_error` di bawah nama |

Pesan error dan validasi memakai `text-kurang-mirip`.

## Kontras yang sudah dicek

| Kombinasi | Rasio | Lolos teks biasa (4,5) |
|---|---|---|
| Putih di atas `biru-utama` #0F6DB5 | 5,42 | Ya |
| `biru-utama` di atas putih | 5,42 | Ya |
| `biru-utama` di atas `biru-muda` | 4,81 | Ya |
| `teks` #0F2A43 di atas putih | 14,66 | Ya |
| `teks` di atas `latar` | 13,73 | Ya |
| `teks-redup` #475569 di atas putih | 7,58 | Ya |
| `teks` di atas `merek-hijau` | 6,74 | Ya |
| Putih di atas `merek-biru` #1385D7 | 3,92 | Tidak, hanya teks besar |
| `sangat-mirip` di atas latarnya | 6,49 | Ya |
| `cukup-mirip` di atas latarnya | 6,37 | Ya |
| `kurang-mirip` di atas latarnya | 6,80 | Ya |

## Logo

Berkas ada di `frontend/public/`:

- `logo.png`: logo lengkap (ikon dan tulisan "Koreksi-in"). Dipakai di halaman Masuk dan Daftar.
- `logo-ikon.png`: ikon saja. Dipakai di bilah atas aplikasi dan sebagai favicon.

Aturan: jangan mengubah warna, rasio, atau memutar logo. Beri ruang kosong di sekeliling minimal setinggi lingkaran kecil pada ikon. Latar logo harus putih atau `latar`. Tinggi ikon di bilah atas sekitar 40 px.

## Inventaris halaman

Daftar halaman target sistem penuh, sumber kebutuhan di `docs/SPEC.md` bagian 9. Rute adalah rute target; mengubah rute yang sudah ada hanya dilakukan oleh tugas refactor tampilan yang memintanya. "Rancangan" adalah status rancangan tampilan per halaman (tata letak, komponen, keadaan) yang ditulis di bagian "Rancangan halaman" sebelum halaman itu dikerjakan.

| # | Halaman | Rute | Peran | FR dan UC | Isi utama | Status fitur | Rancangan |
|---|---|---|---|---|---|---|---|
| 1 | Pemasaran | `/` | Publik (yang sudah login dialihkan ke Beranda atau Dashboard Pantauan) | FR28 | Penjelasan fitur, cara kerja, perbedaan Free dan Pro, tautan Daftar dan Masuk | Belum dikerjakan | Belum |
| 2 | Daftar | `/daftar` | Publik | FR1 | Form nama, email, password | Selesai | Belum |
| 3 | Masuk | `/masuk` | Publik | FR1 | Form email dan password; pesan "Akun berhasil dibuat, silakan masuk" dan "Sesi berakhir, silakan masuk kembali." | Selesai | Belum |
| 4 | Beranda | `/beranda` | Pengajar | FR2, FR3, FR21, FR22, UC-01, UC-02, UC-03, UC-13 | Sapaan, label FREE atau PRO, ringkasan (nanti), daftar batch, "Buat Batch Baru", hapus batch (nanti) | Sebagian selesai | Belum |
| 5 | Halaman Batch | `/batch/:id_batch` | Pengajar | FR4 sampai FR11, FR14 sampai FR17, FR23 | Judul batch, status batch, dua tab: Soal dan Jawaban, dan Dashboard Hasil Koreksi. Aksi: Selesaikan Batch, Hapus Batch, Ekspor Rekap Nilai (nanti) | Sebagian selesai | Belum |
| 6 | Langganan | `/langganan` | Pengajar | FR2, FR19, FR20, UC-10, UC-11 | Status langganan dan masa berlaku, paket Pro, "Upgrade to Pro", status transaksi | Belum dikerjakan | Belum |
| 7 | Dashboard Pantauan | `/admin` | Admin | FR27, UC-18 | Angka jumlah akun (total, Free, Pro), jumlah batch, file jawaban per status, pemakaian kuota API harian | Belum dikerjakan | Belum |
| 8 | Akun Pengajar | `/admin/akun-pengajar` | Admin | FR24 sampai FR26, UC-15 sampai UC-17 | Tabel akun, cari, filter, "Ubah Langganan", "Nonaktifkan" atau "Aktifkan" | Belum dikerjakan | Belum |
| 9 | Lupa Password | `/lupa-password` | Publik | FR1 | Form email, tombol "Kirim Tautan", pesan "Jika email terdaftar, tautan atur ulang password telah dikirim." | Belum dikerjakan | Belum |
| 10 | Atur Ulang Password | `/atur-ulang-password` | Publik (lewat tautan email) | FR1 | Form password baru dan konfirmasi, tombol "Simpan Password", pesan token tidak berlaku | Belum dikerjakan | Belum |

Halaman 9 dan 10 mengikuti SPEC F-RESET. Halaman Masuk mendapat tautan "Lupa password?". Setelah Keluar, pengguna dialihkan ke Halaman Pemasaran (SPEC bagian 6).

Isi Halaman Batch (dua tab):
- Soal dan Jawaban, dua seksi: "Soal dan Kunci Jawaban" (daftar soal, "Tambah Soal", form kunci) dan "Jawaban Peserta Didik" (tombol "Upload Jawaban Peserta Didik", form unggah, lalu daftar semua file jawaban dengan nama, lencana status, dan pesan error untuk yang Gagal).
- Dashboard Hasil Koreksi: pilihan soal, tabel hasil.
- Tidak ada tab Status Pemrosesan. Status tiap file hanya tampil di daftar file jawaban.

## Komponen bersama

Komponen yang dipakai lebih dari satu halaman. Satu definisi per komponen di `frontend/src/components/`.

| Komponen | Dipakai di | Aturan |
|---|---|---|
| Bilah atas | Semua halaman | Tiga varian. Publik: logo, "Masuk", "Daftar". Pengajar: logo, label FREE atau PRO, nama, "Keluar". Admin: logo, menu "Dashboard Pantauan" dan "Akun Pengajar", "Keluar" |
| Lencana | Status pemrosesan, kategori, FREE atau PRO, status aktif akun | Selalu berisi teks, memakai token di bagian Pemakaian |
| Dialog konfirmasi | Hapus batch, selesaikan batch, nonaktifkan akun, tinggalkan halaman unggah | Judul singkat, satu kalimat persis dari SPEC, dua tombol. Hapus dan selesaikan: "Ya" dan "Batal". Tinggalkan halaman: "Tetap di Halaman" dan "Tinggalkan". Tombol utama memakai `bg-biru-utama`; aksi merusak tidak memakai warna merah polos tanpa teks |
| Kartu angka | Ringkasan Pengajar, Dashboard Pantauan | Angka besar dan label teks. Nilai 0 tetap tampil |
| Tabel | Hasil koreksi, Akun Pengajar | Aturan di bagian Tata letak |
| Keadaan data | Semua data yang dimuat | Tiga keadaan: memuat (indikator), kosong (teks dari SPEC), gagal (teks dari SPEC) |
| Pesan sukses dan galat | Semua form | Sukses singkat ("Kunci jawaban tersimpan."), galat memakai `text-kurang-mirip` |

## Tata letak

- Bilah atas: ikon logo, nama "Koreksi-in", dan isi menurut peran (lihat Komponen bersama).
- Halaman Masuk dan Daftar: kartu di tengah dengan `logo.png` di atasnya.
- Beranda: judul "Batch Koreksi", tombol "Buat Batch Baru", lalu daftar batch. Tata letak yang lebih kaya (ringkasan, label langganan) ditetapkan di Rancangan halaman.
- Halaman Batch: judul batch, dua tab (Soal dan Jawaban, Dashboard Hasil Koreksi).
- Tabel: baris cukup lega, header `text-teks-redup`, teks OCR panjang dipotong dengan opsi tampilkan lengkap.
- Tampilkan indikator loading pada unggah, pemrosesan, dan pemuatan data. Tampilkan keadaan kosong dengan teks yang ada di SPEC.
- Responsif: desktop adalah prioritas, tetapi semua halaman tetap bisa dipakai pada lebar ponsel tanpa gulir horizontal untuk isi utama (NFR17).

## Rancangan halaman

Tiap halaman di Inventaris halaman ditambahi satu subbagian di sini sebelum dikerjakan: tata letak (urutan blok dari atas ke bawah), komponen yang dipakai, isi tiap blok, keadaan (memuat, kosong, gagal, sukses), dan perilaku tombol. Halaman yang belum punya subbagian di sini TIDAK BOLEH dirombak atau dibuat; tanyakan pemilik proyek.

(Belum ada. Subbagian pertama yang akan ditulis: Beranda, Halaman Batch, Masuk dan Daftar, lalu Halaman Pemasaran.)