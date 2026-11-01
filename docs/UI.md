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
- Ikon: hanya dari Lucide (paket `lucide-react`), lihat bagian Ikon. Tidak ada keluarga ikon lain dan tidak ada font ikon.

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

## Ikon

Ikon boleh dipakai untuk memperjelas tombol, menu, dan keadaan data. Sumbernya hanya Lucide (lisensi ISC), diimpor per ikon lewat `lucide-react` sehingga hanya ikon yang dipakai ikut terkirim. Penambahan paket atau keluarga ikon lain adalah perubahan dokumen ini, bukan keputusan agent.

- Satu keluarga saja. Ketebalan garis seragam (bawaan Lucide, `stroke-width` 2) dan ukuran seragam: `size-4` (16 px) di dalam tombol atau teks, `size-5` (20 px) pada tombol ikon, `size-6` (24 px) atau lebih untuk ilustrasi keadaan kosong.
- Warna ikon mengikuti teks di sekitarnya (`currentColor`, otomatis di Lucide). TIDAK BOLEH memberi warna ikon dengan HEX atau nilai arbitrer; pemakaian warna mengikuti tabel Pemakaian.
- Ikon tidak pernah menjadi satu-satunya penanda. Tombol, lencana, dan status tetap memuat teks. Ikon di samping teks bersifat dekoratif (`aria-hidden="true"`). Tombol yang hanya berisi ikon (misalnya titik tiga) WAJIB punya nama aksesibel (`aria-label`), dan area sentuhnya minimal 44 px walau gambar ikonnya lebih kecil.
- Ikon tidak boleh menggantikan kata pada aksi yang merusak atau tidak dapat dibatalkan (Hapus Batch, Nonaktifkan): teksnya tetap tertulis, ikon hanya pendamping.
- Pemetaan ikon per aksi ditetapkan perancang tampilan dan dicatat di ringkasan desain; satu aksi memakai satu ikon yang sama di semua halaman (contoh: titik tiga selalu memakai `ellipsis-vertical`, tidak berganti-ganti).
- Logo Koreksi-in bukan ikon Lucide dan tetap memakai berkas di bagian Logo.

## Gaya visual

Ukuran dan bentuk memakai skala Tailwind standar saja; tidak ada nilai piksel arbitrer (`p-[13px]`, `text-[15px]`). Ditetapkan dari desain tahap 1 (lembar komponen dan Halaman Batch). Mengubah gaya adalah perubahan dokumen ini.

### Tipografi

| Peran | Kelas |
|---|---|
| Judul halaman | `text-2xl font-bold leading-8` |
| Judul seksi | `text-lg font-semibold` |
| Judul kelompok kartu angka (Dashboard Pantauan) | `text-sm font-semibold leading-5 text-teks-redup` |
| Isi | `text-base leading-6` |
| Label kecil, keterangan, lencana | `text-sm leading-5` |
| Angka besar di kartu angka | `text-3xl font-bold leading-9` |
| Label kolom di kartu ponsel | `text-xs font-semibold` |

### Jarak

- Celah antar elemen: `gap-2`, `gap-3`, `gap-4`, `gap-6`.
- Isi kartu dan dialog: `p-6`. Isi item daftar dan kartu kecil: `p-4`.
- Samping halaman: `px-4` di ponsel. Isi utama `max-w-5xl`.
- Bilah atas: `px-4 py-3`.
- Area sentuh minimal: `min-h-11` (44 px) untuk semua tombol, tautan menu, dan kendali.

### Radius dan bayangan

| Elemen | Kelas |
|---|---|
| Kartu, tabel, form, tombol, bidang | `rounded-lg` |
| Lencana dan pil status | `rounded-full` |
| Item menu aksi | `rounded-md` |
| Dialog | `rounded-xl` |
| Kartu dan seksi | `shadow-sm` |
| Menu aksi titik tiga | `shadow-sm` |
| Dialog | `shadow-lg` |

### Pemetaan ikon (Lucide)

Semua ikon `stroke="currentColor"`, `stroke-width` 2, `aria-hidden="true"`. Ukuran `size-4` di tombol dan lencana, `size-5` di tombol ikon. Satu aksi memakai satu ikon yang sama di semua halaman.

| Fungsi | Ikon Lucide | Ukuran | Dipakai di |
|---|---|---|---|
| Edit | `pencil` | `size-4` | Aksi di Dashboard Hasil Koreksi (nanti) |
| Ubah Nilai Akhir | `badge-check` | `size-4` | Dashboard Hasil Koreksi (nanti) |
| Buka menu | `menu` | `size-5` | Bilah atas ponsel (`aria-label` "Buka menu") |
| Tutup menu | `x` | `size-5` | Laci menu (`aria-label` "Tutup menu") |
| Menu aksi | `ellipsis-vertical` | `size-5` | Titik tiga (`aria-label` berisi nama batch) |
| Coba Lagi | `rotate-ccw` | `size-4` | File yang Gagal (nanti) |
| Kembali | `arrow-left` | `size-4` | Tautan "Batch Koreksi" |
| Unggah | `upload` | `size-4` | "Upload Jawaban Peserta Didik" |
| Tambah | `plus` | `size-4` | "Tambah Soal" |
| Ekspor | `download` | `size-4` | "Ekspor Rekap Nilai" (nanti) |
| Hapus | `trash-2` | `size-4` | "Hapus Batch" |
| Keluar | `log-out` | `size-4` | "Keluar" |
| Memuat, Diproses | `loader-circle` + `animate-spin motion-reduce:animate-none` | `size-4` (`size-3.5` di dalam lencana) | Indikator. SEMUA spinner memakai `motion-reduce:animate-none` (berlaku saat implementasi, juga untuk berkas mockup lama yang belum memilikinya) |
| Galat | `circle-alert` | `size-4` | Pesan galat |
| File jawaban | `file` | `size-4` | Nama file di form unggah |
| Membaca tulisan tangan | `scan-text` | `size-5` dalam kotak `size-11 rounded-lg bg-biru-muda text-biru-utama` | Kartu fitur Pemasaran |
| Skor kemiripan dan kategori | `gauge` | sama | Kartu fitur Pemasaran |
| Koreksi manual | `pencil` | sama | Kartu fitur Pemasaran (ikon sama dengan Edit) |
| Ekspor rekap nilai | `download` | sama | Kartu fitur Pemasaran (ikon sama dengan Ekspor) |
| Akun, Total akun Pengajar | `users` | `size-4` | Dashboard Pantauan (judul kelompok dan kartu) |
| Akun Free | `user-check` | `size-4` | Dashboard Pantauan |
| Akun Pro | `crown` | `size-4` | Dashboard Pantauan |
| Aktivitas, Jumlah batch | `layers` | `size-4` | Dashboard Pantauan |
| File Selesai | `file-check` | `size-4` | Dashboard Pantauan |
| File Gagal | `file-x` | `size-4` | Dashboard Pantauan |
| Kuota API | `gauge` | `size-4` | Judul kelompok Dashboard Pantauan |
| Ya (tersedia) | `check` | `size-4` | Tabel Free dan Pro, selalu berdampingan dengan teks "Ya" |
| Tidak (tidak tersedia) | `x` | `size-4` | Tabel Free dan Pro, selalu berdampingan dengan teks "Tidak" (`x` juga dipakai untuk "Tutup menu", maknanya ditentukan teks di sampingnya atau `aria-label`) |

