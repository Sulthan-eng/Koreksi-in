import { useParams } from "react-router-dom";

function HalamanBatch() {
  const { id } = useParams();

  return (
    <div className="min-h-screen bg-latar p-8">
      <h1 className="text-xl font-semibold text-teks">Halaman Batch</h1>
      <p className="text-teks-redup">ID Batch: {id}</p>
    </div>
  );
}

export default HalamanBatch;
