import { useEffect } from "react";
import { useBlocker } from "react-router-dom";

export function useKonfirmasiTinggalkan(adaDataBelumTerkirim) {
  const blocker = useBlocker(() => adaDataBelumTerkirim);

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