### Catatan

- Di aplikasi, titik henti memakai varian viewport Tailwind: `lg:` (mulai 1024 px) dan `max-lg:` (di bawah 1024 px). JANGAN memakai `@container`, `@min-[64rem]`, atau `@max-[63.9375rem]` dari berkas mockup: itu hanya akal agar bingkai pratinjau 375 px bisa tampil di layar 1280 px (di Tailwind v4, `@lg` pada container query berarti 32rem, bukan 1024 px).
- Status Aktif batch di ponsel sejajar dengan nama batch (`items-start`, `min-w-0` pada judul).
- Dialog memakai elemen `<dialog>` bawaan.
- Kartu fitur Pemasaran: `rounded-xl p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-lg`, dengan pelindung gerak `motion-reduce:transition-none motion-reduce:hover:translate-y-0`. Garis aksen dekoratif di tepi atas kartu memakai `merek-hijau` atau `merek-biru` (bergantian), `aria-hidden`.
- Kartu angka Dashboard Pantauan: `grid-cols-2` di ponsel dan tablet; di desktop tiga atau empat kolom menurut jumlah kartu per kelompok (Akun 3, Aktivitas 4). Kuota API berupa satu kartu lebar penuh dengan bilah pemakaian. Kartu ganjil yang menggantung di ponsel dibuat lebar penuh (`col-span-2`).
- Pilihan paket di Langganan berupa grup radio. Saat diimplementasi, bungkus dengan `fieldset` dan `legend` (teks "Paket Pro") agar pembaca layar mengenal grupnya.
- Dialog "Ubah Langganan": kolom "Masa berlaku" hanya perlu diisi bila status Pro dipilih.

## Inventaris halaman

Daftar halaman target sistem penuh, sumber kebutuhan di `docs/SPEC.md` bagian 9. Rute adalah rute target; mengubah rute yang sudah ada hanya dilakukan oleh tugas refactor tampilan yang memintanya. "Rancangan" adalah status rancangan tampilan per halaman (tata letak, komponen, keadaan) yang ditulis di bagian "Rancangan halaman" sebelum halaman itu dikerjakan.

| # | Halaman | Rute | Peran | FR dan UC | Isi utama | Status fitur | Rancangan |
|---|---|---|---|---|---|---|---|
| 1 | Pemasaran | `/` | Publik (yang sudah login dialihkan ke Beranda atau Dashboard Pantauan) | FR28 | Penjelasan fitur, cara kerja, perbedaan Free dan Pro, tautan Daftar dan Masuk | Belum dikerjakan | Ada |
| 2 | Daftar | `/daftar` | Publik | FR1 | Form nama, email, password | Selesai | Ada |
| 3 | Masuk | `/masuk` | Publik | FR1 | Form email dan password; pesan "Akun berhasil dibuat, silakan masuk" dan "Sesi berakhir, silakan masuk kembali." | Selesai | Ada |
| 4 | Beranda | `/beranda` | Pengajar | FR2, FR3, FR21, FR22, UC-01, UC-02, UC-03, UC-13 | Sapaan, label FREE atau PRO, ringkasan (nanti), daftar batch, "Buat Batch Baru", hapus batch (nanti) | Sebagian selesai | Ada |
| 5 | Halaman Batch | `/batch/:id_batch` | Pengajar | FR4 sampai FR11, FR14 sampai FR17, FR23 | Judul batch, status batch, dua tab: Soal dan Jawaban, dan Dashboard Hasil Koreksi. Aksi: Selesaikan Batch, Hapus Batch, Ekspor Rekap Nilai (nanti) | Sebagian selesai | Ada |
| 6 | Langganan | `/langganan` | Pengajar | FR2, FR19, FR20, UC-10, UC-11 | Status langganan dan masa berlaku, paket Pro, "Upgrade ke Pro", status transaksi | Belum dikerjakan | Ada |
| 7 | Dashboard Pantauan | `/admin` | Admin | FR27, UC-18 | Angka jumlah akun (total, Free, Pro), jumlah batch, file jawaban per status, pemakaian kuota API harian | Belum dikerjakan | Ada |
| 8 | Akun Pengajar | `/admin/akun-pengajar` | Admin | FR24 sampai FR26, UC-15 sampai UC-17 | Tabel akun, cari, filter, "Ubah Langganan", "Nonaktifkan" atau "Aktifkan" | Belum dikerjakan | Ada |
| 9 | Lupa Password | `/lupa-password` | Publik | FR1 | Form email, tombol "Kirim Tautan", pesan "Jika email terdaftar, tautan atur ulang password telah dikirim." | Belum dikerjakan | Ada |
| 10 | Atur Ulang Password | `/atur-ulang-password` | Publik (lewat tautan email) | FR1 | Form password baru dan konfirmasi, tombol "Simpan Password", pesan token tidak berlaku | Belum dikerjakan | Ada |

