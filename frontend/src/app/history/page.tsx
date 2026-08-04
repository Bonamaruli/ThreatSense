'use client'

import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Globe, Mail, File as FileIcon, Loader2, Search, Inbox } from 'lucide-react'

import RequireAuth from '@/components/RequireAuth'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import { dashboardApi } from '@/lib/services'
import type { ScanResult, ScanType } from '@/types'

type FilterTipe = 'semua' | 'url' | 'email' | 'file'
type FilterStatus = 'semua' | 'aman' | 'mencurigakan' | 'berbahaya'

const gayaStatus: Record<string, string> = {
  aman: 'text-green-400 bg-green-500/10 border-green-500/20',
  mencurigakan: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  berbahaya: 'text-red-400 bg-red-500/10 border-red-500/20',
}

const ikonTipe: Record<ScanType, typeof Globe> = {
  url: Globe,
  email: Mail,
  file: FileIcon,
}

function waktuLengkap(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleString('id-ID', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function HistoryPage() {
  const [typeFilter, setTypeFilter] = useState<FilterTipe>('semua')
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('semua')
  const [cari, setCari] = useState('')

  const [data, setData] = useState<ScanResult[]>([])
  const [memuat, setMemuat] = useState(true)
  const [pesanError, setPesanError] = useState<string | null>(null)

  // Riwayat diambil dari server. Sebelumnya halaman ini hanya punya tombol
  // filter tanpa data apa pun di belakangnya, jadi filternya tidak pernah
  // benar-benar menyaring sesuatu.
  useEffect(() => {
    let batal = false

    dashboardApi
      .getRecentScans(100)
      .then((r) => {
        if (batal) return
        if (r.success && r.data) setData(r.data)
        else setPesanError(r.error?.message ?? 'Gagal memuat riwayat.')
      })
      .catch((e: any) => {
        if (!batal) setPesanError(e?.message ?? 'Gagal memuat riwayat.')
      })
      .finally(() => {
        if (!batal) setMemuat(false)
      })

    return () => {
      batal = true
    }
  }, [])

  // Penyaringan dilakukan di browser karena jumlah barisnya kecil (maksimal
  // 100). Kalau nanti riwayatnya ribuan, penyaringan sebaiknya dipindah ke
  // server supaya tidak semua data dikirim dulu ke browser.
  const terlihat = useMemo(() => {
    const kunci = cari.trim().toLowerCase()
    return data.filter((r) => {
      if (typeFilter !== 'semua' && r.type !== typeFilter) return false
      if (statusFilter !== 'semua' && r.status !== statusFilter) return false
      if (kunci && !r.input.toLowerCase().includes(kunci)) return false
      return true
    })
  }, [data, typeFilter, statusFilter, cari])

  const typeFilters: { id: FilterTipe; label: string }[] = [
    { id: 'semua', label: 'Semua' },
    { id: 'url', label: 'URL' },
    { id: 'email', label: 'Email' },
    { id: 'file', label: 'File' },
  ]

  const statusFilters: { id: FilterStatus; label: string }[] = [
    { id: 'semua', label: 'Semua' },
    { id: 'aman', label: 'Aman' },
    { id: 'mencurigakan', label: 'Mencurigakan' },
    { id: 'berbahaya', label: 'Berbahaya' },
  ]

  return (
    <motion.div
      className="min-h-screen bg-[#0a0a0f] text-white"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Sidebar />

      <main className="ml-64">
        <Header title="Riwayat Scan" subtitle="Semua pemeriksaan dari akun kamu" />

        <div className="p-8">
          {pesanError && (
            <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
              {pesanError}
            </div>
          )}

          {/* Pencarian dan filter */}
          <div className="mb-6 space-y-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={cari}
                onChange={(e) => setCari(e.target.value)}
                placeholder="Cari di riwayat..."
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50"
              />
            </div>

            <div className="flex flex-wrap gap-6">
              <div>
                <p className="text-xs text-gray-500 mb-2">Tipe</p>
                <div className="flex gap-2">
                  {typeFilters.map((f) => (
                    <button
                      key={f.id}
                      onClick={() => setTypeFilter(f.id)}
                      className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                        typeFilter === f.id
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                          : 'bg-white/5 text-gray-400 border border-white/10 hover:text-white'
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs text-gray-500 mb-2">Status</p>
                <div className="flex gap-2">
                  {statusFilters.map((f) => (
                    <button
                      key={f.id}
                      onClick={() => setStatusFilter(f.id)}
                      className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                        statusFilter === f.id
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                          : 'bg-white/5 text-gray-400 border border-white/10 hover:text-white'
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Daftar riwayat */}
          <div className="bg-[#0d1117] border border-white/5 rounded-xl p-6">
            {memuat ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
              </div>
            ) : terlihat.length === 0 ? (
              <div className="text-center py-14">
                <div className="w-14 h-14 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Inbox className="w-7 h-7 text-gray-500" />
                </div>
                <h3 className="text-lg font-bold mb-1">
                  {data.length === 0 ? 'Belum ada riwayat' : 'Tidak ada yang cocok'}
                </h3>
                <p className="text-gray-400 text-sm">
                  {data.length === 0
                    ? 'Lakukan scan pertama kamu, hasilnya akan tersimpan di sini.'
                    : 'Coba ubah kata kunci atau filternya.'}
                </p>
              </div>
            ) : (
              <>
                <p className="text-xs text-gray-500 mb-4">
                  Menampilkan {terlihat.length} dari {data.length} riwayat
                </p>
                <ul className="space-y-2">
                  {terlihat.map((r) => {
                    const Ikon = ikonTipe[r.type] ?? Globe
                    const gaya =
                      gayaStatus[r.status] ??
                      'text-gray-400 bg-gray-500/10 border-gray-500/20'

                    return (
                      <li
                        key={r.id}
                        className="flex items-center gap-4 rounded-lg border border-white/5 bg-black/20 p-3 hover:border-white/10 transition-colors"
                      >
                        <Ikon className="w-4 h-4 text-gray-500 flex-shrink-0" />
                        {/* min-w-0 wajib agar truncate bekerja di dalam flex */}
                        <span className="flex-1 min-w-0 truncate text-sm">{r.input}</span>
                        <span className="text-xs text-gray-500 flex-shrink-0 hidden md:block">
                          {waktuLengkap(r.timestamp)}
                        </span>
                        <span
                          className={`text-xs px-2 py-1 rounded border flex-shrink-0 ${gaya}`}
                        >
                          {Math.round((r.score ?? 0) * 100)}%
                        </span>
                      </li>
                    )
                  })}
                </ul>
              </>
            )}
          </div>
        </div>
      </main>
    </motion.div>
  )
}

// Halaman Riwayat hanya untuk pengguna yang sudah masuk.
// Penjagaan sesungguhnya ada di backend - lihat catatan di RequireAuth.tsx.
export default function HalamanHistoryPage() {
  return (
    <RequireAuth>
      <HistoryPage />
    </RequireAuth>
  )
}
