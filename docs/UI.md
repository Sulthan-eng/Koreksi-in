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
| Teks pendukung (keterangan, label kecil, placeholder input `placeholder:text-teks-redup`) | `text-teks-redup` |
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

- `logo.png`: logo lengkap (ikon dan tulisan "Koreksi-in"). Dipakai di halaman kartu publik (Masuk, Daftar, Lupa Password, Atur Ulang Password).
- `logo-ikon.png`: ikon saja. Dipakai di bilah atas aplikasi dan sebagai favicon.

Aturan: jangan mengubah warna, rasio, atau memutar logo. Beri ruang kosong di sekeliling minimal setinggi lingkaran kecil pada ikon. Latar logo harus putih atau `latar`. Tinggi ikon di bilah atas sekitar 40 px.

## Ikon

Ikon boleh dipakai untuk memperjelas tombol, menu, dan keadaan data. Sumbernya hanya Lucide (lisensi ISC), diimpor per ikon lewat `lucide-react` sehingga hanya ikon yang dipakai ikut terkirim. Penambahan paket atau keluarga ikon lain adalah perubahan dokumen ini, bukan keputusan agent.

- Satu keluarga saja. Ketebalan garis seragam (bawaan Lucide, `stroke-width` 2) dan ukuran seragam: `size-4` (16 px) di dalam tombol atau teks, `size-5` (20 px) pada tombol ikon, `size-6` (24 px) atau lebih untuk ilustrasi keadaan kosong.
- Warna ikon mengikuti teks di sekitarnya (`currentColor`, otomatis di Lucide). TIDAK BOLEH memberi warna ikon dengan HEX atau nilai arbitrer; pemakaian warna mengikuti tabel Pemakaian.
- Ikon tidak pernah menjadi satu-satunya penanda. Tombol, lencana, dan status tetap memuat teks. Ikon di samping teks bersifat dekoratif (`aria-hidden="true"`). Tombol yang hanya berisi ikon (misalnya titik tiga) WAJIB punya nama aksesibel (`aria-label`), dan area sentuhnya minimal 44 px walau gambar ikonnya lebih kecil.
- Ikon tidak boleh menggantikan kata pada aksi yang merusak atau tidak dapat dibatalkan (Hapus Batch, Nonaktifkan): teksnya tetap tertulis, ikon hanya pendamping. Pengecualian yang disetujui: tombol hapus baris pada daftar file terpilih di form unggah jawaban memakai tombol ikon `trash-2` (`size-5`, `min-h-11 min-w-11`, `aria-label` "Hapus {nama file} dari daftar") karena hanya membuang item dari daftar sementara yang belum tersimpan.
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
| Edit | `pencil` | `size-4` | Aksi di Dashboard Hasil Koreksi |
| Ubah Nilai Akhir | `badge-check` | `size-4` | Dashboard Hasil Koreksi |
| Buka menu | `menu` | `size-5` | Bilah atas ponsel (`aria-label` "Buka menu") |
| Tutup menu | `x` | `size-5` | Laci menu (`aria-label` "Tutup menu") |
| Menu aksi | `ellipsis-vertical` | `size-5` | Titik tiga (`aria-label` berisi nama batch) |
| Coba Lagi | `rotate-ccw` | `size-4` | File yang Gagal |
| Kembali | `arrow-left` | `size-4` | Tautan "Batch Koreksi", "Kembali ke beranda" (Masuk, Daftar), "Kembali ke Masuk" (Lupa Password) |
| Unggah | `upload` | `size-4` | "Upload Jawaban Peserta Didik" |
| Tambah | `plus` | `size-4` | "Tambah Soal", "Tambah File" |
| Ekspor | `download` | `size-4` | "Ekspor Rekap Nilai" |
| Hapus | `trash-2` | `size-4` (`size-5` pada tombol ikon hapus baris) | "Hapus Batch", hapus baris daftar file terpilih (`aria-label` "Hapus {nama file} dari daftar") |
| Keluar | `log-out` | `size-4` | "Keluar" |
| Memuat, Diproses | `loader-circle` + `animate-spin motion-reduce:animate-none` | `size-4` (`size-3.5` di dalam lencana) | Indikator. SEMUA spinner memakai `motion-reduce:animate-none` (berlaku saat implementasi, juga untuk berkas mockup lama yang belum memilikinya) |
| Galat | `circle-alert` | `size-4` | Pesan galat |
| Tampilkan/Sembunyikan password | `eye` / `eye-off` | `size-5` | Tombol di kolom Password (`KolomPassword`), `aria-label` berganti "Tampilkan password"/"Sembunyikan password" |
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
| Muat ulang | `refresh-cw` (`+ animate-spin motion-reduce:animate-none` saat memuat ulang) | `size-4` | Tombol "Muat ulang" di Dashboard Pantauan |
| Kelola akun Pengajar | `arrow-right` | `size-4` | Tautan "Kelola akun Pengajar" di Dashboard Pantauan |
| Ya (tersedia) | `check` | `size-4` | Tabel Free dan Pro, selalu berdampingan dengan teks "Ya" |
| Tidak (tidak tersedia) | `x` | `size-4` | Tabel Free dan Pro, selalu berdampingan dengan teks "Tidak" (`x` juga dipakai untuk "Tutup menu", maknanya ditentukan teks di sampingnya atau `aria-label`) |
| Cari | `search` | `size-4` | Kolom pencarian Akun Pengajar |
| Kolom Nama | `user` | `size-4` | Ikon kiri di dalam `KolomIsian` Nama (Daftar) |
| Kolom Email | `mail` | `size-4` | Ikon kiri di dalam `KolomIsian` Email (Masuk, Daftar, Lupa Password) |
| Kolom Password | `lock` | `size-4` | Ikon kiri di dalam `KolomPassword` (Masuk, Daftar, Atur Ulang Password) |
| Halaman tidak ditemukan / keadaan kosong | `search-x` | `size-6` | Halaman 404 (`size-6` adalah ukuran baru untuk ilustrasi keadaan kosong pada halaman 404) |

### Catatan

- Di aplikasi, titik henti memakai varian viewport Tailwind: `lg:` (mulai 1024 px) dan `max-lg:` (di bawah 1024 px). JANGAN memakai `@container`, `@min-[64rem]`, atau `@max-[63.9375rem]` dari berkas mockup: itu hanya akal agar bingkai pratinjau 375 px bisa tampil di layar 1280 px (di Tailwind v4, `@lg` pada container query berarti 32rem, bukan 1024 px).
- Status Aktif batch di ponsel sejajar dengan nama batch (`items-start`, `min-w-0` pada judul).
- Dialog memakai elemen `<dialog>` bawaan.
- Dialog konfirmasi tampil di tengah layar.
- Kartu fitur Pemasaran: `rounded-xl p-5 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-lg`, dengan pelindung gerak `motion-reduce:transition-none motion-reduce:hover:translate-y-0`. Garis aksen dekoratif di tepi atas kartu memakai `merek-hijau` atau `merek-biru` (bergantian), `aria-hidden`.
- Kartu angka Dashboard Pantauan: `grid-cols-2` di ponsel dan tablet; di desktop tiga atau empat kolom menurut jumlah kartu per kelompok (Akun 3, Aktivitas 4). Kuota API berupa satu kartu lebar penuh dengan bilah pemakaian. Kartu ganjil yang menggantung di ponsel dibuat lebar penuh (`col-span-2`).
- Format angka, persentase, dan jam: angka memakai lokal Indonesia (`id-ID`, pemisah ribuan titik dan desimal koma, mis. `1.500`). Persentase memakai desimal koma dengan maksimal 1 angka di belakang koma (dibulatkan ke bawah satu desimal sehingga `100%` hanya tampil bila memang penuh, dan nol di belakang koma dibuang: mis. `12,1%`, `50%`, `0%`, `100%`). Jam memakai format 24 jam dua digit dengan pemisah titik (`HH.MM`, mis. `17.32`).
- Pilihan paket di Langganan berupa grup radio. Saat diimplementasi, bungkus dengan `fieldset` dan `legend` (teks "Paket Pro") agar pembaca layar mengenal grupnya.
- Dialog "Ubah Langganan": kolom "Masa berlaku" hanya perlu diisi bila status Pro dipilih.

## Inventaris halaman

Daftar halaman target sistem penuh, sumber kebutuhan di `docs/SPEC.md` bagian 9. Rute adalah rute target; mengubah rute yang sudah ada hanya dilakukan oleh tugas refactor tampilan yang memintanya. "Rancangan" adalah status rancangan tampilan per halaman (tata letak, komponen, keadaan) yang ditulis di bagian "Rancangan halaman" sebelum halaman itu dikerjakan.

| # | Halaman | Rute | Peran | FR dan UC | Isi utama | Status fitur | Rancangan |
|---|---|---|---|---|---|---|---|
| 1 | Pemasaran | `/` | Publik (yang sudah login dialihkan ke Beranda atau Dashboard Pantauan) | FR28 | Penjelasan fitur, cara kerja, perbedaan Free dan Pro, tautan Daftar dan Masuk | Selesai | Ada |
| 2 | Daftar | `/daftar` | Publik | FR1 | Form nama, email, password | Selesai | Ada |
| 3 | Masuk | `/masuk` | Publik | FR1 | Form email dan password; pesan "Akun berhasil dibuat, silakan masuk" dan "Sesi berakhir, silakan masuk kembali." | Selesai | Ada |
| 4 | Beranda | `/beranda` | Pengajar | FR2, FR3, FR21, FR22, FR23, UC-01, UC-02, UC-03, UC-13, UC-14 | Sapaan, label FREE atau PRO, ringkasan, daftar batch dengan lencana status dan menu aksi (Selesaikan Batch, Hapus Batch), "Buat Batch Baru" | Sebagian selesai | Ada |
| 5 | Halaman Batch | `/batch/:id_batch` | Pengajar | FR4 sampai FR11, FR14 sampai FR17, FR23 | Judul batch, status batch, dua tab: Soal dan Jawaban, dan Dashboard Hasil Koreksi. Aksi: Selesaikan Batch, Ekspor Rekap Nilai, Hapus Batch | Selesai | Ada |
| 6 | Langganan | `/langganan` | Pengajar | FR2, FR19, FR20, UC-10, UC-11 | Status langganan dan masa berlaku, paket Pro, "Upgrade ke Pro", status transaksi | Selesai | Ada |
| 7 | Dashboard Pantauan | `/admin` | Admin | FR27, UC-18 | Angka jumlah akun (total, Free, Pro), jumlah batch, file jawaban per status, pemakaian kuota API harian | Selesai | Ada |
| 8 | Akun Pengajar | `/admin/akun-pengajar` | Admin | FR24 sampai FR26, UC-15 sampai UC-17 | Tabel akun, cari, filter, "Ubah Langganan", "Nonaktifkan" atau "Aktifkan" | Selesai | Ada |
| 9 | Lupa Password | `/lupa-password` | Publik | FR1 | Form email, tombol "Kirim Tautan" (hitung mundur 60 detik "Kirim ulang dalam N detik"), pesan sukses dengan `{email}` dan masa berlaku 30 menit | Selesai | Ada |
| 10 | Atur Ulang Password | `/atur-ulang-password` | Publik (lewat tautan email) | FR1 | Form password baru dan konfirmasi, tombol "Simpan Password", pesan token tidak berlaku | Selesai | Ada |
| 11 | Halaman 404 | `/*` (catch-all, semua rute tak dikenali) | Publik (semua peran; tombol kembali menyesuaikan) | – | Judul "Halaman tidak ditemukan", satu kalimat penjelas, ikon Lucide `search-x`, tombol kembali menurut peran | Rancangan | Ada |

