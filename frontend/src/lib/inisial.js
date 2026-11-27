export function inisialDariNama(nama) {
  if (typeof nama !== "string") return "";
  const kata = nama.trim().split(/\s+/).filter(Boolean);
  if (kata.length === 0) return "";
  if (kata.length === 1) return kata[0].slice(0, 1).toUpperCase();
  return (
    kata[0].slice(0, 1) + kata[kata.length - 1].slice(0, 1)
  ).toUpperCase();
}
