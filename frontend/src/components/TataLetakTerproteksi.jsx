import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { berandaUntukPeran } from "../lib/peran.js";
import BilahAtas from "./BilahAtas.jsx";

function TataLetakTerproteksi({ peran }) {
  const { status, keluarSengaja, peran: peranPengguna } = useAuth();

  if (status !== "terautentikasi") {
    return <Navigate to={keluarSengaja ? "/" : "/masuk"} replace />;
  }

  if (peran && peranPengguna !== peran) {
    return <Navigate to={berandaUntukPeran(peranPengguna)} replace />;
  }

  return (
    <>
      <BilahAtas varian={peran || "pengajar"} />
      <Outlet />
    </>
  );
}

export default TataLetakTerproteksi;