Halaman 9 dan 10 mengikuti SPEC F-RESET. Halaman Masuk mendapat tautan "Lupa password?". Setelah Keluar, pengguna dialihkan ke Halaman Pemasaran (SPEC bagian 6).

Isi Halaman Batch (dua tab):
- Soal dan Jawaban, dua seksi: "Soal dan Kunci Jawaban" (daftar soal, "Tambah Soal", form kunci) dan "Jawaban Peserta Didik" (tombol "Upload Jawaban Peserta Didik", form unggah, lalu daftar semua file jawaban dengan nama, lencana status, dan pesan error untuk yang Gagal).
- Dashboard Hasil Koreksi: pilihan soal, tabel hasil.
- Tidak ada tab Status Pemrosesan. Status tiap file hanya tampil di daftar file jawaban.

## Komponen bersama

Komponen yang dipakai lebih dari satu halaman. Satu definisi per komponen di `frontend/src/components/`.

| Komponen | Dipakai di | Aturan |
|---|---|---|
| Bilah atas | Semua halaman, kecuali halaman kartu publik (Masuk, Daftar, Lupa Password, Atur Ulang Password) yang tampil tanpa bilah atas | Tiga varian. Publik: logo, "Masuk", "Daftar" (di Pemasaran ditambah tiga tautan jangkar, lihat rancangan Pemasaran). Pengajar: logo, menu "Beranda" dan "Langganan" ("Langganan" baru dirender setelah halaman Langganan dikerjakan), label FREE atau PRO, nama, "Keluar". Menu yang sedang dibuka bertanda `aria-current="page"`; "Beranda" tetap menyala di Halaman Batch. Admin: logo, menu "Dashboard Pantauan" dan "Akun Pengajar", "Keluar". Mulai 1024 px menu tampil sebagai bilah horizontal. Di bawah 1024 px (tablet dan ponsel) menu berpindah ke laci dari kiri yang dibuka tombol menu (`aria-label` "Buka menu", tombol tutup "Tutup menu"), berisi item menu, label FREE atau PRO, nama, dan "Keluar" |
| Lencana | Status pemrosesan, kategori, FREE atau PRO, status aktif akun | Selalu berisi teks, memakai token di bagian Pemakaian |
| Dialog konfirmasi | Hapus batch, selesaikan batch, nonaktifkan akun, tinggalkan halaman unggah | Judul singkat ("Hapus Batch", "Selesaikan Batch", "Tinggalkan Halaman"), satu kalimat persis dari SPEC, dua tombol. Hapus dan selesaikan: "Ya" dan "Batal". Tinggalkan halaman: "Tetap di Halaman" dan "Tinggalkan". Tombol utama memakai `bg-biru-utama`; aksi merusak tidak memakai warna merah polos tanpa teks |
| Kartu angka | Ringkasan Pengajar, Dashboard Pantauan | Angka besar dan label teks. Nilai 0 tetap tampil |
| Tabel | Hasil koreksi, Akun Pengajar | Aturan di bagian Tata letak |
| Menu aksi (titik tiga) | Baris daftar batch di Beranda (nanti) | Tombol ikon titik tiga yang membuka daftar aksi kecil. Punya nama aksesibel, dapat dioperasikan dengan papan ketik (Enter, Esc, panah), tertutup saat klik di luar. Aksi yang merusak berteks `text-kurang-mirip` dan membuka dialog konfirmasi |
| Keadaan data | Semua data yang dimuat | Tiga keadaan: memuat (indikator), kosong (teks dari SPEC), gagal (teks dari SPEC) |
| Pesan sukses dan galat | Semua form | Sukses singkat ("Kunci jawaban tersimpan."), galat memakai `text-kurang-mirip` |

## Tata letak

- Bilah atas: ikon logo, nama "Koreksi-in", dan isi menurut peran (lihat Komponen bersama).
- Halaman Masuk dan Daftar: kartu di tengah dengan `logo.png` di atasnya.
- Beranda: judul "Batch Koreksi", tombol "Buat Batch Baru", lalu daftar batch. Tata letak yang lebih kaya (ringkasan, label langganan) ditetapkan di Rancangan halaman.
- Halaman Batch: judul batch, dua tab (Soal dan Jawaban, Dashboard Hasil Koreksi).
- Tabel: baris cukup lega, header `text-teks-redup`, teks OCR panjang dipotong dengan opsi tampilkan lengkap.
- Tampilkan indikator loading pada unggah, pemrosesan, dan pemuatan data. Tampilkan keadaan kosong dengan teks yang ada di SPEC.
- Responsif: desktop adalah prioritas, tetapi semua halaman tetap bisa dipakai pada lebar tablet dan ponsel tanpa gulir horizontal untuk isi utama (NFR17). Titik henti: ponsel di bawah 768 px (`md`), tablet 768 sampai 1023 px, desktop mulai 1024 px (`lg`).

## Rancangan halaman

Tiap halaman di Inventaris halaman ditambahi satu subbagian di sini sebelum dikerjakan: tata letak (urutan blok dari atas ke bawah), komponen yang dipakai, isi tiap blok, keadaan (memuat, kosong, gagal, sukses), dan perilaku tombol. Halaman yang belum punya subbagian di sini TIDAK BOLEH dirombak atau dibuat; tanyakan pemilik proyek.

### Cara membaca rancangan ini

