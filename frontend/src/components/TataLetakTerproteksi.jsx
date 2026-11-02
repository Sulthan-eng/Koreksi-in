import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import BilahAtas from "./BilahAtas.jsx";

function TataLetakTerproteksi() {
  const { status, keluarSengaja } = useAuth();

  if (status !== "terautentikasi") {
    return <Navigate to={keluarSengaja ? "/" : "/masuk"} replace />;
  }

  return (
    <>
      <BilahAtas />
      <Outlet />
    </>
  );
}

export default TataLetakTerproteksi;
