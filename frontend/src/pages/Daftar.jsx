import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as auth from "../api/auth.js";
import PesanForm from "../components/PesanForm.jsx";
import Spinner from "../components/Spinner.jsx";

function Daftar() {
  const [nama, setNama] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [kesalahan, setKesalahan] = useState(null);
  const [sedangKirim, setSedangKirim] = useState(false);
  const navigate = useNavigate();

  async function tanganiSubmit(peristiwa) {
    peristiwa.preventDefault();
    setSedangKirim(true);
    setKesalahan(null);
    try {
      await auth.daftar({ nama, email, password });
      navigate("/masuk", {
        state: { pesan: "Akun berhasil dibuat, silakan masuk" },
      });
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
          Daftar
        </h1>

        {kesalahan && (
          <PesanForm
            varian="galat"
            pesan={kesalahan}
            className="mb-4 text-center"
          />
        )}

        <form onSubmit={tanganiSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="nama"
              className="mb-1 block text-sm text-teks-redup"
            >
              Nama
            </label>
            <input
              id="nama"
              type="text"
              required
              value={nama}
              onChange={(peristiwa) => setNama(peristiwa.target.value)}
              className="w-full rounded-md border border-garis bg-permukaan px-3 py-2 text-teks"
            />
          </div>
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
            className="flex w-full items-center justify-center gap-2 rounded-md bg-biru-utama px-3 py-2 text-permukaan disabled:opacity-50"
          >
            {sedangKirim && <Spinner ukuran="size-4" />}
            Daftar
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-teks-redup">
          Sudah punya akun?{" "}
          <Link to="/masuk" className="text-biru-utama">
            Masuk
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Daftar;
