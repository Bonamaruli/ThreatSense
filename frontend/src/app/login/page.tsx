'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Mail, Lock, User as UserIcon, Loader2, AlertCircle } from 'lucide-react'
import { daftar, masuk, sedangMasuk } from '@/lib/auth'

type Mode = 'masuk' | 'daftar'

export default function LoginPage() {
  const router = useRouter()

  const [mode, setMode] = useState<Mode>('masuk')
  const [nama, setNama] = useState('')
  const [email, setEmail] = useState('')
  const [sandi, setSandi] = useState('')
  const [loading, setLoading] = useState(false)
  const [pesanError, setPesanError] = useState<string | null>(null)

  // Kalau sudah punya sesi, tidak perlu melihat halaman ini lagi
  useEffect(() => {
    if (sedangMasuk()) router.replace('/dashboard')
  }, [router])

  // Pesan khusus saat pengguna terlempar ke sini karena sesinya habis,
  // supaya tidak bingung kenapa tiba-tiba diminta masuk lagi.
  //
  // Dibaca langsung dari alamat halaman, bukan lewat useSearchParams().
  // Hook itu mewajibkan pembungkus <Suspense> di versi Next.js ini, dan
  // tanpa pembungkus itu proses build gagal - padahal yang dibutuhkan cuma
  // satu nilai sederhana.
  useEffect(() => {
    const alasan = new URLSearchParams(window.location.search).get('alasan')
    if (alasan === 'sesi-habis') {
      setPesanError('Sesi kamu sudah berakhir. Silakan masuk kembali.')
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (loading) return

    setLoading(true)
    setPesanError(null)

    try {
      if (mode === 'daftar') {
        await daftar(nama.trim(), email.trim(), sandi)
      } else {
        await masuk(email.trim(), sandi)
      }
      router.replace('/dashboard')
    } catch (err: any) {
      setPesanError(err?.message || 'Terjadi kesalahan. Coba lagi.')
      setLoading(false)
    }
  }

  const gantiMode = (m: Mode) => {
    setMode(m)
    setPesanError(null)
    setSandi('')
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center px-4 py-12">
      {/* Latar bergaris, mengikuti gaya halaman utama */}
      <div
        className="fixed inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />

      <motion.div
        className="relative w-full max-w-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <Shield className="w-7 h-7 text-cyan-400" />
            <span className="text-2xl font-bold">
              Threat<span className="text-cyan-400">Sense</span>
            </span>
          </div>
          <p className="text-gray-400 text-sm">
            {mode === 'masuk'
              ? 'Masuk untuk melihat riwayat scan kamu'
              : 'Buat akun untuk menyimpan riwayat scan'}
          </p>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 sm:p-8">
          {/* Pemilih mode */}
          <div className="flex gap-2 mb-6 bg-black/20 p-1 rounded-lg">
            {(['masuk', 'daftar'] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => gantiMode(m)}
                className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                  mode === m
                    ? 'bg-cyan-500/20 text-cyan-300'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {m === 'masuk' ? 'Masuk' : 'Daftar'}
              </button>
            ))}
          </div>

          <AnimatePresence>
            {pesanError && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mb-5 flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400"
              >
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{pesanError}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'daftar' && (
              <div className="relative">
                <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  type="text"
                  value={nama}
                  onChange={(e) => setNama(e.target.value)}
                  placeholder="Nama lengkap"
                  required
                  minLength={2}
                  disabled={loading}
                  className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
                />
              </div>
            )}

            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
                autoComplete="email"
                disabled={loading}
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="password"
                value={sandi}
                onChange={(e) => setSandi(e.target.value)}
                placeholder={mode === 'daftar' ? 'Sandi (minimal 8 karakter)' : 'Sandi'}
                required
                minLength={mode === 'daftar' ? 8 : 1}
                autoComplete={mode === 'daftar' ? 'new-password' : 'current-password'}
                disabled={loading}
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Memproses...
                </>
              ) : mode === 'masuk' ? (
                'Masuk'
              ) : (
                'Buat Akun'
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6 leading-relaxed">
          Sandi kamu disimpan dalam bentuk teracak (bcrypt), bukan teks asli.
          <br />
          Riwayat scan hanya bisa dilihat oleh pemilik akunnya.
        </p>
      </motion.div>
    </div>
  )
}
