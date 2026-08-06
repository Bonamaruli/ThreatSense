'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Link as LinkIcon, Mail, FileText, LayoutDashboard, History, Info, Search, User, Globe, File } from 'lucide-react'
import { usePathname, useRouter } from 'next/navigation'
import { ScanForm } from '@/components/ui/ScanForm'
import { ScanResult } from '@/components/ui/ScanResult'
import { useToast } from '@/components/ui/Toast'
import { scanApi } from '@/lib/services'
import { profilSaya, sedangMasuk } from '@/lib/auth'
import type { ScanType, ScanResult as ScanResultType } from '@/types'

export default function Home() {
  const router = useRouter()
  const [isScanning, setIsScanning] = useState(false)
  // Hasil scan terakhir. Sebelumnya hasilnya cuma masuk console.log sehingga
  // pengguna tidak pernah melihat apa pun selain notifikasi sekilas.
  const [hasil, setHasil] = useState<ScanResultType | null>(null)
  const [namaAkun, setNamaAkun] = useState<string | null>(null)
  const pathname = usePathname()
  const toast = useToast()

  // Nama akun ditampilkan di tombol kanan atas kalau sudah masuk.
  // Halaman ini terbuka untuk umum, jadi kegagalan diabaikan diam-diam -
  // pengunjung yang belum punya akun tetap melihat tulisan "Akun".
  useEffect(() => {
    if (!sedangMasuk()) return
    let batal = false
    profilSaya().then((u) => {
      if (!batal && u) setNamaAkun(u.nama)
    })
    return () => {
      batal = true
    }
  }, [])

  const diBeranda = pathname === '/'

  /**
   * Gulir ke atas, dipakai saat logo diklik di halaman ini sendiri.
   *
   * Sebagian pengguna mematikan animasi lewat pengaturan sistem (dan browser
   * mengabaikan 'smooth' bila begitu). Kalau pilihannya dipaksa 'smooth',
   * tombolnya bisa terasa tidak berfungsi sama sekali bagi mereka. Karena itu
   * pilihan geraknya menyesuaikan preferensi tersebut.
   */
  const gulirKeAtas = () => {
    const kurangiGerak = window.matchMedia?.(
      '(prefers-reduced-motion: reduce)'
    ).matches
    window.scrollTo({ top: 0, behavior: kurangiGerak ? 'auto' : 'smooth' })
  }

  const handleScan = async (
    type: ScanType, value: string, file?: File, mendalam?: boolean,
  ) => {
    // Scan sekarang butuh akun, karena hasilnya disimpan ke riwayat pemiliknya.
    // Dicegat di sini supaya pengguna mendapat penjelasan yang jelas, bukan
    // sekadar error 401 dari server yang membingungkan.
    if (!sedangMasuk()) {
      toast.warning('Masuk dulu supaya hasil scan tersimpan di riwayatmu.')
      router.push('/login')
      return
    }

    setIsScanning(true)
    setHasil(null)

    try {
      const result = await scanApi.performScan(type, value, file, mendalam)

      if (result.success && result.data) {
        setHasil(result.data)

        // Notifikasi dibedakan supaya temuan berbahaya tidak lewat begitu saja
        // sebagai pesan hijau yang terkesan baik-baik saja.
        if (result.data.status === 'berbahaya') {
          toast.error('Terdeteksi berbahaya — lihat alasannya di bawah.')
        } else if (result.data.status === 'mencurigakan') {
          toast.warning('Ada yang mencurigakan — lihat alasannya di bawah.')
        } else {
          toast.success('Scan selesai, tidak ditemukan tanda bahaya.')
        }
      } else {
        toast.error(result.error?.message || 'Gagal melakukan scan')
      }
    } catch (error: any) {
      toast.error(error.message || 'Terjadi kesalahan saat scan')
    } finally {
      setIsScanning(false)
    }
  }

  return (
    <>
      <motion.div 
        className="min-h-screen bg-[#0a0a0f] text-white relative overflow-x-hidden"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.5 }}
      >
      {/* Background Grid Pattern */}
      <div 
        className="fixed inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}
      />
      
      {/* Gradient Orbs */}
      <motion.div 
        className="fixed top-0 left-0 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl pointer-events-none"
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.2, 0.3, 0.2]
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <motion.div 
        className="fixed bottom-0 right-0 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none"
        animate={{
          scale: [1.1, 1, 1.1],
          opacity: [0.3, 0.2, 0.3]
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Navigation */}
      <motion.nav 
        className="relative z-10 border-b border-white/10 backdrop-blur-xl bg-black/50"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          {/*
            Saat sedang DI beranda, logo bukan tautan melainkan tombol.

            Alasannya: <Link href="/"> yang diklik dari halaman "/" tidak
            melakukan apa-apa - Next.js melewati navigasi ke rute yang sedang
            dibuka, sehingga onClick maupun onNavigate tidak pernah terpanggil
            dan tidak ada cara mencegatnya. Memakai tombol biasa membuat
            perilakunya pasti, tanpa bergantung pada cara kerja <Link> di
            balik layar.
          */}
          {diBeranda ? (
            <button
              type="button"
              onClick={gulirKeAtas}
              aria-label="Kembali ke atas halaman"
              className="flex items-center gap-2 group"
            >
              <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.6 }}>
                <Shield className="w-6 h-6 text-cyan-400" />
              </motion.div>
              <span className="text-xl font-bold">
                Threat<span className="text-cyan-400">Sense</span>
              </span>
            </button>
          ) : (
            <Link href="/" className="flex items-center gap-2 group">
              <motion.div whileHover={{ rotate: 360 }} transition={{ duration: 0.6 }}>
                <Shield className="w-6 h-6 text-cyan-400" />
              </motion.div>
              <span className="text-xl font-bold">
                Threat<span className="text-cyan-400">Sense</span>
              </span>
            </Link>
          )}

          <div className="hidden md:flex items-center gap-8">
            <Link href="/dashboard" className="text-gray-400 hover:text-white transition-colors relative group">
              Dashboard
              <motion.div 
                className="absolute -bottom-1 left-0 w-0 h-0.5 bg-cyan-400"
                whileHover={{ width: '100%' }}
                transition={{ duration: 0.3 }}
              />
            </Link>
            <Link href="/history" className="text-gray-400 hover:text-white transition-colors relative group">
              Riwayat Scan
              <motion.div 
                className="absolute -bottom-1 left-0 w-0 h-0.5 bg-purple-400"
                whileHover={{ width: '100%' }}
                transition={{ duration: 0.3 }}
              />
            </Link>
            <Link href="/about" className="text-gray-400 hover:text-white transition-colors relative group">
              Tentang
              <motion.div 
                className="absolute -bottom-1 left-0 w-0 h-0.5 bg-green-400"
                whileHover={{ width: '100%' }}
                transition={{ duration: 0.3 }}
              />
            </Link>
          </div>

          {/*
            Dulu ini <button> tanpa onClick sama sekali, jadi diklik tidak
            terjadi apa-apa. Sekarang mengantar ke halaman Pengaturan.

            Tujuannya SELALU /settings, tidak dibeda-bedakan berdasarkan
            status masuk. Kalau belum masuk, RequireAuth di halaman itu yang
            mengalihkan ke /login. Menaruh pemeriksaan di dua tempat membuat
            keduanya bisa berbeda pendapat dan sulit ditelusuri kalau salah.
          */}
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link
              href="/settings"
              className="flex items-center gap-2 px-4 py-2 border border-white/20 rounded-lg hover:bg-white/5 transition-colors"
            >
              <User className="w-4 h-4" />
              <span>{namaAkun ?? 'Akun'}</span>
            </Link>
          </motion.div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 py-20">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.8 }}
        >
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            Deteksi Ancaman Siber
            <br />
            <motion.span 
              className="bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4, duration: 0.6 }}
            >
              Sebelum Menyerang
            </motion.span>
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            ThreatSense menganalisis URL, email, dan file menggunakan AI untuk mendeteksi ancaman secara instan.
          </p>
        </motion.div>

        {/* Scan Form - Menggunakan komponen reusable */}
        <motion.div 
          className="max-w-3xl mx-auto mb-20"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.8 }}
        >
          <ScanForm onScan={handleScan} loading={isScanning} />

          {/* Hasil scan, muncul tepat di bawah form */}
          <AnimatePresence mode="wait">
            {hasil && (
              <div className="mt-6">
                <ScanResult
                  key={hasil.id}
                  result={hasil}
                  onClose={() => setHasil(null)}
                />
              </div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Feature Cards */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          {[
            { icon: Globe, title: 'URL Scanner', desc: 'Analisis URL mencurigakan untuk mendeteksi phishing, malware, dan ancaman lain secara real-time.', color: 'cyan' },
            { icon: Mail, title: 'Email Scanner', desc: 'Deteksi percobaan phishing, pengirim palsu, dan tautan berbahaya yang tersembunyi di header maupun isi email.', color: 'purple' },
            { icon: FileText, title: 'File Scanner', desc: 'Unggah file biner, PDF, atau dokumen Office untuk analisis malware statis dan dinamis secara mendalam.', color: 'green' }
          ].map((feature, idx) => (
            <motion.div 
              key={idx}
              className="bg-white/5 border border-white/10 rounded-xl p-6 hover:border-white/20 transition-all group backdrop-blur-sm"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + idx * 0.1, duration: 0.6 }}
              whileHover={{ y: -5 }}
            >
              <motion.div 
                className={`w-12 h-12 bg-${feature.color}-500/20 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
                whileHover={{ rotate: 5 }}
              >
                <feature.icon className={`w-6 h-6 text-${feature.color}-400`} />
              </motion.div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-400">{feature.desc}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Available Pages Section */}
        <motion.div 
          className="text-center mb-12"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <h2 className="text-3xl font-bold mb-4">Halaman yang Tersedia</h2>
          <p className="text-gray-400">Semua fitur dapat diakses setelah masuk ke dashboard</p>
        </motion.div>

        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.8 }}
        >
          {[
            { href: '/dashboard', icon: LayoutDashboard, title: 'Dashboard', desc: 'Ringkasan aktivitas scan dan statistik ancaman yang terdeteksi dari akun Anda.', color: 'cyan' },
            { href: '/history', icon: History, title: 'Riwayat Scan', desc: 'Lihat semua hasil scan sebelumnya, filter berdasarkan tipe atau status, dan ekspor data.', color: 'purple' },
            { href: '/about', icon: Info, title: 'Tentang', desc: 'Pelajari lebih lanjut tentang ThreatSense, teknologi yang digunakan, dan cara kerja sistem deteksi ancaman kami.', color: 'green' }
          ].map((page, idx) => (
            <motion.div
              key={idx}
              className="bg-white/5 border border-white/10 rounded-xl p-6 hover:border-white/20 transition-all backdrop-blur-sm block"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + idx * 0.1, duration: 0.6 }}
              whileHover={{ y: -5, scale: 1.02 }}
            >
              <Link href={page.href}>
                <div className={`w-12 h-12 bg-${page.color}-500/20 rounded-lg flex items-center justify-center mb-4`}>
                  <page.icon className={`w-6 h-6 text-${page.color}-400`} />
                </div>
                <h3 className="text-xl font-semibold mb-2">{page.title}</h3>
                <p className="text-gray-400 mb-4">{page.desc}</p>
                <span className={`text-${page.color}-400 hover:text-${page.color}-300 inline-flex items-center gap-1`}>
                  Buka →
                </span>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </main>

      {/* Footer */}
      <motion.footer 
        className="relative z-10 border-t border-white/10 mt-20"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
      >
        <div className="max-w-7xl mx-auto px-6 py-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-cyan-400" />
            <span className="font-bold">
              Threat<span className="text-cyan-400">Sense</span>
            </span>
          </div>
          <p className="text-gray-500 text-sm">
            © 2026 ThreatSense · Platform verifikasi ancaman siber berbasis AI
          </p>
        </div>
      </motion.footer>
      </motion.div>
      <toast.ToastContainer />
    </>
  )
}