- Rancangan menetapkan ISI dan STRUKTUR: urutan blok, komponen, teks, keadaan, dan perilaku. Gaya visual (ukuran, jarak, bentuk, ilustrasi) diputuskan perancang tampilan, TETAPI hanya memakai token warna dan aturan di bagian atas dokumen ini.
- Semua teks yang tertulis dalam tanda kutip diambil dari `docs/SPEC.md` dan dipakai persis. Perancang TIDAK BOLEH mengarang teks pesan, label tombol, atau angka batas. Teks yang bertanda "(usulan)" belum ada di SPEC dan dapat diganti pemilik proyek.
- Fitur yang bertanda "(nanti)" belum dikerjakan (SPEC bagian 3). Tempatnya dirancang sekarang supaya tata letak tidak dirombak lagi, tetapi elemennya TIDAK dirender sampai fiturnya diminta.
- Semua halaman terproteksi memakai bilah atas sesuai peran (bagian Komponen bersama) dan konten di tengah dengan lebar maksimal setara `max-w-5xl`, margin samping 16 px di ponsel. Halaman publik bertipe kartu (Masuk, Daftar, Lupa Password, Atur Ulang Password) memakai kartu sempit di tengah layar, tanpa bilah atas.
- Setiap data yang dimuat punya tiga keadaan: memuat (indikator), kosong (teks SPEC), gagal (teks SPEC). Setiap form memakai `noValidate` dan menampilkan pesan dari aplikasi di dekat kolom atau di bawah form.
- Di ponsel dan tablet (lebar kurang dari 1024 px, titik henti `lg`) tabel tidak boleh membuat halaman bergulir horizontal. Tabel berubah menjadi daftar kartu, satu kartu per baris, dengan label kolom di dalam kartu. Tabel penuh dipakai mulai 1024 px (laptop, desktop, dan tablet landscape lebar). Tidak ada pilihan gulir horizontal untuk tabel. PENGECUALIAN: tabel perbandingan Free dan Pro di Pemasaran tetap berbentuk tabel di semua lebar (tiga kolom muat di 375 px tanpa gulir), karena tujuannya membandingkan dua kolom berdampingan. Aturan kartu berlaku untuk tabel data (Akun Pengajar dan Dashboard Hasil Koreksi).
- Tombol aksi utama memakai `bg-biru-utama`. Tombol sekunder memakai garis `border-garis` dengan teks `text-teks`. Aksi yang merusak (hapus, nonaktifkan) memakai tombol sekunder dengan teks `text-kurang-mirip` dan SELALU lewat dialog konfirmasi.

### 1. Pemasaran (`/`)

Tujuan: pengunjung yang belum login memahami apa itu Koreksi-in dan terdorong mendaftar. Pengunjung yang sudah login dialihkan ke Beranda (Pengajar) atau Dashboard Pantauan (Admin). Bilah atas varian Publik.

Bilah atas Pemasaran menempel di atas layar saat halaman digulir. Mulai 1024 px, di tengah bilah ada tiga tautan jangkar: "Cara kerja", "Fitur utama", "Free dan Pro" (teksnya sama dengan judul seksi, tanpa teks baru). Mengklik tautan menggulir halaman ke seksi itu, dan judul seksi tidak boleh tertutup bilah. Gulir halus dimatikan bagi pengguna yang memilih gerak berkurang (`motion-reduce`). Di bawah 1024 px tautan jangkar tidak ditampilkan; bilah hanya berisi logo, "Masuk", dan "Daftar".

Blok dari atas ke bawah:
1. **Hero.** Judul (didahului garis aksen pendek `h-1 w-16 rounded-full bg-merek-hijau`, `aria-hidden`; satu-satunya halaman yang memakainya, halaman aplikasi tidak), satu kalimat penjelas, tombol utama "Daftar" ke `/daftar`, dan tautan "Masuk" ke `/masuk`. Teks usulan: judul "Koreksi esai lebih cepat, nilai akhir tetap di tangan Anda"; kalimat "Unggah lembar jawaban peserta didik. Koreksi-in membaca tulisan tangan dan memberi skor kemiripan sebagai rekomendasi."
2. **Cara kerja.** Empat langkah bernomor: (1) Buat batch dan ketik kunci jawaban. (2) Unggah lembar jawaban berupa foto atau PDF, beserta nama peserta didik. (3) Sistem membaca tulisan dan memberi skor kemiripan. (4) Tinjau hasil, koreksi nilai bila perlu, lalu ekspor (akun Pro).
3. **Fitur utama.** Empat kartu kecil: "Membaca tulisan tangan" (OCR), "Skor kemiripan dan kategori" (Sangat Mirip, Cukup Mirip, Kurang Mirip), "Koreksi manual" (edit teks hasil baca dan nilai akhir), "Ekspor rekap nilai" (Pro).
4. **Free dan Pro.** Tabel perbandingan dua kolom (tetap tabel di semua lebar, tanpa gulir horizontal; pengecualian dari aturan tabel menjadi kartu):

| | Free | Pro |
|---|---|---|
| Batch aktif | 1 | Tidak dibatasi |
| Soal per batch | 15 | 30 |
| Jawaban peserta didik per batch | 15 | 50 |
| File per sekali unggah | 10 | 10 |
| Ekspor rekap nilai | Tidak | Ya |
| Harga | Gratis | Rp 30.000 (1 bulan), Rp 80.000 (3 bulan) |

   Header kolom pertama kosong secara visual, tetapi harus berisi teks `sr-only` "Fitur" (bukan sel `th` kosong) agar pembaca layar mengenal kolomnya. Di bawah tabel, satu kalimat kecil: "Langganan Pro tidak diperpanjang otomatis."
5. **Penutup.** Ajakan singkat dan tombol "Daftar".

Keadaan: halaman statis, tanpa pemuatan data. Penegasan isi: skor selalu disebut rekomendasi, sistem tidak mengeluarkan nilai huruf, dan tidak ada klaim akurasi berupa angka.

### 2. Daftar (`/daftar`)

Kartu di tengah dengan `logo.png`, judul "Daftar". Pengguna yang sudah login dialihkan ke Beranda.

- Kolom: Nama, Email, Password. Petunjuk kecil di bawah Password: "Minimal 8 karakter."
- Tombol "Daftar" (indikator putar selama mengirim, tombol nonaktif). Di bawah kartu: "Sudah punya akun? Masuk".
- Galat tampil di atas form (`role="alert"`, `text-kurang-mirip`): "Email sudah terdaftar", "Password minimal 8 karakter", "Password maksimal 72 karakter", "Data yang dikirim tidak valid." (kolom kosong atau email tidak berformat valid).
- Sukses: arahkan ke `/masuk` dengan pesan "Akun berhasil dibuat, silakan masuk". Tidak ada sesi yang dibuat.

### 3. Masuk (`/masuk`)

