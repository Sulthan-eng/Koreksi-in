import { useEffect, useRef, useState } from "react";
import { MoreVertical } from "lucide-react";

function MenuAksi({ label, aksi, nonaktif = false }) {
  const [terbuka, setTerbuka] = useState(false);
  const pembungkusRef = useRef(null);
  const tombolRef = useRef(null);
  const itemRefs = useRef([]);

  useEffect(() => {
    itemRefs.current = itemRefs.current.slice(0, aksi.length);
  }, [aksi.length]);

  useEffect(() => {
    if (!terbuka) return;
    function tanganiKlikLuar(peristiwa) {
      if (!pembungkusRef.current?.contains(peristiwa.target)) {
        setTerbuka(false);
      }
    }
    document.addEventListener("mousedown", tanganiKlikLuar);
    return () => document.removeEventListener("mousedown", tanganiKlikLuar);
  }, [terbuka]);

  function tutupDanFokusTombol() {
    setTerbuka(false);
    tombolRef.current?.focus();
  }

  function pilihItem(item) {
    tombolRef.current?.focus();
    setTerbuka(false);
    item.onPilih();
  }

  function tanganiPapanKetikTombol(peristiwa) {
    if (nonaktif) return;
    if (peristiwa.key === "ArrowDown" || peristiwa.key === "ArrowUp") {
      peristiwa.preventDefault();
      setTerbuka(true);
      const indeks = peristiwa.key === "ArrowDown" ? 0 : aksi.length - 1;
      requestAnimationFrame(() => itemRefs.current[indeks]?.focus());
    }
  }

  function tanganiPapanKetikMenu(peristiwa) {
    const indeksSaatIni = itemRefs.current.indexOf(document.activeElement);
    if (peristiwa.key === "ArrowDown" || peristiwa.key === "ArrowUp") {
      peristiwa.preventDefault();
      const berikutnya =
        peristiwa.key === "ArrowDown"
          ? (indeksSaatIni + 1) % aksi.length
          : (indeksSaatIni - 1 + aksi.length) % aksi.length;
      itemRefs.current[berikutnya]?.focus();
    } else if (peristiwa.key === "Escape") {
      peristiwa.preventDefault();
      tutupDanFokusTombol();
    } else if (peristiwa.key === "Tab") {
      setTerbuka(false);
    }
  }

  return (
    <div className="relative" ref={pembungkusRef}>
      <button
        type="button"
        ref={tombolRef}
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={terbuka}
        aria-disabled={nonaktif || undefined}
        onClick={() => {
          if (nonaktif) return;
          setTerbuka((sebelumnya) => !sebelumnya);
        }}
        onKeyDown={tanganiPapanKetikTombol}
        className={`inline-flex size-11 items-center justify-center rounded-lg border border-garis bg-permukaan text-teks ${
          nonaktif ? "opacity-50" : ""
        }`}
      >
        <MoreVertical className="size-5" aria-hidden="true" />
      </button>
      {terbuka && (
        <div
          role="menu"
          onKeyDown={tanganiPapanKetikMenu}
          className="absolute top-full right-0 z-10 mt-1 flex min-w-48 flex-col gap-0.5 rounded-lg border border-garis bg-permukaan p-1 shadow-sm"
        >
          {aksi.map((item, indeks) => (
            <button
              key={item.key}
              type="button"
              role="menuitem"
              ref={(elemen) => (itemRefs.current[indeks] = elemen)}
              onClick={() => pilihItem(item)}
              className={`flex min-h-11 items-center rounded-md px-3 text-left hover:bg-biru-muda focus-visible:bg-biru-muda ${
                item.varian === "merusak" ? "text-kurang-mirip" : "text-teks"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default MenuAksi;
