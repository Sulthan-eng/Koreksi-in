export function kartuRingkasan(ringkasan) {
  const kartu = [
    { label: "Total batch", nilai: ringkasan.total_batch },
    {
      label: "Peserta didik sudah dikoreksi",
      nilai: ringkasan.peserta_didik_dikoreksi,
    },
  ];
  if (ringkasan.sisa_slot_batch_aktif !== null) {
    kartu.push({
      label: "Sisa slot batch aktif",
      nilai: ringkasan.sisa_slot_batch_aktif,
    });
  }
  if (ringkasan.sisa_slot_jawaban_per_batch !== null) {
    kartu.push({
      label: "Sisa slot jawaban per batch",
      nilai: ringkasan.sisa_slot_jawaban_per_batch,
    });
  }
  return kartu;
}