Kartu di tengah dengan `logo.png`, judul "Masuk". Pengguna yang sudah login dialihkan menurut peran.

- Kolom: Email, Password. Tombol "Masuk" (indikator putar). Tautan "Belum punya akun? Daftar".
- Tautan "Lupa password?" ke `/lupa-password` (nanti, tampil setelah reset password dikerjakan).
- Pesan di atas form, satu pesan sekali tampil: sukses "Akun berhasil dibuat, silakan masuk" (gaya sukses), "Password berhasil diubah, silakan masuk." (gaya sukses), "Sesi berakhir, silakan masuk kembali." (gaya netral, bukan galat).
- Galat: "Email atau password salah" untuk semua kegagalan login, termasuk email tidak terdaftar (SPEC bagian 6).
- Sukses: Pengajar ke `/beranda`, Admin ke `/admin`.

### 4. Beranda (`/beranda`, Pengajar)

Blok dari atas ke bawah:
1. **Sapaan.** "Selamat datang, {nama}" dan "Kelola batch koreksi esai Anda di sini."
2. **Ringkasan (nanti, FR21).** Deret kartu angka: jumlah total batch, jumlah peserta didik yang sudah dikoreksi, dan khusus akun Free: sisa slot batch aktif serta sisa slot jawaban per batch. Nilai 0 tetap tampil. Label kartu (disetujui): "Total batch", "Peserta didik sudah dikoreksi", "Sisa slot batch aktif", "Sisa slot jawaban per batch". Gagal: "Gagal memuat ringkasan, coba muat ulang halaman".
3. **Banner upgrade (nanti).** Tampil untuk akun Free yang baru turun dari Pro atau yang datanya melewati batas Free. Teks usulan: "Masa berlaku Pro Anda telah berakhir. Upgrade ke Pro untuk membuat batch baru dan memakai semua fitur." dengan tautan ke `/langganan`.
4. **Kepala daftar.** Judul "Batch Koreksi" dan tombol utama "Buat Batch Baru".
5. **Form buat batch.** Terbuka di tempat saat tombol ditekan. Kolom "Nama Batch" (maksimal 100 karakter), tombol "Buat". Galat: "Nama batch tidak boleh kosong.", "Gagal membuat batch, silakan coba lagi". Akun Free yang sudah punya 1 batch aktif (nanti, FR18): "Batas batch aktif untuk akun Free telah tercapai. Upgrade ke Pro untuk batch tidak terbatas." dengan tautan ke `/langganan`; tombol "Buat Batch Baru" tetap bisa ditekan dan pesan ini muncul sebagai penolakan, bukan tersembunyi.
6. **Daftar batch.** Satu baris per batch, terbaru di atas: nama batch (tautan ke Halaman Batch), tanggal dibuat, lencana status "Aktif" atau "Selesai" (nanti), dan di ujung kanan tombol menu aksi bergambar titik tiga (nanti, FR22 dan FR23) sehingga Pengajar tidak perlu membuka batch dulu. Menu berisi "Selesaikan Batch" (hanya untuk batch Aktif) dan "Hapus Batch". Aksinya sama dengan di Halaman Batch (lihat "Perilaku tombol aksi di kepala"): "Selesaikan Batch" memunculkan dialog "Batch yang diselesaikan tidak dapat diubah lagi. Lanjutkan?" ("Ya", "Batal"), atau pesan "Tunggu hingga semua file selesai diproses." bila masih ada file Diproses; "Hapus Batch" memunculkan dialog "Batch ini beserta seluruh data koreksi akan dihapus permanen dan tidak dapat dikembalikan. Lanjutkan?" ("Ya", "Batal"). Sukses: baris diperbarui (lencana jadi Selesai) atau hilang dari daftar. Gagal: "Gagal menyelesaikan batch, silakan coba lagi" atau "Gagal menghapus batch, silakan coba lagi". Tombol titik tiga HARUS punya nama aksesibel (usulan: "Aksi untuk batch {nama batch}"), dapat dipakai lewat papan ketik, dan klik pada tombol ini TIDAK membuka batch. Kosong: "Belum ada batch. Buat batch pertama untuk mulai mengoreksi." Gagal memuat: pesan galat dari server dengan teks Indonesia.

Label FREE atau PRO ada di bilah atas (nanti, FR2). Gagal memuat: "Gagal memuat status langganan, coba muat ulang halaman".

### 5. Halaman Batch (`/batch/:id_batch`, Pengajar)

Sketsa (desktop):

```
[Bilah atas]
< Batch Koreksi
Nama Batch  [Aktif]                       [Selesaikan Batch] [Ekspor Rekap Nilai] [Hapus Batch]   <- tiga tombol nanti
-------------------------------------------------------------------------------------------------
 Soal dan Jawaban | Dashboard Hasil Koreksi
-------------------------------------------------------------------------------------------------
 (isi tab)
```

Kepala halaman: tautan "Batch Koreksi" (kembali ke Beranda), nama batch sebagai judul, lencana status batch (nanti), dan kelompok tombol aksi di kanan (nanti): "Selesaikan Batch", "Ekspor Rekap Nilai", "Hapus Batch" (dua aksi pertama dan terakhir juga tersedia dari menu titik tiga di daftar Beranda; "Ekspor Rekap Nilai" hanya ada di Halaman Batch). Di ponsel tombol aksi pindah ke baris di bawah judul. Keadaan memuat dan gagal untuk seluruh halaman: indikator di tengah; gagal menampilkan galat dan tautan "Kembali ke Beranda". Batch yang bukan milik pengguna atau tidak ada: "Batch tidak ditemukan".

Dua tab: **Soal dan Jawaban**, **Dashboard Hasil Koreksi**. Tidak ada tab Status Pemrosesan.

#### Tab Soal dan Jawaban

Dua seksi bertumpuk, masing-masing diberi judul dan dipisah jelas.