Halaman 9 dan 10 mengikuti SPEC F-RESET. Halaman Masuk mendapat tautan "Lupa password?". Setelah Keluar, pengguna dialihkan ke Halaman Pemasaran (SPEC bagian 6).

Isi Halaman Batch (dua tab):
- Soal dan Jawaban, dua seksi: "Soal dan Kunci Jawaban" (daftar soal, "Tambah Soal", form kunci) dan "Jawaban Peserta Didik" (tombol "Upload Jawaban Peserta Didik", form unggah, lalu daftar semua file jawaban dengan nama, lencana status, dan pesan error untuk yang Gagal).
- Dashboard Hasil Koreksi: pilihan soal, tabel hasil.
- Tidak ada tab Status Pemrosesan. Status tiap file hanya tampil di daftar file jawaban.

## Komponen bersama

Komponen yang dipakai lebih dari satu halaman. Satu definisi per komponen di `frontend/src/components/`.

| Komponen | Dipakai di | Aturan |
|---|---|---|
| Bilah atas | Semua halaman, kecuali halaman kartu publik (Masuk, Daftar, Lupa Password, Atur Ulang Password) yang tampil tanpa bilah atas | Tiga varian. Publik: logo, "Masuk", "Daftar" (di Pemasaran ditambah tiga tautan jangkar, lihat rancangan Pemasaran). Pengajar: logo, menu "Beranda" dan "Langganan", label FREE atau PRO, nama, "Keluar". Menu yang sedang dibuka bertanda `aria-current="page"`; "Beranda" tetap menyala di Halaman Batch. Admin: logo, menu "Dashboard Pantauan" dan "Akun Pengajar", "Keluar" (tanpa nama pengguna). Mulai 1024 px menu tampil sebagai bilah horizontal. Di bawah 1024 px (tablet dan ponsel) tombol menu (`aria-label` "Buka menu") ditempatkan di paling kiri sebelum logo dan nama "Koreksi-in", lalu menu berpindah ke laci dari kiri yang dibuka tombol tersebut (tombol tutup "Tutup menu"), berisi item menu, label FREE atau PRO, nama, dan "Keluar" |
| Lencana | Status pemrosesan, kategori, FREE atau PRO, status aktif akun | Selalu berisi teks, memakai token di bagian Pemakaian |
| Dialog konfirmasi | Hapus batch, selesaikan batch, nonaktifkan atau aktifkan akun, ganti kunci jawaban, batalkan pilihan file, tinggalkan halaman unggah | Judul singkat ("Hapus Batch", "Selesaikan Batch", "Nonaktifkan Akun", "Aktifkan Akun", "Ganti Kunci Jawaban", "Batalkan Pilihan File", "Tinggalkan Halaman"), satu kalimat persis dari SPEC, dua tombol. Hapus, selesaikan, nonaktifkan, dan aktifkan: "Ya" dan "Batal". Batalkan pilihan file ("Semua file terpilih dan nama peserta didik yang sudah diisi akan dibuang. Lanjutkan?"): "Kembali" dan "Ya". Tinggalkan halaman: "Tetap di Halaman" dan "Tinggalkan". Tombol utama memakai `bg-biru-utama`; aksi merusak tidak memakai warna merah polos tanpa teks |
| Kartu angka | Ringkasan Pengajar, Dashboard Pantauan | Angka besar dan label teks (komponen `KartuAngka`). Nilai 0 tetap tampil. Angka di kartu selalu rata bawah (`mt-auto`) agar kartu tetap sejajar walau labelnya satu atau dua baris di lebar ponsel. |
| Tabel | Hasil koreksi, Akun Pengajar | Aturan di bagian Tata letak |
| Menu aksi (titik tiga) | Baris daftar batch di Beranda | Tombol ikon titik tiga yang membuka daftar aksi kecil. Punya nama aksesibel, dapat dioperasikan dengan papan ketik (Enter, Esc, panah), tertutup saat klik di luar. Aksi yang merusak berteks `text-kurang-mirip` dan membuka dialog konfirmasi |
| Keadaan data | Semua data yang dimuat | Tiga keadaan: memuat (indikator), kosong (teks dari SPEC), gagal (teks dari SPEC) |
| Pesan sukses dan galat | Semua form | Sukses singkat ("Kunci jawaban tersimpan."), galat memakai `text-kurang-mirip` |
| Kolom isian | Daftar, Masuk, Lupa Password, Atur Ulang Password | Label, input (`placeholder:text-teks-redup` agar kontras placeholder minimal 4,5 : 1), ikon kiri opsional (`size-4 text-teks-redup`, `aria-hidden="true"`, memberi ruang kiri `pl-9` pada input), petunjuk opsional, dan galat opsional tampil tepat di bawah kolom (`KolomIsian`). Varian password (`KolomPassword`) dapat memakai ikon kiri opsional (mis. `lock`) dan menambah tombol tampilkan/sembunyikan password di sisi kanan dalam kolom (`pr-11`), tanpa mengubah label atau posisi petunjuk/galat |

## Tata letak

- Bilah atas: ikon logo, nama "Koreksi-in", dan isi menurut peran (lihat Komponen bersama). Di bawah 1024 px, tombol menu diletakkan di paling kiri sebelum logo.
- Halaman kartu publik (Masuk, Daftar, Lupa Password, Atur Ulang Password): kartu di tengah dengan `logo.png` di atasnya, tanpa bilah atas.
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
- Tombol aksi utama memakai `bg-biru-utama`. Tombol sekunder memakai garis `border-garis` dengan teks `text-teks`. Aksi yang merusak data tersimpan (hapus batch, nonaktifkan akun) memakai tombol sekunder dengan teks `text-kurang-mirip` dan SELALU lewat dialog konfirmasi. Pengecualian yang disetujui: menghapus satu baris dari daftar file terpilih yang belum terkirim di form unggah jawaban langsung menghapus baris tanpa dialog konfirmasi (tidak merusak data tersimpan), sedangkan tombol "Batal" untuk membuang seluruh daftar memakai dialog konfirmasi "Batalkan Pilihan File".

### 1. Pemasaran (`/`)

Tujuan: pengunjung yang belum login memahami apa itu Koreksi-in dan terdorong mendaftar. Pengunjung yang sudah login dialihkan ke Beranda (Pengajar) atau Dashboard Pantauan (Admin). Bilah atas varian Publik.

Bilah atas Pemasaran menempel di atas layar saat halaman digulir (`sticky top-0`), dan diberi bayangan tipis (`shadow-sm`) hanya saat halaman sudah digulir. Mulai 1024 px, di tengah bilah ada tiga tautan jangkar: "Cara kerja", "Fitur utama", "Free dan Pro" (teksnya sama dengan judul seksi, tanpa teks baru). Mengklik tautan menggulir halaman ke seksi itu, dan judul seksi tidak boleh tertutup bilah (`scroll-mt-24`). Membuka alamat dengan hash langsung (misalnya `/#fitur-utama`) juga menggulir ke seksi yang dituju. Gulir halus dimatikan bagi pengguna yang memilih gerak berkurang (`prefers-reduced-motion: reduce`). Keadaan tautan jangkar: normal (`text-teks`), hover (`hover:bg-biru-muda hover:text-biru-utama`), fokus papan ketik (`focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama`), dan seksi aktif yang sedang terlihat bertanda `aria-current="true"` (`aria-[current=true]:bg-biru-muda aria-[current=true]:text-biru-utama`, atribut dihapus pada tautan lain). Di bawah 1024 px tautan jangkar tidak ditampilkan; bilah hanya berisi logo, "Masuk", dan "Daftar".

Latar seksi berselang-seling antara `bg-latar` dan `bg-permukaan`, ditutup pita `bg-biru-utama`. Blok dari atas ke bawah:
1. **Hero (`bg-latar`).** Dua kolom di desktop (`lg:grid-cols-2`), satu kolom di bawah 1024 px dengan ilustrasi di bawah teks. Kolom kiri: judul (didahului garis aksen pendek `h-1 w-16 rounded-full bg-merek-hijau`, `aria-hidden`; satu-satunya halaman yang memakainya, halaman aplikasi tidak), satu kalimat penjelas, tombol utama "Daftar" ke `/daftar`, dan tautan "Masuk" ke `/masuk`. Judul: "Koreksi esai lebih cepat, nilai akhir tetap di tangan Anda"; kalimat: "Unggah lembar jawaban peserta didik. Koreksi-in membaca tulisan tangan dan memberi skor kemiripan sebagai rekomendasi." Kolom kanan: ilustrasi dekoratif berupa HTML (`aria-hidden="true"`, bukan gambar, dengan garis aksen `bg-merek-hijau` di tepi atas kartu) yang menampilkan contoh tabel "Dashboard Hasil Koreksi" (kolom "Peserta Didik", "Skor Kemiripan", "Kategori Kualitatif") dengan tiga baris fiktif: Andi Pratama (92, Sangat Mirip), Budi Hartono (74, Cukup Mirip), dan Citra Dewi (32, Kurang Mirip) (usulan angka 32, sesuai ambang skor di bawah 40 di SPEC baris 178), tanpa teks tambahan yang menyebut akurasi.
2. **Cara kerja (`bg-permukaan`).** Empat langkah bernomor dalam `<ol>` yang berjajar empat kolom di desktop (`lg:grid-cols-4`, lingkaran nomor di tengah atas teks) dan tersusun vertikal di bawah 1024 px dengan garis penghubung vertikal `bg-merek-hijau` antar lingkaran nomor (`border-merek-hijau text-biru-utama`): (1) Buat batch dan ketik kunci jawaban. (2) Unggah lembar jawaban berupa foto atau PDF, beserta nama peserta didik. (3) Sistem membaca tulisan dan memberi skor kemiripan. (4) Tinjau hasil, koreksi nilai bila perlu, lalu ekspor (akun Pro).
3. **Fitur utama (`bg-latar`).** Empat kartu kecil (`md:grid-cols-2 lg:grid-cols-4`): "Membaca tulisan tangan" ("Lembar jawaban foto atau PDF dibaca menjadi teks."), "Skor kemiripan dan kategori" (lencana Sangat Mirip, Cukup Mirip, Kurang Mirip; "Skor sebagai rekomendasi, bukan nilai akhir."), "Koreksi manual" ("Edit teks hasil baca dan nilai akhir."), "Ekspor rekap nilai" (lencana Pro; "Unduh rekap nilai dalam file .xlsx.").
4. **Free dan Pro (`bg-permukaan`).** Tabel perbandingan dua kolom (tetap tabel di semua lebar, tanpa gulir horizontal; pengecualian dari aturan tabel menjadi kartu):

