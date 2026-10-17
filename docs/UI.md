# UI Koreksi-in

Aturan tampilan untuk frontend. Warna diambil dari logo (biru dan hijau). Frontend memakai Tailwind CSS v4 lewat plugin Vite.

## Aturan wajib

- Warna HANYA lewat token di bawah. TIDAK BOLEH ada HEX, `rgb()`, atau nilai arbitrer seperti `bg-[#123456]` di komponen.
- Token didefinisikan sekali di `frontend/src/index.css` dengan `@theme`. Menambah atau mengubah token adalah perubahan dokumen ini, bukan keputusan agent.
- Teks biasa HARUS memenuhi kontras WCAG AA (minimal 4,5 : 1). Kombinasi yang sudah dicek ada di tabel kontras.
- Warna tidak boleh menjadi satu-satunya penanda. Kategori dan status SELALU memakai teks ("Sangat Mirip", "Gagal"), bukan hanya warna.
- Teks UI Bahasa Indonesia. Desktop dulu, tetap responsif sampai lebar ponsel.
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

### Status Pemrosesan

| `status_pemrosesan` | Teks lencana | Kelas |
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

Aturan: jangan mengubah warna, rasio, atau memutar logo. Beri ruang kosong di sekeliling minimal setinggi lingkaran kecil pada ikon. Latar logo harus putih atau `latar`. Tinggi ikon di bilah atas sekitar 32 px.

## Tata letak

- Bilah atas: ikon logo, nama "Koreksi-in", tombol Keluar di kanan.
- Halaman Masuk dan Daftar: kartu di tengah dengan `logo.png` di atasnya.
- Beranda: judul "Batch Koreksi", tombol "Buat Batch Baru", lalu daftar batch.
- Halaman Batch: judul batch, tiga tab (Soal dan Jawaban, Status Pemrosesan, Dashboard Hasil Koreksi).
- Tabel: baris cukup lega, header `text-teks-redup`, teks OCR panjang dipotong dengan opsi tampilkan lengkap.
- Tampilkan indikator loading pada unggah, pemrosesan, dan pemuatan data. Tampilkan keadaan kosong dengan teks yang ada di SPEC.