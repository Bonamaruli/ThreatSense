'use client'

import { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Plus,
  Shield,
  Loader2,
  Globe,
  Mail,
  File as FileIcon,
} from 'lucide-react'
import { motion } from 'framer-motion'

import RequireAuth from '@/components/RequireAuth'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import { dashboardApi } from '@/lib/services'
import type { DashboardStats, ScanResult, ScanStatus, ScanType } from '@/types'

/** Warna dan label per status, dipakai bersama kartu riwayat. */
const gayaStatus: Record<string, { warna: string; label: string }> = {
  aman: { warna: 'text-green-400 bg-green-500/10 border-green-500/20', label: 'Aman' },
  mencurigakan: { warna: 'text-amber-400 bg-amber-500/10 border-amber-500/20', label: 'Mencurigakan' },
  berbahaya: { warna: 'text-red-400 bg-red-500/10 border-red-500/20', label: 'Berbahaya' },
}

const ikonTipe: Record<ScanType, typeof Globe> = {
  url: Globe,
  email: Mail,
  file: FileIcon,
}

function waktuSingkat(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleString('id-ID', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [riwayat, setRiwayat] = useState<ScanResult[]>([])
  const [memuat, setMemuat] = useState(true)
  const [pesanError, setPesanError] = useState<string | null>(null)

  // Data diambil dari server setiap halaman dibuka.
  //
  // Sebelumnya seluruh angka di halaman ini ditulis mati sebagai "0" dan
  // tidak pernah memanggil API sama sekali - jadi berapa pun jumlah scan
  // yang sudah dilakukan, tampilannya tetap nol.
  useEffect(() => {
    let batal = false

    Promise.all([dashboardApi.getStats(), dashboardApi.getRecentScans(8)])
      .then(([s, r]) => {
        if (batal) return
        if (s.success && s.data) setStats(s.data)
        else setPesanError(s.error?.message ?? 'Gagal memuat statistik.')
        if (r.success && r.data) setRiwayat(r.data)
      })
      .catch((e: any) => {
        if (!batal) setPesanError(e?.message ?? 'Gagal memuat data.')
      })
      .finally(() => {
        if (!batal) setMemuat(false)
      })

    return () => {
      batal = true
    }
  }, [])

  const kartu = [
    {
      icon: <Activity className="w-5 h-5 text-cyan-400" />,
      label: 'Total Scan',
      value: stats?.totalScans ?? 0,
      subtext: 'Seluruh pemeriksaan kamu',
      borderColor: 'border-cyan-500/20',
      bgColor: 'bg-cyan-500/10',
      hoverBorder: 'hover:border-cyan-500/50',
    },
    {
      icon: <AlertTriangle className="w-5 h-5 text-red-400" />,
      label: 'Ancaman Terdeteksi',
      value: stats?.threatsDetected ?? 0,
      subtext: 'Berbahaya + mencurigakan',
      borderColor: 'border-red-500/20',
      bgColor: 'bg-red-500/10',
      hoverBorder: 'hover:border-red-500/50',
    },
    {
      icon: <CheckCircle className="w-5 h-5 text-green-400" />,
      label: 'Scan Aman',
      value: stats?.safeScans ?? 0,
      subtext: 'Tidak ditemukan tanda bahaya',
      borderColor: 'border-green-500/20',
      bgColor: 'bg-green-500/10',
      hoverBorder: 'hover:border-green-500/50',
    },
    {
      icon: <XCircle className="w-5 h-5 text-purple-400" />,
      label: 'Scan Berbahaya',
      value: stats?.dangerousScans ?? 0,
      subtext: 'Ditandai berbahaya',
      borderColor: 'border-purple-500/20',
      bgColor: 'bg-purple-500/10',
      hoverBorder: 'hover:border-purple-500/50',
    },
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
        <Header title="Dashboard" subtitle="Ringkasan aktivitas akun kamu" />

        <div className="p-8">
          {pesanError && (
            <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
              {pesanError}
            </div>
          )}

          {/* Kartu statistik */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {kartu.map((stat, idx) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.15 + idx * 0.08 }}
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
              >
                <StatCard {...stat} memuat={memuat} />
              </motion.div>
            ))}
          </motion.div>

          {/* Riwayat terbaru */}
          <motion.div
            className="bg-[#0d1117] border border-white/5 rounded-xl p-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <p className="text-xs text-gray-500 mb-6">Hasil scan terbaru dari akun kamu</p>

            {memuat ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
              </div>
            ) : riwayat.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-cyan-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">Belum ada scan</h3>
                <p className="text-gray-400 mb-6 max-w-md mx-auto text-sm">
                  Hasil scan akan muncul di sini setelah kamu memeriksa URL, email, atau file.
                </p>
                <button
                  onClick={() => (window.location.href = '/')}
                  className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2 mx-auto"
                >
                  <Plus className="w-4 h-4" />
                  Mulai Scan Pertama
                </button>
              </div>
            ) : (
              <ul className="space-y-2">
                {riwayat.map((r) => {
                  const gaya = gayaStatus[r.status] ?? {
                    warna: 'text-gray-400 bg-gray-500/10 border-gray-500/20',
                    label: r.status,
                  }
                  const Ikon = ikonTipe[r.type] ?? Globe

                  return (
                    <li
                      key={r.id}
                      className="flex items-center gap-4 rounded-lg border border-white/5 bg-black/20 p-3"
                    >
                      <Ikon className="w-4 h-4 text-gray-500 flex-shrink-0" />
                      {/* min-w-0 wajib supaya truncate bekerja di dalam flex */}
                      <span className="flex-1 min-w-0 truncate text-sm">{r.input}</span>
                      <span className="text-xs text-gray-500 flex-shrink-0 hidden sm:block">
                        {waktuSingkat(r.timestamp)}
                      </span>
                      <span
                        className={`text-xs px-2 py-1 rounded border flex-shrink-0 ${gaya.warna}`}
                      >
                        {gaya.label} {Math.round((r.score ?? 0) * 100)}%
                      </span>
                    </li>
                  )
                })}
              </ul>
            )}
          </motion.div>
        </div>
      </main>
    </motion.div>
  )
}

function StatCard({
  icon, label, value, subtext, borderColor, bgColor, hoverBorder, memuat,
}: any) {
  return (
    <div
      className={`bg-[#0d1117] border ${borderColor} ${hoverBorder} rounded-xl p-6 transition-all group`}
    >
      <motion.div
        className={`w-10 h-10 ${bgColor} rounded-lg flex items-center justify-center mb-4`}
        whileHover={{ scale: 1.1, rotate: 5 }}
        transition={{ duration: 0.2 }}
      >
        {icon}
      </motion.div>
      <h3 className="text-3xl font-bold mb-1">
        {memuat ? <span className="text-gray-600">—</span> : value}
      </h3>
      <p className="text-sm font-medium text-gray-300 mb-1">{label}</p>
      <p className="text-xs text-gray-500">{subtext}</p>
    </div>
  )
}

// Halaman Dashboard hanya untuk pengguna yang sudah masuk.
// Penjagaan sesungguhnya ada di backend - lihat catatan di RequireAuth.tsx.
export default function HalamanDashboardPage() {
  return (
    <RequireAuth>
      <DashboardPage />
    </RequireAuth>
  )
}