| | Free | Pro |
|---|---|---|
| Batch aktif | 1 | Tidak dibatasi |
| Soal per batch | 15 | 30 |
| Jawaban peserta didik per batch | 15 | 50 |
| Ekspor rekap nilai | Tidak | Ya |
| Harga | Gratis | Rp 30.000 (1 bulan), Rp 80.000 (3 bulan) |

   Header kolom pertama kosong secara visual, tetapi harus berisi teks `sr-only` "Fitur" (bukan sel `th` kosong) agar pembaca layar mengenal kolomnya. Di bawah tabel, satu kalimat kecil: "Langganan Pro tidak diperpanjang otomatis."
5. **Penutup (`bg-biru-utama`).** Pita biru penuh di bagian bawah halaman berisi ajakan "Siap mulai mengoreksi lebih cepat?" (`text-permukaan`) dan tombol "Daftar" (`bg-permukaan text-biru-utama`) ke `/daftar`.

Keadaan: halaman statis, tanpa pemuatan data. Penegasan isi: skor selalu disebut rekomendasi, sistem tidak mengeluarkan nilai huruf, dan tidak ada klaim akurasi berupa angka.

### 2. Daftar (`/daftar`)

Kartu di tengah dengan `logo.png`, judul "Daftar" (TANPA label kecil di atas judul), dan deskripsi tepat di bawah judul (`text-sm leading-5 text-teks-redup`): "Buat akun Pengajar untuk mulai mengoreksi jawaban esai." Pengguna yang sudah login dialihkan ke Beranda. Pojok kiri atas kartu (sebelum logo): tautan "Kembali ke beranda" (ikon `arrow-left` `size-4`, `aria-hidden="true"`, ke `/`).

- Kolom (`KolomIsian`/`KolomPassword`, lihat Komponen bersama):
  - Nama: ikon kiri `user` (`size-4`, `aria-hidden="true"`), placeholder "Nama lengkap".
  - Email: ikon kiri `mail` (`size-4`, `aria-hidden="true"`), placeholder "nama@email.com".
  - Password: ikon kiri `lock` (`size-4`, `aria-hidden="true"`), tombol tampilkan/sembunyikan di kanan, placeholder "Buat password", dan petunjuk kecil tetap di bawah kolom: "Minimal 8 karakter."
  - Placeholder memakai `placeholder:text-teks-redup` (kontras 7,58 : 1 di atas `bg-permukaan`, memenuhi 4,5 : 1) dan tidak menggantikan label maupun petunjuk di bawah kolom.
- Tombol "Daftar" (indikator putar selama mengirim, tombol nonaktif). Di bawah kartu: "Sudah punya akun? Masuk".
- Galat tampil tepat di bawah kolomnya masing-masing, bukan di atas form: "Nama wajib diisi.", "Nama maksimal 100 karakter.", "Email wajib diisi.", "Email maksimal 255 karakter.", "Format email tidak valid. Contoh: nama@email.com.", "Password wajib diisi.", "Password minimal 8 karakter" (dicek juga di klien sebelum mengirim), "Password maksimal 72 karakter", "Email sudah terdaftar". Batas panjang Nama (100) dan Email (255) dihitung dari nilai mentah (belum di-trim) per code point Unicode, sama seperti batas backend. Mengetik di suatu kolom membersihkan galat kolom itu. Kirim gagal karena validasi memindahkan fokus ke kolom bermasalah pertama (urutan Nama, Email, Password). Banner di atas form (`role="alert"`, `text-kurang-mirip`) hanya dipakai untuk galat yang tidak bisa diatribusikan ke satu kolom.
- Sukses: arahkan ke `/masuk` dengan pesan "Akun berhasil dibuat, silakan masuk". Tidak ada sesi yang dibuat.
- Aturan format email (dicek dengan pola yang sama persis seperti backend, menolak titik ganda/berurutan seperti "nama@email..com") berlaku di sini maupun di Masuk dan Lupa Password, karena ketiganya memakai satu `REGEX_EMAIL` bersama di `lib/validasi.js`.

### 3. Masuk (`/masuk`)

Kartu di tengah dengan `logo.png`, judul "Masuk" (TANPA label kecil di atas judul), dan deskripsi tepat di bawah judul (`text-sm leading-5 text-teks-redup`): "Masuk untuk membuat batch koreksi dan melihat hasilnya." Pengguna yang sudah login dialihkan menurut peran. Pojok kiri atas kartu (sebelum logo): tautan "Kembali ke beranda" (ikon `arrow-left` `size-4`, `aria-hidden="true"`, ke `/`).

- Kolom (`KolomIsian`/`KolomPassword`, lihat Komponen bersama):
  - Email: ikon kiri `mail` (`size-4`, `aria-hidden="true"`), placeholder "nama@email.com".
  - Password: ikon kiri `lock` (`size-4`, `aria-hidden="true"`), tombol tampilkan/sembunyikan di kanan, placeholder "Masukkan password".
  - Placeholder memakai `placeholder:text-teks-redup` (kontras >= 4,5 : 1) dan tidak menggantikan label.
- Tombol "Masuk" (indikator putar). Di bawah kartu: tautan "Belum punya akun? Daftar".
- Tautan "Lupa password?" ke `/lupa-password`, rata kanan tepat di bawah kolom Password dan di atas tombol "Masuk".
- Galat kolom kosong/format: "Email wajib diisi.", "Format email tidak valid. Contoh: nama@email.com.", "Password wajib diisi.", tampil tepat di bawah kolomnya, memindahkan fokus ke kolom bermasalah pertama (Email lalu Password), dan hilang saat kolom itu diketik ulang. Kredensial salah (`LOGIN_GAGAL`) sengaja TIDAK diatribusikan ke satu kolom (agar tidak membocorkan apakah email atau password yang salah): kedua kolom diberi tanda tidak valid (garis merah) tanpa teks di bawahnya, dan pesannya hanya tampil sebagai banner di atas form.
- Pesan di atas form, satu pesan sekali tampil: galat "Email atau password salah" (`LOGIN_GAGAL`), sukses "Akun berhasil dibuat, silakan masuk" (gaya sukses), "Password berhasil diubah, silakan masuk." (gaya sukses), "Sesi berakhir, silakan masuk kembali." (gaya netral, bukan galat).
- Galat: "Email atau password salah" untuk semua kegagalan login, termasuk email tidak terdaftar (SPEC bagian 6).
- Sukses: Pengajar ke `/beranda`, Admin ke `/admin`.

### 4. Beranda (`/beranda`, Pengajar)

Blok dari atas ke bawah:
1. **Sapaan.** "Selamat datang, {nama}" dan "Kelola batch koreksi esai Anda di sini."
2. **Ringkasan (FR21).** Deret kartu angka (`KartuAngka`): jumlah total batch, jumlah peserta didik yang sudah dikoreksi, dan khusus akun Free: sisa slot batch aktif serta sisa slot jawaban per batch (ditentukan backend lewat field `null`/bukan-`null`, bukan dari label FREE/PRO di bilah atas). Nilai 0 tetap tampil. Label kartu (disetujui): "Total batch", "Peserta didik sudah dikoreksi", "Sisa slot batch aktif", "Sisa slot jawaban per batch". Dimuat bersamaan dengan daftar batch tapi dengan keadaan memuat/gagal sendiri, dan hanya dirender setelah daftar batch sendiri selesai termuat (indikator memuat halaman penuh dulu, baru ringkasan). Dimuat ulang setelah "Selesaikan Batch" sukses, "Hapus Batch" sukses, atau batch ternyata sudah Selesai, tanpa mengosongkan kartu yang sedang tampil selama pemuatan ulang (nilai diganti diam-diam begitu respons baru tiba). Gagal: "Gagal memuat ringkasan, coba muat ulang halaman".
3. **Banner upgrade (nanti).** Tampil untuk akun Free yang baru turun dari Pro atau yang datanya melewati batas Free. Teks usulan: "Masa berlaku Pro Anda telah berakhir. Upgrade ke Pro untuk membuat batch baru dan memakai semua fitur." dengan tautan ke `/langganan`.
4. **Kepala daftar.** Judul "Batch Koreksi" dan tombol utama "Buat Batch Baru".
5. **Form buat batch.** Terbuka di tempat saat tombol ditekan. Kolom "Nama Batch" (maksimal 100 karakter), tombol "Buat" dan tombol sekunder "Batal" di sampingnya. Form bisa ditutup dua cara: lewat "Batal" atau menekan lagi "Buat Batch Baru"; keduanya memakai satu fungsi reset yang sama yang mengosongkan Nama Batch dan pesan galat, sehingga form selalu bersih saat dibuka lagi. "Batal" mengembalikan fokus ke tombol "Buat Batch Baru"; penutupan lewat toggle tidak memindahkan fokus karena sudah berada di tombol itu. Saat permintaan membuat batch berjalan, "Batal" memakai `aria-disabled` (bukan `disabled`, supaya fokus tidak hilang) dan mengabaikan klik. Galat: "Nama batch tidak boleh kosong.", "Gagal membuat batch, silakan coba lagi". Penolakan batas batch aktif untuk akun Free yang sudah punya 1 batch aktif (FR18): "Batas batch aktif untuk akun Free telah tercapai. Upgrade ke Pro untuk batch tidak terbatas." dengan frasa "Upgrade ke Pro" berupa tautan ke `/langganan`; tombol "Buat Batch Baru" tetap bisa ditekan dan pesan ini muncul sebagai penolakan, bukan tersembunyi.
6. **Daftar batch.** Satu baris per batch, terbaru di atas: nama batch (tautan ke Halaman Batch), tanggal dibuat, lencana status "Aktif" atau "Selesai", dan di ujung kanan tombol menu aksi bergambar titik tiga sehingga Pengajar tidak perlu membuka batch dulu. Menu berisi "Selesaikan Batch" (hanya untuk batch Aktif) dan "Hapus Batch". Aksinya sama dengan di Halaman Batch (lihat "Perilaku tombol aksi di kepala"): "Selesaikan Batch" memunculkan dialog "Batch yang diselesaikan tidak dapat diubah lagi. Lanjutkan?" ("Ya", "Batal"), atau pesan "Tunggu hingga semua file selesai diproses." bila masih ada file Diproses; "Hapus Batch" memunculkan dialog "Batch ini beserta seluruh data koreksi akan dihapus permanen dan tidak dapat dikembalikan. Lanjutkan?" ("Ya", "Batal"). Sukses: "Selesaikan Batch" menampilkan pesan "Batch berhasil diselesaikan." dan baris diperbarui (lencana jadi Selesai); "Hapus Batch" membuat baris hilang dari daftar tanpa pesan. Gagal: "Gagal menyelesaikan batch, silakan coba lagi" atau "Gagal menghapus batch, silakan coba lagi". Tombol titik tiga HARUS punya nama aksesibel (usulan: "Aksi untuk batch {nama batch}"), dapat dipakai lewat papan ketik, dan klik pada tombol ini TIDAK membuka batch. Kosong: "Belum ada batch. Buat batch pertama untuk mulai mengoreksi." Gagal memuat: pesan galat dari server dengan teks Indonesia.

Label FREE atau PRO ada di bilah atas. Gagal memuat: "Gagal memuat status langganan, coba muat ulang halaman".

