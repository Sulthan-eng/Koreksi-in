import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { LogOut, Menu, X } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import Lencana from "./Lencana.jsx";
import Spinner from "./Spinner.jsx";

const KELAS_ITEM_MENU =
  "inline-flex min-h-11 items-center rounded-lg px-3 font-semibold text-teks no-underline aria-[current=page]:bg-biru-muda aria-[current=page]:text-biru-utama";

const KELAS_TAUTAN_JANGKAR =
  "inline-flex min-h-11 items-center rounded-lg px-3 font-semibold text-teks no-underline hover:bg-biru-muda hover:text-biru-utama focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama aria-[current=true]:bg-biru-muda aria-[current=true]:text-biru-utama";

const TAUTAN_JANGKAR_PEMASARAN = [
  { id: "cara-kerja", label: "Cara kerja" },
  { id: "fitur-utama", label: "Fitur utama" },
  { id: "free-dan-pro", label: "Free dan Pro" },
];

function dapatkanDaftarMenu(varian, pathname) {
  if (varian === "admin") {
    return [
      {
        label: "Dashboard Pantauan",
        to: "/admin",
        aktif: pathname === "/admin",
      },
      {
        label: "Akun Pengajar",
        to: "/admin/akun-pengajar",
        aktif: pathname.startsWith("/admin/akun-pengajar"),
      },
    ];
  }

  if (varian === "pengajar") {
    return [
      {
        label: "Beranda",
        to: "/",
        aktif:
          pathname === "/" ||
          pathname === "/beranda" ||
          pathname.startsWith("/batch/"),
      },
    ];
  }

  return [];
}

