import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import Spinner from "./Spinner.jsx";

function BilahAtas() {
  const { nama, keluar } = useAuth();
  const navigate = useNavigate();
  const [sedangKeluar, setSedangKeluar] = useState(false);

  async function tanganiKeluar() {
    setSedangKeluar(true);
    try {
      await keluar();
    } finally {
      navigate("/masuk", { replace: true });
    }
  }

  return (
    <header className="flex items-center justify-between border-b border-garis bg-permukaan px-8 py-5">
      <div className="flex items-center gap-3">
        <img src="/logo-ikon.png" alt="Koreksi-in" className="h-10" />
        <span className="text-lg font-semibold text-teks">Koreksi-in</span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-teks-redup">{nama}</span>
        <button
          type="button"
          onClick={tanganiKeluar}
          disabled={sedangKeluar}
          className="flex items-center gap-2 rounded-md border border-garis px-4 py-2 text-teks disabled:opacity-50"
        >
          {sedangKeluar && <Spinner className="h-4 w-4" />}
          Keluar
        </button>
      </div>
    </header>
  );
}

export default BilahAtas;
