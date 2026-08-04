'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { sedangMasuk } from '@/lib/auth'

/**
 * Pembungkus halaman yang hanya boleh dibuka setelah masuk.
 *
 * CATATAN PENTING SOAL KEAMANAN
 * Penjagaan di sini hanya mengatur TAMPILAN. Siapa pun bisa melewatinya
 * lewat konsol browser, karena semua kode frontend berjalan di komputer
 * pengguna dan bisa diubah.
 *
 * Yang benar-benar menjaga data adalah BACKEND: setiap endpoint riwayat dan
 * statistik menuntut token yang sah dan hanya mengembalikan baris milik
 * pemilik token. Jadi walau seseorang memaksa membuka halaman ini tanpa
 * masuk, yang dia lihat tetap kosong - servernya menolak.
 *
 * Jangan pernah memindahkan pemeriksaan hak akses ke sini saja.
 */
export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [siap, setSiap] = useState(false)

  useEffect(() => {
    if (!sedangMasuk()) {
      router.replace('/login')
    } else {
      setSiap(true)
    }
  }, [router])

  if (!siap) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
      </div>
    )
  }

  return <>{children}</>
}
