import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import BilahAtas from "./BilahAtas.jsx";

function TataLetakTerproteksi() {
  const { status } = useAuth();

  if (status !== "terautentikasi") {
    return <Navigate to="/masuk" replace />;
  }

  return (
    <>
      <BilahAtas />
      <Outlet />
    </>
  );
}

export default TataLetakTerproteksi;
