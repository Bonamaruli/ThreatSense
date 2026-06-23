'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Shield, 
  ArrowLeft, 
  ArrowRight,
  Eye, 
  Lock, 
  Zap,
  Globe, 
  Brain, 
  Code,
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  Mail, 
  FileText,
  Database,
  Cpu,
  RefreshCw,
  ChevronDown,
  Server
} from 'lucide-react'

export default function AboutPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  const faqs = [
    {
      question: 'Apakah ThreatSense gratis?',
      answer: 'Ya, ThreatSense sepenuhnya gratis untuk digunakan. Tidak diperlukan akun atau pembayaran untuk melakukan scan URL, email, maupun file.'
    },
    {
      question: 'Apakah data yang saya scan disimpan?',
      answer: 'Tidak. Kami tidak menyimpan konten yang Anda kirimkan. Setiap permintaan scan diproses secara stateless — setelah hasilnya dikembalikan, data Anda tidak kami pertahankan di server.'
    },
    {
      question: 'Seberapa akurat model AI ThreatSense?',
      answer: 'Model kami mencapai akurasi lebih dari 99% pada dataset pengujian internal. Namun, seperti sistem AI lainnya, tidak ada jaminan 100%. Selalu gunakan penilaian Anda sendiri sebagai lapisan keamanan tambahan.'
    },
    {
      question: 'Apa itu SHAP dan mengapa itu penting?',
      answer: 'SHAP (SHapley Additive exPlanations) adalah metode untuk menjelaskan prediksi model AI. Dengan SHAP, Anda bisa melihat faktor apa saja yang membuat sistem menilai sebuah URL atau file sebagai berbahaya — bukan sekadar skor buta.'
    },
    {
      question: 'Apakah ThreatSense bisa mendeteksi ancaman zero-day?',
      answer: 'ThreatSense menggunakan analisis berbasis perilaku dan fitur struktural, bukan hanya pencocokan signature. Ini memungkinkan deteksi ancaman baru yang belum ada dalam database, meskipun efektivitasnya bervariasi tergantung pola ancaman.'
    },
    {
      question: 'Bagaimana cara melaporkan false positive atau false negative?',
      answer: 'Jika Anda menemukan hasil yang tidak akurat, gunakan tombol \'Bagikan\' di halaman hasil scan dan kirimkan laporan ke tim kami. Laporan ini membantu meningkatkan kualitas model secara berkelanjutan.'
    }
  ]

  const scanTypes = [
    {
      icon: <Globe className="w-6 h-6 text-cyan-400" />,
      title: 'URL Scanner',
      color: 'cyan',
      features: [
        'Deteksi phishing & typosquatting',
        'Analisis reputasi domain',
        'Pemeriksaan rantai redirect',
        'Validasi sertifikat SSL/TLS',
        'Deteksi malware & drive-by download'
      ]
    },
    {
      icon: <Mail className="w-6 h-6 text-purple-400" />,
      title: 'Email Scanner',
      color: 'purple',
      features: [
        'Verifikasi pengirim & SPF/DKIM',
        'Deteksi spoofing & impersonasi',
        'Analisis tautan dalam badan email',
        'Pemeriksaan header mencurigakan',
        'Skor risiko keseluruhan email'
      ]
    },
    {
      icon: <FileText className="w-6 h-6 text-green-400" />,
      title: 'File Scanner',
      color: 'green',
      features: [
        'Analisis statis PE/ELF binary',
        'Pemeriksaan macro berbahaya (Office)',
        'Deteksi JavaScript berbahaya (PDF)',
        'Identifikasi pola ransomware',
        'Hash lookup ke database malware'
      ]
    }
  ]

  const techStack = [
    {
      icon: <Brain className="w-6 h-6 text-purple-400" />,
      title: 'Model Machine Learning',
      description: 'Menggunakan ensemble dari Gradient Boosting dan Neural Network yang dilatih dengan dataset ancaman yang diperbarui secara berkala. Akurasi deteksi mencapai lebih dari 99%.'
    },
    {
      icon: <Code className="w-6 h-6 text-cyan-400" />,
      title: 'Explainability (SHAP)',
      description: 'Setiap prediksi dilengkapi nilai SHAP (SHapley Additive exPlanations) untuk menjelaskan kontribusi tiap fitur terhadap skor risiko akhir.'
    },
    {
      icon: <Server className="w-6 h-6 text-green-400" />,
      title: 'Infrastruktur Real-time',
      description: 'API dibangun di atas arsitektur serverless dengan latensi rata-rata di bawah 200ms. Sistem otomatis melakukan scale untuk menangani lonjakan permintaan.'
    },
    {
      icon: <RefreshCw className="w-6 h-6 text-amber-400" />,
      title: 'Pembaruan Model Berkala',
      description: 'Database ancaman dan model AI diperbarui secara rutin menggunakan data intelijen ancaman dari berbagai sumber terpercaya untuk menjaga relevansi deteksi.'
    }
  ]

  const riskExamples = [
    { domain: 'github.com', score: 3, label: 'Aman', color: 'green', percentage: 3 },
    { domain: 'support@amazon-orders.xyz', score: 58, label: 'Mencurigakan', color: 'amber', percentage: 58 },
    { domain: 'paypal-secure.xyz/login', score: 91, label: 'Berbahaya', color: 'red', percentage: 91 }
  ]

  const getColorClasses = (color: string) => {
    const classes: any = {
      cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', dot: 'bg-cyan-400', border: 'border-cyan-500/20' },
      purple: { bg: 'bg-purple-500/10', text: 'text-purple-400', dot: 'bg-purple-400', border: 'border-purple-500/20' },
      green: { bg: 'bg-green-500/10', text: 'text-green-400', dot: 'bg-green-400', border: 'border-green-500/20' },
      amber: { bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-400', border: 'border-amber-500/20' },
      red: { bg: 'bg-red-500/10', text: 'text-red-400', dot: 'bg-red-400', border: 'border-red-500/20' }
    }
    return classes[color] || classes.cyan
  }

  return (
    <motion.div 
      className="min-h-screen bg-[#0a0a0f] text-white relative overflow-x-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
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
      
      {/* Gradient Orbs dengan Animasi */}
      <motion.div 
        className="fixed top-0 right-0 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl pointer-events-none"
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
        className="fixed bottom-0 left-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"
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

      {/* Top Navigation dengan Animasi */}
      <motion.nav 
        className="relative z-10 border-b border-white/5 backdrop-blur-xl bg-black/50"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <motion.a 
            href="/" 
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            whileHover={{ x: -4 }}
            whileTap={{ scale: 0.95 }}
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Kembali</span>
          </motion.a>

          <motion.a 
            href="/" 
            className="flex items-center gap-2"
            whileHover={{ scale: 1.05 }}
          >
            <Shield className="w-6 h-6 text-cyan-400" />
            <span className="text-xl font-bold">
              Threat<span className="text-cyan-400">Sense</span>
            </span>
          </motion.a>

          <motion.a 
            href="/" 
            className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-medium hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2 text-sm"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Mulai Scan
            <ArrowRight className="w-4 h-4" />
          </motion.a>
        </div>
      </motion.nav>

      <main className="relative z-10 max-w-6xl mx-auto px-6 py-16">
        {/* Hero Section dengan Animasi */}
        <motion.div 
          className="text-center mb-20"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <motion.div 
            className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full mb-8"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <Shield className="w-4 h-4 text-cyan-400" />
            <span className="text-sm font-medium text-cyan-400">Tentang ThreatSense</span>
          </motion.div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Platform Verifikasi Ancaman
            <br />
            <motion.span 
              className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5, duration: 0.6 }}
            >
              Berbasis AI
            </motion.span>
          </h1>

          <motion.p 
            className="text-lg text-gray-400 max-w-3xl mx-auto leading-relaxed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.6 }}
          >
            ThreatSense adalah platform gratis untuk memverifikasi keamanan URL, email, dan file menggunakan model kecerdasan buatan. Kami hadir untuk membantu pengguna dan organisasi mendeteksi ancaman siber sebelum berdampak.
          </motion.p>
        </motion.div>

        {/* Value Propositions dengan Stagger Animation */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-24"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          {[
            {
              icon: <Eye className="w-6 h-6 text-cyan-400" />,
              title: 'Transparansi',
              desc: 'Setiap prediksi AI kami disertai penjelasan SHAP sehingga Anda tahu persis mengapa sesuatu dianggap berbahaya.',
              hoverBorder: 'hover:border-cyan-500/20'
            },
            {
              icon: <Lock className="w-6 h-6 text-purple-400" />,
              title: 'Privasi',
              desc: 'Kami tidak menyimpan konten yang Anda scan. Setiap permintaan diproses secara stateless dan tidak dipersistensikan.',
              hoverBorder: 'hover:border-purple-500/20'
            },
            {
              icon: <Zap className="w-6 h-6 text-green-400" />,
              title: 'Kecepatan',
              desc: 'Hasil analisis tersedia dalam hitungan detik. Infrastruktur kami dioptimalkan untuk latensi rendah di seluruh wilayah.',
              hoverBorder: 'hover:border-green-500/20'
            }
          ].map((item, idx) => (
            <motion.div
              key={idx}
              className={`bg-[#0d1117] border border-white/5 rounded-xl p-8 ${item.hoverBorder} transition-all`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + idx * 0.1, duration: 0.6 }}
              whileHover={{ y: -5 }}
            >
              <motion.div 
                className="w-12 h-12 bg-cyan-500/10 border border-cyan-500/20 rounded-lg flex items-center justify-center mb-6"
                whileHover={{ rotate: 5, scale: 1.1 }}
                transition={{ duration: 0.2 }}
              >
                {item.icon}
              </motion.div>
              <h3 className="text-xl font-bold mb-3">{item.title}</h3>
              <p className="text-gray-400 leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Cara Kerja dengan Animasi */}
        <motion.div 
          className="mb-24"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
        >
          <motion.div 
            className="text-center mb-12"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
          >
            <h2 className="text-4xl font-bold mb-4">Cara Kerja</h2>
            <p className="text-gray-400">Proses verifikasi berlangsung dalam tiga tahap otomatis</p>
          </motion.div>

          <div className="space-y-4">
            {[
              {
                icon: <Globe className="w-6 h-6 text-cyan-400" />,
                step: 'Langkah 01',
                title: 'Input & Pengumpulan Data',
                desc: 'Anda memasukkan URL, email, atau file. Sistem kami mengumpulkan metadata: informasi domain, catatan DNS, data reputasi IP, rantai pengalihan, dan konten halaman.',
                color: 'cyan'
              },
              {
                icon: <Brain className="w-6 h-6 text-purple-400" />,
                step: 'Langkah 02',
                title: 'Analisis Model AI',
                desc: 'Data dikirimkan ke model machine learning yang terlatih dengan jutaan sampel ancaman. Model mengekstraksi lebih dari 40 fitur dan menghasilkan skor risiko 0–100.',
                color: 'purple'
              },
              {
                icon: <Code className="w-6 h-6 text-green-400" />,
                step: 'Langkah 03',
                title: 'Hasil & Penjelasan SHAP',
                desc: 'Anda menerima skor risiko berwarna (hijau/kuning/merah), rincian ancaman per kategori, dan grafik SHAP yang menjelaskan faktor paling berpengaruh terhadap prediksi.',
                color: 'green'
              }
            ].map((step, idx) => (
              <motion.div
                key={idx}
                className={`bg-[#0d1117] border border-white/5 rounded-xl p-8 hover:border-${step.color}-500/20 transition-all`}
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + idx * 0.15, duration: 0.6 }}
                whileHover={{ x: 5 }}
              >
                <div className="flex items-start gap-6">
                  <motion.div 
                    className={`w-12 h-12 bg-${step.color}-500/10 border border-${step.color}-500/20 rounded-lg flex items-center justify-center flex-shrink-0`}
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.6 }}
                  >
                    {step.icon}
                  </motion.div>
                  <div className="flex-1">
                    <p className={`text-xs font-bold text-${step.color}-400 uppercase tracking-wider mb-2`}>{step.step}</p>
                    <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                    <p className="text-gray-400 leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Skala Risiko dengan Animasi */}
        <motion.div 
          className="mb-24"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        >
          <motion.div 
            className="text-center mb-12"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
          >
            <h2 className="text-4xl font-bold mb-4">Skala Risiko</h2>
            <p className="text-gray-400">Setiap scan menghasilkan skor 0–100 dengan tiga tingkat klasifikasi</p>
          </motion.div>

          <motion.div 
            className="bg-[#0d1117] border border-white/5 rounded-xl p-8"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1, duration: 0.6 }}
          >
            <div className="space-y-4 mb-8">
              {riskExamples.map((example, idx) => {
                const colors = getColorClasses(example.color)
                return (
                  <motion.div 
                    key={idx} 
                    className="bg-white/5 border border-white/10 rounded-lg p-6"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1.1 + idx * 0.1, duration: 0.5 }}
                    whileHover={{ scale: 1.02 }}
                  >
                    <div className="flex items-center gap-4 mb-4">
                      <motion.div 
                        className={`w-10 h-10 rounded-full flex items-center justify-center ${colors.bg} border ${colors.border}`}
                        whileHover={{ scale: 1.1, rotate: 5 }}
                      >
                        {example.color === 'green' && <CheckCircle className={`w-5 h-5 ${colors.text}`} />}
                        {example.color === 'amber' && <AlertTriangle className={`w-5 h-5 ${colors.text}`} />}
                        {example.color === 'red' && <XCircle className={`w-5 h-5 ${colors.text}`} />}
                      </motion.div>
                      <span className="font-mono text-sm text-gray-300 flex-1">{example.domain}</span>
                      <span className={`font-bold ${colors.text}`}>{example.score}</span>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${colors.bg} ${colors.text} border ${colors.border}`}>
                        {example.label}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                      <motion.div 
                        className={`h-full rounded-full ${
                          example.color === 'green' ? 'bg-green-500' :
                          example.color === 'amber' ? 'bg-amber-500' : 'bg-red-500'
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${example.percentage}%` }}
                        transition={{ delay: 1.2 + idx * 0.1, duration: 0.8, ease: "easeOut" }}
                      />
                    </div>
                  </motion.div>
                )
              })}
            </div>

            <motion.div 
              className="grid grid-cols-3 gap-4 pt-6 border-t border-white/10"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.5 }}
            >
              <div className="text-center">
                <div className="inline-block px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full text-green-400 text-xs font-bold mb-2">
                  0 – 30
                </div>
                <p className="font-bold mb-1">Aman</p>
                <p className="text-xs text-gray-500">Tidak terdeteksi ancaman signifikan</p>
              </div>
              <div className="text-center">
                <div className="inline-block px-3 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-400 text-xs font-bold mb-2">
                  31 – 70
                </div>
                <p className="font-bold mb-1">Mencurigakan</p>
                <p className="text-xs text-gray-500">Ada sinyal yang perlu diwaspadai</p>
              </div>
              <div className="text-center">
                <div className="inline-block px-3 py-1 bg-red-500/10 border border-red-500/20 rounded-full text-red-400 text-xs font-bold mb-2">
                  71 – 100
                </div>
                <p className="font-bold mb-1">Berbahaya</p>
                <p className="text-xs text-gray-500">Ancaman tinggi, jangan dikunjungi</p>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Tipe Scan dengan Stagger Animation */}
        <motion.div 
          className="mb-24"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1 }}
        >
          <motion.div 
            className="text-center mb-12"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.1 }}
          >
            <h2 className="text-4xl font-bold mb-4">Tipe Scan yang Didukung</h2>
            <p className="text-gray-400">ThreatSense mendukung tiga jenis pemeriksaan ancaman</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {scanTypes.map((type, idx) => {
              const colors = getColorClasses(type.color)
              return (
                <motion.div 
                  key={idx} 
                  className="bg-[#0d1117] border border-white/5 rounded-xl p-8 hover:border-white/10 transition-all"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.2 + idx * 0.1, duration: 0.6 }}
                  whileHover={{ y: -5 }}
                >
                  <motion.div 
                    className={`w-12 h-12 ${colors.bg} border ${colors.border} rounded-lg flex items-center justify-center mb-6`}
                    whileHover={{ scale: 1.1, rotate: 5 }}
                  >
                    {type.icon}
                  </motion.div>
                  <h3 className="text-xl font-bold mb-4">{type.title}</h3>
                  <ul className="space-y-3">
                    {type.features.map((feature, fIdx) => (
                      <motion.li 
                        key={fIdx} 
                        className="flex items-start gap-3 text-sm text-gray-400"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 1.3 + idx * 0.1 + fIdx * 0.05 }}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${colors.dot} flex-shrink-0 mt-1.5`} />
                        {feature}
                      </motion.li>
                    ))}
                  </ul>
                </motion.div>
              )
            })}
          </div>
        </motion.div>

        {/* Teknologi dengan Animasi */}
        <motion.div 
          className="mb-24"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.3 }}
        >
          <motion.div 
            className="text-center mb-12"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.4 }}
          >
            <h2 className="text-4xl font-bold mb-4">Teknologi di Balik ThreatSense</h2>
            <p className="text-gray-400">Stack AI dan infrastruktur yang mendukung deteksi real-time</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {techStack.map((tech, idx) => {
              const colors = getColorClasses(
                idx === 0 ? 'purple' : idx === 1 ? 'cyan' : idx === 2 ? 'green' : 'amber'
              )
              return (
                <motion.div 
                  key={idx} 
                  className="bg-[#0d1117] border border-white/5 rounded-xl p-8 hover:border-white/10 transition-all"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.5 + idx * 0.1, duration: 0.6 }}
                  whileHover={{ y: -5 }}
                >
                  <motion.div 
                    className={`w-12 h-12 ${colors.bg} border ${colors.border} rounded-lg flex items-center justify-center mb-6`}
                    whileHover={{ scale: 1.1, rotate: 5 }}
                  >
                    {tech.icon}
                  </motion.div>
                  <h3 className="text-xl font-bold mb-3">{tech.title}</h3>
                  <p className="text-gray-400 leading-relaxed">{tech.description}</p>
                </motion.div>
              )
            })}
          </div>
        </motion.div>

        {/* FAQ dengan Accordion Animation */}
        <motion.div 
          className="mb-24"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.6 }}
        >
          <motion.div 
            className="text-center mb-12"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.7 }}
          >
            <h2 className="text-4xl font-bold mb-4">Pertanyaan Umum</h2>
          </motion.div>

          <motion.div 
            className="bg-[#0d1117] border border-white/5 rounded-xl overflow-hidden"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1.8, duration: 0.6 }}
          >
            {faqs.map((faq, idx) => (
              <motion.div 
                key={idx} 
                className={idx !== 0 ? 'border-t border-white/5' : ''}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.9 + idx * 0.05 }}
              >
                <motion.button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full px-8 py-6 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
                  whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                >
                  <span className="font-semibold pr-4">{faq.question}</span>
                  <motion.div
                    animate={{ rotate: openFaq === idx ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  </motion.div>
                </motion.button>
                <motion.div
                  initial={false}
                  animate={{
                    height: openFaq === idx ? 'auto' : 0,
                    opacity: openFaq === idx ? 1 : 0
                  }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-8 pb-6">
                    <p className="text-gray-400 leading-relaxed">{faq.answer}</p>
                  </div>
                </motion.div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>

        {/* CTA Section dengan Animasi */}
        <motion.div 
          className="bg-gradient-to-br from-cyan-500/10 via-transparent to-purple-500/10 border border-cyan-500/20 rounded-2xl p-12 text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 2 }}
          whileHover={{ scale: 1.02 }}
        >
          <motion.div 
            className="w-16 h-16 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6"
            whileHover={{ rotate: 360 }}
            transition={{ duration: 0.6 }}
          >
            <Shield className="w-8 h-8 text-cyan-400" />
          </motion.div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Siap Melindungi Diri dari Ancaman?</h2>
          <p className="text-gray-400 mb-8 max-w-xl mx-auto">
            Mulai scan pertama Anda sekarang — gratis, tanpa registrasi, hasil instan.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <motion.a 
              href="/" 
              className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all inline-flex items-center justify-center gap-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Shield className="w-5 h-5" />
              Mulai Scan Sekarang
            </motion.a>
            <motion.a 
              href="/dashboard" 
              className="px-8 py-3 bg-white/5 border border-white/10 rounded-lg font-semibold hover:bg-white/10 transition-all inline-flex items-center justify-center gap-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Buka Dashboard
              <ArrowRight className="w-5 h-5" />
            </motion.a>
          </div>
        </motion.div>

        {/* Footer dengan Animasi */}
        <motion.footer 
          className="text-center pt-8 border-t border-white/5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2.2, duration: 0.6 }}
        >
          <div className="flex items-center justify-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-cyan-400" />
            <span className="font-bold">
              Threat<span className="text-cyan-400">Sense</span>
            </span>
          </div>
          <p className="text-sm text-gray-500">
            © 2026 ThreatSense · Platform verifikasi ancaman siber berbasis AI
          </p>
        </motion.footer>
      </main>
    </motion.div>
  )
}