### 5. Halaman Batch (`/batch/:id_batch`, Pengajar)

Sketsa (desktop):

```
[Bilah atas]
< Batch Koreksi
Nama Batch  [Aktif]
[Selesaikan Batch] [Ekspor Rekap Nilai] [Hapus Batch]  <- baris tombol di bawah judul
-------------------------------------------------------------------------------------------------
 Soal dan Jawaban | Dashboard Hasil Koreksi
-------------------------------------------------------------------------------------------------
 (isi tab)
```

Kepala halaman (diubah sesuai mockup halaman-batch, disetujui pemilik proyek 2026-11-02): tautan "Batch Koreksi" (kembali ke Beranda), nama batch sebagai judul dengan lencana status batch (Aktif atau Selesai) di sampingnya, dan baris tombol aksi di bawah judul pada semua lebar: "Selesaikan Batch" (hanya batch Aktif), "Ekspor Rekap Nilai" (FR17; hanya ada di Halaman Batch, tampil untuk Aktif maupun Selesai serta Pro maupun Free), dan "Hapus Batch". "Selesaikan Batch" dan "Hapus Batch" juga tersedia dari menu titik tiga di daftar Beranda. Selama pemeriksaan file Diproses, request, ekspor, atau unggahan sedang berjalan, tombol-tombol aksi memakai `aria-disabled` (bukan `disabled`, supaya fokus tidak hilang) dan mengabaikan klik. Pesan galat atau sukses aksi tampil sebagai kotak di bagian bawah kepala dan terlihat di kedua tab. Keadaan memuat dan gagal untuk seluruh halaman: indikator di tengah; gagal menampilkan galat dan tautan "Kembali ke Beranda". Batch yang bukan milik pengguna atau tidak ada: "Batch tidak ditemukan".

Dua tab: **Soal dan Jawaban**, **Dashboard Hasil Koreksi**. Tidak ada tab Status Pemrosesan.

#### Tab Soal dan Jawaban

Dua seksi bertumpuk, masing-masing diberi judul dan dipisah jelas.

**Seksi "Soal dan Kunci Jawaban"**
- Daftar soal, urut nomor. Tiap item: "Soal N" dan teks kunci jawaban (baris baru dipertahankan, hanya baca). Kosong: "Belum ada soal pada batch ini."
- Di bawah daftar, tepat satu dari tiga keadaan:
  - tombol "Tambah Soal" (keadaan biasa);
  - pesan netral "Sudah mencapai jumlah maksimal N soal per batch." (batas soal tercapai; N = 15 untuk akun Free dan 30 untuk akun Pro sesuai jenis akun di SPEC bagian 4, FR18);
  - pesan "Soal tidak dapat ditambah setelah jawaban diunggah." (sudah ada lembar jawaban).
- Form tambah soal: label "Soal N: Kunci Jawaban", area teks beberapa baris, tombol "Simpan Kunci Jawaban". Kunci kosong atau hanya spasi: "Kunci jawaban tidak boleh kosong" di bawah kolom, tanpa permintaan terkirim. Sukses: "Kunci jawaban tersimpan." (hilang begitu batch punya lembar jawaban) dan soal masuk ke daftar. Gagal: "Sudah mencapai jumlah maksimal N soal per batch." (N = 15 untuk Free, 30 untuk Pro bila ditolak server karena batas soal), "Gagal menambah soal, silakan coba lagi."
- Di form kunci (FR5-FR7, F-KUNCI-FILE), tepat di atas kolom teks kunci (berdampingan, tidak pindah mode), ada tombol "Upload File" (ikon `upload`, `aria-disabled` + indikator putar `loader-circle` selama OCR berjalan, target sentuh 44 px). Input file sebenarnya disembunyikan (`sr-only`) dan dipicu lewat tombol ini, bukan `<label>`, supaya bisa diberi `aria-disabled` dan spinner seperti tombol "Coba Lagi". Hasil OCR mengisi kolom teks kunci yang sama, dapat diedit, dan fokus berpindah ke kolom itu untuk ditinjau sebelum "Simpan Kunci Jawaban". Kolom teks memakai `readOnly` (bukan `disabled`) selama OCR berjalan, mencegah ketikan manual tertimpa hasil yang datang belakangan. Tombol "Simpan Kunci Jawaban" juga memakai `aria-disabled` selama OCR berjalan (submit diabaikan), supaya tidak menyimpan teks lama tepat saat kolom akan diganti hasil OCR.
  - Jika kolom teks kosong atau hanya spasi saat file dipilih, OCR langsung berjalan tanpa dialog. Jika kolom sudah berisi teks, `DialogKonfirmasi` (komponen bersama) muncul SEBELUM Gemini dipanggil (bukan setelah hasil datang): judul "Ganti Kunci Jawaban" (usulan), isi "Isi kolom akan diganti dengan hasil baca file. Lanjutkan?", tombol "Batal"/"Ya". Urutan ini dipilih agar menekan Batal tidak pernah memboroskan panggilan Gemini yang sudah terkirim (kuota API gratis dan terbatas, lihat CLAUDE.md). Memilih file mengosongkan nilai `<input type="file">` segera (sebelum keputusan dialog), sehingga file yang sama bisa dipilih ulang dan tetap memicu pembacaan.
  - Gagal baca (kuota habis, gangguan sementara, hasil kosong/hanya spasi): "Gagal membaca file, silakan coba lagi atau masukkan teks secara manual", tampil di slot galat yang sama dengan "Kunci jawaban tidak boleh kosong"; kolom teks tidak berubah.
  - File kunci disimpan di state terpisah dari file jawaban, sehingga tidak dihitung oleh dialog "tinggalkan halaman" milik seksi Jawaban Peserta Didik.

**Seksi "Jawaban Peserta Didik"**
- Jika belum ada soal: "Tambahkan minimal satu soal sebelum mengunggah jawaban." dan tombol unggah tidak dirender.
- Keadaan kosong (belum ada file terpilih, batch Aktif):
  - Jika belum ada lembar jawaban yang tersimpan di batch itu: teks kecil "Pastikan semua soal sudah ditambahkan. Setelah jawaban diunggah, soal tidak dapat ditambah lagi."
  - Teks sisa slot: "Sisa {n} slot jawaban untuk batch ini." (`n` dihitung dari batas jawaban jenis akun dikurangi jumlah jawaban yang sudah ada di batch itu).
  - Tombol utama "Upload Jawaban Peserta Didik" (ikon `upload`, memicu `<input type="file" multiple>` tersembunyi `sr-only`, bukan `<label>`).
- Daftar file terpilih (opsi A2, boleh tumbuh sampai sisa slot jawaban batch; duplikat tidak dihapus):
  - Di atas daftar tampil keterangan "Dipilih {n} dari {sisa} slot tersisa."
  - Menambah file lewat tombol "Tambah File" (ikon `plus`, memicu `<input type="file" multiple>` yang sama). Jika jumlah file yang dipilih akan melebihi sisa slot, penambahan ditolak langsung tanpa mengubah daftar dan tampil kotak galat "Tidak bisa menambah file: melebihi sisa slot {n} jawaban untuk batch ini." (`id="galat-slot"`, dihubungkan ke tombol lewat `aria-describedby` hanya saat pesannya tampil).
  - Tiap baris berupa kartu (`rounded-lg border p-4`, `border-kurang-mirip` bila file bermasalah, selain itu `border-garis`) berisi nama berkas (ikon `file` + nama berkas dengan `title`), kolom "Nama peserta didik" (wajib, maksimal 100 karakter), dan tombol hapus baris berikon `trash-2` (`size-5`, `min-h-11 min-w-11 shrink-0`, `aria-label` "Hapus {nama file} dari daftar").
  - Tata letak baris dan urutan fokus papan ketik:
    - Urutan DOM di dalam `<li data-baris>` adalah: (1) blok nama berkas beserta pesan galat baris bila file bermasalah, (2) blok label dan kolom "Nama peserta didik" beserta pesan galat nama bila kosong/terlalu panjang, (3) tombol hapus baris.
    - Ponsel dan tablet (di bawah `lg`, `< 1024 px`): tata letak grid menempatkan tombol hapus di baris atas kartu ujung kanan (`max-lg:col-start-2 max-lg:row-start-1`), sejajar dengan nama berkas di kiri (`min-w-0 flex-1 truncate`). Pesan galat baris (jika file bermasalah) berada di bawah baris atas (`max-lg:col-span-2 max-lg:row-start-2`), di antara baris atas dan kolom nama. Di bawahnya label dan kolom "Nama peserta didik" selebar kartu (`col-span-2`).
    - Desktop (`lg:` ke atas, `>= 1024 px`): tiga kolom (`lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]`): nama berkas (dan pesan galat baris di bawahnya) di kolom kiri, kolom "Nama peserta didik" di kolom tengah, dan tombol hapus di ujung kanan.
    - Urutan fokus papan ketik (`Tab`) pada tiap baris di semua lebar layar mengikuti urutan DOM tanpa duplikasi markup: fokus mengunjungi **input "Nama peserta didik"** terlebih dahulu, lalu **tombol hapus baris** ("Hapus {nama file} dari daftar").
  - Hapus baris langsung membuang baris dari daftar TANPA dialog konfirmasi (pengecualian yang disetujui: belum tersimpan di server). Tombol "Batal" membuka `DialogKonfirmasi` dengan judul "Batalkan Pilihan File", isi "Semua file terpilih dan nama peserta didik yang sudah diisi akan dibuang. Lanjutkan?", tombol "Kembali" dan "Ya".
  - Pemeriksaan di browser sebelum mengirim (tanpa memanggil API): ukuran maksimal 10 MB ("Ukuran file maksimal 10 MB.") dan signature byte (`%PDF-`, PNG, JPEG; bila tidak sesuai termasuk berkas 0 byte ditandai bermasalah dengan "Format file tidak didukung. Gunakan PDF, PNG, atau JPG."), serta saat menekan "Mulai Penilaian" memeriksa nama peserta didik terisi setelah trim ("Nama peserta didik wajib untuk semua file", maksimal 100 karakter "Nama peserta didik maksimal 100 karakter."). Jika pembacaan `slice` byte di browser gagal, pemeriksaan signature di browser dilewati dan diserahkan ke server. Jumlah halaman PDF diperiksa di server.
  - Baris bermasalah HARUS dihapus terlebih dahulu: selama ada baris bermasalah, tombol "Mulai Penilaian" memakai `aria-disabled="true"` dan menampilkan kotak galat "Hapus file yang bermasalah sebelum memulai penilaian." (`id="galat-bermasalah"`, `aria-describedby` hanya dipasang pada "Mulai Penilaian" saat pesannya tampil).
  - Pengiriman ("Mulai Penilaian"): mengirim daftar secara berurutan per 10 file (urutan daftar) ke endpoint yang sama. Selama berjalan, semua tombol ("Mulai Penilaian", "Tambah File", "Batal", semua tombol hapus baris, serta tombol aksi di kepala halaman) dan kolom input nama memakai `aria-disabled="true"` (`readOnly` pada input teks agar fokus tidak hilang), dan tampil kartu status kemajuan dengan spinner, teks "Mengirim {k} dari {n} file.", serta `role="progressbar"`. Jika satu kiriman gagal: pengiriman berhenti, kiriman sebelumnya yang sudah berhasil tetap tersimpan dan baris-barisnya keluar dari daftar, sedangkan sisanya tetap di daftar. Jika sudah ada kiriman yang tersimpan sebelum gagal, tampilkan pesan "{a} file sudah tersimpan. {b} file belum terkirim, silakan coba lagi." Jika respons galat memuat `file_bermasalah`, petakan indeks relatif kiriman ke baris di daftar dan tandai baris tersebut bermasalah dengan pesan sesuai kodenya ("PDF maksimal 15 halaman.", "File PDF rusak atau tidak dapat dibaca.", dll.); selain itu tampilkan pesan galat umum (termasuk "Upload ditolak: ..." untuk batas jawaban akun).
  - Manajemen fokus: setelah satu baris dihapus, fokus pindah ke tombol hapus baris berikutnya (atau ke "Tambah File" bila baris paling bawah dihapus dan daftar masih ada, atau ke "Upload Jawaban Peserta Didik" bila daftar habis); setelah semua kiriman sukses atau pilihan dibatalkan lewat dialog "Batal", fokus pindah ke "Upload Jawaban Peserta Didik"; setelah pesan galat tampil, fokus pindah ke pesan galat tersebut.
