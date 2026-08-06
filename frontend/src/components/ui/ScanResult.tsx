'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheck, ShieldAlert, ShieldX, X, Info, Search,
  ThumbsUp, ThumbsDown, Check,
} from 'lucide-react';
import type { ScanResult as ScanResultType, ScanStatus } from '@/types';
import { feedbackApi } from '@/lib/services';

interface ScanResultProps {
  result: ScanResultType;
  onClose?: () => void;
}

/**
 * Tampilan per tingkat bahaya.
 * Warnanya sengaja mengikuti pola Alert.tsx supaya seragam.
 */
const statusConfig: Record<
  string,
  { icon: typeof ShieldCheck; label: string; colors: string; iconBg: string; bar: string }
> = {
  aman: {
    icon: ShieldCheck,
    label: 'Aman',
    colors: 'bg-green-500/10 border-green-500/20 text-green-400',
    iconBg: 'bg-green-500/20',
    bar: 'bg-green-500',
  },
  mencurigakan: {
    icon: ShieldAlert,
    label: 'Mencurigakan',
    colors: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
    iconBg: 'bg-amber-500/20',
    bar: 'bg-amber-500',
  },
  berbahaya: {
    icon: ShieldX,
    label: 'Berbahaya',
    colors: 'bg-red-500/10 border-red-500/20 text-red-400',
    iconBg: 'bg-red-500/20',
    bar: 'bg-red-500',
  },
};

const fallbackConfig = {
  icon: Info,
  label: 'Tidak diketahui',
  colors: 'bg-gray-500/10 border-gray-500/20 text-gray-400',
  iconBg: 'bg-gray-500/20',
  bar: 'bg-gray-500',
};

function configFor(status: ScanStatus) {
  return statusConfig[status] ?? fallbackConfig;
}

