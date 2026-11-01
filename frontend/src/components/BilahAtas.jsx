import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { LogOut, Menu, X } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import Lencana from "./Lencana.jsx";
import Spinner from "./Spinner.jsx";

const KELAS_ITEM_MENU =
  "inline-flex min-h-11 items-center rounded-lg px-3 font-semibold text-teks no-underline aria-[current=page]:bg-biru-muda aria-[current=page]:text-biru-utama";

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

function BilahAtas({ varian = "pengajar", statusLangganan = null }) {
  const { nama, keluar } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [sedangKeluar, setSedangKeluar] = useState(false);
  const [laciTerbuka, setLaciTerbuka] = useState(false);
  const tombolBukaRef = useRef(null);
  const dialogRef = useRef(null);

  const daftarMenu = dapatkanDaftarMenu(varian, pathname);

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
      navigate("/masuk", { replace: true });
    }
  }

  return (
    <>
      <header className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-garis bg-permukaan px-4 py-3 text-teks">
        <img src="/logo-ikon.png" alt="" className="h-10 w-auto" />
        <span className="text-lg font-bold">Koreksi-in</span>

        {varian === "publik" ? (
          <div className="ml-auto flex items-center gap-3">
            <Link
              to="/masuk"
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-garis bg-permukaan px-4 font-semibold text-teks no-underline"
            >
              Masuk
            </Link>
            <Link
              to="/daftar"
              className="inline-flex min-h-11 items-center justify-center rounded-lg border border-biru-utama bg-biru-utama px-4 font-semibold text-permukaan no-underline"
            >
              Daftar
            </Link>
          </div>
        ) : (
          <>
            <nav
              className="hidden flex-wrap gap-1 lg:flex"
              aria-label="Menu utama"
            >
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
              className="ml-auto inline-flex min-h-11 size-11 items-center justify-center rounded-lg border border-garis bg-permukaan text-teks lg:hidden"
            >
              <Menu aria-hidden="true" className="size-5" />
            </button>
          </>
        )}
      </header>

      {varian !== "publik" && (
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
                className="inline-flex min-h-11 size-11 items-center justify-center rounded-lg border border-garis bg-permukaan text-teks"
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
      )}
    </>
  );
}

export default BilahAtas;
