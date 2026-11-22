export const BATAS_GAGAL_POLLING = 3;

/**
 * Hitung status kegagalan beruntun untuk polling status pemrosesan.
 *
 * - Saat berhasil: hitungan gagal beruntun direset ke 0 dan polling berlanjut.
 * - Saat gagal: hitungan bertambah 1; polling berhenti hanya bila mencapai batas.
 */
export function catatHasilPolling(
  gagalBeruntunSaatIni,
  berhasil,
  batas = BATAS_GAGAL_POLLING,
) {
  if (berhasil) {
    return { gagalBeruntun: 0, berhenti: false };
  }
  const gagalBeruntun = gagalBeruntunSaatIni + 1;
  return {
    gagalBeruntun,
    berhenti: gagalBeruntun >= batas,
  };
}