**Seksi "Soal dan Kunci Jawaban"**
- Daftar soal, urut nomor. Tiap item: "Soal N" dan teks kunci jawaban (baris baru dipertahankan, hanya baca). Kosong: "Belum ada soal pada batch ini."
- Di bawah daftar, tepat satu dari tiga keadaan:
  - tombol "Tambah Soal" (keadaan biasa);
  - pesan netral "Sudah mencapai jumlah maksimal N soal per batch." (batas soal tercapai; N sesuai batas akun, SPEC bagian 4);
  - pesan "Soal tidak dapat ditambah setelah jawaban diunggah." (sudah ada lembar jawaban).
- Form tambah soal: label "Soal N: Kunci Jawaban", area teks beberapa baris, tombol "Simpan Kunci Jawaban". Kunci kosong atau hanya spasi: "Kunci jawaban tidak boleh kosong" di bawah kolom, tanpa permintaan terkirim. Sukses: "Kunci jawaban tersimpan." (hilang begitu batch punya lembar jawaban) dan soal masuk ke daftar. Gagal: "Gagal menambah soal, silakan coba lagi."
- (nanti, FR5 sampai FR7) Di form kunci ada pilihan "Upload File" yang mengisi area teks yang sama dengan hasil baca, dapat diedit sebelum disimpan. Gagal baca: "Gagal membaca file, silakan coba lagi atau masukkan teks secara manual".

**Seksi "Jawaban Peserta Didik"**
- Jika belum ada soal: "Tambahkan minimal satu soal sebelum mengunggah jawaban." dan tombol unggah tidak dirender.
- Jika belum ada lembar jawaban: teks kecil "Pastikan semua soal sudah ditambahkan. Setelah jawaban diunggah, soal tidak dapat ditambah lagi."
- Tombol utama "Upload Jawaban Peserta Didik" memilih 1 sampai 10 file (PDF, PNG, JPG). Setelah dipilih, tombol berganti daftar file terpilih: tiap baris berisi nama file dan kolom "Nama peserta didik" (wajib, maksimal 100 karakter), dengan tombol "Upload" dan "Batal" (kosongkan pilihan, kembali ke tombol awal).
- Galat unggah di atas tombol "Upload", memakai teks SPEC: "Nama peserta didik wajib untuk semua file", "Maksimal 10 file per unggahan.", "Pilih minimal satu file untuk diunggah.", "Format file tidak didukung. Gunakan PDF, PNG, atau JPG.", "Ukuran file maksimal 10 MB.", "PDF maksimal 15 halaman.", "File PDF rusak atau tidak dapat dibaca.", "Gagal menyimpan jawaban, silakan coba lagi." Unggahan semua-atau-tidak-sama-sekali: bila ada yang tidak valid, tidak ada yang tersimpan dan daftar file terpilih tetap tampil.
- Daftar jawaban yang sudah diunggah (tabel ringkas, urut waktu unggah): kolom Peserta Didik dan Status (lencana Diproses, Selesai, Gagal sesuai bagian Pemakaian). Untuk Gagal, `pesan_error` tampil di bawah nama. Kolom aksi "Coba Lagi" untuk file Gagal (nanti, FR11). Daftar diperbarui sendiri tiap 5 detik selama ada file Diproses (tanpa kedipan atau lompatan tata letak). Gagal memuat: "Gagal memuat status pemrosesan, coba muat ulang halaman". Kosong: tidak ada teks khusus, seksi hanya menampilkan tombol unggah.
- Konfirmasi meninggalkan halaman: jika ada file terpilih yang belum diunggah, meninggalkan Halaman Batch (kembali, pindah halaman, tutup tab) memunculkan dialog "Ada file yang belum diunggah. Yakin ingin meninggalkan halaman ini?" dengan tombol "Tetap di Halaman" dan "Tinggalkan". Tanpa file terpilih, tidak ada dialog.

#### Tab Dashboard Hasil Koreksi

- Pilihan soal di atas tabel: dropdown berisi "Soal 1", "Soal 2", dan seterusnya (hingga 30). Soal pertama terpilih awal. Jika batch belum punya soal, dropdown tidak dirender dan pesan kosong tetap tampil.
- Tabel untuk soal terpilih, satu baris per peserta didik yang file-nya berstatus Selesai. Kolom: Peserta Didik, Teks OCR, Skor Kemiripan (0 sampai 100), Kategori Kualitatif (lencana bernama, bukan hanya warna). Teks OCR panjang dipotong beberapa baris dengan tautan "Tampilkan lengkap"; setelah dibuka, tautan berganti "Tampilkan ringkas" untuk memotongnya kembali (tombol dengan `aria-expanded`). Jawaban tidak ditemukan: "(jawaban tidak ditemukan)".
- (nanti) Kolom Nilai Akhir dan aksi per baris: "Edit" (ubah teks OCR, FR15) dan "Ubah Nilai Akhir" (FR16). Nilai akhir yang sudah diisi tampil sebagai nilai resmi dan skor kemiripan sistem tetap terlihat sebagai rekomendasi.
- Kosong: "Belum ada hasil koreksi untuk soal ini. Tunggu proses selesai." Gagal memuat: "Koneksi internet terputus, coba muat ulang halaman."
- Di bawah 1024 px (ponsel dan tablet): tiap baris menjadi kartu dengan nama di atas, skor dan lencana kategori, lalu teks OCR.

#### Batch Selesai (nanti, FR23)

Batch berstatus Selesai bersifat baca saja: lencana "Selesai" di kepala, tombol "Tambah Soal", "Upload Jawaban Peserta Didik", "Coba Lagi", "Edit", dan "Ubah Nilai Akhir" tidak dirender, dan "Selesaikan Batch" tidak tampil. "Ekspor Rekap Nilai" dan "Hapus Batch" tetap ada. Satu catatan kecil di bawah judul (usulan): "Batch ini sudah selesai dan tidak dapat diubah."

#### Perilaku tombol aksi di kepala (nanti)

- "Selesaikan Batch": jika masih ada file Diproses, pesan "Tunggu hingga semua file selesai diproses."; jika tidak, dialog "Batch yang diselesaikan tidak dapat diubah lagi. Lanjutkan?" ("Ya", "Batal"). Gagal: "Gagal menyelesaikan batch, silakan coba lagi".
- "Ekspor Rekap Nilai": akun Pro mengunduh file .xlsx; akun Free melihat "Fitur ekspor hanya tersedia untuk akun Pro. Upgrade untuk mengakses fitur ini." dengan tautan ke `/langganan`. Gagal: "Gagal membuat file ekspor, silakan coba lagi".
- "Hapus Batch": dialog yang sama seperti di menu Beranda; sukses kembali ke Beranda. Gagal: "Gagal menghapus batch, silakan coba lagi".

