'use client'

import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Plus,
  Shield
} from 'lucide-react'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import { motion } from 'framer-motion'

export default function DashboardPage() {
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
        <Header title="Dashboard" subtitle="Jumat, 19 Juni 2026" />

        <div className="p-8">
          {/* Stats Grid dengan Stagger Animation */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {[
              {
                icon: <Activity className="w-5 h-5 text-cyan-400" />,
                label: "Total Scan",
                value: "0",
                subtext: "Belum ada scan",
                borderColor: "border-cyan-500/20",
                bgColor: "bg-cyan-500/10",
                hoverBorder: "hover:border-cyan-500/50"
              },
              {
                icon: <AlertTriangle className="w-5 h-5 text-red-400" />,
                label: "Ancaman Terdeteksi",
                value: "0",
                subtext: "Belum ada data",
                borderColor: "border-red-500/20",
                bgColor: "bg-red-500/10",
                hoverBorder: "hover:border-red-500/50"
              },
              {
                icon: <CheckCircle className="w-5 h-5 text-green-400" />,
                label: "Scan Aman",
                value: "0",
                subtext: "Belum ada data",
                borderColor: "border-green-500/20",
                bgColor: "bg-green-500/10",
                hoverBorder: "hover:border-green-500/50"
              },
              {
                icon: <XCircle className="w-5 h-5 text-purple-400" />,
                label: "Scan Berbahaya",
                value: "0",
                subtext: "Belum ada data",
                borderColor: "border-purple-500/20",
                bgColor: "bg-purple-500/10",
                hoverBorder: "hover:border-purple-500/50"
              }
            ].map((stat, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.2 + idx * 0.1 }}
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
              >
                <StatCard {...stat} />
              </motion.div>
            ))}
          </motion.div>

          {/* Main Content Area dengan Animasi */}
          <motion.div 
            className="bg-[#0d1117] border border-white/5 rounded-xl p-12"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <p className="text-xs text-gray-500 mb-8">Hasil scan terbaru dari akun Anda</p>
            
            <div className="text-center py-12">
              <motion.div 
                className="w-16 h-16 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4"
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ duration: 0.6, delay: 0.7, type: "spring", stiffness: 200 }}
              >
                <Shield className="w-8 h-8 text-cyan-400" />
              </motion.div>
              
              <motion.h3 
                className="text-xl font-bold mb-2"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
              >
                Belum ada scan
              </motion.h3>
              
              <motion.p 
                className="text-gray-400 mb-6 max-w-md mx-auto text-sm"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.9 }}
              >
                Hasil scan akan muncul di sini setelah Anda melakukan pemeriksaan URL, email, atau file.
              </motion.p>
              
              <motion.button 
                onClick={() => window.location.href = '/'}
                className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2 mx-auto"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Plus className="w-4 h-4" />
                Mulai Scan Pertama
              </motion.button>
            </div>
          </motion.div>

          {/* Info Banner dengan Animasi */}
          <motion.div 
            className="mt-6 bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
          >
            <div className="flex items-start gap-4">
              <motion.div 
                className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center flex-shrink-0"
                whileHover={{ rotate: 360 }}
                transition={{ duration: 0.6 }}
              >
                <Activity className="w-5 h-5 text-cyan-400" />
              </motion.div>
              <div>
                <h4 className="font-semibold text-cyan-400 mb-1">Menunggu aktivitas scan pertama</h4>
                <p className="text-gray-400 text-sm">
                  Dashboard ini akan menampilkan ringkasan dan riwayat scan Anda secara otomatis setelah Anda melakukan scan pertama. 
                  Klik <strong>Scan Baru</strong> di sidebar untuk memulai.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </main>
    </motion.div>
  )
}

function StatCard({ icon, label, value, subtext, borderColor, bgColor, hoverBorder }: any) {
  return (
    <div className={`bg-[#0d1117] border ${borderColor} ${hoverBorder} rounded-xl p-6 transition-all group`}>
      <motion.div 
        className={`w-10 h-10 ${bgColor} rounded-lg flex items-center justify-center mb-4`}
        whileHover={{ scale: 1.1, rotate: 5 }}
        transition={{ duration: 0.2 }}
      >
        {icon}
      </motion.div>
      <h3 className="text-3xl font-bold mb-1">{value}</h3>
      <p className="text-sm font-medium text-gray-300 mb-1">{label}</p>
      <p className="text-xs text-gray-500">{subtext}</p>
    </div>
  )
}