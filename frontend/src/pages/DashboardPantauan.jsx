import KeadaanData from "../components/KeadaanData.jsx";

function DashboardPantauan() {
  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6">
      <h1 className="text-2xl font-bold leading-8 text-teks">Dashboard Pantauan</h1>
      <KeadaanData keadaan="kosong" pesan="Dashboard Pantauan belum tersedia." />
    </main>
  );
}

export default DashboardPantauan;