- Daftar jawaban yang sudah diunggah (tabel ringkas, urut waktu unggah): kolom Peserta Didik dan Status (lencana Diproses, Selesai, Gagal sesuai bagian Pemakaian). Untuk Gagal, `pesan_error` tampil di bawah nama. Daftar diperbarui sendiri tiap 5 detik selama ada file Diproses (tanpa kedipan atau lompatan tata letak). Gagal memuat: "Gagal memuat status pemrosesan, coba muat ulang halaman". Kosong: tidak ada teks khusus, seksi hanya menampilkan tombol unggah.
- Kolom Aksi (hanya saat batch Aktif, FR11): tombol "Coba Lagi" (ikon `rotate-ccw`, nama aksesibel "Coba Lagi untuk {nama peserta didik}") hanya untuk baris berstatus Gagal, mengirim ulang file itu sendiri ke OCR. Setelah diklik, baris berpindah ke status Diproses dan tombol tidak dirender lagi (polling 5 detik di atas mengambil alih sampai Selesai atau Gagal lagi). Selama permintaan berjalan: `aria-disabled` dan indikator putar pada tombol, fokus tidak hilang. Gagal diminta: pesan galat tampil di bawah tombol. Fokus dipindah ke lencana Status baris itu begitu tombol hilang karena baris tidak lagi Gagal, supaya tidak jatuh ke tubuh halaman.
- Konfirmasi meninggalkan halaman: jika ada file terpilih yang belum diunggah, meninggalkan Halaman Batch (kembali, pindah halaman, tutup tab) memunculkan dialog "Ada file yang belum diunggah. Yakin ingin meninggalkan halaman ini?" dengan tombol "Tetap di Halaman" dan "Tinggalkan". Tanpa file terpilih, tidak ada dialog.

#### Tab Dashboard Hasil Koreksi

- Pilihan soal di atas tabel: dropdown berisi "Soal 1", "Soal 2", dan seterusnya (hingga 30). Soal pertama terpilih awal. Jika batch belum punya soal, dropdown tidak dirender dan pesan kosong tetap tampil.
- Tabel untuk soal terpilih, satu baris per peserta didik yang file-nya berstatus Selesai. Kolom: Peserta Didik, Teks OCR, Skor Kemiripan (0 sampai 100), Kategori Kualitatif (lencana bernama, bukan hanya warna), Nilai Akhir. Teks OCR panjang dipotong beberapa baris dengan tautan "Tampilkan lengkap"; setelah dibuka, tautan berganti "Tampilkan ringkas" untuk memotongnya kembali (tombol dengan `aria-expanded`). Jawaban tidak ditemukan: "(jawaban tidak ditemukan)".
- Kolom Aksi (hanya saat batch Aktif, FR15): tombol "Edit" (ikon `pencil`, nama aksesibel "Edit jawaban {nama peserta didik}") di tiap baris mengubah sel Teks OCR menjadi area teks beberapa baris berisi teks saat ini, dengan tombol "Simpan" dan "Batal" di bawahnya. Hanya satu baris dan satu mode (Edit teks OCR ATAU Ubah Nilai Akhir, lihat bawah) dapat aktif sekaligus: tombol Edit baris lain, dan tombol Edit pada baris yang sama saat mode Ubah Nilai Akhir aktif, memakai `aria-disabled`; dropdown Soal di atas tabel memakai `disabled` selama ada baris dalam mode apa pun. Fokus pindah ke area teks saat Edit dibuka; Esc atau "Batal" mengembalikan sel ke tampilan semula dan fokus kembali ke tombol Edit baris itu. Batas 10.000 karakter divalidasi saat Simpan ditekan (bukan membatasi ketikan): lebih dari itu menampilkan "Teks jawaban maksimal 10.000 karakter." tanpa permintaan terkirim. Teks kosong atau hanya spasi: "Teks jawaban tidak boleh kosong" di bawah area teks, juga tanpa permintaan terkirim. Simpan tidak diblokir walau teks tidak berubah. Selama permintaan berjalan, tombol Simpan dan Batal memakai `aria-disabled` (fokus tidak hilang) dan Esc diabaikan, dengan indikator putar pada Simpan. Sukses: sel kembali ke tampilan baca, Skor Kemiripan dan Kategori Kualitatif di baris itu ikut diperbarui, fokus kembali ke tombol Edit. Jika skor belum berhasil dihitung ulang (`skor_hitung_ulang` true): "Teks tersimpan, tetapi skor belum berhasil dihitung ulang. Coba lagi." tampil di bawah Skor Kemiripan/Kategori baris itu selama kondisi itu berlaku, termasuk setelah muat ulang halaman (saat itu tampil sebagai teks biasa, bukan pengumuman, karena bukan hasil aksi yang baru saja terjadi). Berpindah ke tab Soal dan Jawaban saat sedang mengedit membuang draf tanpa peringatan (tab ini lepas dari halaman saat tidak aktif, sama seperti keadaan sementara lain di tab ini).
- Kolom Nilai Akhir (FR16): tampil di setiap baris, baik batch Aktif maupun Selesai (ini data, bukan aksi). Saat `skor_revisi` sudah diisi, nilainya tampil tebal sebagai nilai resmi; Skor Kemiripan di kolomnya sendiri tetap tampil apa adanya sebagai rekomendasi sistem, tidak diganti atau digabung. Saat belum pernah diisi: sel menampilkan tanda "—" (`aria-hidden`) disertai teks `sr-only` "Belum diisi" supaya pembaca layar tetap mengumumkan status eksplisit. Aksi "Ubah Nilai Akhir" (hanya batch Aktif, ikon `badge-check`, nama aksesibel "Ubah Nilai Akhir {nama peserta didik}") ditumpuk vertikal di bawah tombol Edit dalam sel Aksi yang sama (tidak menambah lebar kolom, aman dari scroll horizontal di lebar sempit maupun lebar penuh). Klik membuka form inline di sel Nilai Akhir dengan input angka; nilai awal = Nilai Akhir yang sudah tersimpan, atau Skor Kemiripan bila belum pernah diisi, atau kosong bila Skor Kemiripan juga kosong. Validasi di klien sebelum submit: angka bulat 0 sampai 100 (input kosong, desimal seperti "85.5", notasi seperti "1e2", atau di luar rentang semuanya ditolak dengan pesan yang sama seperti galat server, "Nilai akhir harus bilangan bulat 0 sampai 100.", tampil di bawah input). Simpan dan Batal mengikuti pola persis Edit teks OCR: `aria-disabled` dan indikator putar pada Simpan selama permintaan berjalan, Esc diabaikan saat itu, Esc atau Batal saat tidak berjalan mengembalikan sel ke tampilan baca dan fokus ke tombol Ubah Nilai Akhir. Tidak ada aksi untuk mengosongkan kembali Nilai Akhir yang sudah diisi. Gagal simpan karena galat server: "Nilai gagal disimpan, silakan mencoba menyimpan kembali."
- Kosong: "Belum ada hasil koreksi untuk soal ini. Tunggu proses selesai." Gagal memuat: "Koneksi internet terputus, coba muat ulang halaman."
- Di bawah 1024 px (ponsel dan tablet): tiap baris menjadi kartu dengan nama di atas, skor dan lencana kategori, lalu teks OCR, lalu Nilai Akhir. Keadaan edit (area teks/input angka dan tombol Simpan/Batal, untuk mode apa pun) tetap di dalam kartu yang sama, tanpa tata letak terpisah untuk ponsel.

#### Batch Selesai (FR23)

Batch berstatus Selesai bersifat baca saja: lencana "Selesai" di kepala, tombol "Tambah Soal" (berserta form dan pesan di bawah daftar soal), teks peringatan unggah, tombol "Upload Jawaban Peserta Didik", "Coba Lagi", "Edit", dan "Ubah Nilai Akhir" tidak dirender, dan "Selesaikan Batch" tidak tampil; daftar soal dan daftar jawaban yang sudah diunggah tetap tampil dan dapat dibaca. "Ekspor Rekap Nilai" dan "Hapus Batch" tetap ada. Catatan kotak di bawah baris tombol: "Batch ini sudah selesai dan tidak dapat diubah."

#### Perilaku tombol aksi di kepala

- "Selesaikan Batch": jika ada file terpilih yang belum diunggah, pesan galat "Ada file yang belum diunggah. Unggah file tersebut atau batalkan pilihannya sebelum menyelesaikan batch." dan dialog tidak dibuka (pesan hilang saat pilihan file berubah); jika masih ada file Diproses, pesan "Tunggu hingga semua file selesai diproses."; jika tidak, dialog "Batch yang diselesaikan tidak dapat diubah lagi. Lanjutkan?" ("Ya", "Batal"). Gagal: "Gagal menyelesaikan batch, silakan coba lagi".
- "Ekspor Rekap Nilai" (FR17): akun Pro mengunduh file .xlsx (indikator putar selama permintaan berjalan); akun Free melihat "Fitur ekspor hanya tersedia untuk akun Pro. Upgrade untuk mengakses fitur ini." dengan kata "Upgrade" berupa tautan ke `/langganan`; batch tanpa jawaban menampilkan "Belum ada jawaban peserta didik pada batch ini untuk diekspor.". Gagal: "Gagal membuat file ekspor, silakan coba lagi".
- "Hapus Batch": dialog yang sama seperti di menu Beranda; sukses kembali ke Beranda. Gagal: "Gagal menghapus batch, silakan coba lagi".

### 6. Langganan (`/langganan`, Pengajar)

Deskripsi tepat di bawah judul: "Kelola paket Pro dan pantau status pembayaran." (usulan)

