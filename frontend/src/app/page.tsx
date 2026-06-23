'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Shield, Link as LinkIcon, Mail, FileText, LayoutDashboard, History, Info, Search, User, Globe, File } from 'lucide-react'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'url' | 'email' | 'file'>('url')
  const [inputValue, setInputValue] = useState('')

  const handleScan = () => {
    console.log('Scanning:', inputValue, 'Type:', activeTab)
  }

  return (
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
          <Link href="/" className="flex items-center gap-2 group">
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              <Shield className="w-6 h-6 text-cyan-400" />
            </motion.div>
            <span className="text-xl font-bold">
              Threat<span className="text-cyan-400">Sense</span>
            </span>
          </Link>

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

          <motion.button 
            className="flex items-center gap-2 px-4 py-2 border border-white/20 rounded-lg hover:bg-white/5 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <User className="w-4 h-4" />
            <span>Akun</span>
          </motion.button>
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

        {/* Scan Form */}
        <motion.div 
          className="max-w-3xl mx-auto mb-20"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.8 }}
        >
          {/* Tab Selector */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex bg-white/5 border border-white/10 rounded-lg p-1 gap-1">
              {(['url', 'email', 'file'] as const).map((tab) => {
                const icons = {
                  url: <LinkIcon className="w-4 h-4" />,
                  email: <Mail className="w-4 h-4" />,
                  file: <File className="w-4 h-4" />
                }
                const colors = {
                  url: 'cyan',
                  email: 'purple',
                  file: 'green'
                }
                const color = colors[tab]
                const isActive = activeTab === tab
                
                return (
                  <motion.button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex items-center gap-2 px-6 py-2 rounded-md transition-all capitalize ${
                      isActive
                        ? `bg-${color}-500/20 text-${color}-400 border border-${color}-500/50`
                        : 'text-gray-400 hover:text-white'
                    }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {icons[tab]}
                    {tab}
                  </motion.button>
                )
              })}
            </div>
          </div>

          {/* Input Field */}
          <motion.div 
            className="flex gap-3"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={`Masukkan ${activeTab === 'url' ? 'URL' : activeTab === 'email' ? 'email' : 'file'} — contoh: ${
                  activeTab === 'url' ? 'https://suspicious-login.ru' : activeTab === 'email' ? 'phishing@example.com' : 'malware.exe'
                }`}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-12 py-4 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
              />
            </div>
            <motion.button
              onClick={handleScan}
              className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Shield className="w-5 h-5" />
              Scan Sekarang
            </motion.button>
          </motion.div>

          <motion.p 
            className="text-center text-sm text-gray-500 mt-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Coba: suspicious-login.ru · Gratis · Tidak perlu daftar
          </motion.p>
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
  )
}