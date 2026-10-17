import { Route, Routes } from "react-router-dom";
import Masuk from "./pages/Masuk.jsx";
import Daftar from "./pages/Daftar.jsx";
import Beranda from "./pages/Beranda.jsx";
import HalamanBatch from "./pages/HalamanBatch.jsx";

function App() {
  return (
    <Routes>
      <Route path="/masuk" element={<Masuk />} />
      <Route path="/daftar" element={<Daftar />} />
      <Route path="/" element={<Beranda />} />
      <Route path="/batch/:id" element={<HalamanBatch />} />
    </Routes>
  );
}

export default App;
