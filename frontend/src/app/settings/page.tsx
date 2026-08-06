'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  User as UserIcon,
  Lock,
  Sliders,
  Save,
  LogOut,
  Loader2,
  CheckCircle,
  AlertCircle,
} from 'lucide-react'

import RequireAuth from '@/components/RequireAuth'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import { userApi } from '@/lib/services'
import { keluar } from '@/lib/auth'

type Tab = 'profil' | 'keamanan' | 'preferensi'

/** Kunci penyimpanan preferensi tampilan di browser. */
const KUNCI_PREFERENSI = 'threatsense_preferensi'

function SettingsPage() {
  const [tab, setTab] = useState<Tab>('profil')

  // --- Profil ---
  const [nama, setNama] = useState('')
  const [email, setEmail] = useState('')
  const [memuatProfil, setMemuatProfil] = useState(true)
  const [menyimpanProfil, setMenyimpanProfil] = useState(false)

  // --- Ganti sandi ---
  const [sandiLama, setSandiLama] = useState('')
  const [sandiBaru, setSandiBaru] = useState('')
  const [sandiUlang, setSandiUlang] = useState('')
  const [menyimpanSandi, setMenyimpanSandi] = useState(false)

  // --- Preferensi (hanya tersimpan di browser) ---
  const [notifAncaman, setNotifAncaman] = useState(true)
  const [notifScan, setNotifScan] = useState(true)

  const [kabar, setKabar] = useState<{ tipe: 'ok' | 'salah'; teks: string } | null>(null)

  // Profil diambil dari server, bukan ditulis mati.
  // Sebelumnya halaman ini menampilkan "John Doe" untuk semua orang, padahal
  // header di atasnya sudah menampilkan nama akun yang sebenarnya.
  useEffect(() => {
    let batal = false
    userApi
      .getProfile()
      .then((r) => {
        if (batal) return
        if (r.success && r.data) {
          setNama(r.data.nama ?? '')
          setEmail(r.data.email ?? '')
        } else {
          setKabar({ tipe: 'salah', teks: r.error?.message ?? 'Gagal memuat profil.' })
        }
      })
      .finally(() => !batal && setMemuatProfil(false))

    // Preferensi tampilan dibaca dari browser
    try {
      const tersimpan = localStorage.getItem(KUNCI_PREFERENSI)
      if (tersimpan) {
        const p = JSON.parse(tersimpan)
        if (typeof p.notifAncaman === 'boolean') setNotifAncaman(p.notifAncaman)
        if (typeof p.notifScan === 'boolean') setNotifScan(p.notifScan)
      }
    } catch {
      // Nilai rusak diabaikan, pakai bawaan saja
    }

    return () => {
      batal = true
    }
  }, [])

  // Pesan hilang sendiri supaya tidak menumpuk di layar
  useEffect(() => {
    if (!kabar) return
    const t = setTimeout(() => setKabar(null), 5000)
    return () => clearTimeout(t)
  }, [kabar])

  const simpanProfil = async (e: React.FormEvent) => {
    e.preventDefault()
    setMenyimpanProfil(true)
    setKabar(null)

    const r = await userApi.updateProfile({ nama: nama.trim(), email: email.trim() })
    if (r.success) {
      setKabar({ tipe: 'ok', teks: 'Profil tersimpan.' })
    } else {
      setKabar({ tipe: 'salah', teks: r.error?.message ?? 'Gagal menyimpan profil.' })
    }
    setMenyimpanProfil(false)
  }

  const simpanSandi = async (e: React.FormEvent) => {
    e.preventDefault()

    // Diperiksa di sini supaya pengguna langsung tahu, tanpa perlu menunggu
    // jawaban server. Pemeriksaan sesungguhnya tetap ada di backend.
    if (sandiBaru !== sandiUlang) {
      setKabar({ tipe: 'salah', teks: 'Ketikan sandi baru tidak sama.' })
      return
    }

    setMenyimpanSandi(true)
    setKabar(null)

    const r = await userApi.changePassword({
      sandi_lama: sandiLama,
      sandi_baru: sandiBaru,
    })

    if (r.success) {
      setKabar({ tipe: 'ok', teks: 'Sandi berhasil diganti.' })
      setSandiLama('')
      setSandiBaru('')
      setSandiUlang('')
    } else {
      setKabar({ tipe: 'salah', teks: r.error?.message ?? 'Gagal mengganti sandi.' })
    }
    setMenyimpanSandi(false)
  }

  const simpanPreferensi = (baru: { notifAncaman?: boolean; notifScan?: boolean }) => {
    const nilai = { notifAncaman, notifScan, ...baru }
    setNotifAncaman(nilai.notifAncaman)
    setNotifScan(nilai.notifScan)
    localStorage.setItem(KUNCI_PREFERENSI, JSON.stringify(nilai))
  }

  const menu = [
    { id: 'profil' as Tab, label: 'Profil', desc: 'Nama dan email', icon: UserIcon },
    { id: 'keamanan' as Tab, label: 'Keamanan', desc: 'Sandi dan sesi', icon: Lock },
    { id: 'preferensi' as Tab, label: 'Preferensi', desc: 'Notifikasi', icon: Sliders },
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
        <Header title="Pengaturan" subtitle="Kelola akun kamu" />

        <div className="p-8 max-w-4xl">
          <AnimatePresence>
            {kabar && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`mb-6 flex items-start gap-2 rounded-lg border p-3 text-sm ${
                  kabar.tipe === 'ok'
                    ? 'border-green-500/20 bg-green-500/10 text-green-400'
                    : 'border-red-500/20 bg-red-500/10 text-red-400'
                }`}
              >
                {kabar.tipe === 'ok' ? (
                  <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                )}
                <span>{kabar.teks}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="grid grid-cols-1 md:grid-cols-[16rem_1fr] gap-6">
            {/* Menu samping */}
            <nav className="space-y-1">
              {menu.map((m) => {
                const Ikon = m.icon
                const aktif = tab === m.id
                return (
                  <button
                    key={m.id}
                    onClick={() => setTab(m.id)}
                    className={`w-full text-left flex items-start gap-3 rounded-lg p-3 transition-colors ${
                      aktif
                        ? 'bg-cyan-500/10 border border-cyan-500/30'
                        : 'border border-transparent hover:bg-white/5'
                    }`}
                  >
                    <Ikon
                      className={`w-4 h-4 mt-0.5 ${
                        aktif ? 'text-cyan-400' : 'text-gray-500'
                      }`}
                    />
                    <span>
                      <span className="block text-sm font-medium">{m.label}</span>
                      <span className="block text-xs text-gray-500">{m.desc}</span>
                    </span>
                  </button>
                )
              })}
            </nav>

            {/* Isi */}
            <div className="bg-[#0d1117] border border-white/5 rounded-xl p-6">
              {tab === 'profil' && (
                <form onSubmit={simpanProfil} className="space-y-5">
                  <h3 className="font-semibold">Profil</h3>

                  {memuatProfil ? (
                    <div className="flex justify-center py-10">
                      <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                    </div>
                  ) : (
                    <>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1.5">
                          Nama lengkap
                        </label>
                        <input
                          type="text"
                          value={nama}
                          onChange={(e) => setNama(e.target.value)}
                          minLength={2}
                          required
                          className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500/50"
                        />
                      </div>

                      <div>
                        <label className="block text-xs text-gray-500 mb-1.5">Email</label>
                        <input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          required
                          className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500/50"
                        />
                        <p className="text-xs text-gray-600 mt-1.5">
                          Email dipakai untuk masuk, jadi pastikan masih kamu ingat.
                        </p>
                      </div>

                      <button
                        type="submit"
                        disabled={menyimpanProfil}
                        className="flex items-center gap-2 px-5 py-2.5 bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 rounded-lg text-sm font-medium hover:bg-cyan-500/30 transition-colors disabled:opacity-50"
                      >
                        {menyimpanProfil ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Save className="w-4 h-4" />
                        )}
                        Simpan Perubahan
                      </button>
                    </>
                  )}
                </form>
              )}

              {tab === 'keamanan' && (
                <div className="space-y-8">
                  <form onSubmit={simpanSandi} className="space-y-5">
                    <h3 className="font-semibold">Ganti Sandi</h3>

                    <div>
                      <label className="block text-xs text-gray-500 mb-1.5">
                        Sandi sekarang
                      </label>
                      <input
                        type="password"
                        value={sandiLama}
                        onChange={(e) => setSandiLama(e.target.value)}
                        required
                        autoComplete="current-password"
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500/50"
                      />
                    </div>

                    <div>
                      <label className="block text-xs text-gray-500 mb-1.5">
                        Sandi baru (minimal 8 karakter)
                      </label>
                      <input
                        type="password"
                        value={sandiBaru}
                        onChange={(e) => setSandiBaru(e.target.value)}
                        minLength={8}
                        required
                        autoComplete="new-password"
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500/50"
                      />
                    </div>

                    <div>
                      <label className="block text-xs text-gray-500 mb-1.5">
                        Ulangi sandi baru
                      </label>
                      <input
                        type="password"
                        value={sandiUlang}
                        onChange={(e) => setSandiUlang(e.target.value)}
                        minLength={8}
                        required
                        autoComplete="new-password"
                        className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500/50"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={menyimpanSandi}
                      className="flex items-center gap-2 px-5 py-2.5 bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 rounded-lg text-sm font-medium hover:bg-cyan-500/30 transition-colors disabled:opacity-50"
                    >
                      {menyimpanSandi ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Lock className="w-4 h-4" />
                      )}
                      Ganti Sandi
                    </button>

                    {/* Batasan ditulis terbuka, bukan disembunyikan */}
                    <p className="text-xs text-gray-600 leading-relaxed">
                      Catatan: sesi yang sudah terbuka di perangkat lain masih
                      berlaku sampai 30 menit setelah ini. Memutus semua sesi
                      lama seketika belum didukung.
                    </p>
                  </form>

                  <div className="pt-6 border-t border-white/5">
                    <h3 className="font-semibold mb-1">Keluar</h3>
                    <p className="text-xs text-gray-500 mb-4">
                      Token di perangkat ini akan dihapus.
                    </p>
                    <button
                      onClick={keluar}
                      className="flex items-center gap-2 px-5 py-2.5 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm font-medium hover:bg-red-500/20 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Keluar dari Akun
                    </button>
                  </div>
                </div>
              )}

              {tab === 'preferensi' && (
                <div className="space-y-5">
                  <h3 className="font-semibold">Preferensi</h3>

                  <Sakelar
                    label="Peringatan ancaman"
                    desc="Tampilkan notifikasi saat hasil scan berbahaya"
                    aktif={notifAncaman}
                    onUbah={(v) => simpanPreferensi({ notifAncaman: v })}
                  />
                  <Sakelar
                    label="Scan selesai"
                    desc="Tampilkan notifikasi setiap scan selesai"
                    aktif={notifScan}
                    onUbah={(v) => simpanPreferensi({ notifScan: v })}
                  />

                  {/*
                    Dikatakan apa adanya. Menampilkan sakelar yang seolah
                    tersimpan di akun padahal cuma di browser akan menyesatkan -
                    pengguna mengira pengaturannya ikut kalau ganti perangkat.
                  */}
                  <p className="text-xs text-gray-600 leading-relaxed pt-4 border-t border-white/5">
                    Preferensi ini disimpan di browser ini saja, belum ikut ke
                    akun. Kalau kamu membuka ThreatSense dari perangkat lain,
                    pengaturannya kembali ke bawaan.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </motion.div>
  )
}

function Sakelar({
  label, desc, aktif, onUbah,
}: {
  label: string
  desc: string
  aktif: boolean
  onUbah: (v: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <div className="min-w-0">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-gray-500">{desc}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={aktif}
        aria-label={label}
        onClick={() => onUbah(!aktif)}
        className={`w-11 h-6 rounded-full p-0.5 flex-shrink-0 transition-colors ${
          aktif ? 'bg-cyan-500' : 'bg-white/10'
        }`}
      >
        <motion.div
          className="w-5 h-5 bg-white rounded-full"
          animate={{ x: aktif ? 20 : 0 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        />
      </button>
    </div>
  )
}

// Halaman Pengaturan hanya untuk pengguna yang sudah masuk.
// Penjagaan sesungguhnya ada di backend - lihat catatan di RequireAuth.tsx.
export default function HalamanSettingsPage() {
  return (
    <RequireAuth>
      <SettingsPage />
    </RequireAuth>
  )
}
