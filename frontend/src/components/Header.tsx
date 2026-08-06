'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Search, Bell, ChevronDown, LogOut, Settings } from 'lucide-react'
import { AuthUser, keluar, profilSaya } from '@/lib/auth'

interface HeaderProps {
  title: string
  subtitle: string
}

/** Ambil huruf awal nama untuk lingkaran avatar, contoh "Budi Santoso" -> "BS". */
function inisial(nama: string): string {
  return nama
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((k) => k[0]?.toUpperCase() ?? '')
    .join('')
}

export default function Header({ title, subtitle }: HeaderProps) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [menuTerbuka, setMenuTerbuka] = useState(false)

  // Profil diambil dari SERVER setiap halaman dimuat, bukan dari salinan di
  // browser. Data yang disimpan di browser bisa diubah lewat konsol, jadi
  // nama yang tampil bisa berbohong kalau sumbernya dari sana.
  useEffect(() => {
    let batal = false
    profilSaya().then((u) => {
      if (!batal) setUser(u)
    })
    return () => {
      batal = true
    }
  }, [])

  return (
    <header className="h-16 border-b border-white/5 bg-[#0a0a0f]/80 backdrop-blur-xl sticky top-0 z-10">
      <div className="h-full px-8 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">{title}</h1>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>

        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Cari..."
              className="w-64 bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
            />
          </div>

          {/* Notification */}
          <button className="relative p-2 text-gray-400 hover:text-white transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          </button>
          
          {/* Akun pengguna */}
          <div className="relative pl-4 border-l border-white/10">
            <button
              type="button"
              onClick={() => setMenuTerbuka((v) => !v)}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold">
                  {user ? inisial(user.nama) : '·'}
                </span>
              </div>
              <span className="text-sm font-medium max-w-[10rem] truncate">
                {user ? user.nama : 'Memuat...'}
              </span>
              <ChevronDown
                className={`w-4 h-4 text-gray-400 transition-transform ${
                  menuTerbuka ? 'rotate-180' : ''
                }`}
              />
            </button>

            {menuTerbuka && user && (
              <>
                {/* Lapisan tak terlihat menutupi seluruh layar: klik di mana
                    pun akan menutup menu. Tanpa ini menu tetap terbuka dan
                    menghalangi isi halaman. */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setMenuTerbuka(false)}
                />
                <div className="absolute right-0 top-12 z-20 w-60 rounded-xl border border-white/10 bg-[#12121a] p-2 shadow-xl">
                  <div className="px-3 py-2 border-b border-white/5 mb-1">
                    <p className="text-sm font-medium truncate">{user.nama}</p>
                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                  </div>
                  {/* Menu ke Pengaturan. Sebelumnya isi dropdown ini hanya
                      tombol Keluar, sehingga satu-satunya jalan ke halaman
                      Pengaturan adalah lewat menu samping. */}
                  <Link
                    href="/settings"
                    onClick={() => setMenuTerbuka(false)}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-white/5 transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                    Pengaturan
                  </Link>

                  <button
                    type="button"
                    onClick={keluar}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Keluar
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}