function BilahAtas({ varian = "pengajar", seksiAktif = null }) {
  const { nama, statusLangganan, keluar } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [sedangKeluar, setSedangKeluar] = useState(false);
  const [laciTerbuka, setLaciTerbuka] = useState(false);
  const [sudahDigulir, setSudahDigulir] = useState(false);
  const tombolBukaRef = useRef(null);
  const dialogRef = useRef(null);

  const daftarMenu = dapatkanDaftarMenu(varian, pathname);

  useEffect(() => {
    if (varian !== "publik") return;
    function cekGulir() {
      setSudahDigulir(window.scrollY > 0);
    }
    cekGulir();
    window.addEventListener("scroll", cekGulir, { passive: true });
    return () => window.removeEventListener("scroll", cekGulir);
  }, [varian]);

  useEffect(() => {
    if (!laciTerbuka) return;
    const media = window.matchMedia("(min-width: 1024px)");
    function saatUkuranBerubah(peristiwa) {
      if (peristiwa.matches) {
        dialogRef.current?.close();
      }
    }
    media.addEventListener("change", saatUkuranBerubah);
    return () => media.removeEventListener("change", saatUkuranBerubah);
  }, [laciTerbuka]);

  function tanganiKlikJangkar(peristiwa, idSeksi) {
    const elemen = document.getElementById(idSeksi);
    if (!elemen) return;
    peristiwa.preventDefault();
    const gerakKurang = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    elemen.scrollIntoView({
      behavior: gerakKurang ? "auto" : "smooth",
      block: "start",
    });
    window.history.replaceState(null, "", `#${idSeksi}`);
  }

  function bukaLaci() {
    const dialog = dialogRef.current;
    if (!dialog || dialog.open) return;
    dialog.showModal();
    setLaciTerbuka(true);
    dialog.querySelector("nav a")?.focus();
  }

  function tutupLaci() {
    const dialog = dialogRef.current;
    if (dialog?.open) {
      dialog.close();
    }
  }

  function tanganiDialogTutup() {
    setLaciTerbuka(false);
    tombolBukaRef.current?.focus();
  }

  async function tanganiKeluar() {
    setSedangKeluar(true);
    try {
      await keluar();
    } finally {
      tutupLaci();
      navigate("/", { replace: true });
    }
  }

  if (varian === "publik") {
    return (
      <header
        className={`sticky top-0 z-30 border-b border-garis bg-permukaan px-4 py-3 text-teks${sudahDigulir ? " shadow-sm" : ""}`}
      >
        <div className="mx-auto flex w-full max-w-5xl items-center gap-4">
          <div className="flex items-center gap-2">
            <img src="/logo-ikon.png" alt="" className="h-10 w-auto" />
            <span className="text-lg font-bold">Koreksi-in</span>
          </div>

          <nav
            aria-label="Seksi halaman"
            className="hidden flex-1 items-center justify-center gap-1 lg:flex"
          >
            {TAUTAN_JANGKAR_PEMASARAN.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                onClick={(peristiwa) => tanganiKlikJangkar(peristiwa, item.id)}
                aria-current={seksiAktif === item.id ? "true" : undefined}
                className={KELAS_TAUTAN_JANGKAR}
              >
                {item.label}
              </a>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <Link
              to="/masuk"
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks no-underline hover:bg-latar focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
            >
              Masuk
            </Link>
            <Link
              to="/daftar"
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan no-underline hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-biru-utama"
            >
              Daftar
            </Link>
          </div>
        </div>
      </header>
    );
  }

  return (
    <>
      <header className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-garis bg-permukaan px-4 py-3 text-teks">
        <img src="/logo-ikon.png" alt="" className="h-10 w-auto" />
        <span className="text-lg font-bold">Koreksi-in</span>

        <nav className="hidden flex-wrap gap-1 lg:flex" aria-label="Menu utama">
          {daftarMenu.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              aria-current={item.aktif ? "page" : undefined}
              className={KELAS_ITEM_MENU}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto hidden items-center gap-3 lg:flex">
          {varian === "pengajar" && statusLangganan && (
            <Lencana varian={statusLangganan} />
          )}
          {nama && <span>{nama}</span>}
          <button
            type="button"
            onClick={tanganiKeluar}
            disabled={sedangKeluar}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks disabled:opacity-50"
          >
            {sedangKeluar ? (
              <Spinner ukuran="size-4" />
            ) : (
              <LogOut aria-hidden="true" className="size-4" />
            )}
            Keluar
          </button>
        </div>

        <button
          ref={tombolBukaRef}
          type="button"
          aria-label="Buka menu"
          aria-expanded={laciTerbuka}
          onClick={bukaLaci}
          className="ml-auto inline-flex size-11 items-center justify-center rounded-lg border border-garis bg-permukaan text-teks lg:hidden"
        >
          <Menu aria-hidden="true" className="size-5" />
        </button>
      </header>

      <dialog
        ref={dialogRef}
        aria-label="Menu utama"
        onClose={tanganiDialogTutup}
        onClick={(peristiwa) => {
          if (peristiwa.target === dialogRef.current) {
            tutupLaci();
          }
        }}
        className="m-0 h-dvh max-h-none w-72 max-w-full border-0 border-r border-garis bg-permukaan p-0 text-teks backdrop:bg-teks/40 lg:hidden"
      >
        <aside className="flex h-full w-full flex-col gap-4 overflow-y-auto p-4">
          <div className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-2">
              <img src="/logo-ikon.png" alt="" className="h-10 w-auto" />
              <span className="text-lg font-bold">Koreksi-in</span>
            </span>
            <button
              type="button"
              aria-label="Tutup menu"
              onClick={tutupLaci}
              className="inline-flex size-11 items-center justify-center rounded-lg border border-garis bg-permukaan text-teks"
            >
              <X aria-hidden="true" className="size-5" />
            </button>
          </div>

          <nav className="flex flex-col gap-1" aria-label="Menu utama">
            {daftarMenu.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                aria-current={item.aktif ? "page" : undefined}
                onClick={tutupLaci}
                className={KELAS_ITEM_MENU}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="mt-auto flex flex-col gap-3 border-t border-garis pt-4">
            {((varian === "pengajar" && statusLangganan) || nama) && (
              <div className="flex items-center gap-2">
                {varian === "pengajar" && statusLangganan && (
                  <Lencana varian={statusLangganan} />
                )}
                {nama && <span>{nama}</span>}
              </div>
            )}
            <button
              type="button"
              onClick={tanganiKeluar}
              disabled={sedangKeluar}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks disabled:opacity-50"
            >
              {sedangKeluar ? (
                <Spinner ukuran="size-4" />
              ) : (
                <LogOut aria-hidden="true" className="size-4" />
              )}
              Keluar
            </button>
          </div>
        </aside>
      </dialog>
    </>
  );
}

export default BilahAtas;
