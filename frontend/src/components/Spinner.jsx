import { LoaderCircle } from "lucide-react";

function Spinner({ ukuran = "size-4", className = "" }) {
  const kelasUkuran = className || ukuran;
  return (
    <LoaderCircle
      aria-hidden="true"
      className={`animate-spin motion-reduce:animate-none ${kelasUkuran}`.trim()}
    />
  );
}

export default Spinner;