export function ScanResult({ result, onClose }: ScanResultProps) {
  const config = configFor(result.status);
  const Icon = config.icon;
  const persen = Math.round((result.score ?? 0) * 100);
  const explanations = result.details?.explanations ?? [];
  const bukti = result.details?.evidenceSummary ?? [];
  const mendalam = Boolean(result.details?.deepScan);

  // Koreksi pengguna. Inilah yang membuat model bisa membaik dari waktu ke
  // waktu - setiap koreksi jadi bahan pelatihan berikutnya.
  const [koreksiTerkirim, setKoreksiTerkirim] = React.useState<string | null>(null);
  const [mengirim, setMengirim] = React.useState(false);

  const kirimKoreksi = async (koreksi: 'safe' | 'malicious') => {
    if (mengirim || koreksiTerkirim) return;
    setMengirim(true);
    const r = await feedbackApi.kirim(result.id, koreksi);
    if (r.success) {
      setKoreksiTerkirim(koreksi);
    }
    setMengirim(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.35 }}
      className={`rounded-2xl border p-5 sm:p-6 ${config.colors}`}
    >
      {/* --- Kepala: status, skor, alamat --- */}
      <div className="flex items-start gap-4">
        <div
          className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${config.iconBg}`}
        >
          <Icon className="w-6 h-6" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-3 flex-wrap">
            <h3 className="text-xl font-bold">{config.label}</h3>
            <span className="text-2xl font-bold tabular-nums">{persen}%</span>
          </div>

          {/* break-all supaya URL panjang tidak melebarkan layar di HP */}
          <p className="text-sm text-gray-400 mt-1 break-all">{result.input}</p>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            aria-label="Tutup hasil scan"
            className="p-1 hover:bg-white/10 rounded transition-colors flex-shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* --- Batang skor --- */}
      <div className="mt-4 h-2 w-full bg-white/10 rounded-full overflow-hidden">
        <motion.div
          className={`h-full ${config.bar}`}
          initial={{ width: 0 }}
          animate={{ width: `${persen}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>

      {/* --- Alasan --- */}
      {/*
        Bagian inilah yang paling berguna bagi pengguna. Angka "90%" saja
        tidak memberi tahu apa pun; "menyebut bri padahal bukan domain resmi
        BRI" langsung bisa dimengerti dan ditindaklanjuti.
      */}
      {explanations.length > 0 && (
        <div className="mt-5">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">
            Alasan penilaian
          </h4>

          <ul className="space-y-2.5">
            {explanations.map((e, i) => (
              <motion.li
                key={`${e.judul}-${i}`}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + i * 0.07 }}
                className="rounded-lg bg-black/20 border border-white/5 p-3"
              >
                <div className="flex items-center justify-between gap-3 mb-1">
                  <span className="font-semibold text-sm text-white">
                    {e.judul}
                  </span>
                  {/* Bobot 0 dipakai untuk catatan netral, jadi tidak perlu label */}
                  {e.bobot > 0 && (
                    <span className="text-xs tabular-nums opacity-70 flex-shrink-0">
                      +{Math.round(e.bobot * 100)}%
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">
                  {e.alasan}
                </p>
              </motion.li>
            ))}
          </ul>
        </div>
      )}

      {/* --- Bukti hasil pemeriksaan mendalam --- */}
      {/*
        Ditampilkan sebagai daftar netral, termasuk yang menenangkan. Inilah
        yang membedakan "kesimpulan" dari "tuduhan": pengguna bisa melihat
        sendiri dasar penilaiannya dan menilai ulang kalau tidak setuju.
      */}
      {/* Ditampilkan kapan pun buktinya ADA, tidak khusus pemindaian mendalam.
          Hasil File Scanner juga membawa bukti (jenis berkas sebenarnya,
          entropi, SHA-256) padahal deep_scan-nya bernilai false - kalau
          syaratnya dipatok ke deep_scan, bukti itu tidak akan pernah tampil. */}
      {bukti.length > 0 && (
        <div className="mt-5">
          <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">
            <Search className="w-3.5 h-3.5" />
            Bukti yang dikumpulkan
          </h4>

          <div className="rounded-lg bg-black/20 border border-white/5 divide-y divide-white/5">
            {bukti.map((b, i) => (
              <motion.div
                key={`${b.label}-${i}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.05 + i * 0.03 }}
                className="flex items-start justify-between gap-4 px-3 py-2"
              >
                <span className="text-xs text-gray-500 flex-shrink-0">{b.label}</span>
                <span className="text-xs text-gray-200 text-right break-all">
                  {b.nilai}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* --- Koreksi pengguna --- */}
      {/*
        Kalau penilaiannya salah, koreksi di sini langsung jadi bahan
        pelatihan model berikutnya. Ditaruh di hasil scan, bukan disembunyikan
        di menu - saat inilah pengguna paling tahu jawaban yang benar.
      */}
      <div className="mt-5 pt-4 border-t border-white/10">
        {koreksiTerkirim ? (
          <p className="flex items-center gap-2 text-xs text-green-400">
            <Check className="w-3.5 h-3.5" />
            Terima kasih. Koreksimu tersimpan dan akan dipakai melatih model
            berikutnya.
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs text-gray-500">Menurutmu penilaian ini salah?</span>
            <button
              type="button"
              disabled={mengirim}
              onClick={() => kirimKoreksi('safe')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 text-xs text-gray-300 hover:bg-white/5 transition-colors disabled:opacity-50"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
              Sebenarnya aman
            </button>
            <button
              type="button"
              disabled={mengirim}
              onClick={() => kirimKoreksi('malicious')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 text-xs text-gray-300 hover:bg-white/5 transition-colors disabled:opacity-50"
            >
              <ThumbsDown className="w-3.5 h-3.5" />
              Sebenarnya berbahaya
            </button>
          </div>
        )}
      </div>

      {/* --- Batasan yang diakui terbuka --- */}
      {/*
        Ditulis di layar, bukan cuma di laporan, supaya pengguna tidak merasa
        terlalu aman setelah melihat label "Aman". Kalimatnya dibedakan per
        jenis scan karena batas masing-masing memang berbeda.
      */}
      {/*
        Kalimat batasannya HARUS ikut berubah saat pemeriksaan mendalam.
        Sebelumnya selalu tertulis "hanya membaca nama domain" - padahal di
        pemindaian mendalam halamannya benar-benar dibuka, dan buktinya
        terpampang tepat di atas kalimat itu. Keterangan yang bertentangan
        dengan isi layarnya sendiri membuat seluruh hasil jadi tidak
        meyakinkan.
      */}
      <p className="mt-5 pt-4 border-t border-white/10 text-xs text-gray-500 leading-relaxed">
        {result.type === 'email'
          ? 'Pemeriksaan ini membaca header dan isi email, tapi belum memverifikasi keaslian pengirim lewat SPF/DKIM. Pemalsuan alamat pengirim yang rapi masih mungkin lolos.'
          : result.type === 'file'
          ? 'Pemeriksaan file masih terbatas dan belum membuka isi berkasnya. Jangan jadikan hasil ini satu-satunya dasar keputusan.'
          : mendalam
          ? 'Halaman ini benar-benar dibuka dan dibaca, tapi tanpa menjalankan skrip di dalamnya. Halaman yang isinya baru muncul setelah skrip berjalan belum bisa diperiksa.'
          : 'Pemeriksaan ini baru menganalisis nama domain, belum membuka isi halamannya. Nyalakan Pemeriksaan mendalam untuk bukti yang lebih meyakinkan.'}
        {' '}Tetap berhati-hati sebelum memasukkan data pribadi.
      </p>
    </motion.div>
  );
}
