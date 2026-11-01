import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import * as auth from "../api/auth.js";
import { useAuth } from "../context/AuthContext.jsx";
import Spinner from "../components/Spinner.jsx";

function Masuk() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [kesalahan, setKesalahan] = useState(null);
  const [sedangKirim, setSedangKirim] = useState(false);
  const { tandaiMasuk, pesanSesi, bersihkanPesanSesi } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [pesanFlash] = useState(
    () => location.state?.pesan ?? pesanSesi ?? null,
  );

  useEffect(() => {
    if (location.state?.pesan) {
      navigate(location.pathname, { replace: true, state: null });
    }
  }, [location, navigate]);

  useEffect(() => {
    if (pesanSesi) {
      bersihkanPesanSesi();
    }
  }, [pesanSesi, bersihkanPesanSesi]);

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    setSedangKirim(true);
    setKesalahan(null);
    try {
      await auth.masuk({ email, password });
      const hasil = await auth.saya();
      tandaiMasuk(hasil.nama);
      navigate("/", { replace: true });
    } catch (error) {
      setKesalahan(error.pesan);
      setSedangKirim(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-latar">
      <div className="w-full max-w-sm rounded-lg border-2 border-garis bg-permukaan p-8 shadow-sm">
        <img src="/logo.png" alt="Koreksi-in" className="mx-auto mb-6 h-16" />
        <h1 className="mb-4 text-center text-xl font-semibold text-teks">
          Masuk
        </h1>

        {pesanFlash && (
          <p className="mb-4 text-center text-teks-redup">{pesanFlash}</p>
        )}
        {kesalahan && (
          <p role="alert" className="mb-4 text-center text-kurang-mirip">
            {kesalahan}
          </p>
        )}

        <form onSubmit={tanganiSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm text-teks-redup"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(peristiwa) => setEmail(peristiwa.target.value)}
              className="w-full rounded-md border border-garis bg-permukaan px-3 py-2 text-teks"
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm text-teks-redup"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(peristiwa) => setPassword(peristiwa.target.value)}
              className="w-full rounded-md border border-garis bg-permukaan px-3 py-2 text-teks"
            />
          </div>
          <button
            type="submit"
            disabled={sedangKirim}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-biru-utama px-3 py-2 text-white disabled:opacity-50"
          >
            {sedangKirim && <Spinner ukuran="size-4" />}
            Masuk
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-teks-redup">
          Belum punya akun?{" "}
          <Link to="/daftar" className="text-biru-utama">
            Daftar
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Masuk;