Blok dari atas ke bawah:
1. **Status akun.** Lencana FREE (ikon `user-check`) dengan teks "Akun Anda memakai paket Free.", atau lencana PRO (ikon `crown`) dengan teks "Berlaku hingga {tanggal}" (zona waktu `Asia/Jakarta`). Gagal memuat: "Gagal memuat status langganan, coba muat ulang halaman".
2. **Paket Pro.** Dua pilihan radio dalam `fieldset`/`legend` ("Paket Pro"): "1 bulan (30 hari), Rp 30.000" dan "3 bulan (90 hari), Rp 80.000" (satu terpilih, default 1 bulan). Daftar manfaat ("Manfaat"): "Batch aktif tidak dibatasi", "30 soal per batch", "50 jawaban per batch", "Ekspor rekap nilai". Catatan: "Langganan Pro tidak diperpanjang otomatis."
3. **Tombol.** "Upgrade ke Pro" (untuk akun Pro yang masih berlaku, label "Perpanjang Pro") membuka ringkasan paket terpilih ("1 bulan (30 hari), Rp 30.000" atau "3 bulan (90 hari), Rp 80.000" beserta daftar manfaat) dengan tombol "Lanjutkan ke Pembayaran", yang membawa pengguna ke halaman pembayaran Midtrans (Sandbox). Galat: "Transaksi gagal dibuat, silakan coba lagi", "Gagal mencatat transaksi, silakan coba lagi", "Koneksi internet terputus, silakan coba lagi.".
4. **Status transaksi terakhir.** Tidak dirender bila belum ada transaksi. Saat ada transaksi: lencana status ("Menunggu", "Berhasil", "Gagal", "Kedaluwarsa") beserta paket dan nominalnya ("1 bulan (30 hari), Rp 30.000" atau "3 bulan (90 hari), Rp 80.000"). Jika transaksi terakhir berstatus Menunggu, halaman melakukan polling terbatas tiap 3 detik (maksimal 10 kali percobaan atau berhenti setelah 3 kegagalan beruntun); saat status berubah menjadi Berhasil, profil dimuat ulang sehingga lencana akun di bilah atas dan kartu status akun berubah menjadi PRO (kegagalan memuat ulang profil saat polling tidak mengosongkan label akun yang sudah ada). Bila polling berhenti dan transaksi masih Menunggu, tampil pesan "Pembayaran belum terkonfirmasi. Jika sudah membayar, periksa status beberapa saat lagi." dengan tombol "Periksa Status" untuk memuat ulang transaksi dan profil. Gagal memuat daftar transaksi: "Gagal memuat status langganan, coba muat ulang halaman" atau "Koneksi internet terputus, coba muat ulang halaman.".

5. **Kartu kendala pembayaran.** Tidak dirender (disembunyikan) bila variabel `VITE_NOMOR_WA_ADMIN` kosong. Saat terisi: judul kartu "Ada kendala pembayaran?", lalu tombol "Hubungi Admin via WhatsApp" yang membuka `https://wa.me/<VITE_NOMOR_WA_ADMIN>?text=<pesan>` di tab baru (`rel="noopener noreferrer"`). Nomor admin format internasional tanpa tanda plus (misalnya `628123456789`), dibaca dari env `VITE_NOMOR_WA_ADMIN`. Pesan template di-encode untuk URL: "Halo Admin Koreksi-in, saya mengalami kendala pembayaran. Email akun: {email}."; ditambah "ID transaksi: {id}" hanya bila ID transaksi sudah ada di respons API (frontend hanya menambahkan data yang sudah diterima, tidak ada permintaan field baru dan tidak mengubah backend).

### 7. Dashboard Pantauan (`/admin`, Admin)

Hanya angka agregat, tanpa isi kunci, jawaban, atau hasil koreksi. Tata letak harus rapi di desktop 1280 px maupun ponsel 375 px tanpa gulir horizontal, dan semua target sentuh (tombol, tautan) memiliki tinggi minimal `min-h-11` (44 px).

- **Kepala halaman:**
  - Judul halaman "Dashboard Pantauan" (`text-2xl font-bold leading-8 text-teks`) TANPA garis aksen (garis aksen hanya di Pemasaran).
  - Deskripsi tepat di bawah judul: "Ringkasan akun, aktivitas koreksi, dan pemakaian kuota API." (satu baris, teks redup `text-sm leading-5 text-teks-redup`).
  - Baris info dan tombol di dekat judul (di sisi kanan kepala sejajar judul pada desktop `lg:flex lg:items-start lg:justify-between`, dan bertumpuk rapi di bawah deskripsi pada ponsel 375 px): teks waktu "Diperbarui pukul HH.MM" (`text-sm leading-5 text-teks-redup`, format 24 jam dengan titik, mis. `17.32`; jam diambil saat data berhasil dimuat) dan tombol sekunder "Muat ulang" (`min-h-11 rounded-lg border border-garis bg-permukaan px-4 text-sm font-medium text-teks`, ikon `refresh-cw` `size-4`). Klik pada tombol yang sedang `aria-disabled="true"` HARUS diabaikan di handler (tidak mengirim permintaan baru).
