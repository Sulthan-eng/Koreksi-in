import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import {
  jenisInputPassword,
  labelTombolPassword,
} from "../lib/kolomPassword.js";
import KolomIsian from "./KolomIsian.jsx";

function KolomPassword({
  id,
  label,
  value,
  onChange,
  autoComplete,
  placeholder,
  petunjuk,
  galat,
  ariaInvalid,
  ariaDescribedby,
  Ikon,
}) {
  const [tampilkan, setTampilkan] = useState(false);

  return (
    <KolomIsian
      id={id}
      label={label}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      petunjuk={petunjuk}
      galat={galat}
      ariaInvalid={ariaInvalid}
      ariaDescribedby={ariaDescribedby}
      Ikon={Ikon}
      type={jenisInputPassword(tampilkan)}
      autoComplete={autoComplete}
      autoCapitalize="off"
      autoCorrect="off"
      spellCheck={false}
      kelasInputTambahan="pr-11"
      anak={
        <button
          type="button"
          onMouseDown={(peristiwa) => peristiwa.preventDefault()}
          onClick={() => setTampilkan((sebelumnya) => !sebelumnya)}
          aria-label={labelTombolPassword(tampilkan)}
          className="absolute inset-y-0 right-0 flex min-h-11 min-w-11 items-center justify-center text-teks-redup"
        >
          {tampilkan ? (
            <EyeOff className="size-5" aria-hidden="true" />
          ) : (
            <Eye className="size-5" aria-hidden="true" />
          )}
        </button>
      }
    />
  );
}

export default KolomPassword;