### 6. Langganan (`/langganan`, Pengajar, nanti)

Blok dari atas ke bawah:
1. **Status akun.** Lencana FREE atau PRO; untuk Pro tampilkan "Berlaku hingga {tanggal}". Gagal memuat: "Gagal memuat status langganan, coba muat ulang halaman".
2. **Paket Pro.** Dua pilihan berdampingan (satu terpilih): "1 bulan, Rp 30.000" dan "3 bulan, Rp 80.000". Daftar manfaat: batch aktif tidak dibatasi, 30 soal per batch, 50 jawaban per batch, ekspor rekap nilai. Catatan: "Langganan Pro tidak diperpanjang otomatis."
3. **Tombol.** "Upgrade ke Pro" (untuk akun Pro yang masih berlaku, label "Perpanjang Pro", usulan) membuka ringkasan paket terpilih (harga dan manfaat) dengan tombol "Lanjutkan ke Pembayaran", yang membawa pengguna ke halaman pembayaran Midtrans (Sandbox). Galat: "Transaksi gagal dibuat, silakan coba lagi", "Gagal mencatat transaksi, silakan coba lagi".
4. **Status transaksi terakhir.** Saat pengguna kembali dari pembayaran: lencana status (Menunggu, Berhasil, Gagal, Kedaluwarsa; label usulan) beserta paket dan nominalnya. Status Berhasil diikuti perubahan lencana akun menjadi PRO.

### 7. Dashboard Pantauan (`/admin`, Admin, nanti)

Hanya angka agregat, tanpa isi kunci, jawaban, atau hasil koreksi. Judul halaman TANPA garis aksen (garis aksen hanya di Pemasaran). Kartu angka dalam grid, dikelompokkan dengan judul kecil yang berikon:
- **Akun** (`users`): total akun Pengajar (`users`), akun Free (`user-check`), akun Pro (`crown`, kotak ikon `bg-biru-utama text-permukaan`).
- **Aktivitas** (`layers`): jumlah batch (`layers`); file Diproses (`loader-circle`, berputar HANYA bila jumlah lebih dari 0 dan dengan `motion-reduce:animate-none`), File Selesai (`file-check`), File Gagal (`file-x`, angka `text-kurang-mirip`).
- **Kuota API** (`gauge`): satu kartu berisi "Terpakai hari ini" dan "Batas harian" serta bilah pemakaian (`role="progressbar"`, `aria-valuenow` dan `aria-valuemax` dari data). Lebar isi bilah dihitung dari data (gaya sebaris, `terpakai / batas`, batas 0 menghasilkan lebar 0, maksimal 100 persen), bukan kelas tetap. Warna isi `bg-biru-utama` di atas jalur `bg-biru-muda` (kontras komponen non-teks minimal 3:1; `merek-hijau` di atas `biru-muda` hanya sekitar 1,9:1).
- Kartu angka: `rounded-lg border border-garis bg-permukaan p-4 shadow-sm` (padat, supaya label muat di ponsel dua kolom). Kartu Kuota API `p-6`. Ukuran ini sementara (pilihan pemilik proyek, boleh disesuaikan setelah dilihat di aplikasi).
- Kartu angka memakai garis aksen dekoratif di tepi atas (`h-1`, `aria-hidden`; warna `merek-biru`, `merek-hijau`, `biru-utama`, atau `kurang-mirip` menurut maknanya) dan kotak ikon `size-9 rounded-lg`. Ikon dan garis aksen bersifat dekoratif; angka dan label teks tetap pembawa makna.

Tanpa data: kartu menampilkan 0. Gagal: "Gagal memuat dashboard pantauan, coba muat ulang halaman."

### 8. Akun Pengajar (`/admin/akun-pengajar`, Admin, nanti)

- **Bilah alat:** kolom cari (nama atau email), filter status langganan (Semua, Free, Pro), filter status akun (Semua, Aktif, Nonaktif).
- **Tabel:** Nama, Email, Langganan (lencana FREE atau PRO, untuk Pro dengan masa berlaku), Status akun (lencana Aktif atau Nonaktif), Tanggal daftar, Jumlah batch, Aksi. Aksi per baris: "Ubah Langganan" dan "Nonaktifkan" atau "Aktifkan" (menyesuaikan status).
- **Ubah Langganan:** dialog dengan pilihan status Free atau Pro; untuk Pro, kolom tanggal masa berlaku wajib. Galat: "Masa berlaku wajib diisi dengan tanggal setelah hari ini." Sukses: "Status langganan berhasil diubah". Gagal: "Gagal mengubah status langganan, silakan coba lagi.", "Koneksi internet terputus, silakan coba lagi."
- **Nonaktifkan atau Aktifkan:** dialog konfirmasi yang menyebut nama akun dan tindakan. Sukses: "Akun berhasil dinonaktifkan" atau "Akun berhasil diaktifkan". Gagal: "Gagal mengubah status akun, silakan coba lagi."
- **Keadaan:** kosong "Belum ada akun Pengajar yang terdaftar."; pencarian tanpa hasil "Tidak ada akun yang sesuai dengan pencarian."; gagal "Gagal memuat daftar akun, coba muat ulang halaman."; offline "Koneksi internet terputus, coba muat ulang halaman."
- Di bawah 1024 px (ponsel dan tablet) tiap baris menjadi kartu dengan aksi di bagian bawah kartu.

### 9. Lupa Password (`/lupa-password`, publik, nanti)

