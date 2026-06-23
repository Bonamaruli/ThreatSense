'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  User, 
  Bell, 
  Moon, 
  Sun,
  Save,
  Camera,
  ChevronRight,
  HelpCircle,
  Trash2,
  Shield
} from 'lucide-react'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'

type SettingsTab = 'profil' | 'notifikasi' | 'tampilan'
type Theme = 'gelap' | 'terang'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profil')
  const [notifAncaman, setNotifAncaman] = useState(true)
  const [notifScan, setNotifScan] = useState(true)
  const [theme, setTheme] = useState<Theme>('gelap')
  const [nama, setNama] = useState('John Doe')
  const [email, setEmail] = useState('john@example.com')

  const menuItems = [
    { 
      id: 'profil' as SettingsTab, 
      label: 'Profil', 
      desc: 'Nama, email, informasi akun', 
      icon: User 
    },
    { 
      id: 'notifikasi' as SettingsTab, 
      label: 'Notifikasi', 
      desc: 'Atur preferensi notifikasi', 
      icon: Bell 
    },
    { 
      id: 'tampilan' as SettingsTab, 
      label: 'Tampilan', 
      desc: 'Tema dan antarmuka', 
      icon: Moon 
    },
  ]

  const pageVariants = {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 }
  }

  return (
    <motion.div 
      className="min-h-screen bg-[#0a0a0f] text-white flex"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {/* Main Sidebar */}
      <Sidebar />
      
      {/* Settings Sidebar (Nested) */}
      <aside className="w-80 bg-[#0d1117] border-r border-white/5 flex flex-col fixed left-64 top-0 h-full z-10">
        {/* User Profile Card */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
                <span className="text-lg font-bold text-white">JD</span>
              </div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-[#0d1117] rounded-full" />
            </div>
            <div>
              <h3 className="font-semibold text-white">John Doe</h3>
              <p className="text-sm text-gray-400">john@example.com</p>
            </div>
          </div>
        </div>

        {/* Settings Menu */}
        <div className="flex-1 p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-3">
            Pengaturan
          </p>
          <nav className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = activeTab === item.id
              return (
                <motion.button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all text-left ${
                    isActive
                      ? 'bg-cyan-500/10 border border-cyan-500/20'
                      : 'hover:bg-white/5 border border-transparent'
                  }`}
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    isActive ? 'bg-cyan-500/20' : 'bg-white/5'
                  }`}>
                    <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-gray-400'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${isActive ? 'text-cyan-400' : 'text-white'}`}>
                      {item.label}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{item.desc}</p>
                  </div>
                  <ChevronRight className={`w-4 h-4 flex-shrink-0 ${
                    isActive ? 'text-cyan-400' : 'text-gray-600'
                  }`} />
                </motion.button>
              )
            })}
          </nav>
        </div>

        {/* Help Button */}
        <div className="p-4">
          <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-400 hover:text-white transition-colors">
            <span className="text-xs">Ciutkan</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-[calc(16rem+20rem)]">
        <Header title="Pengaturan" subtitle="Jumat, 19 Juni 2026" />

        <div className="p-8 max-w-4xl">
          <AnimatePresence mode="wait">
            {/* PROFIL TAB */}
            {activeTab === 'profil' && (
              <motion.div
                key="profil"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <div className="mb-8">
                  <h1 className="text-3xl font-bold mb-2">Profil</h1>
                  <div className="w-12 h-1 bg-cyan-400 rounded-full" />
                </div>

                {/* Foto Profil */}
                <div className="mb-8">
                  <h2 className="text-xl font-semibold mb-4">Foto Profil</h2>
                  <div className="flex items-center gap-6">
                    <div className="relative group">
                      <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                        <span className="text-3xl font-bold text-white">JD</span>
                      </div>
                      <motion.button
                        className="absolute -bottom-2 -right-2 w-9 h-9 bg-[#1a1f2e] border border-white/10 rounded-lg flex items-center justify-center hover:bg-white/10 transition-colors"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        <Camera className="w-4 h-4 text-gray-300" />
                      </motion.button>
                    </div>
                    <div className="flex-1">
                      <p className="text-gray-300 mb-1">
                        Inisial nama Anda ditampilkan secara otomatis.
                      </p>
                      <p className="text-gray-400">
                        Unggah foto untuk menggantinya.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border-t border-white/5 my-8" />

                {/* Informasi Akun */}
                <div className="mb-8">
                  <h2 className="text-xl font-semibold mb-6">Informasi Akun</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                        Nama Lengkap
                      </label>
                      <input
                        type="text"
                        value={nama}
                        onChange={(e) => setNama(e.target.value)}
                        className="w-full bg-[#0d1117] border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition-colors"
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        Nama yang ditampilkan di seluruh aplikasi
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                        Alamat Email
                      </label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full bg-[#0d1117] border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition-colors"
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        Digunakan untuk notifikasi dan login
                      </p>
                    </div>
                  </div>

                  <motion.button
                    className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Save className="w-4 h-4" />
                    Simpan Perubahan
                  </motion.button>
                </div>

                <div className="border-t border-white/5 my-8" />

                {/* Zona Berbahaya */}
                <div>
                  <h2 className="text-xl font-semibold mb-2 text-red-400">Zona Berbahaya</h2>
                  <p className="text-gray-400 mb-4">
                    Tindakan ini bersifat permanen dan tidak dapat dibatalkan.
                  </p>
                  <motion.button
                    className="px-6 py-3 border border-red-500/50 text-red-400 rounded-lg font-semibold hover:bg-red-500/10 transition-all flex items-center gap-2"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Trash2 className="w-4 h-4" />
                    Hapus Akun
                  </motion.button>
                </div>
              </motion.div>
            )}

            {/* NOTIFIKASI TAB */}
            {activeTab === 'notifikasi' && (
              <motion.div
                key="notifikasi"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <div className="mb-8">
                  <h1 className="text-3xl font-bold mb-2">Notifikasi</h1>
                  <div className="w-12 h-1 bg-cyan-400 rounded-full" />
                </div>

                <div className="mb-6">
                  <h2 className="text-xl font-semibold mb-2">Preferensi Notifikasi</h2>
                  <p className="text-gray-400">
                    Pilih jenis notifikasi yang ingin Anda terima dari ThreatSense.
                  </p>
                </div>

                <div className="bg-[#0d1117] border border-white/5 rounded-xl overflow-hidden">
                  {/* Peringatan Ancaman */}
                  <div className="flex items-center justify-between p-6 border-b border-white/5">
                    <div>
                      <h3 className="font-semibold mb-1">Peringatan Ancaman</h3>
                      <p className="text-sm text-gray-400">
                        Beri tahu saat URL, email, atau file berisiko tinggi terdeteksi
                      </p>
                    </div>
                    <ToggleSwitch 
                      checked={notifAncaman} 
                      onChange={setNotifAncaman} 
                    />
                  </div>

                  {/* Scan Selesai */}
                  <div className="flex items-center justify-between p-6">
                    <div>
                      <h3 className="font-semibold mb-1">Scan Selesai</h3>
                      <p className="text-sm text-gray-400">
                        Beri tahu ketika setiap proses scan selesai diproses
                      </p>
                    </div>
                    <ToggleSwitch 
                      checked={notifScan} 
                      onChange={setNotifScan} 
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAMPILAN TAB */}
            {activeTab === 'tampilan' && (
              <motion.div
                key="tampilan"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <div className="mb-8">
                  <h1 className="text-3xl font-bold mb-2">Tampilan</h1>
                  <div className="w-12 h-1 bg-cyan-400 rounded-full" />
                </div>

                <div className="mb-6">
                  <h2 className="text-xl font-semibold mb-2">Tema Antarmuka</h2>
                  <p className="text-gray-400">
                    Pilih tema tampilan yang nyaman untuk Anda.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Tema Gelap */}
                  <motion.button
                    onClick={() => setTheme('gelap')}
                    className={`relative p-8 rounded-xl border-2 transition-all text-center ${
                      theme === 'gelap'
                        ? 'border-cyan-500 bg-cyan-500/5'
                        : 'border-white/10 bg-[#0d1117] hover:border-white/20'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className={`w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center ${
                      theme === 'gelap' ? 'bg-cyan-500/20' : 'bg-white/5'
                    }`}>
                      <Moon className={`w-7 h-7 ${theme === 'gelap' ? 'text-cyan-400' : 'text-gray-400'}`} />
                    </div>
                    <p className={`font-semibold mb-1 ${theme === 'gelap' ? 'text-cyan-400' : 'text-white'}`}>
                      Gelap
                    </p>
                    <p className="text-sm text-gray-500 mb-3">Default</p>
                    {theme === 'gelap' && (
                      <motion.span 
                        className="inline-flex items-center gap-1 px-3 py-1 bg-cyan-500/20 text-cyan-400 text-xs rounded-full font-medium"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                      >
                        ✓ Aktif
                      </motion.span>
                    )}
                  </motion.button>

                  {/* Tema Terang */}
                  <motion.button
                    onClick={() => setTheme('terang')}
                    className={`relative p-8 rounded-xl border-2 transition-all text-center ${
                      theme === 'terang'
                        ? 'border-cyan-500 bg-cyan-500/5'
                        : 'border-white/10 bg-[#0d1117] hover:border-white/20'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className={`w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center ${
                      theme === 'terang' ? 'bg-cyan-500/20' : 'bg-white/5'
                    }`}>
                      <Sun className={`w-7 h-7 ${theme === 'terang' ? 'text-cyan-400' : 'text-gray-400'}`} />
                    </div>
                    <p className={`font-semibold mb-1 ${theme === 'terang' ? 'text-cyan-400' : 'text-white'}`}>
                      Terang
                    </p>
                    <p className="text-sm text-gray-500 mb-3">Mode siang</p>
                    {theme === 'terang' && (
                      <motion.span 
                        className="inline-flex items-center gap-1 px-3 py-1 bg-cyan-500/20 text-cyan-400 text-xs rounded-full font-medium"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                      >
                        ✓ Aktif
                      </motion.span>
                    )}
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Help Button Floating */}
      <motion.button
        className="fixed bottom-6 right-6 w-10 h-10 bg-white/10 border border-white/20 rounded-full flex items-center justify-center hover:bg-white/20 transition-colors z-50"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        <HelpCircle className="w-5 h-5 text-gray-300" />
      </motion.button>
    </motion.div>
  )
}

// Toggle Switch Component
function ToggleSwitch({ checked, onChange }: { checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <motion.button
      onClick={() => onChange(!checked)}
      className={`relative w-14 h-7 rounded-full transition-colors ${
        checked ? 'bg-cyan-500' : 'bg-gray-600'
      }`}
      whileTap={{ scale: 0.95 }}
    >
      <motion.div
        className="absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow-lg"
        animate={{ x: checked ? 28 : 0 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
      />
    </motion.button>
  )
}