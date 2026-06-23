'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Search, 
  Download, 
  Plus,
  Shield,
  ArrowUpDown,
  Link,
  Mail,
  FileText,
  Eye,
  Trash2
} from 'lucide-react'
import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'

export default function HistoryPage() {
  const [typeFilter, setTypeFilter] = useState<'semua' | 'url' | 'email' | 'file'>('semua')
  const [statusFilter, setStatusFilter] = useState<'semua' | 'aman' | 'mencurigakan' | 'berbahaya'>('semua')

  const typeFilters = [
    { id: 'semua', label: 'Semua' },
    { id: 'url', label: 'URL' },
    { id: 'email', label: 'Email' },
    { id: 'file', label: 'File' },
  ]

  const statusFilters = [
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
        <Header title="Riwayat Scan" subtitle="Jumat, 19 Juni 2026" />

        <div className="p-8">
          {/* Filter Bar dengan Animasi */}
          <motion.div 
            className="flex items-center gap-4 mb-6 flex-wrap"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {/* Search */}
            <motion.div 
              className="relative flex-1 min-w-[300px]"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
            >
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Cari URL, email, file..."
                className="w-full bg-[#0d1117] border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-colors"
              />
            </motion.div>

            {/* Type Filter */}
            <motion.div 
              className="flex bg-[#0d1117] border border-white/10 rounded-lg p-1"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
            >
              {typeFilters.map((filter, idx) => (
                <motion.button
                  key={filter.id}
                  onClick={() => setTypeFilter(filter.id as any)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                    typeFilter === filter.id
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                      : 'text-gray-400 hover:text-white'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.3 + idx * 0.05 }}
                >
                  {filter.label}
                </motion.button>
              ))}
            </motion.div>

            {/* Status Filter */}
            <motion.div 
              className="flex bg-[#0d1117] border border-white/10 rounded-lg p-1"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
            >
              {statusFilters.map((filter, idx) => (
                <motion.button
                  key={filter.id}
                  onClick={() => setStatusFilter(filter.id as any)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                    statusFilter === filter.id
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                      : 'text-gray-400 hover:text-white'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.4 + idx * 0.05 }}
                >
                  {filter.label}
                </motion.button>
              ))}
            </motion.div>

            {/* Export Button */}
            <motion.button 
              className="ml-auto px-4 py-2.5 bg-[#0d1117] border border-white/10 rounded-lg text-sm font-medium hover:bg-white/5 transition-all flex items-center gap-2"
              whileHover={{ scale: 1.05, backgroundColor: 'rgba(255,255,255,0.1)' }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.5 }}
            >
              <Download className="w-4 h-4" />
              Ekspor CSV
            </motion.button>
          </motion.div>

          {/* Table Container dengan Animasi */}
          <motion.div 
            className="bg-[#0d1117] border border-white/5 rounded-xl overflow-hidden"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            {/* Table Header */}
            <motion.div 
              className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-white/5 text-xs font-semibold text-gray-400 uppercase tracking-wider"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, delay: 0.6 }}
            >
              <div className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-white transition-colors">
                Tanggal <ArrowUpDown className="w-3 h-3" />
              </div>
              <div className="col-span-1">Tipe</div>
              <div className="col-span-5">Input</div>
              <div className="col-span-1 flex items-center gap-1 cursor-pointer hover:text-white transition-colors">
                Skor <ArrowUpDown className="w-3 h-3" />
              </div>
              <div className="col-span-2">Status</div>
              <div className="col-span-1 text-right">Aksi</div>
            </motion.div>

            {/* Empty State dengan Animasi */}
            <div className="py-20 text-center">
              <motion.div 
                className="w-16 h-16 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4"
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ duration: 0.6, delay: 0.7, type: "spring", stiffness: 200 }}
                whileHover={{ scale: 1.1, rotate: 5 }}
              >
                <Shield className="w-8 h-8 text-cyan-400" />
              </motion.div>
              
              <motion.h3 
                className="text-xl font-bold mb-2"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.4 }}
              >
                Belum ada riwayat scan
              </motion.h3>
              
              <motion.p 
                className="text-gray-400 mb-6 text-sm"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.9, duration: 0.4 }}
              >
                Riwayat scan Anda akan muncul di sini<br />
                setelah melakukan pemindaian pertama.
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
                Mulai Scan
              </motion.button>
            </div>
          </motion.div>
        </div>
      </main>
    </motion.div>
  )
}