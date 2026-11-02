import { useEffect } from "react";
import { useBlocker } from "react-router-dom";

/**
 * Memblokir navigasi (bila argumen dipenuhi) dan menutup tab.
 * bolehLewatRef (opsional) adalah ref boolean dari pemanggil: bila berisi
 * true, pemblokir navigasi diam — dipakai contohnya setelah batch berhasil
 * dihapus atau diselesaikan, ketika halaman memang harus ditinggalkan.
 * Ref dibaca langsung pada saat navigasi, bukan nilai hasil render, agar
 * berpindah halaman di tick yang sama tetap melewati pemblokir.
 */
export function useKonfirmasiTinggalkan(adaDataBelumTerkirim, bolehLewatRef) {
  const blocker = useBlocker(
    () => !bolehLewatRef?.current && adaDataBelumTerkirim,
  );

  useEffect(() => {
    if (!adaDataBelumTerkirim) return;

    function tanganiBeforeUnload(peristiwa) {
      peristiwa.preventDefault();
      peristiwa.returnValue = "";
    }

    window.addEventListener("beforeunload", tanganiBeforeUnload);
    return () =>
      window.removeEventListener("beforeunload", tanganiBeforeUnload);
  }, [adaDataBelumTerkirim]);

  return blocker;
}