- **Kelompok kartu angka:** disusun dalam grid dan dikelompokkan dengan judul kecil berikon (`text-sm font-semibold leading-5 text-teks-redup`):
  - **Akun** (`users`): baris kepala kelompok (`flex items-center justify-between gap-2`) memuat judul kelompok "Akun" berikon `users` di kiri dan tautan teks "Kelola akun Pengajar" (`min-h-11 inline-flex items-center gap-1.5 text-sm font-medium text-biru-utama`) dengan ikon `arrow-right` (`size-4`) di sisi kanan, menuju halaman Akun Pengajar (`/admin/akun-pengajar`). Di bawahnya tiga kartu angka (`grid-cols-2 lg:grid-cols-3`, kartu ketiga `max-lg:col-span-2`): Total akun Pengajar (`users`), Akun Free (`user-check`), Akun Pro (`crown`, kotak ikon `bg-biru-utama text-permukaan`).
  - **Aktivitas** (`layers`): empat kartu angka (`grid-cols-2 lg:grid-cols-4`): Jumlah batch (`layers`), File Diproses (`loader-circle`, berputar HANYA bila jumlah lebih dari 0 dan dengan `motion-reduce:animate-none`), File Selesai (`file-check`), File Gagal (`file-x`, angka `text-kurang-mirip`).
  - **Kuota API** (`gauge`): satu kartu lebar penuh (`p-6`) berisi:
    - Angka "Terpakai hari ini" dan "Batas harian" (format angka `id-ID`), serta lencana status pemakaian (bila mencapai ambang peringatan/batas).
    - Bilah pemakaian (`role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, dan `aria-valuemax` dari data) di atas jalur `bg-biru-muda`. Lebar isi bilah dihitung dari nilai asli (`terpakai / batas`, maksimal 100 persen; bila `batas <= 0` maka lebar bilah `0%`), dengan gaya sebaris, bukan kelas tetap.
    - Warna bilah dan teks status pendamping (warna tidak boleh menjadi satu-satunya penanda; perbandingan ambang memakai perkalian bilangan bulat dari nilai asli sebelum pembulatan tampilan):
      - Bila `batas <= 0`: lebar bilah `0%`, warna `bg-kurang-mirip`, dan tampil teks status "Batas tercapai" (`bg-kurang-mirip-latar text-kurang-mirip`).
      - Normal (`terpakai * 100 < batas * 80`): bilah `bg-biru-utama` (kontras komponen non-teks minimal 3:1 di atas `bg-biru-muda`; `merek-hijau` di atas `biru-muda` hanya sekitar 1,9:1), tanpa teks status peringatan.
      - Mulai 80% (`terpakai * 100 >= batas * 80` dan `terpakai * 100 < batas * 95`): bilah `bg-cukup-mirip`, disertai lencana/teks status "Mendekati batas" (`bg-cukup-mirip-latar text-cukup-mirip`).
      - Mulai 95% (`terpakai * 100 >= batas * 95` dan `terpakai < batas`): bilah `bg-kurang-mirip`, disertai lencana/teks status "Hampir habis" (`bg-kurang-mirip-latar text-kurang-mirip`).
      - 100% (`terpakai >= batas` dengan `batas > 0`): bilah `bg-kurang-mirip`, disertai lencana/teks status "Batas tercapai" (`bg-kurang-mirip-latar text-kurang-mirip`).
    - Baris ringkasan tepat di bawah bilah (`flex items-center justify-between gap-2 text-sm leading-5`): di kiri "NN,N% terpakai" dan di kanan "Sisa N panggilan" (`N` = `max(0, batas - terpakai)` dalam format `id-ID`). Persentase yang ditampilkan dibulatkan ke bawah satu desimal dengan mengalikan bilangan bulat terlebih dahulu (`Math.floor((terpakai * 1000) / batas) / 10`, maksimal 100% bila `terpakai >= batas`, atau 0% bila `batas <= 0`; jangan memakai `Math.floor((terpakai / batas) * 100 * 10) / 10` karena galat floating-point seperti `29 / 100` menjadi `28,9%`) sehingga `100%` hanya tampil bila kuota memang penuh, dengan koma desimal `id-ID` dan nol di belakang koma dibuang (contoh: `12,1% terpakai`, `50% terpakai`, `0% terpakai`, `100% terpakai`). Tes fungsi persen wajib mencakup kasus `29` dari `100` = `"29%"`.
    - Keterangan kecil di bagian bawah kartu (`text-sm leading-5 text-teks-redup`): catatan "Diatur ulang setiap hari pukul 00.00 waktu Pasifik (AS)." dan nama model "Model: gemini-3.5-flash-lite" (nama model datang dari server, ditampilkan dengan pola `"Model: {nama_model}"`).
- **Gaya kartu:**
  - Kartu angka: `rounded-lg border border-garis bg-permukaan p-4 shadow-sm` (padat, supaya label muat di ponsel dua kolom). Kartu Kuota API `p-6`. Ukuran ini sementara (pilihan pemilik proyek, boleh disesuaikan setelah dilihat di aplikasi).
  - Kartu angka memakai garis aksen dekoratif di tepi atas (`h-1`, `aria-hidden`; warna `merek-biru`, `merek-hijau`, `biru-utama`, atau `kurang-mirip` menurut maknanya) dan kotak ikon `size-9 rounded-lg`. Ikon dan garis aksen bersifat dekoratif; angka dan label teks tetap pembawa makna.
- **Keadaan halaman:**
  - **Biasa:** semua kartu menampilkan angka dari server, Kuota API menampilkan bilah beserta persentase, sisa panggilan, catatan reset, dan nama model dari server, serta kepala halaman menampilkan "Diperbarui pukul HH.MM" sesuai jam saat data berhasil dimuat.
  - **Memuat (awal):** kepala halaman tetap tampil beserta tombol "Muat ulang" dalam keadaan nonaktif (`aria-disabled="true"`, klik diabaikan, ikon `refresh-cw` diam/tidak berputar karena hanya berputar saat memuat ulang, teks waktu "Diperbarui pukul HH.MM" belum ditampilkan), sedangkan area isi menampilkan indikator memuat.
  - **Kosong (tanpa data / semua 0):** kartu angka menampilkan `0`; pada kartu Kuota API terpakai `0`, sisa = batas ("Sisa N panggilan"), persentase "0% terpakai", lebar bilah `0%`, tanpa teks status peringatan (kecuali bila `batas <= 0` yang menampilkan status "Batas tercapai").
  - **Gagal (pemuatan awal gagal):** area isi menampilkan pesan galat "Gagal memuat dashboard pantauan, coba muat ulang halaman." (`role="alert"`, `text-kurang-mirip`); tombol "Muat ulang" di kepala halaman aktif dan dapat ditekan untuk mencoba memuat kembali.
  - **Memuat ulang:** saat tombol "Muat ulang" ditekan ketika data sudah pernah tampil, tombol menjadi nonaktif (`aria-disabled="true"`, klik diabaikan) dengan ikon `refresh-cw` berputar (`animate-spin motion-reduce:animate-none`); seluruh angka lama dan teks waktu "Diperbarui pukul HH.MM" lama tetap terlihat (tidak dikosongkan dan tidak diganti spinner halaman penuh). Bila muat ulang berhasil, angka dan waktu "Diperbarui pukul HH.MM" diperbarui (pesan galat lama jika ada dibersihkan). Bila muat ulang gagal, tampil pesan galat yang sama seperti keadaan gagal ("Gagal memuat dashboard pantauan, coba muat ulang halaman.", `role="alert"`, `text-kurang-mirip`) di atas kelompok kartu, sementara angka dan waktu "Diperbarui pukul HH.MM" lama tetap terlihat.

### 8. Akun Pengajar (`/admin/akun-pengajar`, Admin)

- **Bilah alat:** kolom cari (nama atau email, live dengan debounce), filter status langganan (Semua, Free, Pro), filter status akun (Semua, Aktif, Nonaktif); pencarian dan filter dikirim lewat query param backend, tanpa pagination.
- **Tabel:** Nama, Email, Langganan (lencana FREE atau PRO menurut `jenis_akun_efektif`; untuk Pro disertai teks `"Berlaku hingga <tanggal>"` dalam zona waktu WIB), Status akun (lencana Aktif atau Nonaktif), Tanggal daftar (WIB), Jumlah batch, Aksi. Aksi per baris: "Ubah Langganan" dan "Nonaktifkan" atau "Aktifkan" (menyesuaikan status).
- **Ubah Langganan:** dialog dengan pilihan status Free atau Pro; untuk Pro, kolom tanggal masa berlaku wajib (berlaku inklusif sampai 23:59 WIB pada tanggal terpilih; memilih Free mengosongkan masa berlaku). Galat: "Masa berlaku wajib diisi dengan tanggal setelah hari ini." Sukses: "Status langganan berhasil diubah". Gagal: "Gagal mengubah status langganan, silakan coba lagi.", "Koneksi internet terputus, silakan coba lagi."
- **Nonaktifkan atau Aktifkan:** dialog konfirmasi yang menyebut nama akun dan tindakan (memakai `DialogKonfirmasi` bersama dengan gaya tombol sesuai mockup). Sukses: "Akun berhasil dinonaktifkan" atau "Akun berhasil diaktifkan". Gagal: "Gagal mengubah status akun, silakan coba lagi."
- **Keadaan:** kosong "Belum ada akun Pengajar yang terdaftar."; pencarian tanpa hasil "Tidak ada akun yang sesuai dengan pencarian."; gagal "Gagal memuat daftar akun, coba muat ulang halaman."; offline "Koneksi internet terputus, coba muat ulang halaman."
- Di bawah 1024 px (ponsel dan tablet) tiap baris menjadi kartu dengan aksi di bagian bawah kartu.

### 9. Lupa Password (`/lupa-password`, publik)

Kartu di tengah dengan `logo.png`, judul "Lupa Password" (TANPA label kecil di atas judul), dan deskripsi tepat di bawah judul (`text-sm leading-5 text-teks-redup`): "Masukkan email akun Anda. Jika terdaftar, kami kirim tautan untuk mengatur ulang password." Tanpa bilah atas. Dibungkus `RouteTamu` sehingga pengguna yang sudah login dialihkan ke Beranda. Pojok kiri atas kartu (sebelum logo): tautan "Kembali ke Masuk" (ikon `arrow-left` `size-4`, `aria-hidden="true"`, ke `/masuk`), tanpa tautan "Kembali ke beranda".

- Kolom Email memakai `KolomIsian` dengan ikon kiri `mail` (`size-4`, `aria-hidden="true"`) dan placeholder "nama@email.com" (`placeholder:text-teks-redup`, kontras >= 4,5 : 1, tidak menggantikan label).
- Tombol submit berlabel normal "Kirim Tautan" (indikator putar dan `aria-disabled="true"` selama mengirim).
- Format email tidak valid (kosong atau tidak sesuai `REGEX_EMAIL`): tampilkan "Format email tidak valid. Contoh: nama@email.com." tepat di bawah kolom Email, pindahkan fokus ke kolom Email, tanpa permintaan terkirim dan tanpa memulai hitungan mundur. Mengetik di kolom Email membersihkan galat kolom itu.
- Setelah permintaan sukses, apa pun hasilnya (email terdaftar atau tidak, akun aktif atau tidak, atau sedang dalam jeda 60 detik di server — U12):
  - Tampilkan kotak pesan sukses di atas form (`role="status"`): "Tautan atur ulang password telah dikirim ke {email}. Periksa kotak masuk dan folder spam. Tautan berlaku 30 menit." (`{email}` adalah alamat email yang sudah di-trim saat dikirim). Tampil sama untuk semua email agar tidak membocorkan apakah email terdaftar.
  - Kolom Email tetap terisi dan tetap bisa diedit (tidak memakai `disabled` atau `readOnly`).
  - Tombol submit memakai `aria-disabled="true"` selama 60 detik dengan label "Kirim ulang dalam N detik" (`N` berjalan dari 60 turun ke 1). Selama hitungan mundur aktif (maupun selama permintaan sedang dikirim), baik klik pada tombol maupun handler `onSubmit` form HARUS mengabaikan pengiriman (menekan Enter di kolom Email tidak boleh mengirim form).
  - Hitungan mundur berjalan murni di klien sebagai bantuan tampilan dan muncul untuk semua email, bukan hanya yang terdaftar; server tetap menegakkan batas jeda 60 detik per akun secara independen (U12).
  - Hitungan mundur tidak diumumkan tiap detik ke pembaca layar (teks tombol tidak diberi `aria-live`; pembaca layar hanya menerima satu pengumuman saat keadaan sukses dimulai lewat kotak pesan sukses `role="status"`).
  - Persistensi hitungan mundur saat muat ulang halaman: saat permintaan sukses (untuk semua email, terdaftar atau tidak), simpan `{email, waktuBerakhir}` di `sessionStorage`. Saat halaman dibuka atau dimuat ulang dan `waktuBerakhir` belum lewat, pulihkan keadaan sukses: kolom Email terisi `email` tersebut, kotak pesan sukses tampil, dan hitungan mundur lanjut dari sisa detik (sisa detik dibatasi pada rentang `0..60`). Bila `waktuBerakhir` sudah lewat (atau data tidak valid), hapus data dari `sessionStorage` dan tampilkan keadaan awal. Seluruh akses `sessionStorage` (baca, tulis, hapus) dibungkus `try/catch` dan boleh gagal tanpa merusak halaman.
  - Mengubah isi kolom Email langsung menghapus data tersimpan di `sessionStorage`, menghentikan hitungan mundur, menyembunyikan pesan sukses, dan mengaktifkan tombol kembali ke "Kirim Tautan".
- Gagal mengirim karena galat server atau koneksi terputus: tampilkan "Gagal mengirim tautan, silakan coba lagi." (kotak galat di atas form, `role="alert"`), tanpa memulai hitungan mundur dan tanpa menyimpan ke `sessionStorage`. Pesan lama dibersihkan saat submit berikutnya, dan galat serta sukses tidak pernah tampil bersamaan.
- Status keadaan halaman:
  - **Awal:** kolom Email kosong (placeholder "nama@email.com") dan dapat diedit, tidak ada banner pesan, tombol "Kirim Tautan" aktif.
  - **Sukses dengan hitungan:** kotak pesan sukses "Tautan atur ulang password telah dikirim ke {email}. Periksa kotak masuk dan folder spam. Tautan berlaku 30 menit." tampil di atas form (satu pengumuman saat mulai), kolom Email tetap terisi dan bisa diedit, tombol `aria-disabled="true"` dengan label "Kirim ulang dalam N detik" (`N` = 60..1, klik tombol dan submit form/Enter diabaikan), dan `{email, waktuBerakhir}` tersimpan di `sessionStorage` (dipulihkan dengan sisa detik dibatasi `0..60` bila halaman dimuat ulang sebelum waktu berakhir).
  - **Hitungan habis:** saat waktu berakhir tercapai (`N` mencapai 0), data di `sessionStorage` dihapus, tombol kembali aktif dengan label "Kirim Tautan" (`aria-disabled` dilepas), sedangkan pesan sukses dan isi kolom Email tetap tampil sampai pengguna mengirim ulang atau mengubah email.
  - **Email diubah:** saat pengguna mengubah isi kolom Email (baik saat hitungan mundur masih berjalan maupun setelah hitungan habis), data di `sessionStorage` dihapus, hitungan mundur dihentikan, pesan sukses disembunyikan, dan tombol langsung aktif dengan label "Kirim Tautan".
  - **Gagal:** saat pengiriman gagal (jaringan/galat server), tampil kotak galat "Gagal mengirim tautan, silakan coba lagi." (`role="alert"`) di atas form (atau galat format di bawah kolom Email bila gagal validasi), tidak ada hitungan mundur, dan tombol aktif dengan label "Kirim Tautan".

### 10. Atur Ulang Password (`/atur-ulang-password?token=...`, publik)

Kartu di tengah dengan `logo.png`, judul "Atur Ulang Password" (TANPA label kecil di atas judul), dan deskripsi tepat di bawah judul (`text-sm leading-5 text-teks-redup`): "Buat password baru untuk akun Anda. Minimal 8 karakter." Deskripsi ini hanya tampil bersama form (token valid); disembunyikan saat tampilan token tidak sah (tanpa token, kedaluwarsa, sudah dipakai, atau tidak sah), karena tampilan itu tidak menampilkan form. Tanpa bilah atas, dan tanpa tautan "Kembali ke beranda" maupun "Kembali ke Masuk" yang persisten. Rute ini TIDAK dibungkus `RouteTamu` supaya tautan dari email tetap bekerja di browser yang masih memiliki sesi login.
- Token dibaca sekali dari query `?token=...` ke state saat inisialisasi (aman terhadap `StrictMode`) lalu langsung dihapus dari URL lewat `navigate(pathname, { replace: true })` sehingga bilah alamat menjadi `/atur-ulang-password` saja; `<meta name="referrer" content="no-referrer">` dipasang di `index.html`, dan token tidak pernah ditulis ke log, `console`, atau storage. Konsekuensi yang diterima: memuat ulang halaman membuat tautan tampil tidak berlaku.
- Kolom (`KolomPassword`, lihat Komponen bersama):
  - Password baru: ikon kiri `lock` (`size-4`, `aria-hidden="true"`), tombol tampilkan/sembunyikan di kanan, placeholder "Password baru". Tidak ada petunjuk terpisah di bawah kolom karena aturan minimal 8 karakter sudah tertulis pada deskripsi di bawah judul.
  - Konfirmasi password: ikon kiri `lock` (`size-4`, `aria-hidden="true"`), tombol tampilkan/sembunyikan di kanan, placeholder "Ulangi password baru". Tidak ada petunjuk di bawah kolom.
  - Placeholder memakai `placeholder:text-teks-redup` (kontras >= 4,5 : 1) dan tidak menggantikan label.
- Tombol "Simpan Password" (indikator putar, `aria-disabled` selama mengirim).
- Galat kolom tampil tepat di bawah kolomnya (`role="alert"`): password baru kosong → "Password wajib diisi."; password baru kurang dari 8 byte atau lebih dari 72 byte UTF-8 → "Password minimal 8 karakter" atau "Password maksimal 72 karakter"; konfirmasi kosong → "Konfirmasi password wajib diisi."; konfirmasi tidak sama dengan password baru (hanya diperiksa bila password baru sudah diisi) → "Konfirmasi password tidak sama.". Semua pemeriksaan kolom berjalan sekaligus saat submit; fokus pindah ke kolom bermasalah pertama (Password baru lalu Konfirmasi password), dan mengetik di kolom password baru membersihkan galat kedua kolom sementara mengetik di konfirmasi membersihkan galat konfirmasi. Galat panjang password dari server (`PASSWORD_TERLALU_PENDEK`/`PASSWORD_TERLALU_PANJANG`) juga tampil di bawah kolom password baru. Banner di atas form hanya untuk galat umum, misalnya "Gagal mengubah password, silakan coba lagi."
- Tanpa token di URL (atau token kosong), atau bila token kedaluwarsa, sudah dipakai, atau tidak sah (`TOKEN_RESET_TIDAK_VALID`): halaman menampilkan kotak galat "Tautan tidak berlaku atau sudah kedaluwarsa." dan tautan "Lupa Password" (ikon `arrow-left` `size-4`, `aria-hidden="true"`, ke `/lupa-password`) di pojok kiri atas kartu (sebelum logo) untuk meminta tautan baru, tanpa form.
- Sukses (`204`): jika browser masih memiliki sesi login (`status === "terautentikasi"`), panggil `keluar()` terlebih dahulu (dibungkus `try/catch` yang mengabaikan kegagalan agar tidak menghalangi navigasi), lalu arahkan ke `/masuk` dengan pesan "Password berhasil diubah, silakan masuk."

### 11. Halaman 404 (`/*`)

Rute catch-all untuk semua rute tak dikenali. Halaman statis tanpa pemuatan data.

Blok dari atas ke bawah:
1. **Judul.** "Halaman tidak ditemukan" (`text-2xl font-bold leading-8`), tanpa garis aksen (garis aksen hanya dipakai di Pemasaran).
2. **Kalimat penjelas.** Satu kalimat di bawah judul (`text-base leading-6`): "Halaman yang Anda cari tidak tersedia." (usulan, boleh disesuaikan pemilik proyek).
3. **Ikon keadaan.** Ikon Lucide `search-x`, `size-6`, `aria-hidden="true"`, ilustrasi keadaan kosong.
4. **Tombol kembali.** Mengikuti peran lewat `berandaUntukPeran`: belum masuk → `/` ("Kembali ke beranda"); Pengajar → `/` ("Kembali ke Beranda"); Admin → `/admin` ("Kembali ke Dashboard Pantauan"). Peran dibaca dari sesi/auth frontend.

**Bilah atas: TIDAK tampil.** Halaman ini mandiri tanpa bilah atas, sebagaimana halaman publik kartu. Rute catch-all tidak mengikat peran tertentu karena tombol kembali sudah mengarahkan pengguna sesuai peran.

Keadaan: statis, tidak ada pemuatan data/polling.

### Keputusan pemilik proyek

1. Tombol "Upgrade ke Pro" dan pesan "batch tidak terbatas" memakai Bahasa Indonesia (SPEC sudah disesuaikan).
2. Akun Pro yang masih berlaku boleh membeli paket lagi. Masa berlaku baru dihitung dari masa berlaku saat ini (SPEC F-LANGGANAN). Tombol berlabel "Perpanjang Pro" untuk akun itu (label usulan).
3. Kolom kosong atau tidak valid di Daftar, Masuk, Lupa Password, dan Atur Ulang Password menampilkan pesan spesifik tepat di bawah kolomnya masing-masing (lewat komponen `KolomIsian`/`KolomPassword`), bukan lagi pesan generik "Data yang dikirim tidak valid." di atas form (keputusan lama pada poin ini, diganti 23 November 2026). Banner di atas form hanya dipakai untuk galat yang tidak bisa diatribusikan ke satu kolom, contohnya `LOGIN_GAGAL` yang sengaja ambigu agar tidak membocorkan apakah email atau password yang salah, atau galat umum saat mengirim tautan / mengubah password.
4. Teks yang bertanda "(usulan)" dan label kecil di luar daftar pesan SPEC disetujui untuk sementara. Perancang TIDAK BOLEH menambah teks baru di luar itu; perubahan teks lewat pemilik proyek.
5. Akun nonaktif yang mencoba masuk (SPEC U6) memakai pesan generik "Email atau password salah".
6. Halaman Batch tetap halaman tersendiri di `/batch/:id_batch`, bukan item navbar. Navbar Pengajar tetap memakai menu "Beranda" (menyala saat di Halaman Batch) dan "Langganan"; Halaman Batch dibuka dari daftar batch di Beranda.
7. Ikon diizinkan, hanya dari Lucide (bagian Ikon).
8. Tautan di halaman Atur Ulang Password untuk token tidak sah memakai teks "Lupa Password" (pilihan pemilik proyek). Alt teks logo: "Koreksi-in". Tautan "Langganan" di navbar memakai penanda "nanti" sampai fiturnya dikerjakan.
9. Tampilan mendukung tablet: tabel berubah menjadi kartu di bawah 1024 px, dan menu Bilah atas berpindah ke laci di bawah 1024 px (tombol menu diletakkan di paling kiri sebelum logo), satu titik henti (`lg`) yang sama untuk tabel dan menu (bagian Gaya visual dan Komponen bersama).
10. Teks tambahan dari desain tahap 3, disetujui sementara (perubahan lewat pemilik proyek):
    - Pemasaran: judul seksi "Cara kerja", "Fitur utama", "Free dan Pro". Deskripsi kartu fitur: "Lembar jawaban foto atau PDF dibaca menjadi teks.", "Skor sebagai rekomendasi, bukan nilai akhir.", "Edit teks hasil baca dan nilai akhir.", "Unduh rekap nilai dalam file .xlsx.". Penutup: "Siap mulai mengoreksi lebih cepat?".
    - Langganan: judul halaman "Langganan"; teks status Free "Akun Anda memakai paket Free." dan Pro "Berlaku hingga {tanggal}"; judul seksi "Paket Pro", "Manfaat", dan "Status transaksi terakhir"; label paket "1 bulan (30 hari), Rp 30.000" dan "3 bulan (90 hari), Rp 80.000" (dipakai di pilihan radio, ringkasan, dan status transaksi terakhir); tombol "Upgrade ke Pro", "Perpanjang Pro", "Lanjutkan ke Pembayaran", dan "Periksa Status"; lencana transaksi "Menunggu", "Berhasil", "Gagal", "Kedaluwarsa"; pesan saat polling berhenti pada status Menunggu "Pembayaran belum terkonfirmasi. Jika sudah membayar, periksa status beberapa saat lagi."; tautan inline ke `/langganan` berdasarkan kode error pada pesan penolakan `BATAS_BATCH_AKTIF_TERCAPAI` ("Upgrade ke Pro"), `BATAS_JAWABAN_TERLAMPAUI` khusus Free ("upgrade ke Pro"), dan `EKSPOR_KHUSUS_PRO` ("Upgrade").
    - Dashboard Pantauan: judul halaman "Dashboard Pantauan"; deskripsi "Ringkasan akun, aktivitas koreksi, dan pemakaian kuota API."; info waktu "Diperbarui pukul HH.MM"; tombol "Muat ulang"; kelompok "Akun", "Aktivitas", "Kuota API"; tautan "Kelola akun Pengajar"; label kartu "Total akun Pengajar", "Akun Free", "Akun Pro", "Jumlah batch", "File Diproses", "File Selesai", "File Gagal", "Terpakai hari ini", "Batas harian"; teks kuota "NN,N% terpakai" (nol di belakang koma dibuang, mis. "0% terpakai", "50% terpakai", "12,1% terpakai", "100% terpakai") dan "Sisa N panggilan"; status kuota "Mendekati batas", "Hampir habis", "Batas tercapai"; catatan kuota "Diatur ulang setiap hari pukul 00.00 waktu Pasifik (AS)." dan "Model: {nama_model}" (contoh "Model: gemini-3.5-flash-lite").
    - Akun Pengajar: judul halaman "Akun Pengajar"; label "Cari" (placeholder "Cari berdasarkan nama atau email"), "Status langganan", "Status akun", "Masa berlaku"; keterangan masa berlaku Pro "Berlaku hingga <tanggal>"; tombol dialog "Simpan", "Batal", "Ya". Dialog nonaktifkan: judul "Nonaktifkan Akun", kalimat "Akun {nama} akan dinonaktifkan dan tidak dapat masuk. Lanjutkan?". Dialog aktifkan: judul "Aktifkan Akun", kalimat "Akun {nama} akan diaktifkan dan dapat masuk kembali. Lanjutkan?".
11. Ejaan baku "silakan" dipakai di semua pesan (SPEC sudah disesuaikan, SRS menyusul saat sinkronisasi).
12. Tabel Free dan Pro di Pemasaran tetap tabel di semua lebar tanpa gulir horizontal (pengecualian dari aturan tabel menjadi kartu di bawah 1024 px).
13. Garis hijau pendek di atas judul hanya dipakai di Pemasaran. Halaman aplikasi (termasuk Dashboard Pantauan) tidak memakainya.
14. Teks OCR di Dashboard Hasil Koreksi: tautan "Tampilkan lengkap" berganti menjadi "Tampilkan ringkas" setelah teks dibuka (pilihan pemilik proyek, 1 November 2026)
15. Halaman kartu publik (Masuk, Daftar, Lupa Password, Atur Ulang Password) tidak memakai bilah atas dan tidak memakai label kecil di atas judul; hanya kartu di tengah layar dengan logo, judul, dan deskripsi singkat di bawahnya, seperti referensi situs lain (pilihan pemilik proyek, 2 dan 25 November 2026; rincian deskripsi, ikon kiri kolom, placeholder, tautan kembali, serta pesan dan hitungan mundur Lupa Password ada di subbagian halaman 2, 3, 9, dan 10). Mockup Masuk dan Daftar yang masih menampilkan bilah atas varian Publik diabaikan; varian Publik hanya dipakai di Pemasaran.
16. Bilah atas Pemasaran menempel di atas dan memuat tiga tautan jangkar yang menggulir ke seksi "Cara kerja", "Fitur utama", dan "Free dan Pro", mengikuti situs referensi (pilihan pemilik proyek, 2 November 2026). Label memakai judul seksi yang sudah ada; mockup Pemasaran belum menampilkannya, jadi UI.md yang diikuti.