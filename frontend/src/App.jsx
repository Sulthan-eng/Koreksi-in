import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext.jsx";
import Spinner from "./components/Spinner.jsx";
import TataLetakTerproteksi from "./components/TataLetakTerproteksi.jsx";
import Masuk from "./pages/Masuk.jsx";
import Daftar from "./pages/Daftar.jsx";
import Beranda from "./pages/Beranda.jsx";
import HalamanBatch from "./pages/HalamanBatch.jsx";

function RouteTamu({ children }) {
  const { status } = useAuth();
  if (status === "terautentikasi") {
    return <Navigate to="/" replace />;
  }
  return children;
}

function Rute() {
  const { status } = useAuth();

  if (status === "memuat") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-latar">
        <Spinner ukuran="size-5" />
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/masuk"
        element={
          <RouteTamu>
            <Masuk />
          </RouteTamu>
        }
      />
      <Route
        path="/daftar"
        element={
          <RouteTamu>
            <Daftar />
          </RouteTamu>
        }
      />
      <Route element={<TataLetakTerproteksi />}>
        <Route path="/" element={<Beranda />} />
        <Route path="/batch/:id" element={<HalamanBatch />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Rute />
    </AuthProvider>
  );
}

export default App;
