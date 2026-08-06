'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Link, Mail, File, Loader2, Search } from 'lucide-react';

interface ScanFormProps {
  onScan: (
    type: 'url' | 'email' | 'file',
    value: string,
    file?: File,
    mendalam?: boolean,
  ) => void;
  loading?: boolean;
}

export function ScanForm({ onScan, loading = false }: ScanFormProps) {
  const [activeTab, setActiveTab] = React.useState<'url' | 'email' | 'file'>('url');
  const [inputValue, setInputValue] = React.useState('');
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  // Pemeriksaan mendalam benar-benar MEMBUKA alamatnya untuk mengambil bukti.
  // Bawaannya mati karena butuh 3-13 detik, dan pengguna berhak memilih
  // sendiri kapan menunggu selama itu sepadan.
  const [mendalam, setMendalam] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (loading) return;

    if (activeTab === 'file') {
      if (selectedFile) {
        onScan(activeTab, selectedFile.name, selectedFile);
      }
    } else {
      if (inputValue.trim()) {
        onScan(activeTab, inputValue.trim(), undefined,
               activeTab === 'url' ? mendalam : false);
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setInputValue(file.name);
    }
  };

  const getPlaceholder = () => {
    switch (activeTab) {
      case 'url':
        return 'https://suspicious-login.ru';
      case 'email':
        // Yang diperiksa adalah ISI email, bukan alamat pengirimnya saja.
        // Sebelumnya kolom ini meminta alamat email ("phishing@example.com"),
        // padahal backend menganalisis header dan isi surat lengkap - jadi
        // apa pun yang diketik pengguna tidak pernah bisa dinilai benar.
        return 'Tempel seluruh isi email di sini, termasuk baris From: dan Subject: bila ada';
      case 'file':
        return 'Pilih file untuk di-scan';
    }
  };

  const getExampleText = () => {
    switch (activeTab) {
      case 'url':
        return 'Coba: suspicious-login.ru';
      case 'email':
        return 'Tip: di Gmail buka menu ⋮ → "Show original" agar header ikut tersalin';
      case 'file':
        return 'Format: PDF, DOCX, EXE, ZIP (max 10MB)';
    }
  };

  const tabColors = {
    url: 'cyan',
    email: 'purple',
    file: 'green',
  };

  const activeColor = tabColors[activeTab];

  return (
    <form onSubmit={handleSubmit} className="w-full">
      {/* Tab Selector */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex bg-white/5 border border-white/10 rounded-lg p-1 gap-1">
          {(['url', 'email', 'file'] as const).map((tab) => {
            const icons = {
              url: <Link className="w-4 h-4" />,
              email: <Mail className="w-4 h-4" />,
              file: <File className="w-4 h-4" />,
            };
            const color = tabColors[tab];
            const isActive = activeTab === tab;

            return (
              <motion.button
                key={tab}
                type="button"
                onClick={() => {
                  setActiveTab(tab);
                  setInputValue('');
                  setSelectedFile(null);
                }}
                disabled={loading}
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
            );
          })}
        </div>
      </div>

      {/* Input Field */}
      {/*
        items-start supaya tombol Scan tidak ikut memanjang mengikuti tinggi
        textarea email yang 8 baris.
      */}
      <motion.div
        className="flex gap-3 items-start"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
      >
        <div className="flex-1 relative">
          {activeTab === 'file' ? (
            <>
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileSelect}
                className="hidden"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.exe,.dll,.zip,.rar,.txt,.js,.vbs,.ps1"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-12 py-4 text-left text-gray-400 hover:border-white/20 transition-colors flex items-center gap-3"
              >
                <File className="w-5 h-5 flex-shrink-0" />
                <span className="truncate">
                  {selectedFile ? selectedFile.name : getPlaceholder()}
                </span>
              </button>
            </>
          ) : activeTab === 'email' ? (
            /*
              Email dipisah dari URL karena bentuk masukannya beda jauh:
              URL cuma sebaris, sedangkan email bisa puluhan baris berisi
              header, isi surat, dan tautan. Memaksakan keduanya ke satu
              kotak sebaris membuat email tidak mungkin ditempel utuh.
            */
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={getPlaceholder()}
              disabled={loading}
              rows={8}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-4 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 transition-colors disabled:opacity-50 font-mono text-sm resize-y"
            />
          ) : (
            <>
              <Shield className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={getPlaceholder()}
                disabled={loading}
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-12 pr-4 py-4 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-colors disabled:opacity-50"
              />
            </>
          )}
        </div>
        <motion.button
          type="submit"
          disabled={loading || (activeTab === 'file' ? !selectedFile : !inputValue.trim())}
          className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          whileHover={{ scale: loading ? 1 : 1.05 }}
          whileTap={{ scale: loading ? 1 : 0.95 }}
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Memindai...
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              Scan Sekarang
            </>
          )}
        </motion.button>
      </motion.div>

      {/* Hidden file input */}
      {activeTab === 'file' && (
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.xls,.xlsx,.exe,.dll,.zip,.rar,.txt,.js,.vbs,.ps1"
        />
      )}

      {/* Sakelar pemeriksaan mendalam - hanya untuk URL.
          Email dan file tidak punya "alamat untuk dibuka", jadi pilihan ini
          tidak berarti apa-apa di sana dan sengaja disembunyikan daripada
          ditampilkan tapi tidak berfungsi. */}
      {activeTab === 'url' && (
        <motion.div
          className="mt-5 flex items-start justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <label className="flex items-start gap-3 cursor-pointer max-w-xl">
            <button
              type="button"
              role="switch"
              aria-checked={mendalam}
              aria-label="Pemeriksaan mendalam"
              onClick={() => setMendalam((v) => !v)}
              className={`mt-0.5 w-11 h-6 rounded-full p-0.5 flex-shrink-0 transition-colors ${
                mendalam ? 'bg-cyan-500' : 'bg-white/10'
              }`}
            >
              <motion.div
                className="w-5 h-5 bg-white rounded-full"
                animate={{ x: mendalam ? 20 : 0 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            </button>

            <span className="text-left">
              <span className="flex items-center gap-1.5 text-sm font-medium text-gray-200">
                <Search className="w-3.5 h-3.5 text-cyan-400" />
                Pemeriksaan mendalam
              </span>
              <span className="block text-xs text-gray-500 mt-0.5 leading-relaxed">
                {mendalam
                  ? 'Alamatnya akan dibuka untuk mengambil bukti: umur domain, negara server, sertifikat, dan isi halaman. Butuh 3-13 detik.'
                  : 'Hanya membaca nama domain (cepat, di bawah 1 detik). Nyalakan untuk bukti yang lebih meyakinkan.'}
              </span>
            </span>
          </label>
        </motion.div>
      )}

      <motion.p
        className="text-center text-sm text-gray-500 mt-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {getExampleText()} · Gratis · Tidak perlu daftar
      </motion.p>
    </form>
  );
}
