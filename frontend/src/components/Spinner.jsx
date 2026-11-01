import { LoaderCircle } from "lucide-react";

function Spinner({ ukuran = "size-4" }) {
  return (
    <LoaderCircle
      aria-hidden="true"
      className={`animate-spin motion-reduce:animate-none ${ukuran}`}
    />
  );
}

export default Spinner;