Kartu di tengah dengan `logo.png`, judul "Lupa Password".
- Kolom Email, tombol "Kirim Tautan" (indikator putar), tautan kembali "Kembali ke Masuk".
- Format email tidak valid: "Format email tidak valid." di bawah kolom, tanpa permintaan terkirim.
- Setelah dikirim, apa pun hasilnya (email terdaftar atau tidak, akun aktif atau tidak): "Jika email terdaftar, tautan atur ulang password telah dikirim." (gaya sukses). Halaman TIDAK BOLEH membedakan hasilnya. Form tetap tampil setelah pesan sukses.

### 10. Atur Ulang Password (`/atur-ulang-password?token=...`, publik, nanti)

Kartu di tengah dengan `logo.png`, judul "Atur Ulang Password".
- Kolom Password baru dan Konfirmasi password, tombol "Simpan Password".
- Galat: "Konfirmasi password tidak sama.", "Password minimal 8 karakter", "Password maksimal 72 karakter", "Gagal mengubah password, silakan coba lagi."
- Token kedaluwarsa, sudah dipakai, atau tidak sah: halaman menampilkan "Tautan tidak berlaku atau sudah kedaluwarsa." dan tautan "Lupa Password" untuk meminta tautan baru (ke `/lupa-password`), tanpa form.
- Sukses: arahkan ke `/masuk` dengan pesan "Password berhasil diubah, silakan masuk."

### Keputusan pemilik proyek

1. Tombol "Upgrade ke Pro" dan pesan "batch tidak terbatas" memakai Bahasa Indonesia (SPEC sudah disesuaikan).
2. Akun Pro yang masih berlaku boleh membeli paket lagi. Masa berlaku baru dihitung dari masa berlaku saat ini (SPEC F-LANGGANAN). Tombol berlabel "Perpanjang Pro" untuk akun itu (label usulan).
3. Kolom kosong di Daftar dan Masuk cukup memakai "Data yang dikirim tidak valid." untuk sementara.
4. Teks yang bertanda "(usulan)" dan label kecil di luar daftar pesan SPEC disetujui untuk sementara. Perancang TIDAK BOLEH menambah teks baru di luar itu; perubahan teks lewat pemilik proyek.
5. Akun nonaktif yang mencoba masuk (SPEC U6) memakai pesan generik "Email atau password salah".
6. Halaman Batch tetap halaman tersendiri di `/batch/:id_batch`, bukan item navbar. Navbar Pengajar tetap memakai menu "Beranda" (menyala saat di Halaman Batch) dan "Langganan"; Halaman Batch dibuka dari daftar batch di Beranda.
7. Ikon diizinkan, hanya dari Lucide (bagian Ikon).
8. Tautan di halaman Atur Ulang Password untuk token tidak sah memakai teks "Lupa Password" (pilihan pemilik proyek). Alt teks logo: "Koreksi-in". Tautan "Langganan" di navbar dan "Lupa password?" di Masuk memakai penanda "nanti" sampai fiturnya dikerjakan.
9. Tampilan mendukung tablet: tabel berubah menjadi kartu di bawah 1024 px, dan menu Bilah atas berpindah ke laci di bawah 1024 px, satu titik henti (`lg`) yang sama untuk tabel dan menu (bagian Gaya visual dan Komponen bersama).
10. Teks tambahan dari desain tahap 3, disetujui sementara (perubahan lewat pemilik proyek):
    - Pemasaran: judul seksi "Cara kerja", "Fitur utama", "Free dan Pro". Deskripsi kartu fitur: "Lembar jawaban foto atau PDF dibaca menjadi teks.", "Skor sebagai rekomendasi, bukan nilai akhir.", "Edit teks hasil baca dan nilai akhir.", "Unduh rekap nilai dalam file .xlsx.". Penutup: "Siap mulai mengoreksi lebih cepat?".
    - Langganan: judul halaman "Langganan"; judul seksi "Paket Pro" dan "Status transaksi terakhir"; lencana transaksi "Menunggu", "Berhasil", "Gagal", "Kedaluwarsa".
    - Dashboard Pantauan: judul halaman "Dashboard Pantauan"; kelompok "Akun", "Aktivitas", "Kuota API"; label kartu "Total akun Pengajar", "Akun Free", "Akun Pro", "Jumlah batch", "File Diproses", "File Selesai", "File Gagal", "Terpakai hari ini", "Batas harian".
    - Akun Pengajar: judul halaman "Akun Pengajar"; label "Cari", "Status langganan", "Status akun", "Masa berlaku"; tombol dialog "Simpan", "Batal", "Ya". Dialog nonaktifkan: judul "Nonaktifkan Akun", kalimat "Akun {nama} akan dinonaktifkan dan tidak dapat masuk. Lanjutkan?". Dialog aktifkan: judul "Aktifkan Akun", kalimat "Akun {nama} akan diaktifkan dan dapat masuk kembali. Lanjutkan?".
11. Ejaan baku "silakan" dipakai di semua pesan (SPEC sudah disesuaikan, SRS menyusul saat sinkronisasi).
12. Tabel Free dan Pro di Pemasaran tetap tabel di semua lebar tanpa gulir horizontal (pengecualian dari aturan tabel menjadi kartu di bawah 1024 px).
13. Garis hijau pendek di atas judul hanya dipakai di Pemasaran. Halaman aplikasi (termasuk Dashboard Pantauan) tidak memakainya.
14. Teks OCR di Dashboard Hasil Koreksi: tautan "Tampilkan lengkap" berganti menjadi "Tampilkan ringkas" setelah teks dibuka (pilihan pemilik proyek, 1 November 2026)
15. Halaman kartu publik (Masuk, Daftar, Lupa Password, Atur Ulang Password) tidak memakai bilah atas; hanya kartu di tengah layar dengan logo, seperti referensi situs lain (pilihan pemilik proyek, 2 November 2026). Mockup Masuk dan Daftar yang masih menampilkan bilah atas varian Publik diabaikan; varian Publik hanya dipakai di Pemasaran.
16. Bilah atas Pemasaran menempel di atas dan memuat tiga tautan jangkar yang menggulir ke seksi "Cara kerja", "Fitur utama", dan "Free dan Pro", mengikuti situs referensi (pilihan pemilik proyek, 2 November 2026). Label memakai judul seksi yang sudah ada; mockup Pemasaran belum menampilkannya, jadi UI.md yang diikuti..